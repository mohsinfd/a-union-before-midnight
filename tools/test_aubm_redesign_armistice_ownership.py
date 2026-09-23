"""Authored-state checks, not native queue or peace simulation."""
import unittest
from pathlib import Path
from dh_save_spans import parse, walk
from aubm_redesign_peace_scope import transform as peace, actions
from aubm_redesign_armistice_ownership import (
    transform, REGISTRY, MODULE, OUT, target, retry, COUNTRIES, lifecycle_ids)
from test_aubm_redesign_withdrawal import State, evaluate, bookkeeping


class OwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).resolve().parents[1]/'mod/db/events/aubm_v4'/MODULE
        cls.source={MODULE:p.read_bytes().decode('latin1')}
        cls.before,_=peace(cls.source)
        cls.output,cls.records=transform(cls.before)
        cls.events={int(e.get('id')):e for e in parse(cls.output[MODULE]).all('event')}
        cls.original={int(e.get('id')):e for e in parse(cls.before[MODULE]).all('event')}

    def state(self,c=None):
        c=c or COUNTRIES[0]
        return State(flags={OUT,target(c),'ind_aubm_global_current_'+c.key},
                     countries={'IND',c.tag},wars={frozenset(('IND',c.tag))},
                     owners={c.capital:c.tag},controllers={c.capital:'IND'})

    def test_all_210_families_covered_no_new_ids_idempotent(self):
        self.assertEqual(1680,len(self.records))
        self.assertEqual(set(REGISTRY),set(self.records))
        self.assertEqual(set(self.events),set(self.original))
        self.assertEqual(self.output,transform(self.output)[0])
        self.assertTrue(all(not r[0]['engine_tested'] for r in self.records.values()))

    def test_withdrawal_preserves_battlefield_and_has_only_existing_timer(self):
        for i,c in enumerate(COUNTRIES):
            ids=lifecycle_ids(i);s=self.state(c)
            marks={'ind_aubm_global_'+x+'_'+c.key for x in ('pending','active','victory','current','suspended')}
            s.flags |= marks
            a=next(a for a in actions(self.events[ids.accept]) if a.get('name')=='Withdraw offer - retry in 90 days')
            effects=bookkeeping(a,s)
            self.assertTrue(marks <= s.flags)
            self.assertNotIn(OUT,s.flags);self.assertNotIn(target(c),s.flags)
            self.assertIn(retry(c),s.flags)
            self.assertEqual({'setflag','clrflag','event'},{x[0] for x in effects})
            q=next(x for x in a.all('command') if x.get('type')=='event')
            self.assertEqual((str(ids.retry_release),'90','IND'),(q.get('which'),q.get('when'),q.get('where')))
            request=actions(self.events[ids.docket])[0]
            self.assertFalse(evaluate(request.get('trigger'),s))

    def test_old_country_callbacks_cannot_touch_new_country(self):
        a,b=COUNTRIES[:2];ids=lifecycle_ids(0)
        for role in ('normal_response','backed_response','accept','counter','refuse','lapse'):
            s=self.state(b);before=set(s.flags)
            for action in actions(self.events[getattr(ids,role)]):
                self.assertEqual([],bookkeeping(action,s),(role,action.get('name')))
            self.assertEqual(before,s.flags)

    def test_retry_release_only_owns_retry_not_another_offer(self):
        a,b=COUNTRIES[:2];ids=lifecycle_ids(0)
        s=self.state(b);s.flags.add(retry(a));before=set(s.flags)
        effects=bookkeeping(actions(self.events[ids.retry_release])[0],s)
        self.assertEqual([('clrflag',retry(a),None)],effects)
        self.assertEqual(before-{retry(a)},s.flags)
        s=self.state(a);s.flags.add(retry(a))
        self.assertEqual([],bookkeeping(actions(self.events[ids.retry_release])[0],s))

    def test_owned_lapse_audits_then_cools_down_unowned_does_nothing(self):
        c=COUNTRIES[0];ids=lifecycle_ids(0);s=self.state(c)
        s.wars.clear()
        a=actions(self.events[ids.lapse])[0]
        effects=bookkeeping(a,s)
        self.assertNotIn(OUT,s.flags);self.assertNotIn(target(c),s.flags)
        self.assertIn(retry(c),s.flags)
        self.assertIn('ind_aubm_global_suspended_'+c.key,s.flags)
        self.assertNotIn('ind_aubm_global_current_'+c.key,s.flags)
        self.assertIn(('event',str(ids.retry_release),None),effects)
        self.assertEqual([],bookkeeping(a,s))

    def test_no_owner_close_is_effect_free_and_no_foreign_dead_end(self):
        c=COUNTRIES[0];ids=lifecycle_ids(0);s=self.state(c);s.flags.clear()
        for role in ('normal_response','backed_response','accept','counter','refuse','lapse','retry_release'):
            aa=actions(self.events[getattr(ids,role)])
            allowed=[a for a in aa if evaluate(a.get('trigger'),s)]
            self.assertTrue(allowed,role)
            self.assertTrue(all(not a.all('command') for a in allowed),role)

    def test_pending_docket_reachable_after_annexation_without_queue_filters(self):
        for i,c in enumerate(COUNTRIES):
            e=self.events[lifecycle_ids(i).docket];s=self.state(c)
            s.countries.remove(c.tag);s.wars.clear();s.owners.clear();s.controllers.clear()
            self.assertTrue(evaluate(e.get('decision'),s))
            self.assertTrue(evaluate(e.get('decision_trigger'),s))
            for field in ('trigger','date','offset'):self.assertIsNone(e.get(field))
            aa=actions(e)
            self.assertFalse(evaluate(aa[0].get('trigger'),s))
            substantive=[a for a in aa if a.all('command') and evaluate(a.get('trigger'),s)]
            self.assertEqual(['Withdraw offer - retry in 90 days'],[a.get('name') for a in substantive])
            s.flags.remove(target(c))
            self.assertFalse(evaluate(e.get('decision'),s))
            self.assertFalse(evaluate(e.get('decision_trigger'),s))

    def test_current_scope_checked_on_requests_and_foreign_answers(self):
        c=COUNTRIES[0];ids=lifecycle_ids(0)
        for role in ('normal_response','backed_response','accept','counter'):
            s=self.state(c);s.masters[c.tag]='JAP'
            self.assertFalse(evaluate(actions(self.events[getattr(ids,role)])[0].get('trigger'),s))
        s=self.state(c);s.flags-={OUT,target(c)};s.masters[c.tag]='JAP'
        self.assertFalse(evaluate(actions(self.events[ids.docket])[0].get('trigger'),s))

    def test_odds_delays_rewards_preserved_and_queued_persistent(self):
        for i,c in enumerate(COUNTRIES):
            ids=lifecycle_ids(i)
            for role,odds in (('normal_response',['60','25','15']),('backed_response',['75','20','5'])):
                aa=actions(self.events[getattr(ids,role)])
                self.assertEqual(odds,[a.get('ai_chance') for a in aa[:3]])
                self.assertEqual(['3']*3,[a.all('command')[0].get('when') for a in aa[:3]])
            for role in ('accept','counter','refuse'):
                def material(e):
                    return [(x.get('type'),x.get('which'),x.get('value')) for a in actions(e)
                            for x in a.all('command') if x.get('type') not in ('event','setflag','clrflag')]
                self.assertEqual(material(self.original[getattr(ids,role)]),material(self.events[getattr(ids,role)]))
            for role in ('normal_response','backed_response','accept','counter','refuse','lapse','retry_release'):
                e=self.events[getattr(ids,role)]
                self.assertEqual('yes',e.get('persistent'))
                for field in ('trigger','date','offset'):self.assertIsNone(e.get(field))

    def test_bounded_predicates_commands_and_honest_docket_prose(self):
        for eid in self.records:
            e=self.events[eid]
            for a in actions(e):
                self.assertLessEqual(len(a.all('command')),60)
                t=a.get('trigger')
                if t:self.assertLessEqual(t.end-t.start,9999)
                for n in walk(a):
                    for f in n.fields:
                        if f.key in ('OR','AND','NOT'):self.assertTrue(f.value.fields)
            if REGISTRY[eid][1]=='docket':
                self.assertNotIn('converts any formal coalition',e.get('desc'))
                self.assertNotIn('separate peace',e.get('desc'))


if __name__=='__main__':unittest.main()

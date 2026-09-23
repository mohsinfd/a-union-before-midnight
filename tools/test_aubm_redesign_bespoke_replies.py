"""Script-state proofs, not a Darkest Hour queue or diplomacy emulator."""
from pathlib import Path
import copy
import unittest
from dh_save_spans import Node, parse
import aubm_redesign_bespoke_replies as m


def state(tag='PER'):
    return dict(flags={'ind_aubm_regional_current_'+tag.lower()},
        exists={'IND',*m.TARGETS},puppets=set(),participants=set(),leaders=set(),
        wars={tag},owned={p:t for t,p in m.TARGETS.items()},
        control={p:'IND' for p in m.TARGETS.values()},dissent=10,
        access=set(),relations={},queued=[],peace_calls=[],peace_works=True,ai=False)


def evaluate(node,s):
    if node is None:return True
    def one(key,v):
        if key in ('AND','OR','NOT'):
            vals=[one(f.key,f.value) for f in v.fields]
            return all(vals) if key=='AND' else any(vals) if key=='OR' else not any(vals)
        if key=='flag':return v in s['flags']
        if key=='exists':return v in s['exists']
        if key=='ispuppet':return v in s['puppets']
        if key=='participant':return v.get('country') in s['participants']
        if key=='alliance_leader':return v.get('country') in s['leaders']
        if key=='war':return next(t for t in v.all('country') if t!='IND') in s['wars']
        if key in ('owned','control'):return s[key].get(int(v.get('province')))==v.get('data')
        if key=='ai':return s['ai']==(v=='yes')
        raise AssertionError('Unknown predicate '+key)
    return all(one(f.key,f.value) for f in node.fields)


def apply(a,s,country='IND'):
    assert evaluate(a.get('trigger'),s)
    for c in a.all('command'):
        if not evaluate(c.get('trigger'),s):continue
        kind,which=c.get('type'),c.get('which')
        if kind=='setflag':s['flags'].add(which)
        elif kind=='clrflag':s['flags'].discard(which)
        elif kind=='event':s['queued'].append((int(which),c.get('where'),int(c.get('when'))))
        elif kind=='dissent':s['dissent']+=int(c.get('value'))
        elif kind=='relation':s['relations'][country]=s['relations'].get(country,0)+int(c.get('value'))
        elif kind=='access':s['access'].add((country,which))
        elif kind=='peace':
            s['peace_calls'].append((which,c.get('value')))
            if s['peace_works']:s['wars'].discard(which)
        else:raise AssertionError('Unknown command '+kind)


def canon(n):return tuple((f.key,canon(f.value) if isinstance(f.value,Node) else f.value) for f in n.fields)


class BespokeReplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).resolve().parents[1]/'mod/db/events/aubm_v4'/m.MODULE
        cls.source={p.name:p.read_text(encoding='cp1252')}
        cls.output,cls.records=m.transform(cls.source)
        cls.before={int(e.get('id')):e for e in parse(cls.source[p.name]).all('event')}
        cls.after={int(e.get('id')):e for e in parse(cls.output[p.name]).all('event')}

    def aa(self,eid):return [f.value for f in m.actions(self.after[eid])]
    def named(self,eid,name):return next(a for a in self.aa(eid) if a.get('name')==name)
    def offer(self,s,tag):apply(self.aa(next(i for i,t in m.ROOTS.items() if t==tag))[0],s)
    def foreign(self,tag):return next(i for i,t in m.FOREIGN.items() if t==tag)
    def choose(self,s,tag,kind):apply(self.aa(self.foreign(tag))[('full','limited','refused').index(kind)],s,tag)
    def receive(self,s,tag,kind):
        eid={'full':9282288,'limited':9282289,'refused':9282290}[kind]
        apply(self.named(eid,m.NAMES[tag]+': record '+kind+' answer'),s)

    def test_all_eight_accept_counter_lifecycles_no_early_rewards(self):
        for tag in m.TARGETS:
            for kind,reduction in (('full',2),('limited',1)):
                s=state(tag);self.offer(s,tag);self.choose(s,tag,kind);self.receive(s,tag,kind)
                self.assertEqual(s['dissent'],10);self.assertEqual(s['access'],set())
                self.assertEqual(s['relations'],{})
                self.assertNotIn('ind_aubm_global_campaign_victory',s['flags'])
                sign=self.named(9282291,'Sign '+m.NAMES[tag]+' '+kind+' peace')
                apply(sign,s);self.assertEqual(s['dissent'],10)
                self.assertEqual(s['peace_calls'],[(tag,'0')])
                confirm=self.named(9282291,m.NAMES[tag]+': confirm observed '+kind+' peace')
                apply(confirm,s)
                self.assertEqual(s['dissent'],10-reduction)
                self.assertNotIn(m.OUT,s['flags']);self.assertNotIn(m.flag(tag,'target'),s['flags'])
                self.assertIn('ind_aubm_regional_settled_'+tag.lower(),s['flags'])
                self.assertEqual(s['access'],set())
                delivery=self.named(self.foreign(tag),'Deliver the signed '+kind+' settlement')
                apply(delivery,s,tag)
                self.assertEqual(s['access'],{(tag,'IND')} if kind=='full' else set())
                self.assertEqual(s['relations'][tag],30 if kind=='full' else 10)
                self.assertFalse(evaluate(delivery.get('trigger'),s));self.assertFalse(evaluate(confirm.get('trigger'),s))

    def test_failed_peace_cannot_pay_or_mark_settled(self):
        s=state();s['peace_works']=False
        self.offer(s,'PER');self.choose(s,'PER','full');self.receive(s,'PER','full')
        apply(self.named(9282291,'Sign Persia full peace'),s)
        self.assertFalse(evaluate(self.named(9282291,'Persia: confirm observed full peace').get('trigger'),s))
        self.assertEqual(s['dissent'],10);self.assertNotIn('ind_aubm_regional_settled_per',s['flags'])
        apply(self.named(9282291,'Withdraw Persia offer: 90-day wait'),s)
        self.assertIn(m.COOLING,s['flags']);self.assertNotIn(m.OUT,s['flags'])
        self.assertIn(('PER','0'),s['peace_calls'])

    def test_refusal_and_withdrawal_serialize_only_bespoke_cooling(self):
        for tag in m.TARGETS:
            s=state(tag);self.offer(s,tag);self.choose(s,tag,'refused');self.receive(s,tag,'refused')
            self.assertEqual(s['dissent'],11);self.assertIn(m.COOLING,s['flags'])
            self.assertEqual(s['relations'][tag],-30)
            self.assertIn((9282292,'IND',90),s['queued'])
            for root in m.ROOTS:self.assertFalse(evaluate(self.aa(root)[0].get('trigger'),s))
            apply(self.named(9282292,'End '+m.NAMES[tag]+' cooling period'),s)
            self.assertNotIn(m.COOLING,s['flags']);self.assertNotIn(m.flag(tag,'retry'),s['flags'])
            self.assertIn('ind_aubm_regional_current_'+tag.lower(),s['flags'])

    def test_selected_refusal_cannot_escape_cost_by_another_window(self):
        s=state();self.offer(s,'PER');self.choose(s,'PER','refused')
        close=self.aa(9282290)[-1]
        self.assertFalse(evaluate(close.get('trigger'),s))
        apply(self.named(9282270,'Withdraw this offer: 90-day wait'),s)
        self.assertEqual(s['dissent'],11)
        self.assertFalse(evaluate(self.named(9282290,'Persia: record refused answer').get('trigger'),s))

    def test_owned_decision_survives_respondent_disappearance(self):
        for eid,tag in m.ROOTS.items():
            s=state(tag);self.offer(s,tag);s['exists'].discard(tag)
            s['control'][m.TARGETS[tag]]='CHI';s['owned'][m.TARGETS[tag]]='CHI'
            self.assertTrue(evaluate(self.after[eid].get('decision'),s))
            self.assertFalse(evaluate(self.aa(eid)[0].get('trigger'),s))
            self.assertTrue(evaluate(self.named(eid,'Withdraw this offer: 90-day wait').get('trigger'),s))

    def test_queued_roots_keep_no_calendar_or_event_trigger(self):
        for eid in m.ROOTS:
            event=self.after[eid]
            for key in ('trigger','date','offset','deathdate'):
                self.assertIsNone(event.get(key),(eid,key))
            self.assertIsInstance(event.get('decision'),Node)
            self.assertIsInstance(event.get('decision_trigger'),Node)
            self.assertIsInstance(self.aa(eid)[0].get('trigger'),Node)

    def test_stale_callbacks_after_withdrawal_and_different_new_offer(self):
        s=state();self.offer(s,'PER');self.choose(s,'PER','full')
        apply(self.named(9282270,'Withdraw this offer: 90-day wait'),s)
        apply(self.named(9282292,'End Persia cooling period'),s)
        s['flags'].add('ind_aubm_regional_current_irq');s['wars'].add('IRQ');self.offer(s,'IRQ')
        snapshot=copy.deepcopy(s)
        for eid in (9282280,9282288,9282289,9282290,9282291,9282292):
            enabled=[a for a in self.aa(eid) if evaluate(a.get('trigger'),s)]
            # Even a withdrawal button would let a stale shared ratifier
            # consume this newer, unanswered transaction.
            effectful=[a for a in enabled if a.all('command')]
            self.assertEqual(effectful,[],eid)
        self.assertEqual(s,snapshot)
        # Even an old same-target answer cannot consume a fresh unanswered offer.
        apply(self.named(9282271,'Withdraw this offer: 90-day wait'),s)
        apply(self.named(9282292,'End Iraq cooling period'),s);self.offer(s,'PER')
        self.assertFalse(evaluate(self.named(9282288,'Persia: record full answer').get('trigger'),s))

    def test_ratifier_withdrawal_requires_selected_ready_answer(self):
        for tag in m.TARGETS:
            s=state(tag);self.offer(s,tag)
            withdraw=self.named(9282291,'Withdraw '+m.NAMES[tag]+' offer: 90-day wait')
            self.assertFalse(evaluate(withdraw.get('trigger'),s))
            self.choose(s,tag,'full')
            self.assertFalse(evaluate(withdraw.get('trigger'),s))
            self.receive(s,tag,'full')
            self.assertTrue(evaluate(withdraw.get('trigger'),s))
            s['exists'].discard(tag)
            self.assertTrue(evaluate(withdraw.get('trigger'),s))

    def test_current_minor_authority_and_battlefield_rechecked(self):
        for change in ('ind_puppet','target_puppet','ind_nonleader','target_allied','capital_lost','ownership_lost','annexed'):
            s=state();self.offer(s,'PER')
            if change=='ind_puppet':s['puppets'].add('IND')
            elif change=='target_puppet':s['puppets'].add('PER')
            elif change=='ind_nonleader':s['participants'].add('IND')
            elif change=='target_allied':s['participants'].add('PER')
            elif change=='capital_lost':s['control'][1085]='PER'
            elif change=='ownership_lost':s['owned'][1085]='IND'
            else:s['exists'].discard('PER')
            self.assertFalse(evaluate(self.aa(9282280)[0].get('trigger'),s),change)
            self.assertTrue(evaluate(self.named(9282270,'Withdraw this offer: 90-day wait').get('trigger'),s))
        s=state();s['participants'].add('IND');s['leaders'].add('IND')
        self.assertTrue(evaluate(self.aa(9282270)[0].get('trigger'),s))

    def test_foreign_odds_original_annexation_payloads_and_scoped_commands(self):
        for eid in m.FOREIGN:
            self.assertEqual([a.get('ai_chance') for a in self.aa(eid)[:3]],['60','25','15'])
        for eid in m.ROOTS:
            before=[f.value for f in m.actions(self.before[eid])]
            for old,new in zip(before[1:],self.aa(eid)[1:4]):self.assertEqual(canon(old),canon(new))
        for a in self.aa(9282291):
            commands=a.all('command');peace=[c for c in commands if c.get('type')=='peace']
            if peace:self.assertFalse(any(c.get('type') in ('dissent','access') for c in commands))
            self.assertFalse(any(c.get('type')=='leave_alliance' for c in commands))
            self.assertFalse(any(c.get('which','').startswith(('ind_v4a_treaty_','ind_gc_formal')) for c in commands))

    def test_no_owner_close_and_ambiguous_targets_cannot_clear_lock(self):
        s=state();s['flags'].update({m.OUT,m.flag('PER','target'),m.flag('IRQ','target')})
        for eid in (9282279,*m.FOREIGN,9282288,9282289,9282290,9282291,9282292):
            for a in self.aa(eid):
                if evaluate(a.get('trigger'),s):self.assertEqual(a.all('command'),[],eid)

    def test_ids_idempotence_cancel_and_human_bounds(self):
        self.assertEqual(set(self.before),set(self.after));self.assertEqual(set(self.records),set(m.IDS))
        self.assertEqual(m.transform(self.output)[0],self.output)
        self.assertEqual(canon(self.before[9282278]),canon(self.after[9282278]))
        self.assertEqual(canon(self.before[9287690]),canon(self.after[9287690]))
        for eid in m.IDS:
            e=self.after[eid];self.assertEqual(e.get('persistent'),'yes')
            for f in m.actions(e):
                self.assertIn(f.key,('action','action_a','action_b','action_c','action_d'))
                self.assertLessEqual(len(f.value.get('name')),58,(eid,f.value.get('name')))
            if eid in m.ROOTS:self.assertEqual(self.aa(eid)[-1].all('command'),[])


if __name__=='__main__':unittest.main()

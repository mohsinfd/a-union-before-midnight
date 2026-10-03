"""Transaction tests, not a native engine simulator."""
import copy
import unittest
from dh_save_spans import parse
import aubm_redesign_final_treaties as f
from test_aubm_redesign_campaign_stories import fresh
from test_aubm_redesign_decolonisation import evaluate as previous
from test_aubm_redesign_focus_outcomes import serialize


def evaluate(node,st):
    def one(k,v):
        if k in ('AND','OR','NOT'):
            vv=[one(x.key,x.value) for x in v.fields]
            return all(vv) if k=='AND' else any(vv) if k=='OR' else not any(vv)
        if k in ('access','guarantee','non_aggression'):
            pair=tuple(v.all('country'))
            return (frozenset(pair) if k=='non_aggression' else pair) in st[k]
        return previous(parse(serialize(k,v)),st)
    return all(one(x.key,x.value) for x in node.fields)


def apply(a,st,country='IND'):
    assert evaluate(a.get('trigger'),st)
    for c in a.all('command'):
        kind=c.get('type');which=c.get('which')
        if kind=='setflag':st['flags'].add(which)
        elif kind=='clrflag':st['flags'].discard(which)
        elif kind=='access':st['access'].add((country,which))
        elif kind=='end_access':st['access'].discard((which,country) if c.get('when')=='1' else (country,which))
        elif kind=='non_aggression':st[kind].add(frozenset((which,c.get('where'))))
        elif kind=='guarantee':st[kind].add((which,c.get('where')))
        elif kind=='secedeprovince':
            p=int(c.get('value'));assert st['owned'].get(p)==country
            st['owned'][p]=which;st['control'][p]=which
        elif kind in st['stocks']:st['stocks'][kind]+=int(c.get('value'))
        else:st['effects'].append((country,kind,which,c.get('value')))


class FinalTreatyTests(unittest.TestCase):
    def state(self,t):
        st=fresh();st.update(access=set(),guarantee=set(),non_aggression=set(),masters={})
        st['exists'].add(t['tag'])
        if t['family']!='sovereign':st['alliances'].add(frozenset(('IND',t['tag'])))
        proof={'german':'ind_aubm_soviet_major_victory','soviet':'ind_aubm_germany_major_victory',
               'sovereign':'ind_aubm_national_western_victory'}[t['family']]
        st['flags'].add(proof)
        if t['family']=='german':st['owned'][t['province']]='GER';st['control'][t['province']]='GER'
        return st

    def events(self,t):return parse(f.render(t)).all('event')

    def accepted(self,t,alternative=False):
        st=self.state(t);o,r,v=self.events(t)
        apply(o.all('action')[int(alternative)],st)
        apply(r.all('action')[2*int(alternative)],st,t['tag'])
        return st,v.all('action')[int(alternative)]

    def test_all_twelve_agreements_and_rewards_once(self):
        for t in f.TALKS:
            for alt in (False,True):
                with self.subTest(t=t['key'],alt=alt):
                    st,a=self.accepted(t,alt)
                    self.assertTrue(evaluate(a.get('trigger'),st))
                    apply(a,st)
                    self.assertFalse(evaluate(a.get('trigger'),st))
                    self.assertFalse(evaluate(parse(f.opening(t)),st))
                    self.assertNotIn(f.BUSY,st['flags'])

    def test_refusals_have_no_treaty_effects(self):
        for t in f.TALKS:
            for alt in (0,1):
                st=self.state(t);o,r,v=self.events(t);apply(o.all('action')[alt],st)
                before=copy.deepcopy(st);apply(r.all('action')[2*alt+1],st,t['tag'])
                for key in ('access','guarantee','non_aggression','owned','control'):self.assertEqual(before[key],st[key])
                self.assertFalse(evaluate(v.all('action')[alt].get('trigger'),st))
                apply(v.all('action')[-1],st);self.assertNotIn(f.BUSY,st['flags'])

    def test_cancellation_and_disappearance_make_callbacks_inert(self):
        for t in f.TALKS:
            for change in ('cancel','gone','war','puppet'):
                st=self.state(t);o,r,v=self.events(t);apply(o.all('action')[0],st)
                if change=='cancel':apply(v.all('action')[-1],st)
                if change=='gone':st['exists'].remove(t['tag'])
                if change=='war':st['wars'].add(frozenset(('IND','JAP')))
                if change=='puppet':st['puppets'].add(t['tag'])
                for a in r.all('action')[:4]:self.assertFalse(evaluate(a.get('trigger'),st),(t['key'],change))
                self.assertTrue(evaluate(r.all('action')[-1].get('trigger'),st))

    def test_no_unearned_or_unfunded_offers(self):
        for t in f.TALKS:
            st=self.state(t);st['flags'].clear();self.assertFalse(evaluate(parse(f.opening(t)),st))
            st=self.state(t);st['stocks']['money']=499
            for a in self.events(t)[0].all('action')[:2]:self.assertFalse(evaluate(a.get('trigger'),st))
            st=self.state(t);st['flags'].add(f.BUSY);self.assertFalse(evaluate(parse(f.opening(t)),st))

    def test_signatures_are_not_outcomes(self):
        for t in f.TALKS:
            for alt in (False,True):
                st=self.state(t);o,r,v=self.events(t);apply(o.all('action')[int(alt)],st)
                n=f.names(t);st['flags'].update((n['accepted'],n['responded']))
                self.assertFalse(evaluate(v.all('action')[int(alt)].get('trigger'),st))

    def test_german_transfer_requires_actual_german_ownership(self):
        for t in f.TALKS[:2]:
            st=self.state(t);st['owned'][t['province']]='SOV'
            self.assertFalse(evaluate(parse(f.opening(t)),st))
            st,a=self.accepted(t);self.assertEqual(st['owned'][t['province']],'IND')
            st['control'][t['province']]='SOV';self.assertFalse(evaluate(a.get('trigger'),st))

    def test_moscow_closed_zones_and_reciprocal_workshops(self):
        t=f.TALKS[2];st=self.state(t);st['access']={('IND','SOV'),('SOV','IND')}
        o,r,v=self.events(t);apply(o.all('action')[0],st);apply(r.all('action')[0],st,'SOV')
        self.assertEqual(st['access'],set());self.assertTrue(evaluate(v.all('action')[0].get('trigger'),st))
        before=copy.deepcopy(st['alliances']);apply(v.all('action')[0],st);self.assertEqual(before,st['alliances'])
        st,a=self.accepted(t,True);self.assertNotIn(('IND','SOV'),st['access']);apply(a,st)
        self.assertIn(('IND','SOV'),st['access']);self.assertIn(('SOV','IND'),st['access'])

    def membership(self,defence):
        st=self.state(f.TALKS[3])
        for t in f.TALKS[3:5]:
            st['exists'].add(t['tag'])
            n=f.names(t);st['flags'].add(n['ratified'])
            if not defence:st['flags'].add(n['alternative'])
            st['access'].update(((t['tag'],'IND'),('IND',t['tag'])))
            st['non_aggression'].add(frozenset((t['tag'],'IND')))
            if defence:st['guarantee'].update(((t['tag'],'IND'),('IND',t['tag'])))
        return st

    def test_charter_needs_two_real_members_and_is_once_only(self):
        for defence in (False,True):
            st=self.membership(defence);e=parse(f.charter()).get('event');a=e.all('action')[int(defence)]
            self.assertTrue(evaluate(a.get('trigger'),st));apply(a,st)
            for a in e.all('action')[:2]:self.assertFalse(evaluate(a.get('trigger'),st))
        st=self.membership(False);self.assertFalse(evaluate(parse(f.charter_gate(True)),st))

    def test_member_lost_access_expired_pact_or_puppeted_blocks_charter(self):
        for change in ('access','non_aggression','puppet','hostile','one_member'):
            st=self.membership(True)
            if change=='access':st['access'].discard(('IND','EGY'))
            if change=='non_aggression':st['non_aggression'].discard(frozenset(('IND','EGY')))
            if change=='puppet':st['puppets'].add('EGY')
            if change=='hostile':st['wars'].add(frozenset(('IND','EGY')))
            if change=='one_member':st['flags'].discard(f.names(f.TALKS[3])['ratified'])
            self.assertFalse(evaluate(parse(f.charter_gate()),st),change)

    def test_defer_and_close_do_not_revoke_completed_foreign_effects(self):
        for t in f.TALKS:
            st,a=self.accepted(t);v=self.events(t)[2];before=copy.deepcopy(st)
            apply(v.all('action')[-2],st);self.assertEqual(before,st)
            apply(v.all('action')[-1],st)
            for k in ('owned','control','access','non_aggression','guarantee'):self.assertEqual(before[k],st[k])

    def test_registry_text_and_prohibited_effects(self):
        from build_aubm_redesign import registered_new_ids
        self.assertTrue(set(f.NEW_EVENT_IDS)<=registered_new_ids())
        source={'51_bespoke_route_arcs.txt':'event = { id = 1 }'};out,records=f.transform(source)
        self.assertEqual(f.transform(out)[0],out);self.assertEqual(len(records),19)
        events=parse(out['51_bespoke_route_arcs.txt']).all('event')[1:]
        for e in events:
            self.assertLessEqual(len(e.get('desc').encode('latin1')),500)
            self.assertLessEqual(len(e.get('name')),58)
            for key in ('trigger','date','offset','deathdate'):self.assertIsNone(e.get(key))
            for a in e.all('action'):
                self.assertLessEqual(len(a.get('name')),58)
                gate=a.get('trigger');self.assertLessEqual(gate.end-gate.start,6000)
                for c in a.all('command'):
                    self.assertNotIn(c.get('type'),('war','peace','alliance','leave_alliance','make_puppet','independence'))
                    if c.get('type')=='secedeprovince':self.assertEqual(e.get('country'),'GER')


if __name__=='__main__':unittest.main()

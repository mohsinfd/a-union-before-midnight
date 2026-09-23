import copy
import unittest
from dh_save_spans import parse
import aubm_redesign_decolonisation as d
from test_aubm_redesign_campaign_stories import fresh, evaluate as simple, apply as simple_apply


def evaluate(node,state):
    def one(k,v):
        if k in ('AND','OR','NOT'):
            values=[one(f.key,f.value) for f in v.fields]
            return all(values) if k=='AND' else any(values) if k=='OR' else not any(values)
        if k=='atwar' and v not in ('yes','no'):return any(v in pair for pair in state['wars'])
        if k=='puppet':
            a,b=v.all('country');return state['masters'].get(a)==b
        from test_aubm_redesign_focus_outcomes import serialize
        return simple(parse(serialize(k,v)),state)
    return all(one(f.key,f.value) for f in node.fields)


def apply(a,state):
    assert evaluate(a.get('trigger'),state)
    for c in a.all('command'):
        kind=c.get('type')
        if kind=='setflag':state['flags'].add(c.get('which'))
        elif kind=='clrflag':state['flags'].discard(c.get('which'))
        elif kind in ('money','dissent'):state['stocks'][kind]+=int(c.get('value'))
        elif kind=='end_mastery':
            target=c.get('which');state['masters'].pop(target,None);state['puppets'].discard(target)
        elif kind in ('event','relation'):state['effects'].append((kind,c.get('which')))
        else:raise AssertionError(kind)


class DecolonisationTests(unittest.TestCase):
    def source(self,tag='EGY',name='Egypt'):
        return parse(d.render(tag,name,9398600)).all('event')

    def state(self,tag='EGY'):
        st=fresh();st['exists'].add(tag);st['puppets'].add(tag);st['masters']={tag:'ENG'}
        st['alliances']={frozenset(('IND','ENG'))}
        st['flags'].add('ind_lib1_suez_reward')
        return st

    def test_every_country_both_offers_acceptance_and_refusal(self):
        for tag,name in d.COUNTRIES:
            for funded in (0,1):
                for accept in (True,False):
                    with self.subTest(tag=tag,funded=funded,accept=accept):
                        st=self.state(tag);offer,reply,review=self.source(tag,name)
                        apply(offer.all('action')[funded],st)
                        expected=5000-(750 if funded else 250)
                        self.assertEqual(st['stocks']['money'],expected)
                        a=reply.all('action')[funded*2+(0 if accept else 1)]
                        self.assertEqual(int(a.get('ai_chance')),(80 if funded else 60) if accept else (20 if funded else 40))
                        apply(a,st)
                        self.assertFalse(evaluate(a.get('trigger'),st))
                        self.assertEqual(evaluate(review.all('action')[0].get('trigger'),st),accept)
                        apply(review.all('action')[0 if accept else 2],st)
                        self.assertNotIn(d.BUSY,st['flags'])
                        self.assertFalse(evaluate(parse(d.offer(tag)),st))
                        self.assertEqual(st['stocks']['money'],expected)

    def test_proof_real_master_and_peace_required(self):
        for change in ('no_proof','wrong_master','ind_war','eng_war','target_war','hostile_eng','puppet_ind'):
            st=self.state()
            if change=='no_proof':st['flags'].clear()
            elif change=='wrong_master':st['masters']['EGY']='GER'
            elif change=='puppet_ind':st['puppets'].add('IND')
            else:st['wars'].add(frozenset(({'ind_war':'IND','eng_war':'ENG','target_war':'EGY','hostile_eng':'IND'}[change], 'ENG' if change=='hostile_eng' else 'JAP')))
            self.assertFalse(evaluate(parse(d.offer('EGY')),st),change)

    def test_change_during_queue_blocks_release(self):
        for change in ('war','master','gone','alignment'):
            st=self.state();opening,reply,_=self.source();apply(opening.all('action')[0],st)
            if change=='war':st['wars'].add(frozenset(('EGY','ITA')))
            if change=='master':st['masters']['EGY']='GER'
            if change=='gone':st['exists'].remove('EGY')
            if change=='alignment':st['alliances'].clear()
            for a in reply.all('action')[:4]:self.assertFalse(evaluate(a.get('trigger'),st))

    def test_cancel_before_reply_makes_all_late_effects_inert(self):
        st=self.state();opening,reply,review=self.source();apply(opening.all('action')[0],st)
        apply(review.all('action')[2],st)
        for a in reply.all('action')[:4]:self.assertFalse(evaluate(a.get('trigger'),st))
        self.assertTrue(evaluate(reply.all('action')[-1].get('trigger'),st))
        self.assertEqual(reply.all('action')[-1].all('command'),[])

    def test_acceptance_flag_without_release_cannot_award(self):
        st=self.state();opening,_,review=self.source();apply(opening.all('action')[0],st)
        st['flags'].update((d.names('EGY')['responded'],d.names('EGY')['accepted']))
        self.assertFalse(evaluate(review.all('action')[0].get('trigger'),st))
        st['masters']['EGY']='GER'
        self.assertFalse(evaluate(review.all('action')[0].get('trigger'),st))

    def test_recognition_once_and_no_alliance_change(self):
        st=self.state();o,r,v=self.source();alliances=copy.deepcopy(st['alliances'])
        apply(o.all('action')[1],st);apply(r.all('action')[2],st);apply(v.all('action')[0],st)
        self.assertEqual(st['alliances'],alliances)
        self.assertFalse(evaluate(v.all('action')[0].get('trigger'),st))
        self.assertEqual(st['stocks']['dissent'],8)

    def test_defer_is_free_and_only_one_proposal_open(self):
        st=self.state();o,_,v=self.source();before=copy.deepcopy(st)
        apply(o.all('action')[2],st);self.assertEqual(before,st)
        apply(o.all('action')[0],st);before=copy.deepcopy(st)
        apply(v.all('action')[1],st);self.assertEqual(before,st)
        st['exists'].add('IRQ');st['masters']['IRQ']='ENG';st['puppets'].add('IRQ')
        self.assertFalse(evaluate(parse(d.offer('IRQ')),st))

    def test_offer_affordability(self):
        for choice,cost in ((0,250),(1,750)):
            st=self.state();st['stocks']['money']=cost-1
            self.assertFalse(evaluate(self.source()[0].all('action')[choice].get('trigger'),st))

    def test_text_and_foreign_command_scope(self):
        for tag,name in d.COUNTRIES:
            for e in self.source(tag,name):
                self.assertLessEqual(len(e.get('desc').encode('latin1')),500)
                self.assertLessEqual(len(e.get('name')),58)
                for key in ('trigger','date','offset','deathdate'):self.assertIsNone(e.get(key))
                for a in e.all('action'):
                    self.assertLessEqual(len(a.get('name')),58)
                    for c in a.all('command'):
                        self.assertNotIn(c.get('type'),('peace','war','make_puppet','leave_alliance','independence','access'))
                        if c.get('type')=='end_mastery':self.assertEqual(e.get('country'),'ENG')

    def test_registration_idempotence_and_collision(self):
        from build_aubm_redesign import registered_new_ids
        self.assertTrue(set(d.NEW_EVENT_IDS)<=registered_new_ids())
        src={'51_bespoke_route_arcs.txt':'event = { id = 1 }'}
        out,records=d.transform(src)
        self.assertEqual(d.transform(out)[0],out)
        self.assertEqual(set(records),set(d.NEW_EVENT_IDS))
        with self.assertRaises(ValueError):d.transform({'51_bespoke_route_arcs.txt':'event = { id = 9398600 }'})


if __name__=='__main__':unittest.main()

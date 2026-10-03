"""Cold observer/state tests, not native attribution or war-entry execution."""
from dataclasses import dataclass, field
from pathlib import Path
import unittest
from dh_save_spans import Node, parse, walk
from aubm_redesign_diplomacy import actions
from aubm_redesign_aggression import transform, EDITED_IDS, OBSERVER_IDS, PAGE_IDS, PROOF, NOTIFIED, USED


@dataclass
class State:
    flags: set = field(default_factory=set)
    wars: set = field(default_factory=set)
    alliances: set = field(default_factory=set)
    puppets: set = field(default_factory=set)
    countries: set = field(default_factory=lambda: {'IND','JAP','USA','SOV','ENG','PER','CHI','AFG'})
    attacks: set = field(default_factory=set)  # (attacker, this-country context)
    actor: str = 'USA'
    dissent: int = 0


def pair(a, b): return frozenset((a,b))


def permits(node, s):
    if not isinstance(node, Node): return True
    def ev(f):
        k, v = f.key, f.value
        if k == 'AND': return permits(v,s)
        if k == 'OR': return any(ev(x) for x in v.fields)
        if k == 'NOT': return not any(ev(x) for x in v.fields)
        if k == 'flag': return v in s.flags
        if k == 'exists': return v in s.countries
        if k == 'ispuppet': return v in s.puppets
        if k in ('alliance','war'): return frozenset(v.all('country')) in (s.wars if k=='war' else s.alliances)
        if k == 'attack': return (v,s.actor) in s.attacks
        if k == 'ai': return v == 'no'
        raise AssertionError(k)
    return all(ev(f) for f in node.fields)


def apply(a,s):
    if not permits(a.get('trigger'),s): return None
    effects=[]
    for c in a.all('command'):
        if not permits(c.get('trigger'),s): continue
        k,w=c.get('type'),c.get('which')
        if k=='setflag': s.flags.add(w)
        elif k=='clrflag': s.flags.discard(w)
        elif k=='war': s.wars.add(pair(s.actor,w))
        elif k=='dissent': s.dissent+=int(c.get('value'))
        effects.append((k,w))
    return effects


class AggressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        cls.path='db/events/aubm_v4/43_wartime_settlements.txt'
        cls.source={cls.path:(root/'mod'/cls.path).read_text(encoding='cp1252')}
        cls.output,cls.records=transform(cls.source)
        cls.events={int(e.get('id')):e for e in parse(cls.output[cls.path]).all('event')}
        cls.original={int(e.get('id')):e for e in parse(cls.source[cls.path]).all('event')}
        cls.witnesses={cls.events[i].get('country'):i for i in OBSERVER_IDS if i%2==0}

    def a(self,eid,key='action_a'): return self.events[eid].get(key)
    def fire(self,eid,s,key='action_a'):
        s.actor=self.events[eid].get('country')
        if not permits(self.events[eid].get('trigger'),s): return None
        return apply(self.a(eid,key),s)
    def witness(self,s,tag='USA'):
        base=self.witnesses[tag]
        s.countries.add(tag)
        self.assertIsNotNone(self.fire(base,s))
        s.wars.add(pair('JAP',tag));s.attacks.add(('JAP',tag))
        self.assertIsNotNone(self.fire(base+1,s))

    def test_exact_complete_registry_no_new_ids_and_idempotence(self):
        self.assertEqual(set(self.records),EDITED_IDS)
        self.assertEqual(set(self.events),set(self.original))
        self.assertEqual(len(self.witnesses),340)
        self.assertEqual(transform(self.output)[0],self.output)
        def canon(n): return [(f.key,canon(f.value) if isinstance(f.value,Node) else f.value) for f in n.fields]
        for eid in self.events.keys()-EDITED_IDS:
            self.assertEqual(canon(self.events[eid]),canon(self.original[eid]),eid)

    def test_existing_1933_war_is_not_new_aggression(self):
        s=State(wars={pair('JAP','USA')},attacks={('JAP','USA')})
        base=self.witnesses['USA']
        self.assertIsNone(self.fire(base,s))
        self.assertIsNone(self.fire(base+1,s))
        self.assertNotIn(PROOF,s.flags)
        s.wars.clear();s.attacks.clear()
        self.assertIsNotNone(self.fire(base,s))
        s.wars.add(pair('JAP','USA'));s.attacks.add(('JAP','USA'))
        self.assertIsNotNone(self.fire(base+1,s));self.assertIn(PROOF,s.flags)

    def test_victim_declaring_war_does_not_prove_japanese_aggression(self):
        s=State();base=self.witnesses['USA']
        self.fire(base,s)
        s.wars.add(pair('JAP','USA'));s.attacks.add(('USA','JAP'))
        self.assertIsNone(self.fire(base+1,s));self.assertNotIn(PROOF,s.flags)

    def test_every_foreign_pair_retains_country_relative_baseline_and_attack(self):
        for tag,base in self.witnesses.items():
            s=State();s.countries.add(tag)
            self.assertIsNotNone(self.fire(base,s),tag)
            self.assertIsNone(self.fire(base,s),tag)
            s.wars.add(pair('JAP',tag));s.attacks.add(('JAP',tag))
            self.assertIsNotNone(self.fire(base+1,s),tag)
            self.assertIn(PROOF,s.flags)
            self.assertNotIn(pair('IND','JAP'),s.wars)
            for eid in (base,base+1):
                self.assertEqual(self.events[eid].get('date').get('year'),'1933')
                self.assertEqual(self.events[eid].get('country'),tag)
                self.assertNotIn('war',{c.get('type') for c in self.a(eid).all('command')})

    def test_foreign_observation_not_blocked_by_indian_route_or_commitment(self):
        s=State(flags={'ind_aubm_commitment_german'},alliances={pair('IND','GER')})
        self.witness(s)
        self.assertIn(PROOF,s.flags)
        self.assertIsNotNone(self.fire(9294002,s))
        self.assertIsNone(self.fire(9294004,s,'action_b'))

    def test_first_proof_stops_all_observers_and_notice_fires_once(self):
        s=State();self.witness(s)
        for eid in OBSERVER_IDS:
            self.assertIsNone(self.fire(eid,s),eid)
        self.assertIsNotNone(self.fire(9294002,s))
        self.assertIsNone(self.fire(9294002,s))
        self.assertIn(NOTIFIED,s.flags)
        self.assertNotIn(pair('IND','JAP'),s.wars)

    def test_witnessed_war_ending_or_victim_annexation_keeps_proof_and_option(self):
        s=State();self.witness(s);self.fire(9294002,s)
        s.wars.clear();s.countries.remove('USA')
        self.assertEqual(self.fire(9294003,s),[])
        self.assertTrue({PROOF,NOTIFIED}<=s.flags)
        self.assertIsNotNone(self.fire(9294004,s,'action_b'))
        self.assertIsNone(self.fire(9294002,s))
        self.assertNotIn(pair('IND','JAP'),s.wars)

    def test_confirmation_declares_explicitly_once_preserving_other_war(self):
        s=State(wars={pair('IND','SOV')});self.witness(s)
        self.fire(9294004,s,'action_b')
        self.assertNotIn(pair('IND','JAP'),s.wars)
        effects=self.fire(9294005,s,'action_b')
        self.assertIn(('war','JAP'),effects);self.assertEqual(s.dissent,2)
        self.assertIn(pair('IND','SOV'),s.wars)
        self.assertTrue({PROOF,USED}<=s.flags)
        s.wars.discard(pair('IND','JAP'))
        self.assertIsNone(self.fire(9294005,s,'action_b'))
        self.assertEqual(s.dissent,2)

    def test_confirmation_rechecks_current_master_alliance_commitment_and_cancel(self):
        for change in ('indpuppet','jappuppet','japanally','otherally','compact','alreadywar','absentjapan'):
            s=State();self.witness(s);self.fire(9294004,s,'action_b')
            if change=='indpuppet':s.puppets.add('IND')
            if change=='jappuppet':s.puppets.add('JAP')
            if change=='japanally':s.alliances.add(pair('IND','JAP'))
            if change=='otherally':s.alliances.add(pair('IND','USA'))
            if change=='compact':s.flags.add('ind_v4a_treaty_cobelligerent')
            if change=='alreadywar':s.wars.add(pair('IND','JAP'))
            if change=='absentjapan':s.countries.remove('JAP')
            self.assertIsNone(self.fire(9294005,s,'action_b'),change)
            flags,wars=set(s.flags),set(s.wars)
            self.assertEqual(self.fire(9294005,s),[])
            self.assertEqual((s.flags,s.wars,s.dissent),(flags,wars,0))

    def test_regional_friendship_does_not_force_major_bloc_membership(self):
        s=State(alliances={pair('IND','PER')});self.witness(s)
        self.assertIsNotNone(self.fire(9294005,s,'action_b'))
        self.assertEqual(s.alliances,{pair('IND','PER')})

    def test_old_reset_stub_is_not_an_automatic_timer_or_proof_eraser(self):
        e=self.events[9294003]
        for k in ('trigger','date','offset','deathdate','decision'):self.assertIsNone(e.get(k))
        self.assertFalse(self.a(9294003).all('command'))
        for eid in EDITED_IDS:
            for af in actions(self.events[eid]):
                self.assertFalse(any(c.get('type')=='clrflag' and c.get('which') in (PROOF,NOTIFIED,USED) for c in af.value.all('command')))

    def test_human_predicates_and_prose_are_bounded(self):
        for eid in PAGE_IDS:
            e=self.events[eid]
            self.assertLessEqual(len(e.get('desc')),340)
            for n in walk(e):
                for f in n.fields:
                    if f.key in ('trigger','decision','decision_trigger'):
                        self.assertLess(f.value.end-f.value.start,2000,eid)
                        count=sum(len(x.fields) for x in walk(f.value))
                        self.assertLess(count,125,eid)
                        self.assertNotIn('aggression_live_',self.output[self.path][f.value.start:f.value.end])


if __name__=='__main__': unittest.main()

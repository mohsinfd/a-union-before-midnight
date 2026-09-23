"""Cold regional bookkeeping scenarios; native peace/queue semantics unproved."""
from dataclasses import dataclass,field
from pathlib import Path
import unittest
from dh_save_spans import Node,parse
from aubm_redesign_diplomacy import actions
from aubm_redesign_regional_replies import (transform,TAGS,CAPITALS,token,target,OUT,RETRY,EDITED_IDS,LEGACY_IDS)
from aubm_redesign_withdrawal import generic_peace,TREATY_DOWNGRADES

@dataclass
class State:
    flags:set=field(default_factory=set)
    wars:set=field(default_factory=set)
    alliances:set=field(default_factory=set)
    puppets:set=field(default_factory=set)
    leaders:set=field(default_factory=set)
    countries:set=field(default_factory=lambda:set(TAGS)|{'IND','JAP','ENG'})
    owners:dict=field(default_factory=dict)
    controls:dict=field(default_factory=dict)
    dissent:int=0
    peace_succeeds:bool=True

def pair(a,b):return frozenset((a,b))
def permits(n,s):
    if not isinstance(n,Node):return True
    def ev(f):
        k,v=f.key,f.value
        if k=='AND':return permits(v,s)
        if k=='OR':return any(ev(x) for x in v.fields)
        if k=='NOT':return not any(ev(x) for x in v.fields)
        if k=='flag':return v in s.flags
        if k=='exists':return v in s.countries
        if k=='ispuppet':return v in s.puppets
        if k=='war':return frozenset(v.all('country')) in s.wars
        if k=='participant':return any(v.get('country') in p for p in s.alliances)
        if k=='alliance_leader':return v.get('country') in s.leaders
        if k=='owned':return s.owners.get(int(v.get('province')))==v.get('data')
        if k=='control':return s.controls.get(int(v.get('province')))==v.get('data')
        if k=='ai':return v=='no'
        raise AssertionError(k)
    return all(ev(f) for f in n.fields)
def apply(a,s):
    if not permits(a.get('trigger'),s):return None
    effects=[]
    for c in a.all('command'):
        if not permits(c.get('trigger'),s):continue
        k,w=c.get('type'),c.get('which')
        if k=='setflag':s.flags.add(w)
        elif k=='clrflag':s.flags.discard(w)
        elif k=='dissent':s.dissent+=int(c.get('value'))
        elif k=='peace' and s.peace_succeeds:s.wars.discard(pair('IND',w))
        effects.append((k,w,c.get('when')))
    return effects

class RegionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).resolve().parents[1]/'mod/db/events/aubm_v4/46_regional_campaigns.txt'
        cls.source={path.name:path.read_text(encoding='cp1252')}
        cls.input=generic_peace(cls.source)[0]
        cls.output,cls.records=transform(cls.input)
        cls.events={int(e.get('id')):e for e in parse(cls.output[path.name]).all('event')}
        cls.old={int(e.get('id')):e for e in parse(cls.input[path.name]).all('event')}
    def state(self,tag):
        return State(flags={'ind_aubm_regional_current_'+tag.lower()},wars={pair('IND',tag)},owners={CAPITALS[tag]:tag},controls={CAPITALS[tag]:'IND'})
    def a(self,eid,key='action_a'):return self.events[eid].get(key)
    def pick(self,eid,s,text):
        return next(a.value for a in actions(self.events[eid]) if text in a.value.get('name') and permits(a.value.get('trigger'),s))
    def offer(self,tag,s):return apply(self.a(9282210+TAGS.index(tag)),s)
    def answer(self,tag,s,index=0):return apply(self.a(9282220+TAGS.index(tag),('action_a','action_b','action_c')[index]),s)

    def test_exact_scope_idempotence_and_annexation_choices_preserved(self):
        self.assertEqual(set(self.records),EDITED_IDS)
        self.assertEqual(transform(self.output)[0],self.output)
        def canon(n):return [(f.key,canon(f.value) if isinstance(f.value,Node) else f.value) for f in n.fields]
        for eid in range(9282210,9282220):
            for key in ('action_b','action_c','action_d'):
                self.assertEqual(canon(self.old[eid].get(key)),canon(self.a(eid,key)))
        for eid in self.events.keys()-EDITED_IDS:self.assertEqual(canon(self.events[eid]),canon(self.old[eid]))

    def test_owned_root_recovery_survives_annexation_and_has_no_queue_filters(self):
        from aubm_redesign_regional_replies import PHASES
        for tag in TAGS:
            eid=9282210+TAGS.index(tag);e=self.events[eid]
            for key in ('date','offset','trigger','deathdate'):
                self.assertEqual(self.old[eid].get(key),e.get(key))
            for phase in PHASES:
                s=self.state(tag);s.countries.discard(tag)
                s.flags.update((OUT,target(tag),token(tag,phase)))
                self.assertTrue(permits(e.get('decision'),s))
                self.assertTrue(permits(e.get('decision_trigger'),s))
                effects=apply(self.pick(eid,s,'withdraw'),s)
                self.assertIn(('event','9282264','90'),effects)
                self.assertNotIn(OUT,s.flags)
                self.assertTrue(all(token(tag,p) not in s.flags for p in PHASES))
                self.assertFalse(permits(e.get('decision'),s))
                self.assertEqual(phase=='refused',s.dissent)

    def test_refusal_withdrawal_and_recording_both_charge_once(self):
        for tag in TAGS:
            for eid,needle in ((9282263,'record refusal'),(9282263,'withdraw'),(9282210+TAGS.index(tag),'withdraw')):
                s=self.state(tag);self.offer(tag,s);self.answer(tag,s,2)
                chosen=self.pick(eid,s,needle)
                self.assertIsNotNone(apply(chosen,s));self.assertEqual(1,s.dissent)
                self.assertIsNone(apply(chosen,s));self.assertEqual(1,s.dissent)

    def test_new_button_names_are_readable_and_bounded(self):
        for eid in EDITED_IDS:
            for f in actions(self.events[eid]):
                name=f.value.get('name')
                self.assertLessEqual(len(name.encode('latin1')),58,(eid,name))
                self.assertFalse(any(name.startswith(t+':') for t in TAGS),(eid,name))

    def test_all_ten_full_limited_refusal_flows_keep_odds_and_rewards(self):
        for tag in TAGS:
            for index in range(3):
                s=self.state(tag)
                self.assertIsNotNone(self.offer(tag,s));self.assertIsNotNone(self.answer(tag,s,index))
                self.assertEqual(s.dissent,0)
                reply=9282261+index
                apply(self.pick(reply,s,'record refusal' if index==2 else 'send the'),s)
                if index==2:
                    self.assertEqual(s.dissent,1);self.assertIn(token(tag,'cooldown'),s.flags)
                    apply(self.pick(9282264,s,'cooling period'),s)
                    self.assertNotIn(RETRY,s.flags)
                    self.assertIsNotNone(self.offer(tag,s))
                else:
                    self.assertEqual(s.dissent,0)
                    apply(self.pick(9282260,s,': ratify'),s)
                    self.assertEqual(s.dissent,-2 if index==0 else -1)
                    self.assertIn('ind_aubm_regional_settled_'+tag.lower(),s.flags)
                    self.assertNotIn(OUT,s.flags);self.assertNotIn(pair('IND',tag),s.wars)
                self.assertEqual([self.a(9282220+TAGS.index(tag),k).get('ai_chance') for k in ('action_a','action_b','action_c')],['60','25','15'])

    def test_old_siam_shared_refusal_cannot_consume_new_china_offer(self):
        s=self.state('SIA');self.offer('SIA',s);self.answer('SIA',s,2)
        apply(self.pick(9282263,s,'withdraw'),s)
        apply(self.pick(9282264,s,'cooling period'),s)
        s.flags.add('ind_aubm_regional_current_chi');s.wars.add(pair('IND','CHI'))
        s.owners[CAPITALS['CHI']]='CHI';s.controls[CAPITALS['CHI']]='IND'
        self.assertIsNotNone(self.offer('CHI',s))
        before=set(s.flags)
        stale=self.pick(9282263,s,'no matching offer')
        self.assertEqual(apply(stale,s),[])
        self.assertEqual(s.flags,before);self.assertIn(OUT,s.flags)
        self.assertIn(token('CHI','offer'),s.flags)

    def test_stale_foreign_reply_does_not_clear_selected_indian_answer(self):
        s=self.state('SIA');self.offer('SIA',s);self.answer('SIA',s)
        self.assertEqual(apply(self.pick(9282222,s,'no matching offer'),s),[])
        self.assertIn(token('SIA','full'),s.flags)
        self.assertIn(OUT,s.flags)

    def test_withdraw_before_ratification_no_reward_and_owned_90day_timer(self):
        for eid in (9282261,9282260):
            s=self.state('CHI');self.offer('CHI',s);self.answer('CHI',s)
            if eid==9282260:apply(self.pick(9282261,s,'send the'),s)
            s.flags.add('unrelated_pending')
            effects=apply(self.pick(eid,s,'withdraw'),s)
            self.assertEqual(s.dissent,0);self.assertIn(('event','9282264','90'),effects)
            self.assertIn('unrelated_pending',s.flags);self.assertNotIn(OUT,s.flags)
            self.assertIn(RETRY,s.flags);self.assertIsNone(self.offer('CHI',s))

    def test_new_master_alliance_missing_country_capital_or_war_lapses(self):
        for change in ('puppet','alliance','absent','capital','peace','indsubject'):
            s=self.state('SIA');self.offer('SIA',s);self.answer('SIA',s)
            if change=='puppet':s.puppets.add('SIA')
            if change=='alliance':s.alliances.add(pair('SIA','JAP'))
            if change=='absent':s.countries.remove('SIA')
            if change=='capital':s.controls[1423]='SIA'
            if change=='peace':s.wars.clear()
            if change=='indsubject':s.puppets.add('IND')
            effects=apply(self.pick(9282261,s,'lapsed'),s)
            self.assertFalse(any(k in ('dissent','peace') for k,*_ in effects))
            self.assertNotIn(OUT,s.flags);self.assertEqual(s.dissent,0)

    def test_siam_japanese_puppet_cannot_enter_generic_peace(self):
        s=self.state('SIA');s.puppets.add('SIA')
        self.assertIsNone(self.offer('SIA',s))
        s.puppets.clear();s.flags.add('ind_lib1_siam_break_pending')
        self.assertIsNone(self.offer('SIA',s))

    def test_failed_native_peace_model_withholds_reward_and_retries(self):
        s=self.state('CHI');s.peace_succeeds=False
        self.offer('CHI',s);self.answer('CHI',s);apply(self.pick(9282261,s,'send the'),s)
        apply(self.pick(9282260,s,': ratify'),s)
        self.assertEqual(s.dissent,0)
        self.assertNotIn('ind_aubm_regional_settled_chi',s.flags)
        self.assertIn(RETRY,s.flags);self.assertIn(pair('IND','CHI'),s.wars)

    def test_old_retry_does_not_clear_new_offer_or_queue_other_docket(self):
        s=self.state('CHI');self.offer('CHI',s)
        before=set(s.flags)
        self.assertEqual(apply(self.pick(9282264,s,'no matching offer'),s),[])
        self.assertEqual(before,s.flags)

    def test_every_offer_serialized_during_any_country_cooldown(self):
        for cooling in TAGS:
            for offered in TAGS:
                s=self.state(offered)
                # Even missing legacy global bookkeeping cannot bypass a local
                # staged cooldown and create overlapping shared timer owners.
                s.flags.add(token(cooling,'cooldown'))
                self.assertIsNone(self.offer(offered,s),(cooling,offered))
                s.flags.add(RETRY)
                self.assertIsNone(self.offer(offered,s))

    def test_retry_local_cleanup_preserves_another_record_and_global_lock(self):
        s=self.state('SIA')
        s.flags.update({token('SIA','cooldown'),token('CHI','cooldown'),RETRY})
        apply(self.pick(9282264,s,'Siam: the cooling'),s)
        self.assertNotIn(token('SIA','cooldown'),s.flags)
        self.assertIn(token('CHI','cooldown'),s.flags)
        self.assertIn(RETRY,s.flags)

    def test_indian_alliance_leader_keeps_treaty_records(self):
        s=self.state('CHI');s.alliances.add(pair('IND','ENG'));s.leaders.add('IND')
        s.flags.add('ind_v4a_treaty_formal_alliance')
        self.offer('CHI',s);self.answer('CHI',s);apply(self.pick(9282261,s,'send the'),s)
        apply(self.pick(9282260,s,': ratify'),s)
        self.assertIn('ind_v4a_treaty_formal_alliance',s.flags)
        self.assertEqual(s.alliances,{pair('IND','ENG')})
        for a in actions(self.events[9282260]):
            self.assertFalse(any(c.get('which') in TREATY_DOWNGRADES for c in a.value.all('command')))

    def test_legacy_reward_stubs_and_callbacks_have_no_calendar_flood(self):
        for eid in LEGACY_IDS:
            self.assertFalse(any(a.value.all('command') for a in actions(self.events[eid])))
        for eid in range(9282260,9282265):
            for k in ('date','offset','trigger','one_action'):
                self.assertIsNone(self.events[eid].get(k))

if __name__=='__main__':unittest.main()

"""Execute the generated predicates against synthetic campaign states.

This is a script-level contract test, not an emulation or claim of DH engine QA.
Unknown predicates fail loudly; rewards are exercised from the parsed output.
"""
from __future__ import annotations

import copy
import re
import unittest
from dataclasses import dataclass, field

import generate_aubm_liberator as lib
from aubm_menu_safety import event_spans


def parse(text):
    tokens = re.findall(r'"[^"\n]*"|#[^\n]*|[{}=]|[^\s{}=#"]+', text)
    tokens = [t for t in tokens if not t.startswith('#')]
    pos = 0
    def body(nested=False):
        nonlocal pos
        result = []
        while pos < len(tokens):
            if tokens[pos] == '}':
                if not nested: raise ValueError('extra closing brace')
                pos += 1
                return result
            key = tokens[pos]; pos += 1
            if tokens[pos] != '=': raise ValueError(f'missing assignment after {key}')
            pos += 1
            value = tokens[pos]; pos += 1
            if value == '{': value = body(True)
            else: value = value.strip('"')
            result.append((key,value))
        if nested: raise ValueError('unclosed block')
        return result
    return body()


def get(node, key, default=None): return next((v for k,v in node if k == key), default)
def values(node,key): return [v for k,v in node if k == key]


def is_action(key): return key == 'action' or key.startswith('action_')


@dataclass
class State:
    flags: set = field(default_factory=lambda: {'ind_aubm_route_sovereign',lib.P+'enabled'})
    exists: set = field(default_factory=lambda: {'IND','JAP','ENG','SOV','USA','EGY'})
    wars: set = field(default_factory=set)
    alliances: set = field(default_factory=set)
    puppets: dict = field(default_factory=dict)
    owned: dict = field(default_factory=dict)
    control: dict = field(default_factory=dict)
    garrisons: dict = field(default_factory=dict)
    resources: dict = field(default_factory=lambda: {'manpower':80,'money':5000,'supplies':10000,'army':146,'dissent':0,'tc_mod':0,'research_mod':0})
    year: int = 1940
    ai: bool = False
    queued: list = field(default_factory=list)
    day: int = 0
    event_dates: dict = field(default_factory=dict)
    attacked_by: set = field(default_factory=set)  # relative to the receiving event country


def pair(tags): return frozenset(tags)


def evaluate(node, state):
    def clause(k,v):
        if k == 'AND': return evaluate(v,state)
        if k == 'OR': return any(clause(a,b) for a,b in v)
        if k == 'NOT': return not any(clause(a,b) for a,b in v)
        if k == 'flag': return v in state.flags
        if k == 'year': return state.year >= int(v)
        if k == 'ai': return state.ai == (v == 'yes')
        if k == 'attack': return v in state.attacked_by
        if k == 'exists': return v in state.exists
        if k == 'ispuppet': return v in state.puppets
        if k == 'atwar':
            tag = 'IND' if v in ('yes','no') else v
            present = any(tag in p for p in state.wars)
            return not present if v=='no' else present
        if k == 'event':
            eid=int(get(v,'id')); days=int(get(v,'days'))
            return eid in state.event_dates and state.day-state.event_dates[eid] >= days
        if k in ('war','alliance'):
            return pair(values(v,'country')) in (state.wars if k == 'war' else state.alliances)
        if k == 'puppet':
            a,b = values(v,'country'); return state.puppets.get(a) == b
        if k in ('owned','control'):
            return getattr(state,k).get(int(get(v,'province'))) == get(v,'data')
        if k == 'garrison':
            return state.garrisons.get((get(v,'country'),int(get(v,'province'))),0) >= int(get(v,'size'))
        if k in ('army','manpower','money','supplies'):
            return state.resources[k] >= float(v)
        raise AssertionError(f'Unsupported predicate {k}')
    return all(clause(k,v) for k,v in node)


def execute(a, s):
    if not evaluate(get(a,'trigger',[]),s): return False
    for c in values(a,'command'):
        if not evaluate(get(c,'trigger',[]),s): continue
        typ = get(c,'type')
        if typ == 'setflag': s.flags.add(get(c,'which'))
        elif typ == 'clrflag': s.flags.discard(get(c,'which'))
        elif typ == 'event': s.queued.append((int(get(c,'which')),get(c,'where'),int(get(c,'when'))))
        elif typ == 'manpowerpool': s.resources['manpower'] += int(get(c,'value'))
        elif typ in ('money','supplies','dissent','tc_mod','research_mod'):
            s.resources[typ] = s.resources.get(typ,0) + int(get(c,'value'))
        elif typ in ('industrial_modifier','guarantee','relation','access'):
            pass  # Presence/recipient tested separately; no invented engine effects.
        else: raise AssertionError(f'Engine-only command {typ} cannot be simulated')
    return True


class LiberatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = lib.render()
        cls.events = {int(get(e,'id')):e for k,e in parse(cls.text) if k=='event'}

    def gate(self,eid,s,key='trigger'): return evaluate(get(self.events[eid],key,[]),s)
    def choose(self,eid,letter,s):
        done=execute(get(self.events[eid],'action_'+letter),s)
        if done and get(self.events[eid],'save_date')=='yes': s.event_dates[eid]=s.day
        return done
    def lib_state(self,r,owner):
        s = State(); s.exists.add(owner)
        s.flags |= {lib.P+'japan_war',f'ind_aubm_sea_land_{r.key}_liberated'}
        for p in r.minimum+r.hubs: s.owned[p]=owner; s.control[p]=owner
        return s
    def partner_state(self,r):
        s = self.lib_state(r,r.tag)
        s.flags |= {lib.P+r.key+'_partner',lib.P+r.key+'_reward'}
        return s

    def test_generated_output_current_and_prefix_preserved(self):
        raw = lib.OUTPUT.read_bytes()
        self.assertEqual(raw,lib.apply_to_bytes(raw))
        seed = b'# unrelated user content\r\nevent = { id = 1 }\r\n'
        first = lib.apply_to_bytes(seed)
        self.assertTrue(first.startswith(seed))
        self.assertEqual(first,lib.apply_to_bytes(first))

    def test_ids_unique_and_targets_resolve(self):
        all_ids=[]
        for p in (lib.ROOT/'mod/db/events').rglob('*.txt'):
            all_ids += [i for _,_,i in event_spans(p.read_text(encoding='cp1252'))]
        for eid in self.events: self.assertEqual(all_ids.count(eid),1,eid)
        for e in self.events.values():
            for k,a in e:
                if not is_action(k): continue
                for c in values(a,'command'):
                    if get(c,'type')=='event':
                        target=int(get(c,'which'))
                        external={9282046:'SOV',9282043:'IND',9282045:'IND'}
                        self.assertTrue(target in self.events or target in external,target)
                        self.assertEqual(get(c,'where'),external.get(target) or get(self.events[target],'country'))

    def test_every_decision_and_information_page_has_effect_free_cancel(self):
        for eid,e in self.events.items():
            if get(e,'decision') is not None or eid in (9289802,9289803,9289806,9289807,9289808):
                cancels=[a for k,a in e if is_action(k) and get(a,'name')=='Cancel - close without changes']
                self.assertEqual(len(cancels),1,eid)
                self.assertIsNone(get(cancels[0],'trigger'))
                self.assertFalse(values(cancels[0],'command'))

    def test_optin_does_not_declare_war_award_resources_or_change_route(self):
        s=State(); s.flags.discard(lib.P+'enabled'); before=copy.deepcopy(s)
        self.assertTrue(self.gate(9289800,s,'decision'))
        self.assertTrue(self.choose(9289800,'a',s))
        self.assertEqual(s.resources,before.resources); self.assertEqual(s.wars,before.wars)
        self.assertEqual(s.flags,before.flags|{lib.P+'enabled'})
        self.assertFalse(self.gate(9289800,s,'decision'))

    def test_no_ai_or_other_route_optin(self):
        s=State(); s.flags.clear(); s.ai=True
        self.assertFalse(self.gate(9289800,s,'decision'))
        s.ai=False; s.flags.add('ind_aubm_route_japan')
        self.assertFalse(self.gate(9289800,s,'decision'))

    def test_japan_attacking_britain_does_not_count_as_indian_war(self):
        s=State(); s.wars.add(pair(('JAP','ENG')))
        self.assertFalse(self.gate(9289804,s))
        s.wars.add(pair(('IND','JAP')))
        self.assertTrue(self.gate(9289804,s)); self.choose(9289804,'a',s)
        self.assertFalse(self.gate(9289804,s))

    def test_each_release_needs_complete_legal_territory_and_liberation(self):
        for r in lib.REGIONS:
            for n,owner in enumerate(r.owners):
                s=self.lib_state(r,owner); eid=r.base+2*n
                self.assertTrue(self.gate(eid,s,'decision'),(r.key,owner))
                s.control[r.minimum[0]]='JAP'
                self.assertFalse(self.gate(eid,s,'decision'))
                s.control[r.minimum[0]]=owner; s.owned[r.minimum[0]]='JAP'
                self.assertFalse(self.gate(eid,s,'decision'))
                s.owned[r.minimum[0]]=owner; s.flags.remove(f'ind_aubm_sea_land_{r.key}_liberated')
                self.assertFalse(self.gate(eid,s,'decision'))

    def test_enemy_or_japanese_aligned_owner_cannot_be_petitioned(self):
        r=lib.REGIONS[0]; s=self.lib_state(r,'ENG')
        s.wars.add(pair(('IND','ENG'))); self.assertFalse(self.gate(r.base,s,'decision'))
        s.wars.clear(); s.alliances.add(pair(('ENG','JAP')))
        self.assertFalse(self.gate(r.base,s,'decision'))

    def test_requests_paid_once_and_refusal_cooldown(self):
        r=lib.REGIONS[0]; s=self.lib_state(r,'ENG')
        self.choose(r.base,'a',s); self.assertEqual(s.resources['money'],4900)
        self.assertFalse(self.choose(r.base,'a',s)); self.assertEqual(s.resources['money'],4900)
        self.assertTrue(self.choose(r.base+1,'b',s)); self.assertFalse(self.gate(r.base,s,'decision'))
        self.assertIn((r.base+8,'IND',180),s.queued)
        self.choose(r.base+8,'a',s); self.assertTrue(self.gate(r.base,s,'decision'))

    def test_request_resource_gates(self):
        r=lib.REGIONS[0]; s=self.lib_state(r,'ENG'); s.resources['money']=99
        self.assertFalse(self.choose(r.base,'a',s))

    def test_existing_puppet_can_gain_independence_without_re_release(self):
        r=lib.REGIONS[3]; s=self.lib_state(r,'PHI'); s.puppets['PHI']='USA'
        self.assertTrue(self.gate(r.base,s,'decision'))
        response=get(self.events[r.base+1],'action_a')
        cmds=values(response,'command')
        release=next(c for c in cmds if get(c,'type')=='independence')
        end=next(c for c in cmds if get(c,'type')=='end_mastery')
        self.assertFalse(evaluate(get(release,'trigger'),s))
        self.assertTrue(evaluate(get(end,'trigger'),s))

    def test_treaty_reward_requires_actual_sovereignty_and_live_hubs(self):
        for r in lib.REGIONS:
            s=self.partner_state(r); s.flags.remove(lib.P+r.key+'_reward')
            self.assertTrue(self.gate(r.base+6,s))
            s.puppets[r.tag]='JAP'; self.assertFalse(self.gate(r.base+6,s))
            s.puppets.clear(); s.control[r.hubs[0]]='JAP'; self.assertFalse(self.gate(r.base+6,s))

    def test_treaty_acceptance_reward_not_repeatable(self):
        r=lib.REGIONS[0]; s=self.partner_state(r)
        s.flags -= {lib.P+r.key+'_reward',lib.P+r.key+'_partner'}
        self.assertTrue(self.choose(r.base+4,'a',s))
        self.assertFalse(self.choose(r.base+4,'a',s))
        self.assertTrue(self.choose(r.base+5,'a',s))
        self.assertTrue(self.choose(r.base+6,'a',s))
        self.assertFalse(self.choose(r.base+6,'a',s))
        self.assertEqual(s.resources['tc_mod'],1)

    def test_stale_foreign_callback_does_not_release_a_country(self):
        r=lib.REGIONS[0]; s=self.lib_state(r,'ENG'); self.choose(r.base,'a',s)
        s.control[r.minimum[0]]='JAP'
        self.assertFalse(evaluate(get(get(self.events[r.base+1],'action_a'),'trigger'),s))
        self.assertTrue(self.choose(r.base+1,'c',s))
        self.assertNotIn(lib.P+r.key+'_petition',s.flags)

    def test_missing_recipient_and_route_switch_clear_pending_without_rewards(self):
        r=lib.REGIONS[0]; s=self.lib_state(r,'ENG'); self.choose(r.base,'a',s)
        s.exists.remove('ENG'); money=s.resources['money']
        self.assertTrue(self.gate(9289890,s)); self.choose(9289890,'a',s)
        self.assertNotIn(lib.P+r.key+'_petition',s.flags); self.assertEqual(s.resources['money'],money)

    def test_china_requires_three_correct_map_hubs_and_japanese_puppet(self):
        s=State(); s.exists.add('U87'); s.flags.add(lib.P+'japan_war')
        s.wars |= {pair(('IND','JAP')),pair(('IND','U87'))}; s.puppets['U87']='JAP'
        s.alliances.add(pair(('U87','JAP')))
        for p in lib.CHINA_HUBS: s.control[p]='IND'
        for p in lib.CHINA_RETURN: s.owned[p]='U87'
        s.owned[1338]='JAP'
        self.assertTrue(self.gate(9289850,s,'decision'))
        for p in lib.CHINA_HUBS:
            s.control[p]='JAP'; self.assertFalse(self.gate(9289850,s,'decision')); s.control[p]='IND'
        s.exists.add('CHI'); self.assertFalse(self.gate(9289850,s,'decision'))

    def test_chinese_reward_does_not_require_japan_to_cede_shanghai(self):
        s=State(); s.exists.add('U87'); s.flags.add(lib.P+'china_break')
        for p in lib.CHINA_RETURN: s.owned[p]='U87'; s.control[p]='U87'
        s.owned[1338]='JAP'; s.control[1338]='IND'
        s.wars.add(pair(('IND','JAP')))
        self.assertTrue(self.gate(9289852,s))

    def test_all_ui_text_fits_engine_limits(self):
        for eid,e in self.events.items():
            self.assertLessEqual(len(get(e,'desc','').encode('cp1252')),500,eid)
            for k,a in e:
                if is_action(k):
                    self.assertLessEqual(len(get(a,'name','').encode('cp1252')),58,(eid,get(a,'name')))

    def test_china_consent_changes_only_the_receiving_chinese_state(self):
        e=self.events[9289851]; self.assertEqual(get(e,'country'),'U87')
        c=values(get(e,'action_a'),'command')
        kinds=[get(x,'type') for x in c]
        self.assertIn('end_puppet',kinds); self.assertIn('leave_alliance',kinds)
        self.assertNotIn('inherit',kinds); self.assertNotIn('war',kinds); self.assertNotIn('country',kinds)
        self.assertNotIn('peace',kinds)
        withdrawal=next(x for x in c if get(x,'type')=='leave_alliance')
        self.assertEqual(get(withdrawal,'when'),'1')

    def suez_state(self):
        s=State(); s.wars.add(pair(('IND','ITA')))
        s.control.update({783:'ITA',900:'ENG',791:'EGY'}); s.garrisons[('IND',900)]=3
        return s

    def test_suez_needs_actual_threat_and_war_not_just_access(self):
        s=self.suez_state(); self.assertTrue(self.gate(9289860,s))
        s.wars.clear(); self.assertFalse(self.gate(9289860,s))
        s.wars.add(pair(('IND','ITA'))); s.control[783]='ENG'
        self.assertFalse(self.gate(9289860,s))

    def test_suez_success_and_no_repeat(self):
        s=self.suez_state(); self.choose(9289860,'a',s)
        self.assertIn((9289862,'IND',30),s.queued); self.assertFalse(self.gate(9289863,s))
        self.choose(9289862,'a',s); self.assertTrue(self.gate(9289863,s))
        self.choose(9289863,'a',s); self.assertFalse(self.gate(9289860,s))
        self.assertEqual(s.resources['supplies'],11500)

    def test_suez_interruption_cannot_be_cured_on_last_day(self):
        s=self.suez_state(); self.choose(9289860,'a',s); s.garrisons.clear()
        self.assertTrue(self.gate(9289861,s)); self.choose(9289861,'a',s)
        s.garrisons[('IND',900)]=3; self.choose(9289862,'a',s)
        self.assertFalse(self.gate(9289863,s)); self.assertTrue(self.gate(9289864,s))
        self.choose(9289864,'a',s); self.assertTrue(self.gate(9289860,s))
        self.assertEqual(s.resources['supplies'],10000)

    def test_soviet_reconstruction_not_paid_for_base_rights_or_current_war(self):
        s=State(); s.flags |= {lib.P+'soviet_war','ind_aubm_settlement_central_asia_sovereign'}; s.exists.add('UZB')
        self.assertTrue(self.gate(9289870,s,'decision'))
        s.wars.add(pair(('IND','SOV'))); self.assertFalse(self.gate(9289870,s,'decision'))
        s.wars.clear(); s.flags.remove('ind_aubm_settlement_central_asia_sovereign')
        self.assertFalse(self.gate(9289870,s,'decision'))

    def two_partner_state(self):
        s=self.partner_state(lib.REGIONS[0]); t=self.partner_state(lib.REGIONS[1])
        s.flags |= t.flags; s.exists |= t.exists; s.owned.update(t.owned); s.control.update(t.control)
        s.flags.add('ind_aubm_sea_theatre_achieved'); return s

    def test_southern_peace_needs_two_live_partners_and_actual_japan_war_ended(self):
        s=self.two_partner_state(); self.assertTrue(self.gate(9289871,s))
        s.wars.add(pair(('IND','JAP'))); self.assertFalse(self.gate(9289871,s))
        s.wars.clear(); s.puppets['INO']='JAP'; self.assertFalse(self.gate(9289871,s))

    def test_final_conference_delayed_by_any_war_and_pays_only_one_choice(self):
        s=self.two_partner_state(); s.exists.add('UZB'); s.flags |= {lib.P+'southern_peace',lib.P+'ca_reconstruction'}
        self.assertTrue(self.gate(9289872,s,'decision'))
        s.wars.add(pair(('IND','GER'))); self.assertFalse(self.gate(9289872,s,'decision'))
        s.wars.clear(); self.assertTrue(self.choose(9289872,'a',s)); self.assertFalse(self.choose(9289872,'b',s))

    def test_replacement_class_once_per_year_not_per_enemy(self):
        s=State(); s.wars.add(pair(('IND','JAP')))
        self.assertTrue(self.choose(9289880,'a',s)); self.assertEqual(s.resources['manpower'],260)
        self.assertFalse(self.choose(9289880,'a',s)); s.wars.add(pair(('IND','SOV')))
        self.assertFalse(self.choose(9289880,'a',s))
        s.year=1941; self.assertTrue(self.choose(9289880,'a',s)); self.assertEqual(s.resources['manpower'],440)
        self.assertNotIn('ind_v41_recruit_class_1941',s.flags)

    def test_replacement_class_requires_resources_size_shortage_and_relevant_war(self):
        for key,value in (('supplies',899),('money',99),('army',99),('manpower',400)):
            s=State(); s.wars.add(pair(('IND','JAP'))); s.resources[key]=value
            self.assertFalse(self.choose(9289880,'a',s),(key,value))
        s=State(); s.wars.add(pair(('IND','ITA'))); self.assertFalse(self.choose(9289880,'a',s))

    def test_all_foreign_responses_have_guarded_success_and_stale_fallback(self):
        for eid,e in self.events.items():
            if get(e,'country')=='IND': continue
            if get(e,'one_action')=='yes':
                # LIBERATOR3 has country-scoped factual/AI observers, not
                # diplomatic reply callbacks. Their single action is guarded.
                self.assertIsNotNone(get(get(e,'action_a'),'trigger'),eid)
                continue
            a=get(e,'action_a'); self.assertIsNotNone(get(a,'trigger'),eid)
            self.assertIn('ind_lib1_',str(get(a,'trigger')))
            # Deterministic settlements need only accept/stale buttons; older
            # negotiated settlements also contain refusal before stale.
            fallback=[a for k,a in e if is_action(k)][-1]
            self.assertEqual(get(fallback,'ai_chance'),'100')
            self.assertIsNotNone(get(get(fallback,'trigger',[]),'NOT'),eid)

    def test_direct_state_changes_are_confined_to_consent_events(self):
        for eid,e in self.events.items():
            for k,a in e:
                if not is_action(k): continue
                for c in values(a,'command'):
                    typ=get(c,'type')
                    self.assertNotIn(typ,('inherit','secedeprovince','country','alliance','peace'))
                    if typ=='war':
                        self.assertEqual(eid,9294005)
                        self.assertEqual(get(c,'which'),'JAP')
                        self.assertIsNone(get(e,'trigger'))  # only explicit confirmation
                    if typ=='make_puppet':
                        self.assertIn((eid,get(c,'which')),((9289905,'U87'),(9294015,'U03'),(9297005,'SIA')))
                    if typ in ('peace','leave_alliance','end_puppet'):
                        self.assertIn((eid,get(e,'country')),((9289851,'U87'),(9289904,'U87'),(9294014,'U03'),(9297004,'SIA')))
                    if typ in ('independence','end_mastery'):
                        if get(e,'country')=='IND':
                            self.assertEqual(typ,'end_mastery')
                            self.assertIn(eid,(*range(9289941,9289952,2),9294019))
                        else: self.assertIn(eid,tuple(r.base+n*2+1 for r in lib.REGIONS for n in range(len(r.owners))))


if __name__ == '__main__': unittest.main()

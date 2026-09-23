"""Static/state tests. Engine exit, peace and puppet commands are NOT simulated."""
from dataclasses import dataclass, field
from pathlib import Path
import unittest

from dh_save_spans import Node, parse, walk
from aubm_redesign_campaign_access import transform as access
from aubm_redesign_withdrawal import (
    transform, EDITED_IDS, NEW_EVENT_IDS, GENERIC_IDS, WITHDRAWALS, OUTCOMES,
    CALLBACKS, SITES, DONE, snapshot, prefix, aa, SNAPSHOT_TAGS, TREATY_DOWNGRADES,
)


@dataclass
class State:
    flags: set = field(default_factory=set)
    countries: set = field(default_factory=lambda: {'IND', 'JAP', 'SOV', 'SIA', 'U87', 'U03'})
    masters: dict = field(default_factory=dict)
    alliances: set = field(default_factory=set)
    leaders: set = field(default_factory=set)
    wars: set = field(default_factory=lambda: {frozenset(('IND', 'JAP')), frozenset(('IND', 'SOV'))})
    owners: dict = field(default_factory=dict)
    controllers: dict = field(default_factory=dict)


def evaluate(node, s):
    if not isinstance(node, Node):
        return True
    values = []
    for f in node.fields:
        k, v = f.key, f.value
        if k == 'AND': r = evaluate(v, s)
        elif k == 'OR': r = any(evaluate(Node(fields=[x]), s) for x in v.fields)
        elif k == 'NOT': r = not any(evaluate(Node(fields=[x]), s) for x in v.fields)
        elif k == 'flag': r = v in s.flags
        elif k == 'exists': r = v in s.countries
        elif k == 'ispuppet': r = v in s.masters
        elif k == 'puppet':
            tags = v.all('country'); r = s.masters.get(tags[0]) == tags[1]
        elif k in ('war', 'alliance'):
            r = frozenset(v.all('country')) in (s.wars if k == 'war' else s.alliances)
        elif k == 'participant': r = any(v.get('country') in a for a in s.alliances)
        elif k == 'alliance_leader': r = v.get('country') in s.leaders
        elif k == 'atwar': r = any(v in w for w in s.wars)
        elif k in ('owned', 'control'):
            r = (s.owners if k == 'owned' else s.controllers).get(int(v.get('province'))) == v.get('data')
        elif k == 'ai': r = v == 'no'
        else: raise AssertionError('Unmodelled predicate ' + str(k))
        values.append(r)
    return all(values)


def bookkeeping(action, state):
    """Apply only flags after an allowed click; merely report other commands."""
    if not evaluate(action.get('trigger'), state):
        return []
    effects = []
    for c in action.all('command'):
        if not evaluate(c.get('trigger'), state):
            continue
        kind, which = c.get('type'), c.get('which')
        if kind == 'setflag': state.flags.add(which)
        elif kind == 'clrflag': state.flags.discard(which)
        effects.append((kind, which, c.get('value')))
    return effects


class WithdrawalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / 'mod/db/events/aubm_v4'
        cls.source = {p.name: p.read_bytes().decode('latin1') for p in root.glob('*.txt')
                      if p.name in ('43_wartime_settlements.txt', '46_regional_campaigns.txt', '47_global_campaign_matrix.txt')}
        cls.before, _ = access(cls.source)
        cls.output, cls.records = transform(cls.before)
        cls.events = {int(e.get('id')): e for t in cls.output.values() for e in parse(t).all('event')}
        cls.original = {int(e.get('id')): e for t in cls.before.values() for e in parse(t).all('event')}

    def valid(self, p):
        return State(flags={snapshot(p), prefix(p)+'verifying', prefix(p)+'war_sov'},
                     masters={p.tag: 'IND'},
                     owners={i: p.tag for i in SITES[p.tag]},
                     controllers={i: p.tag for i in SITES[p.tag]})

    def test_exact_registered_callbacks_and_idempotence(self):
        self.assertEqual(NEW_EVENT_IDS, set(self.events)-set(self.original))
        self.assertEqual(EDITED_IDS | NEW_EVENT_IDS | GENERIC_IDS, set(self.records))
        self.assertEqual(self.output, transform(self.output)[0])
        collision = dict(self.before, bad='event = { id = 9297200 country = IND }')
        with self.assertRaisesRegex(ValueError, 'collision'):
            transform(collision)

    def test_all_withdrawals_are_minor_side_and_snapshot_only_named_major_wars(self):
        for eid, p in WITHDRAWALS.items():
            ev = self.events[eid]
            self.assertEqual(p.tag, ev.get('country'))
            a = next(a for a in aa(ev) if any(c.get('type') == 'end_puppet' for c in a.all('command')))
            cs = a.all('command')
            leave = next(c for c in cs if c.get('type') == 'leave_alliance')
            self.assertEqual('1', leave.get('when'))
            end_index = next(i for i,c in enumerate(cs) if c.get('type') == 'end_puppet')
            flags = {c.get('which') for c in cs[:end_index] if c.get('type') == 'setflag'}
            self.assertIn(snapshot(p), flags)
            for tag in SNAPSHOT_TAGS:
                self.assertIn(prefix(p)+'war_'+tag.lower(), flags)
            self.assertEqual({prefix(p)+'war_'+tag.lower() for tag in SNAPSHOT_TAGS},
                             {f for f in flags if f.startswith(prefix(p)+'war_')})
            for c in cs:
                if c.get('type') in ('access', 'relation'):
                    self.assertIsInstance(c.get('trigger'), Node)

    def test_no_indian_peace_or_compensating_war_in_unit(self):
        for eid in EDITED_IDS | NEW_EVENT_IDS:
            kinds = {c.get('type') for a in aa(self.events[eid]) for c in a.all('command')}
            self.assertFalse({'peace', 'war'} & kinds, eid)
        for eid, p in OUTCOMES.items():
            for a in aa(self.events[eid]):
                if any(c.get('type') == 'make_puppet' for c in a.all('command')):
                    self.assertEqual({'make_puppet', 'setflag', 'event'}, {c.get('type') for c in a.all('command')})
                    self.assertEqual({prefix(p)+'verifying'}, {c.get('which') for c in a.all('command') if c.get('type') == 'setflag'})

    def test_callbacks_accept_only_actual_protected_government_and_live_wars(self):
        for eid,p in CALLBACKS.items():
            success = aa(self.events[eid])[0]
            self.assertTrue(evaluate(success.get('trigger'), self.valid(p)))
            for failure in ('wrong_master', 'indian_puppet', 'japan_peace', 'unrelated_peace', 'lost_territory', 'lost_control', 'missing_token', 'no_snapshot', 'already_done'):
                s = self.valid(p)
                if failure == 'wrong_master': s.masters[p.tag] = 'JAP'
                elif failure == 'indian_puppet': s.masters['IND'] = 'ENG'
                elif failure == 'japan_peace': s.wars.remove(frozenset(('IND','JAP')))
                elif failure == 'unrelated_peace': s.wars.remove(frozenset(('IND','SOV')))
                elif failure == 'lost_territory': s.owners[SITES[p.tag][0]] = 'JAP'
                elif failure == 'lost_control': s.controllers[SITES[p.tag][0]] = 'JAP'
                elif failure == 'missing_token': s.flags.remove(prefix(p)+'verifying')
                elif failure == 'no_snapshot': s.flags.remove(snapshot(p))
                else: s.flags.add(DONE[p.tag])
                self.assertFalse(evaluate(success.get('trigger'), s), (eid,failure))
                available = [a for a in aa(self.events[eid]) if evaluate(a.get('trigger'),s)]
                self.assertEqual(1,len(available),(eid,failure))
                effects = bookkeeping(available[0],s)
                self.assertTrue(all(k == 'clrflag' for k, *_ in effects),(eid,failure))

    def test_success_releases_original_rewards_once(self):
        expected = {9297200: {('tc_mod',None,'4'),('supplies',None,'2000'),('dissent',None,'3')},
                    9297201: {('tc_mod',None,'2'),('dissent',None,'3')},
                    9297202: {('event','9297006',None),('event','9297007',None)}}
        for eid,p in CALLBACKS.items():
            s = self.valid(p)
            a = aa(self.events[eid])[0]
            self.assertTrue(expected[eid] <= set(bookkeeping(a,s)))
            self.assertFalse(evaluate(a.get('trigger'),s))
            self.assertEqual([],bookkeeping(a,s))

    def test_queued_targets_have_no_event_calendar_gates(self):
        for eid in NEW_EVENT_IDS | {9297005}:
            for key in ('trigger','date','offset','deathdate'):
                self.assertIsNone(self.events[eid].get(key),(eid,key))

    def test_siam_final_confirmation_also_withholds_on_soviet_war_loss(self):
        p = CALLBACKS[9297202]
        s = self.valid(p);s.flags.add('ind_lib1_siam_detached')
        a = aa(self.events[9297007])[0]
        self.assertTrue(evaluate(a.get('trigger'),s))
        s.wars.remove(frozenset(('IND','SOV')))
        self.assertFalse(evaluate(a.get('trigger'),s))
        effects = bookkeeping(a,s)
        self.assertNotIn(('setflag','ind_lib1_siam_protected',None),effects)
        self.assertTrue(evaluate(aa(self.events[9297007])[1].get('trigger'),s))

    def test_generic_minor_peace_has_no_japanese_puppet_bypass(self):
        for eid in GENERIC_IDS:
            before,after = aa(self.original[eid])[0],aa(self.events[eid])[0]
            # Check the newly added direct predicates separately: the existing
            # campaign predicates are preserved and remain required as well.
            old = before.get('trigger')
            new = after.get('trigger')
            self.assertIsInstance(new,Node)
            old_count = len(old.fields) if isinstance(old,Node) else 0
            added = Node(fields=new.fields[:len(new.fields)-old_count])
            tag = 'SIA' if eid in (9282212,9282260) else ('U03' if eid in (9282943,9286443,9286743) else 'U87')
            s = State()
            if eid == 9282260:
                s.flags.add('ind_aubm_regional_armistice_target_sia')
                s.wars.add(frozenset(('IND','SIA')))
            self.assertTrue(evaluate(added,s),eid)
            s.masters[tag]='JAP';self.assertFalse(evaluate(added,s),eid)
            s.masters.clear();s.alliances.add(frozenset((tag,'JAP')))
            self.assertFalse(evaluate(added,s),eid)
            s.alliances={frozenset(('IND','ENG'))};self.assertFalse(evaluate(added,s),eid)
            s.leaders.add('IND');self.assertTrue(evaluate(added,s),eid)
            s.countries.remove(tag);self.assertFalse(evaluate(added,s),'Annexed respondent cannot receive a stale settlement')
            s.countries.add(tag)
            for c in after.all('command'):
                if c.get('type')=='peace' and c.get('which') in DONE:self.assertEqual('0',c.get('value'))
            if eid == 9282260:
                s.flags.clear();s.masters['SIA']='JAP'
                self.assertTrue(evaluate(added,s),'Unrelated regional peace must not depend on Siam')
                s.flags.add('ind_aubm_regional_armistice_target_sia');s.wars.discard(frozenset(('IND','SIA')))
                self.assertFalse(evaluate(added,s),'Stale selected Siam still requires safe affiliation')

    def test_generic_prose_and_existing_nonpeace_commands_preserved(self):
        def canon(n):
            return [(f.key,canon(f.value) if isinstance(f.value,Node) else f.value) for f in n.fields]
        for eid in GENERIC_IDS:
            if eid != 9282260:self.assertEqual(self.original[eid].get('desc'),self.events[eid].get('desc'))
            else:self.assertNotIn('first becomes',self.events[eid].get('desc'))
            before = [canon(c) for a in aa(self.original[eid]) for c in a.all('command') if c.get('type')!='peace' and c.get('which') not in TREATY_DOWNGRADES]
            after = [canon(c) for a in aa(self.events[eid]) for c in a.all('command') if c.get('type')!='peace' and c.get('which') not in TREATY_DOWNGRADES]
            self.assertEqual(before,after)
            self.assertTrue(any(not a.all('command') for a in aa(self.events[eid])))

    def test_no_empty_boolean_nodes_or_false_native_proof(self):
        for eid in self.records:
            for n in walk(self.events[eid]):
                for f in n.fields:
                    if f.key in ('AND','OR','NOT'):
                        self.assertTrue(f.value.fields,eid)
            self.assertFalse(self.records[eid][0]['engine_tested'])

    def test_lost_major_war_blocks_action_and_watcher_without_an_audit_token(self):
        for eid,p in CALLBACKS.items():
            a = aa(self.events[eid])[0]
            s = self.valid(p)
            other = 'ind_exit_other_snapshot';s.flags.add(other)
            s.wars.remove(frozenset(('IND','SOV')))
            effects = bookkeeping(a,s)
            self.assertFalse(any(k in ('make_puppet','supplies','tc_mod','dissent','event') for k,*_ in effects))
            self.assertIn(snapshot(p),s.flags)
            self.assertIn(other,s.flags)
            self.assertFalse(evaluate(a.get('trigger'),s))
        # The automatic Nanjing reward watcher must stop, not refire forever.
        p = CALLBACKS[9297200]
        s = self.valid(p);s.masters.clear()
        s.flags.discard(prefix(p)+'verifying')
        s.flags.update(('ind_lib1_china_break','ind_lib1_china_reward_dummy'))
        s.wars.remove(frozenset(('IND','SOV')))
        ev = self.events[9289852]
        self.assertFalse(evaluate(ev.get('trigger'),s))
        self.assertFalse(evaluate(aa(ev)[0].get('trigger'),s))
        bookkeeping(aa(ev)[0],s)
        self.assertFalse(evaluate(ev.get('trigger'),s))

    def test_commands_and_new_predicate_sizes_bounded(self):
        for eid in EDITED_IDS | NEW_EVENT_IDS:
            ev = self.events[eid]
            for a in aa(ev):
                self.assertLessEqual(len(a.all('command')),60,eid)
                self.assertFalse(any(c.get('which','').endswith('_wars_verified') for c in a.all('command')))
            for i,a in enumerate(aa(ev)):
                n = a.get('trigger')
                previous = aa(self.original[eid]) if eid in self.original else []
                old = previous[i].get('trigger') if i<len(previous) else None
                self.assertLessEqual(n.end-n.start if n else 0,max(9999,old.end-old.start if old else 0),eid)

    def test_each_named_major_is_preserved_but_untracked_minor_wars_are_not_certified(self):
        for eid,p in CALLBACKS.items():
            a = aa(self.events[eid])[0]
            for tag in SNAPSHOT_TAGS:
                s = self.valid(p)
                s.flags.add(prefix(p)+'war_'+tag.lower())
                s.wars.add(frozenset(('IND',tag)))
                self.assertTrue(evaluate(a.get('trigger'),s),(eid,tag))
                s.wars.remove(frozenset(('IND',tag)))
                self.assertFalse(evaluate(a.get('trigger'),s),(eid,tag))
            s = self.valid(p)
            s.flags.add(prefix(p)+'war_per')
            self.assertTrue(evaluate(a.get('trigger'),s),'An untracked minor war is explicitly outside this contract')
            self.assertIn('Other wars are not checked',self.events[eid].get('desc'))
            self.assertTrue(any('not an all-war' in line for line in self.records[eid][0]['remaining']))


if __name__ == '__main__':unittest.main()

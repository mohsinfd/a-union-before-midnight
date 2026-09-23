"""Protocol simulation and byte-preservation checks, not native engine tests."""
import copy
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from dh_save_spans import Node,parse,walk,replace
import aubm_campaign_clock_fix as clocks
import aubm_diplomacy_consistency as diplomacy
import aubm_continue1_portraits as portraits


def evaluate(node,state):
    def one(k,v):
        if k in ('AND','OR','NOT'):
            values=[one(f.key,f.value) for f in v.fields]
            return all(values) if k=='AND' else any(values) if k=='OR' else not any(values)
        if k=='flag':
            if not isinstance(v,Node):return bool(state.get(v,0))
            a=state.get(v.get('which'),0);b=int(v.get('value'));op=v.get('when','1')
            return a>=b if op=='1' else a==b if op=='0' else a<=b
        if k=='exists':return state.get('exists_'+v,True)
        if k in ('war','participant'):return state.get(k,False)
        if k in ('money','supplies'):return state.get(k,10000)>=int(v)
        raise AssertionError(('Unhandled predicate',k))
    return node is None or all(one(f.key,f.value) for f in node.fields)


def execute(action,state,queue,precheck=False):
    commands=action.all('command')
    allowed=[evaluate(c.get('trigger'),state) for c in commands] if precheck else None
    for j,c in enumerate(commands):
        if not (allowed[j] if precheck else evaluate(c.get('trigger'),state)):continue
        kind=c.get('type');key=c.get('which')
        if kind=='setflag':state[key]=(state.get(key,0) if c.get('when')=='1' else 0)+int(c.get('value','1'))
        elif kind=='clrflag':state.pop(key,None)
        elif kind=='event':queue.append(int(key))


class ClockProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parts=[]
        for i in clocks.SOURCES:
            guard=f'AND = {{ exists = IND flag = world_{i} NOT = {{ flag = watch_{i} }} }}'
            parts.append(f'event = {{ id = {i} persistent = yes trigger = {{ {guard} }} action_a = {{ command = {{ type = setflag which = watch_{i} }} }} }}')
            parts.append(f'event = {{ id = {i+100000} trigger = {{ flag = watch_{i} event = {{ id = {i} days = 21 }} }} action_a = {{ command = {{ type = clrflag which = watch_{i} }} }} }}')
        cls.original={'campaign.txt':'\n'.join(parts)}
        cls.output,cls.records=clocks.transform(cls.original)
        cls.idx={int(e.get('id')):e for e in parse(cls.output['campaign.txt']).all('event')}

    def start(self,i,state,queue,pre=False):execute(self.idx[i].get('action_a'),state,queue,pre)

    def tick(self,state,queue,pre=False):
        eid=queue.pop(0);e=self.idx[eid]
        valid=[a for a in clocks.acts(e) if evaluate(a.get('trigger'),state)]
        self.assertEqual(len(valid),1)
        execute(valid[0],state,queue,pre)

    def test_all_clocks_exact_duration_and_reload_under_both_guard_timings(self):
        for i in clocks.SOURCES:
            for pre in (False,True):
                s={f'world_{i}':1};q=[];self.start(i,s,q,pre)
                for day in range(1,22):
                    s,q=copy.deepcopy((s,q)) # Only saved flags and queued IDs; no dates.
                    self.assertEqual(len(q),1)
                    self.tick(s,q,pre)
                    self.assertEqual(s[clocks.count(i)],day+1)
                    self.assertEqual(evaluate(self.idx[i+100000].get('trigger'),s),day==21)
                self.assertFalse(q);self.assertFalse(s.get(clocks.pending(i)))

    def test_cancel_then_restart_discards_old_partial_day_without_duplicate_callback(self):
        for pre in (False,True):
            i=clocks.SOURCES[0];s={f'world_{i}':1};q=[];self.start(i,s,q,pre)
            for _ in range(10):self.tick(s,q,pre)
            execute(self.idx[i+100000].get('action_a'),s,q,pre)
            self.assertFalse(s.get(clocks.count(i)));self.assertEqual(len(q),1)
            self.start(i,s,q,pre);self.assertEqual(len(q),1)
            self.tick(s,q,pre);self.assertEqual(s[clocks.count(i)],1)
            for _ in range(20):self.tick(s,q,pre)
            self.assertFalse(evaluate(self.idx[i+100000].get('trigger'),s))
            self.tick(s,q,pre);self.assertTrue(evaluate(self.idx[i+100000].get('trigger'),s));self.assertFalse(q)

    def test_lost_hold_is_invalidated_and_bootstrap_restarts_at_zero(self):
        i=clocks.SOURCES[0];s={f'world_{i}':1};q=[];self.start(i,s,q)
        for _ in range(10):self.tick(s,q)
        s[f'world_{i}']=0;self.tick(s,q)
        self.assertFalse(q);self.assertFalse(s.get(clocks.count(i)))
        s[f'world_{i}']=1
        execute(self.idx[clocks.BOOT].get('action_a'),s,q)
        self.assertEqual(s[clocks.count(i)],1);self.assertEqual(q,[clocks.CALLBACKS[i]])

    def test_protectorate_age_continues_through_temporary_world_change(self):
        i=clocks.SOURCES[-1];s={f'world_{i}':1};q=[];self.start(i,s,q)
        s[f'world_{i}']=0
        for _ in range(21):self.tick(s,q)
        self.assertEqual(s[clocks.count(i)],22)

    def test_bootstrap_preserves_partial_progress_and_does_not_duplicate(self):
        for pre in (False,True):
            i=clocks.SOURCES[0];s={f'world_{i}':1,f'watch_{i}':1,clocks.count(i):9};q=[]
            execute(self.idx[clocks.BOOT].get('action_a'),s,q,pre)
            execute(self.idx[clocks.BOOT].get('action_a'),s,q,pre)
            self.assertEqual(s[clocks.count(i)],9);self.assertEqual(len(q),1)

    def test_idempotence_callback_format_and_no_timestamp_dependency(self):
        self.assertEqual(clocks.transform(self.output)[0],self.output)
        for i in clocks.CALLBACKS.values():
            e=self.idx[i]
            for k in ('trigger','date','offset','deathdate','save_date'):self.assertIsNone(e.get(k))
            self.assertEqual(e.get('persistent'),'yes');self.assertEqual(e.get('name'),'AI_EVENT')
        self.assertFalse(any(n.get('days') is not None for n in walk(parse(self.output['campaign.txt']))))
        with self.assertRaises(ValueError):clocks.transform({'campaign.txt':self.original['campaign.txt']+f'\nevent = {{ id = {clocks.BOOT} }}'})


class DiplomacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source={'d.txt':(Path(__file__).parent/'fixtures/continue1_diplomacy.txt').read_bytes().decode('latin1')}
        cls.output,_=diplomacy.transform(cls.source)
        cls.idx={int(e.get('id')):e for e in parse(cls.output['d.txt']).all('event')}

    def test_every_council_choice_synchronizes_legacy_and_current_programmes(self):
        expected={(9280501,'a'):'nam',(9280501,'b'):'european',(9280501,'c'):'socialist',
                  (9280502,'a'):'european',(9280502,'b'):'asian',(9280502,'c'):'asian',(9280502,'d'):'nam'}
        for (i,a),program in expected.items():
            s=dict.fromkeys(diplomacy.PROGRAMS+diplomacy.ORIENTATIONS,1)
            execute(self.idx[i].get('action_'+a),s,[])
            self.assertEqual({f for f in diplomacy.PROGRAMS if f.startswith('ind_v42') and s.get(f)}, {'ind_v42_program_'+program})
            self.assertEqual({f for f in diplomacy.PROGRAMS[:3] if s.get(f)},set() if program=='nam' else {'ind_v3_'+{'european':'european_balance','asian':'asian_security','socialist':'socialist_compact'}[program]})
            if program!='european':self.assertFalse(evaluate(self.idx[9270401].get('decision'),s))
        s={};execute(self.idx[9280502].get('action_c'),s,[])
        self.assertTrue(s['ind_v3_non_aligned']);self.assertTrue(s['ind_v3_independent_asia'])

    def test_current_european_choice_remains_available_but_conflicts_and_commitments_block_it(self):
        e=self.idx[9270401];s={'ind_v3_european_balance':1,'ind_v42_program_european':1}
        self.assertTrue(evaluate(e.get('decision'),s));self.assertTrue(evaluate(e.get('decision_trigger'),s))
        for conflict in ('ind_v3_non_aligned','ind_v3_soviet_orientation','ind_v4_strategy_japan','ind_aubm_diplomatic_negotiation_pending','ind_aubm_commitment_allied','ind_v4a_treaty_formal_alliance'):
            bad=dict(s);bad[conflict]=1
            self.assertFalse(evaluate(e.get('decision'),bad))
            for a in clocks.acts(e):self.assertFalse(evaluate(a.get('trigger'),bad))
        for a,orientation in [('a','ind_v3_allied_orientation'),('b','ind_v3_axis_orientation')]:
            chosen=dict(s);execute(e.get('action_'+a),chosen,[])
            self.assertEqual({f for f in diplomacy.ORIENTATIONS if chosen.get(f)},{orientation})
            self.assertFalse(evaluate(e.get('decision'),chosen))

    def test_costs_wars_alliances_and_nonflag_commands_unchanged(self):
        def commands(t):
            return [(int(e.get('id')),t[c.start:c.end]) for e in parse(t).all('event') for a in clocks.acts(e) for c in a.all('command') if c.get('type') not in ('setflag','clrflag')]
        self.assertEqual(commands(self.source['d.txt']),commands(self.output['d.txt']))
        self.assertEqual(diplomacy.transform(self.output)[0],self.output)


class PortraitTests(unittest.TestCase):
    def test_only_reserve_picture_columns_change_and_all_64_faces_are_used(self):
        raw=(portraits.ROOT/'mod/db/leaders/india.csv').read_bytes();new,mapping=portraits.roster(raw)
        self.assertEqual(len(mapping),375);self.assertEqual(len(set(mapping.values())),64)
        for a,b in zip(raw.splitlines(),new.splitlines()):
            ar=a.split(b';');br=b.split(b';')
            if ar!=br:ar[14]=br[14]
            self.assertEqual(ar,br)
        self.assertEqual(portraits.roster(new)[0],new)

    def test_save_migration_changes_only_matching_indian_reserve_picture(self):
        raw=b'header = { name = "keep" } country = { tag = IND leader = { id = { type = 6 id = 252000 } skill = 5 picture = "old" } leader = { id = { type = 6 id = 1 } picture = "history" } } country = { tag = ENG leader = { id = { type = 6 id = 252000 } picture = "old" } }'
        new,n=portraits.migrate(raw,{252000:'new'})
        self.assertEqual(n,1);self.assertEqual(new,raw.replace(b'picture = "old"',b'picture = "new"',1))

    def test_new_bitmaps_are_unique_rgb_36_by_50(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);portraits.pack(p)
            files=list(p.glob('*.bmp'));self.assertEqual(len(files),16)
            self.assertEqual(len({f.read_bytes() for f in files}),16)
            for f in files:
                with Image.open(f) as im:self.assertEqual((im.size,im.mode),((36,50),'RGB'))

if __name__=='__main__':unittest.main()

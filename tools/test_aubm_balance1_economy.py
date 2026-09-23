"""Regression checks on actual installed baseline; never mutates the game."""
import os
from pathlib import Path
import unittest
import aubm_balance1_economy as b
from dh_save_spans import parse, walk, Node

SNAPSHOT = Path(__file__).resolve().parents[1]/'build/balance1/baseline'
BASE = Path(os.environ.get('AUBM_TEST_MOD', str(SNAPSHOT) if SNAPSHOT.exists() else r'C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1'))
PATHS = ['db/events/india_v3/'+p+'.txt' for p in ['20_development','22_resources','32_navy']] + ['db/events/aubm_v4/05_union_integration.txt']

def index(files):
    return {int(e.get('id')):e for t in files.values() for e in parse(t).all('event')}

class EconomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source={p:(BASE/p).read_bytes().decode('latin1') for p in PATHS}
        cls.out,cls.records=b.transform(cls.source)
        cls.events=index(cls.out)

    def test_idempotence(self):
        out,records=b.transform(self.out)
        self.assertEqual(out,self.out)
        self.assertEqual(records,[])

    def test_preserve_unowned_events(self):
        owned=set(b.PLANS)|{9271111,9271112,9297180,9297181,9297182}
        for p,old in self.source.items():
            new=self.out[p]
            newer={e.get('id'):new[e.start:e.end] for e in parse(new).all('event')}
            for e in parse(old).all('event'):
                if int(e.get('id')) not in owned:
                    self.assertEqual(old[e.start:e.end],newer[e.get('id')])

    def test_factory_and_output_budgets(self):
        before=index(self.source)
        ids=list(range(9270200,9270207))
        def maximum(events):
            return sum(max(sum(float(c.get('value',0)) for c in a.value.all('command') if c.get('type')=='construct' and c.get('which')=='ic') for a in b.actions(events[i])) for i in ids)
        self.assertEqual(maximum(before),140)
        self.assertEqual(maximum(self.events),114)
        for e in [self.events[i] for i in b.PLANS]:
            for a in b.actions(e):
                for c in a.value.all('command'):
                    if c.get('type')=='industrial_modifier' and c.get('which') in ('ic','total'):
                        self.assertLessEqual(float(c.get('value')),2)

    def test_all_paid_choices_guard_gross_cost_and_sites(self):
        for eid,(_,plans) in b.PLANS.items():
            e=self.events[eid]
            for af in b.actions(e)[:len(plans)]:
                gate=af.value.get('trigger')
                cmds=af.value.all('command')
                required=parse(b.requirements(cmds))
                for f in required.fields:
                    self.assertIn(f.key,[x.key for x in gate.fields],(eid,f.key))
                    if not isinstance(f.value,Node):
                        self.assertIn(f.value,gate.all(f.key),(eid,f.key,f.value))
                    else:
                        self.assertTrue(any(v.get('province')==f.value.get('province') and v.get('data')=='IND' for v in gate.all(f.key)))
                old=b.actions(index(self.source)[eid])[b.actions(e).index(af)].value
                old_flags=[c.get('which') for c in old.all('command') if c.get('type')=='setflag']
                self.assertEqual(old_flags,[c.get('which') for c in cmds if c.get('type')=='setflag'])

    def test_naval_discount_state_cycle(self):
        def effects(eid,war):
            totals={h:0 for h in b.HULLS}
            for af in b.actions(self.events[eid]):
                for c in af.value.all('command'):
                    if c.get('type')!='build_time':continue
                    t=c.get('trigger',Node())
                    if t.get('atwar')=='yes' and not war:continue
                    totals[c.get('which')]+=int(c.get('value'))
            return totals
        self.assertEqual(set(effects(9271111,False).values()),{-25})
        self.assertEqual(set(effects(9271111,True).values()),{-40})
        fleet=effects(9271111,False)
        for _ in range(5):
            fleet={h:v+effects(9297182,True)[h] for h,v in fleet.items()}
            self.assertEqual(set(fleet.values()),{-40})
            fleet={h:v+effects(9297181,False)[h] for h,v in fleet.items()}
            self.assertEqual(set(fleet.values()),{-25})
        # No build-cost or naval combat-stat additions in this overlay.
        for eid in (9271111,9271112,9297180,9297181,9297182):
            self.assertEqual([c.get('value') for n in walk(self.events[eid]) for c in n.all('command') if c.get('type')=='build_cost'],[])

    def test_late_projects_one_time_and_cancel(self):
        for eid in b.NEW_EVENT_IDS:
            e=self.events[eid];acts=b.actions(e)
            self.assertEqual(len(acts),3)
            flags=[]
            for af in acts[:2]:
                a=af.value
                flag=[c.get('which') for c in a.all('command') if c.get('type')=='setflag'][0]
                flags.append(flag)
                self.assertTrue(any(n.get('flag')==flag for n in a.get('trigger').all('NOT')))
                self.assertTrue(any(n.get('flag')==flag for n in e.get('decision').all('NOT')))
                self.assertGreater(float(a.get('trigger').get('money')),0)
                self.assertFalse(any(c.get('type') in ('construct','industrial_modifier','event') for c in a.all('command')))
            self.assertEqual(flags[0],flags[1])
            self.assertEqual(acts[2].value.all('command'),[])

    def test_presentation(self):
        for eid in set(b.PLANS)|b.NEW_EVENT_IDS:
            e=self.events[eid]
            self.assertLessEqual(len(e.get('desc')),520)
            self.assertNotIn('\xa7',e.get('desc'))
            for af in b.actions(e):self.assertLessEqual(len(af.value.get('name')),100)

if __name__=='__main__':unittest.main()

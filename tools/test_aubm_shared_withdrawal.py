import unittest
from dh_save_spans import parse
from aubm_shared_withdrawal import EXITS,BASE,detached,protected,prefix,transform,aa
from test_aubm_cleanup import permits
from test_aubm_liberator import State,pair
import build_aubm_cleanup as build

class SharedWithdrawalTests(unittest.TestCase):
    def check(self,gate,s):return permits(parse('trigger = { '+gate+' }').get('trigger'),s)
    def state(self,p):
        s=State();s.exists.add(p.tag);s.wars.add(pair(('IND','JAP')));return s
    def test_all_policies_require_master_war(self):
        for p in EXITS:
            s=self.state(p);self.assertTrue(self.check(detached(p),s))
            s.wars.clear();self.assertFalse(self.check(detached(p),s))
    def test_every_recorded_other_war_is_required(self):
        for p in EXITS:
            s=self.state(p);s.flags.add(prefix(p)+'war_sov')
            self.assertFalse(self.check(detached(p),s))
            s.wars.add(pair(('IND','SOV')));self.assertTrue(self.check(detached(p),s))
    def test_minor_alliances_and_old_masters_block_all(self):
        for p in EXITS:
            s=self.state(p);s.alliances.add(pair((p.tag,'AFG')))
            self.assertFalse(self.check(detached(p),s))
            s.alliances.clear();s.puppets[p.tag]='JAP';self.assertFalse(self.check(detached(p),s))
    def test_actual_indian_puppet_required_before_rewards(self):
        for p in EXITS:
            s=self.state(p);self.assertFalse(self.check(protected(p),s))
            s.puppets[p.tag]='IND';self.assertTrue(self.check(protected(p),s))
            s.wars.clear();self.assertFalse(self.check(protected(p),s))
    def test_compiled_coverage_and_deferred_rewards(self):
        source=build.load_sources()['db/events/aubm_v4/43_wartime_settlements.txt']
        result=transform(source);events={int(e.get('id')):e for e in parse(result).all('event')}
        self.assertTrue(all(i in events for i in range(BASE,BASE+3)))
        for p in EXITS:
            for eid in p.withdrawals:self.assertIn(prefix(p)+'war_sov',result[events[eid].start:events[eid].end])
            for eid in p.outcomes:
                for a in aa(events[eid]):
                    types=[c.get('type') for c in a.all('command')]
                    if 'make_puppet' in types:self.assertEqual(types,['make_puppet','setflag','event'])
        with self.assertRaises(ValueError):transform(source,EXITS[:-1])

if __name__=='__main__':unittest.main()

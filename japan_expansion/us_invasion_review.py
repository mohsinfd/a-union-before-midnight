"""Regression cases for US invasion terms; deliberately no engine execution."""
import copy
import json
from pathlib import Path
import unittest
from simulate import World,BY_KEY,MAP_AREAS
from build import HERE,TARGET,VERSION,read,parse,get,getall,compiled_event,resolve
import us_invasion as inv


class USInvasionTests(unittest.TestCase):
    def world(self):
        w=World();w.year=1943;w.national_losses['USA']=40
        w.owned[1874]='USA';w.controlled[1874]='JAP'
        w.addwar('USA','GER');w.addwar('GER','ENG')
        return w

    def eligible(self,w):
        return w.year>=BY_KEY['us_mainland'].year and w.test(parse(BY_KEY['us_mainland'].gate),'JAP')

    def choose(self,w,level=1):
        self.assertTrue(self.eligible(w));self.assertTrue(w.action('us_national_terms',level))

    def test_boundary_year_loss_and_all_four_ports(self):
        w=self.world();self.assertTrue(self.eligible(w))
        w.year=1942;self.assertFalse(self.eligible(w));w.year=1943
        w.national_losses['USA']=39.9;self.assertFalse(self.eligible(w));w.national_losses['USA']=40
        for p in inv.PORTS:
            w.controlled[1874]='USA';w.controlled[p]='JAP';self.assertTrue(self.eligible(w));w.controlled[p]='USA'
        self.assertFalse(self.eligible(w))

    def test_wait_returns_and_is_not_permanent_dismissal(self):
        w=self.world();w.action('us_mainland',1);self.assertFalse(self.eligible(w))
        w.advance(89);self.assertFalse(self.eligible(w));w.advance(1);self.assertTrue(self.eligible(w))
        self.assertNotIn('JX_US_MAINLAND_OFFERED',w.flags)
        w.action('us_mainland',2);w.advance(100);self.assertFalse(self.eligible(w))

    def test_refusal_preserves_wars_and_retry(self):
        w=self.world();self.choose(w);w.queue=[]
        self.assertTrue(w.action('us_inv_offer',4));w.advance(1)
        self.assertTrue(w.atwar('JAP','USA'));self.assertNotIn('JX_US_INV_PENDING',w.flags)
        w.advance(90);self.assertTrue(self.eligible(w));self.assertTrue(w.flags['JX_US_INV_REFUSED_ONCE'])

    def test_two_refusals_enable_only_acceptance_on_next_qualifying_offer(self):
        w=self.world()
        for _ in range(2):
            self.choose(w);w.queue=[];self.assertTrue(w.action('us_inv_offer',4));w.advance(91)
        self.choose(w);w.queue=[]
        self.assertFalse(w.action('us_inv_offer',4));self.assertTrue(w.action('us_inv_offer',5))
        w.advance(8);self.assertTrue(w.flags['JX_US_INV_DONE'])

    def test_west_coast_needs_whole_area_not_just_port(self):
        w=self.world();self.assertFalse(w.action('us_national_terms',3))
        for p in MAP_AREAS['Washington']:w.owned[p]='USA';w.controlled[p]='JAP'
        self.assertTrue(w.action('us_national_terms',3));w.advance(8)
        for p in MAP_AREAS['Washington']|MAP_AREAS['Oregon']:
            # Only actual American-owned land is promised.
            if w.flags.get('JX_US_INV_LAND_'+str(p)+'_JAP'):self.assertEqual(w.owned[p],'JAP')
        self.assertTrue(w.flags['JX_US_INV_DONE'])

    def test_lost_port_before_offer_aborts_without_peace(self):
        w=self.world();self.choose(w);w.controlled[1874]='USA';w.advance(2)
        self.assertTrue(w.atwar('USA','JAP'));self.assertNotIn('JX_US_INV_PENDING',w.flags)
        self.assertNotIn('JX_US_INV_DONE',w.flags)

    def test_third_party_property_is_not_awarded_and_us_occupation_returns_under_peace(self):
        w=self.world();ps=[p for p,t in inv.REPORT['claims'] if t=='JAP' and p not in inv.PORTS][:3]
        self.assertEqual(len(set(ps)),3)
        a,b,c=ps
        w.owned[a]='ENG';w.controlled[a]='JAP'
        w.owned[b]='USA';w.controlled[b]='GER'
        w.owned[c]='USA';w.controlled[c]='USA'
        self.choose(w,2);w.advance(1)
        self.assertEqual(w.owned[b],'USA');self.assertEqual(w.controlled[b],'GER')
        w.advance(7)
        self.assertEqual(w.owned[a],'ENG');self.assertEqual(w.controlled[a],'JAP')
        self.assertEqual(w.owned[b],'USA');self.assertEqual(w.controlled[b],'USA')
        self.assertEqual(w.owned[c],'JAP');self.assertTrue(w.flags['JX_US_INV_DONE'])

    def test_failed_transfer_never_orders_peace_or_claims_success(self):
        w=self.world();p=next(p for p,t in inv.REPORT['claims'] if t=='JAP' and p not in inv.PORTS)
        w.owned[p]='USA';w.controlled[p]='USA';w.blocked_transfers.add(p)
        self.choose(w,2);w.advance(12)
        self.assertIn('us_inv_failed',w.received);self.assertNotIn('us_inv_peace',w.received)
        self.assertTrue(w.atwar('USA','JAP'));self.assertNotIn('JX_US_INV_DONE',w.flags)
        self.assertEqual(w.received.count('us_inv_land'),3);self.assertEqual(w.properties['USA','dissent',None,None],0)

    def test_transient_transfer_failure_recovers_before_peace(self):
        w=self.world();p=next(p for p,t in inv.REPORT['claims'] if t=='JAP' and p not in inv.PORTS)
        w.owned[p]='USA';w.controlled[p]='USA';w.blocked_transfers.add(p)
        self.choose(w,2);w.advance(2);self.assertTrue(w.atwar('USA','JAP'))
        w.blocked_transfers.clear();w.advance(8)
        self.assertEqual(w.owned[p],'JAP');self.assertTrue(w.flags['JX_US_INV_DONE'])

    def test_national_surrender_ends_us_wars_without_ending_other_countries_wars(self):
        w=self.world();self.choose(w,0);w.advance(8)
        self.assertFalse(w.atwar('USA','JAP'));self.assertFalse(w.atwar('USA','GER'))
        self.assertTrue(w.atwar('GER','SOV'));self.assertTrue(w.atwar('GER','ENG'))
        self.assertTrue(w.atwar('JAP','SOV'));self.assertTrue(w.atwar('JAP','ENG'))
        self.assertEqual(w.properties['USA','dissent',None,None],10)

    def test_duplicate_callbacks_cannot_repeat_dissent_or_rewards(self):
        w=self.world();self.choose(w,1);w.advance(8);before=dict(w.properties)
        for key in ('us_inv_snapshot','us_inv_land','us_inv_check','us_inv_peace','us_inv_signed'):w.dispatch(key) if any(not a.gate or w.test(parse(a.gate),'USA' if key in {'us_inv_snapshot','us_inv_land','us_inv_peace'} else 'JAP') for a in BY_KEY[key].actions) else None
        w.advance(10);self.assertEqual(dict(w.properties),before)
        self.assertEqual(w.properties['JAP','dissent',None,None],-2)

    def test_armistice_and_national_surrender_cannot_overlap(self):
        w=self.world();w.flags['JX_US_PENDING']=1;self.assertFalse(self.eligible(w));w.flags.pop('JX_US_PENDING')
        self.choose(w);self.assertFalse(w.test(parse(BY_KEY['us_peace'].gate),'JAP'))

    def test_pending_save_model_roundtrip_keeps_provincial_promises(self):
        w=self.world();self.choose(w,2);w.advance(1)
        restored=copy.deepcopy(w);w.advance(12);restored.advance(12)
        self.assertEqual(restored.flags,w.flags);self.assertEqual(restored.owned,w.owned);self.assertEqual(restored.wars,w.wars)

    def test_changed_control_during_handover_prevents_force_secession(self):
        w=self.world();p=next(p for p,t in inv.REPORT['claims'] if t=='JAP' and p not in inv.PORTS)
        w.owned[p]='USA';w.controlled[p]='USA';w.blocked_transfers.add(p)
        self.choose(w,2);w.advance(1);w.controlled[p]='SOV';w.blocked_transfers.clear();w.advance(12)
        self.assertEqual(w.owned[p],'USA');self.assertEqual(w.controlled[p],'SOV')
        self.assertTrue(w.atwar('USA','JAP'));self.assertNotIn('JX_US_INV_DONE',w.flags)

    def test_stale_offer_cannot_start_a_second_peace_after_success(self):
        w=self.world();self.choose(w,2);w.advance(10);before=copy.deepcopy(w.flags)
        for i in range(len(BY_KEY['us_inv_offer'].actions)):self.assertFalse(w.action('us_inv_offer',i))
        self.assertEqual(w.flags,before)

    def test_duplicate_acceptance_and_snapshot_do_not_reset_pending_promises(self):
        w=self.world();self.choose(w,2);w.advance(1)
        before=copy.deepcopy(w.flags)
        self.assertFalse(w.action('us_inv_offer',6));self.assertFalse(w.action('us_inv_snapshot'))
        self.assertEqual(w.flags,before);w.advance(10)
        self.assertEqual(w.properties['USA','dissent',None,None],30)

    def test_legacy_refusal_flag_does_not_disable_new_menu(self):
        w=self.world();w.flags['JX_US_MAINLAND_OFFERED']=1
        self.assertTrue(self.eligible(w));self.choose(w);w.advance(8);self.assertTrue(w.flags['JX_US_INV_DONE'])


def installed_checks():
    root=getall(parse(read(TARGET/'db/events/USA.txt')),'event')
    for eid in inv.REPORT['protected_native_ids']:
        node=next(n for n in root if get(n,'id')==str(eid))
        assert 'JX_ACTIVE' in str(get(node,'trigger'))
        for a in getall(node,'action')[:-1]:assert 'JX_ACTIVE' in str(get(a,'trigger'))
        assert not get(getall(node,'action')[-1],'command') or get(getall(node,'action')[-1],'command')==[]
    # No stock demand/acceptance calls or original allocation flags survive.
    for key,e in BY_KEY.items():
        if key not in {'us_mainland','us_national_terms'} and e.module!='usa_invasion':continue
        text=compiled_event(e)
        assert not any('which = '+str(n) in text for n in (2011031,2049047,2049046))
        assert 'japclaim' not in text and 'jappeace' not in text
        if e.desc:
            assert all(len(a.gate)<2500 and len(a.commands)<=10 for a in e.actions),'Large visible tooltip '+key
    installed={get(e,'id'):e for e in getall(parse(read(TARGET/'db/events/japan_rising/usa_invasion.txt')),'event')}
    for e in BY_KEY.values():
        if e.module=='usa_invasion':assert installed[str(e.id)]==get(parse(compiled_event(e)),'event')
    old=json.loads((HERE/'backups/before_R7_20261111/events.json').read_text())
    assert all(BY_KEY[e['key']].id==e['id'] for e in old)
    # R7 deliberately changes preparation and fuel. US settlement
    # definitions must remain exactly equal; country-flow changes are tested by FLOW_review.
    # Compare to the prior installed R6 catalogue.
    from dataclasses import asdict
    for record in old:
        if record['module'] not in {'usa','usa_invasion'}:continue
        current=asdict(BY_KEY[record['key']]);current['gate']=resolve(current['gate']);current['ready']=resolve(current['ready'])
        for action in current['actions']:
            action['gate']=resolve(action['gate']);action['commands']=[resolve(c) for c in action['commands']]
        prior={k:v for k,v in record.items() if k!='follows'}
        assert current==prior,record['key']
    return len(old)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(USInvasionTests))
    preserved=installed_checks() if result.wasSuccessful() else 0
    report={'result':'PASS' if result.wasSuccessful() else 'FAIL','version':VERSION,'tests':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'prior_event_ids_preserved':preserved,
            'game_executed':False,'scope':'Source/installed checks and documented-command state model; not engine save/reload or AI probability measurement',**inv.REPORT}
    (HERE/'US_INVASION_REVIEW.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

"""Regress the actual R15 failure with persistent-event history unavailable."""
import copy,json,unittest,gzip
from pathlib import Path
import build as b
from FLOW_review import HumanWorld
from PREWAR_review import World as PrewarWorld
from simulate import BY_KEY,BY_ID
import timer_reliability as timers

b.prepare_catalog()
BY_KEY.update({e.key:e for e in b.EVENTS});BY_ID.update({str(e.id):e for e in b.EVENTS})


class NativeHistoryWorld(HumanWorld,PrewarWorld):
    def action(self,key,index=0):
        result=super().action(key,index)
        e=BY_KEY[key]
        if e.persistent or e.triggered:self.history.pop(str(e.id),None)
        return result


class TimerReview(unittest.TestCase):
    def world(self):
        w=NativeHistoryWorld();w.flags.pop('JX_PACIFIC',None);w.wars.clear()
        w.year=1934;w.technologies=None
        for p in (1557,1552,1554,1549):
            w.owned[p]=w.controlled[p]='JAP';w.buildings[p,'infrastructure']=.6
            w.buildings[p,'flak']=0
        return w

    def test_original_failure_is_reproduced_without_persistent_history(self):
        w=self.world();w.flags['JX_prewar_rural_works_PENDING']=1
        w.flags['JX_prewar_rural_works_SELECTED_0']=1;w.day=300
        old=json.loads(gzip.decompress((b.HERE/'R15_BASELINE_EVENTS.json.gz').read_bytes()))
        finish=next(e for e in old if e['key']=='prewar_rural_works_finish_0')
        self.assertFalse(w.test(b.parse(finish['actions'][0]['gate']),'JAP'))
        self.assertTrue(w.test(b.parse(finish['actions'][2]['gate']),'JAP'))

    def test_nagoya_delivers_once_at_270_days_without_history(self):
        w=self.world();before=w.buildings[1557,'ic'];money=w.resources['JAP']['money']
        self.assertTrue(w.action('prewar_rural_works',0));w.advance(269)
        self.assertEqual(w.buildings[1557,'ic'],before)
        w.dispatch('prewar_rural_works_finish_0');self.assertEqual(w.buildings[1557,'ic'],before)
        # Save/load: only queue, flags and ordinary game state survive.
        w=copy.deepcopy(w);w.history={};w.advance(1)
        self.assertEqual(w.buildings[1557,'ic'],before+3)
        self.assertTrue(w.flags['JX_prewar_rural_works_DONE'])
        self.assertFalse(w.flags.get('JX_prewar_rural_works_PENDING'))
        self.assertEqual(w.resources['JAP']['money'],money-45)
        w.dispatch('prewar_rural_works_finish_0');w.advance(10)
        self.assertEqual(w.buildings[1557,'ic'],before+3)

    def test_lost_site_refunds_exactly_once(self):
        w=self.world();before=copy.deepcopy(w.resources['JAP'])
        w.action('prewar_rural_works',0);w.controlled[1557]='CHI';w.advance(270)
        self.assertEqual(w.resources['JAP'],before)
        self.assertTrue(w.flags['JX_prewar_rural_works_CANCELLED'])
        w.dispatch('prewar_rural_works_finish_0');self.assertEqual(w.resources['JAP'],before)

    def test_reserve_branch_and_all_six_prewar_programmes_mature(self):
        import prewar_content
        for spec in prewar_content.programmes():
            for i,choice in enumerate(spec.choices):
                w=self.world();w.year=1940
                self.assertTrue(w.action(spec.key,i),(spec.key,i))
                w.advance(spec.days)
                self.assertTrue(w.flags.get('JX_'+spec.key+'_DONE'),(spec.key,i))
                self.assertFalse(w.flags.get('JX_'+spec.key+'_PENDING'),(spec.key,i))

    def test_all_old_ids_and_decisions_preserved_and_no_history_dependencies(self):
        old=json.loads(gzip.decompress((b.HERE/'R15_BASELINE_EVENTS.json.gz').read_bytes()))
        for e in old:self.assertEqual(BY_KEY[e['key']].id,e['id'])
        self.assertEqual(sum(e.decision for e in b.EVENTS),128)
        self.assertEqual(len(timers.REPORT['pairs']),len(set((r['source'],r['days']) for r in timers.REPORT['pairs'])))
        for e in b.EVENTS:
            for text in [e.gate,e.ready]+[a.gate for a in e.actions]+[c for a in e.actions for c in a.commands]:
                self.assertIsNone(timers.PATTERN.search(text),e.key)


if __name__=='__main__':unittest.main(verbosity=2)

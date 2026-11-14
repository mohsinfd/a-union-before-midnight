"""Raw native-token, delayed-reward and finite-import regression tests."""
import copy,re,unittest
import build as b
import purchase_reliability as p
from timer_reliability_review import NativeHistoryWorld
from simulate import BY_KEY,BY_ID

b.prepare_catalog();BY_KEY.update({e.key:e for e in b.EVENTS});BY_ID.update({str(e.id):e for e in b.EVENTS})


class ImportWorld(NativeHistoryWorld):
    def __init__(self):super().__init__();self.embargoes=set()
    def test(self,node,actor):
        for key,value in node:
            if key=='embargo':
                tags=b.getall(value,'country')
                if tuple(tags) not in self.embargoes:return False
            elif not super().test([(key,value)],actor):return False
        return True
    def command(self,node,actor):
        if b.get(node,'type')=='end_trades':
            parties={b.get(node,'which'),b.get(node,'where')}
            self.trades=[x for x in self.trades if {x['which'],x['where']}!=parties]
        else:
            super().command(node,actor)
            if b.get(node,'type')=='trade':self.trades[-1]['protected']=b.get(node,'value')=='1'


class PurchaseReview(unittest.TestCase):
    def test_quoted_symbolic_references_render_as_native_integer_tokens(self):
        key='prewar_deck_commission_finish_0'
        self.assertEqual(b.resolve('which = "@'+key+'"'),'which = '+str(b.IDS[key]))
        self.assertEqual(b.resolve('which = @'+key),'which = '+str(b.IDS[key]))
        for text in ('type = event which = "28601743" when = 240',
                     'type = trigger which = "28601743"','type = event which = @unresolved',
                     'type = event which = 0','type = event which = 2147483648'):
            with self.assertRaises(ValueError):b.check_native_event_target(text)

    def test_every_native_dispatch_is_checked_before_parsing(self):
        count=0
        for e in b.EVENTS:
            native=b.compiled_event(e)
            for a in e.actions:
                for command in a.commands:
                    text=b.resolve(command);b.check_native_event_target(text)
                    if re.search(r'\btype\s*=\s*(event|trigger)\b',text):count+=1
            self.assertNotRegex(native,r'\bwhich\s*=\s*"286\d+"',e.key)
        self.assertGreater(count,100)

    def world(self):
        w=ImportWorld();w.wars.clear();w.flags.pop('JX_PACIFIC',None);w.year=1936
        w.resources['JAP'].update(money=1000,supplies=10000,oil=1000)
        return w

    def test_all_paid_import_variants_keep_rates_duration_and_do_not_repeat(self):
        for row in p.REPORT['contracts']:
            w=self.world();start=copy.deepcopy(w.resources['JAP'])
            self.assertTrue(w.action(row['event'],row['choice']))
            self.assertEqual(len(w.trades),1)
            trade=w.trades[0]
            self.assertTrue(trade['protected'])
            for key in ('oil','metal','supplies','money'):self.assertEqual(trade['flows'].get(key,0),row[key])
            self.assertEqual(trade['end']-w.day,row['days'])
            self.assertFalse(w.action(row['event'],row['choice']));self.assertEqual(len(w.trades),1)
            self.assertLess(w.resources['JAP']['money'],start['money'])

    def test_protected_imports_expire_without_renewing(self):
        w=self.world();w.action('fx1933',0);w.advance(720)
        stock=w.resources['JAP']['oil'];w.advance(10)
        self.assertEqual(w.resources['JAP']['oil'],stock);self.assertFalse(w.action('fx1933',0))

    def test_actual_war_or_embargo_stops_contracts_and_payments_once(self):
        for mode in ('war','embargo'):
            w=self.world();w.action('fx1933',0);w.action('oil1934',0)
            self.assertFalse(w.action('paid_us_imports_end'))
            if mode=='war':w.addwar('JAP','USA')
            else:w.embargoes.add(('USA','JAP'))
            self.assertTrue(w.action('paid_us_imports_end'))
            self.assertFalse(w.trades);self.assertFalse(w.action('paid_us_imports_end'))


if __name__=='__main__':unittest.main(verbosity=2)

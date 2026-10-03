"""Read-only integration checks against the explicitly selected campaign."""
from decimal import Decimal
from pathlib import Path
import unittest
from dh_save_spans import parse, walk
from repair_naval1_save import recover, ORDERS

MOD = Path('C:/Program Files (x86)/Steam/steamapps/common/Darkest Hour A HOI Game/Mods/AUBM Terrain Prototype P1')


@unittest.skipUnless((MOD/'scenarios/save games/autosave.eug').exists(), 'Local campaign fixture unavailable')
class SaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (MOD/'scenarios/save games/autosave.eug').read_bytes()
        cls.fixed, cls.report = recover(cls.original, MOD, 'NAVAL1_India_1941_June_1_90pct.eug')
        cls.before = parse(cls.original); cls.after = parse(cls.fixed)
        cls.india = next(c for c in cls.after.all('country') if c.get('tag') == 'IND')

    def test_exactly_ten_unique_orders_at_ninety_percent(self):
        orders=[n for n in self.india.all('division_development') if n.get('name') in {o[0] for o in ORDERS}]
        self.assertEqual(len(orders),10)
        self.assertEqual(len({n.get('name') for n in orders}),10)
        for n in orders:
            self.assertEqual(Decimal(n.get('total_progress')),Decimal('.9'))
            self.assertEqual(n.get('size'),'1')
            self.assertEqual(n.get('days'),n.get('days_for_first'))

    def test_original_ids_and_queues_preserved(self):
        before=next(c for c in self.before.all('country') if c.get('tag')=='IND')
        old=[self.original[n.start:n.end] for n in before.all('division_development')]
        new=[self.fixed[n.start:n.end] for n in self.india.all('division_development')[:len(old)]]
        self.assertEqual(old,new)
        old_ids={int(n.get('id')) for n in walk(self.before) if n.get('type')=='4712' and isinstance(n.get('id'),str)}
        new_ids={o['id'] for o in self.report['orders']}
        self.assertFalse(old_ids & new_ids)

    def test_fees_and_crews_deducted_once(self):
        old=next(c for c in self.before.all('country') if c.get('tag')=='IND')
        for key,fee in self.report['charges'].items():
            self.assertEqual(Decimal(old.get(key))-Decimal(self.india.get(key)),Decimal(str(fee)))
        self.assertEqual(Decimal(self.report['charges']['manpower']),sum(Decimal(x['crew']) for x in self.report['orders']))

    def test_other_countries_and_world_state_unchanged(self):
        old={n.get('tag'):self.original[n.start:n.end] for n in self.before.all('country') if n.get('tag')!='IND'}
        new={n.get('tag'):self.fixed[n.start:n.end] for n in self.after.all('country') if n.get('tag')!='IND'}
        self.assertEqual(old,new)
        for key in ['province','history','sleepevent','save_date','battlehistory']:
            self.assertEqual([self.original[n.start:n.end] for n in self.before.all(key)],
                             [self.fixed[n.start:n.end] for n in self.after.all(key)])

    def test_only_two_notices_added_to_existing_callbacks(self):
        old=self.before.get('globaldata').get('queued_events').all('event')
        new=self.after.get('globaldata').get('queued_events').all('event')
        self.assertEqual(len(new),len(old)+2)
        self.assertEqual([self.original[n.start:n.end] for n in old],[self.fixed[n.start:n.end] for n in new[:len(old)]])
        self.assertEqual([(n.get('id'),n.get('hour')) for n in new[-2:]],[('9297195','1'),('9297196','2')])

    def test_reapplying_fails_without_a_second_charge(self):
        with self.assertRaises(ValueError): recover(self.fixed,MOD,'duplicate.eug')


if __name__ == '__main__': unittest.main()

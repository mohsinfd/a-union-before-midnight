import unittest
from dh_save_spans import Node, parse, walk
from aubm_redesign_stock import transform, canonical, transform_files
from aubm_stock_settlement_guard import apply_guard, FALLBACK_NAME
from test_aubm_liberator import State, evaluate, pair


class StockBridgeTests(unittest.TestCase):
    SOURCE = b'''event = { id = 2011028 country = JAP trigger = { exists = USA }
action_a = { name = "Surrender" command = { type = peace which = USA value = 0 } }
action_b = { name = "Fight" command = { type = dissent value = 5 } } }
event = { id = 123 country = CHI action_a = { name = "Other" } }'''

    def test_guard_covers_no_opt_in_campaign_and_keeps_native_commands(self):
        guarded = apply_guard(self.SOURCE)
        output, records = transform(guarded)
        before = parse(guarded).all('event')[0]
        after = parse(output).all('event')[0]
        for key in ('action_a', 'action_b'):
            self.assertEqual([canonical(c) for c in before.get(key).all('command')],
                             [canonical(c) for c in after.get(key).all('command')])
        state = State(flags=set(), wars={pair(('IND', 'JAP'))}, control={1552: 'IND'})
        fallback = next(f.value for f in after.fields if isinstance(f.value, Node) and f.value.get('name') == FALLBACK_NAME)
        self.assertTrue(evaluate(canonical(fallback.get('trigger')), state))
        self.assertFalse(evaluate(canonical(after.get('action_a').get('trigger')), state))
        state.wars.clear()
        self.assertFalse(evaluate(canonical(fallback.get('trigger')), state))
        self.assertTrue(evaluate(canonical(after.get('action_a').get('trigger')), state))

    def test_missing_territory_does_not_block_stock_event(self):
        output, _ = transform(self.SOURCE)
        ev = parse(output).all('event')[0]
        state = State(flags=set(), wars={pair(('IND', 'JAP'))}, control={})
        self.assertTrue(evaluate(canonical(ev.get('action_a').get('trigger')), state))

    def test_idempotent_and_unrelated_event_unchanged(self):
        output, records = transform(self.SOURCE)
        self.assertEqual(output, transform(output)[0])
        self.assertEqual(canonical(parse(self.SOURCE).all('event')[1]), canonical(parse(output).all('event')[1]))
        self.assertFalse(records[2011028][0]['engine_tested'])

    def test_complete_stock_unit_preserves_indian_clients_and_is_idempotent(self):
        source={'db/events/japan.txt': self.SOURCE+b'''\nevent = { id = 2011018 country = JAP action = {
command = { type = end_mastery which = MAN } command = { type = end_mastery which = MEN }
command = { type = money value = 10 } } }''',
            'db/events/china.txt': b'''event = { id = 2012004 country = CHI action = {
command = { type = inherit which = MAN } command = { type = dissent value = -5 } } }
event = { id = 2012005 country = CHI action = { command = { type = make_puppet which = MEN } } }'''}
        output,records=transform_files(source)
        self.assertEqual(output,transform_files(output)[0])
        self.assertEqual({2011028,2011018,2012004,2012005},set(records))
        for path in output:
            for e in parse(output[path]).all('event'):
                for f in e.fields:
                    if f.key!='action':continue
                    for c in f.value.all('command'):
                        if c.get('type') in ('inherit','end_mastery','make_puppet'):
                            self.assertIn('puppet',str(canonical(c.get('trigger'))))
                        else:self.assertIsNone(c.get('trigger'))
        with self.assertRaises(ValueError):transform_files({'db/events/japan.txt':self.SOURCE})


if __name__ == '__main__':
    unittest.main()

import unittest
from aubm_redesign_version import transform,scenario,TITLE
from dh_save_spans import parse


class VersionTests(unittest.TestCase):
    def test_identification_changes_no_effects_and_is_idempotent(self):
        source={'x':'event = { id = 9270000 name = "Old" desc = "Story" action_a = { command = { type = money value = 1000 } } }'}
        out,_=transform(source)
        self.assertEqual(TITLE,parse(out['x']).get('event').get('name'))
        self.assertEqual('1000',parse(out['x']).get('event').get('action_a').get('command').get('value'))
        self.assertEqual(out,transform(out)[0])

    def test_scenario_stamp_preserves_start(self):
        out=scenario(b'header = { name = "Old" startdate = { year = 1933 } } globaldata = { startdate = { year = 1933 } }')
        e=parse(out)
        self.assertIn('UNVERIFIED',e.get('header').get('name'))
        self.assertEqual('1933',e.get('header').get('startdate').get('year'))
        self.assertEqual(out,scenario(out))


if __name__=='__main__':unittest.main()

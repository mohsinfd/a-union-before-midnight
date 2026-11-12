"""Explicit recruitment accounting and once-only expiry; no engine launch."""
import unittest
from simulate import World,BY_KEY
from recruitment_endurance import RESERVES,DAILY


class RecruitmentTests(unittest.TestCase):
    def first(self):
        w=World();w.year=1941
        self.assertTrue(w.action('national_callup_1941'))
        return w

    def test_exact_initial_recruits_and_no_second_payment(self):
        w=self.first()
        self.assertEqual(w.resources['JAP']['manpower'],500+RESERVES[0])
        self.assertAlmostEqual(w.properties['JAP','free_manpower',None,None],DAILY)
        before=w.resources['JAP'].copy()
        self.assertFalse(w.action('national_callup_1941'))
        self.assertEqual(w.resources['JAP'],before)

    def test_wave_year_and_three_hundred_day_spacing(self):
        w=self.first();w.year=1942;w.advance(299)
        self.assertFalse(w.action('national_callup_1942'))
        w.advance(1);before=w.resources['JAP']['manpower']
        self.assertTrue(w.action('national_callup_1942'))
        self.assertEqual(w.resources['JAP']['manpower']-before,RESERVES[1])
        w.advance(300);self.assertFalse(w.action('national_callup_1943'))
        w.year=1943;before=w.resources['JAP']['manpower']
        self.assertTrue(w.action('national_callup_1943'))
        self.assertEqual(w.resources['JAP']['manpower']-before,RESERVES[2])

    def test_five_year_flow_ends_exactly_once(self):
        w=self.first();w.advance(1825)
        self.assertAlmostEqual(w.resources['JAP']['manpower'],500+RESERVES[0]+1825*DAILY)
        self.assertAlmostEqual(w.properties['JAP','free_manpower',None,None],0)
        before=w.resources['JAP']['manpower'];w.advance(365)
        self.assertEqual(w.resources['JAP']['manpower'],before)
        self.assertFalse(w.action('national_mobilization_end'))

    def test_peace_and_minor_war_do_not_release_the_reserve(self):
        w=World();w.year=1941;w.wars.clear()
        self.assertFalse(w.action('national_callup_1941'))
        w.flags.pop('JX_PACIFIC');w.addwar('JAP','CHI')
        self.assertFalse(w.action('national_callup_1941'))


if __name__=='__main__':unittest.main(verbosity=2)

"""Compiled human eligibility and actual delivery checks, without game/save edits."""
import unittest
from FLOW_review import HumanWorld
from simulate import BY_KEY
from build import EVENTS, compiled_event, parse, get, resolve
import event_accessibility

event_accessibility.apply()


def available(w, key):
    e = BY_KEY[key]; script = get(parse(compiled_event(e)), 'event')
    # Test the compiled decision/trigger, not merely Event.gate or a direct
    # action bypass. The compiled lifetime also bounds automatic events.
    year = w.year or 1933
    if not 1933 <= year <= 1950 or year < int(get(get(script, 'date', []), 'year', e.year)):
        return False
    if e.decision:
        ready=get(script,'decision_trigger',[])
        if not ready:ready=get(script,'trigger',[])
        return w.test(get(script, 'decision'), e.country) and w.test(ready, e.country)
    return w.test(get(script, 'trigger', []), e.country)


def campaign(year=1942, peace=False):
    w = HumanWorld(); w.year = year
    if peace: w.wars.clear()
    return w


class AccessibilityReview(unittest.TestCase):
    def test_1942_each_us_port_opens_real_occupation_safe_support(self):
        for port in event_accessibility.US_PORTS:
            for choice in (0, 1):
                with self.subTest(port=port, choice=choice):
                    w = campaign()
                    for p in event_accessibility.US_PORTS:
                        w.owned[p] = w.controlled[p] = 'USA'
                        w.buildings[p, 'naval_base'] = w.buildings[p, 'air_base'] = 10
                    w.controlled[port] = 'JAP'
                    self.assertTrue(available(w, 'american_base'))
                    script = get(parse(compiled_event(BY_KEY['american_base'])), 'event')
                    self.assertFalse(w.test(get(script, 'trigger'), 'JAP'))
                    before = w.resources['JAP'].copy()
                    self.assertTrue(w.action('american_base', choice))
                    self.assertFalse(w.action('american_base', choice))
                    w.advance(90)
                    self.assertEqual(w.owned[port], 'USA')
                    self.assertEqual(w.buildings[port, 'naval_base'], 10)
                    self.assertEqual(w.resources['JAP']['money'], before['money'] - 180)
                    self.assertEqual(w.resources['JAP']['supplies'], before['supplies'] + (1000 if choice == 0 else 3000))
                    self.assertEqual(w.properties['JAP', 'transport_pool', '-1', None], 120 if choice == 0 else 0)
                    self.assertEqual(w.properties['JAP', 'tc_mod', None, None], 5 if choice == 1 else 0)
                    self.assertFalse(w.action('american_base_finish_' + str(choice)))
                    self.assertFalse(any(k[1] in {'construct', 'build_time'} and v for k, v in w.properties.items()))

    def test_bridgehead_date_war_control_and_full_refund(self):
        w = campaign(1940); w.controlled[1887] = 'JAP'
        self.assertFalse(available(w, 'american_base'))
        w.year = 1941; self.assertTrue(available(w, 'american_base'))
        before = w.resources['JAP'].copy()
        self.assertTrue(w.action('american_base'))
        for p in event_accessibility.US_PORTS: w.controlled[p] = 'USA'
        w.advance(90); self.assertEqual(w.resources['JAP'], before)
        w.dispatch('american_base_finish_0'); self.assertEqual(w.resources['JAP'], before)
        w = campaign(1942, peace=True); w.controlled[1887] = 'JAP'
        self.assertFalse(available(w, 'american_base'))

    def test_german_supply_alternative_needs_no_oil_at_start_or_finish(self):
        w = campaign(); w.resources['JAP']['oil'] = 0
        self.assertTrue(available(w, 'axis_fuel'))
        self.assertFalse(w.action('axis_fuel', 0))
        before = w.resources['JAP'].copy(); recipient = w.resources['GER']['supplies']
        self.assertTrue(w.action('axis_fuel', 1)); w.advance(120)
        self.assertEqual(w.resources['JAP']['oil'], 0)
        self.assertEqual(w.resources['GER']['supplies'], recipient + 1500)
        self.assertEqual(w.resources['JAP']['supplies'], before['supplies'] - 1000)
        self.assertFalse(w.action('axis_fuel_finish_1'))

    def test_german_fuel_is_reserved_upfront_and_returns_if_partner_disappears(self):
        w = campaign(); w.resources['JAP']['oil'] = 3000
        before = w.resources['JAP'].copy()
        self.assertTrue(w.action('axis_fuel', 0)); self.assertEqual(w.resources['JAP']['oil'], 2000)
        w.countries.discard('GER'); w.advance(120)
        self.assertEqual(w.resources['JAP'], before)
        w.dispatch('axis_fuel_finish_0'); self.assertEqual(w.resources['JAP'], before)

    def test_colombo_capped_enemy_owned_base_delivers_shipping_and_stock(self):
        w = campaign(); w.owned[1511] = 'ENG'; w.controlled[1511] = 'JAP'
        w.buildings[1511, 'air_base'] = w.buildings[1511, 'naval_base'] = 10
        self.assertTrue(available(w, 'colombo_station'))
        self.assertFalse(w.action('colombo_station', 0))
        before = w.resources['JAP']['supplies']
        self.assertTrue(w.action('colombo_station', 1)); w.advance(150)
        self.assertEqual(w.properties['JAP', 'transport_pool', '-1', None], 60)
        self.assertEqual(w.properties['JAP', 'escort_pool', '-1', None], 20)
        self.assertEqual(w.resources['JAP']['supplies'], before + 1150)
        self.assertEqual(w.owned[1511], 'ENG')

    def test_optional_map_activities_have_manual_access_and_no_auto_popup(self):
        w = campaign(); w.owned[1726] = 'AST'; w.controlled[1726] = 'JAP'
        self.assertTrue(available(w, 'rabaul_workshops'))
        for key in event_accessibility.REPORT['manual_activities']:
            e = BY_KEY[key]; self.assertTrue(e.decision)
            script = get(parse(compiled_event(e)), 'event')
            self.assertFalse(w.test(get(script, 'trigger'), 'JAP'), key)
            close = next(a for a in e.actions if a.name == 'Leave this proposal available')
            self.assertFalse(close.commands, key)
        self.assertFalse(w.action('rabaul_workshops', 0))
        self.assertTrue(w.action('rabaul_workshops', 1)); w.advance(150)
        self.assertEqual(w.properties['JAP', 'transport_pool', '-1', None], 40)

    def test_siberian_occupied_rail_reserve_has_actual_stocks_and_no_unit_promise(self):
        w = campaign()
        for p in (1191, 1190, 1169): w.owned[p] = 'SOV'; w.controlled[p] = 'JAP'
        self.assertTrue(available(w, 'siberian_rail'))
        before = w.resources['JAP']['supplies']
        self.assertTrue(w.action('siberian_rail', 1)); w.advance(180)
        self.assertEqual(w.resources['JAP']['supplies'], before + 3000)
        self.assertFalse(w.orders)
        self.assertFalse(any(k[1] == 'build_time' and v for k, v in w.properties.items()))
        self.assertNotIn('four mountain divisions', BY_KEY['siberian_rail'].desc)

    def test_postwar_shipping_alternative_delivers_and_war_refunds(self):
        w = campaign(1947, peace=True)
        self.assertTrue(available(w, 'naval_treaty'))
        before = w.resources['JAP']['supplies']
        self.assertTrue(w.action('naval_treaty', 1)); w.advance(60)
        self.assertEqual(w.properties['JAP', 'transport_pool', '-1', None], 200)
        self.assertEqual(w.properties['JAP', 'escort_pool', '-1', None], 60)
        self.assertEqual(w.resources['JAP']['supplies'], before + 1300)
        self.assertFalse(any(k[1] == 'build_time' and v for k, v in w.properties.items()))
        v = campaign(1947, peace=True); before = v.resources['JAP'].copy()
        self.assertTrue(v.action('naval_treaty', 1)); v.addwar('JAP', 'USA'); v.advance(60)
        self.assertEqual(v.resources['JAP'], before)


if __name__ == '__main__': unittest.main(verbosity=2)

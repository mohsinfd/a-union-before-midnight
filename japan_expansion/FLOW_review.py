"""Counterfactual human event-flow tests; no game launch or installation."""
import copy
import json
from pathlib import Path
import unittest
from simulate import World, BY_KEY
from build import EVENTS, compiled_event, parse, get, resolve
import campaign_flow

campaign_flow.apply()


class HumanWorld(World):
    """One human Japan; support documented ai=yes/no and ai=country tag."""
    def test(self, node, actor):
        return all(((actor != 'JAP') if v == 'yes' else ((actor == 'JAP') if v == 'no' else v != 'JAP')) if k == 'ai'
                   else super(HumanWorld, self).test([(k, v)], actor)
                   for k, v in node)


def eligible(w, key):
    e = BY_KEY[key]
    return w.test(parse(resolve(e.gate)), e.country)


class FlowReview(unittest.TestCase):
    def test_no_new_ids_and_existing_registry_preserved(self):
        baseline = json.loads((Path(__file__).parent / 'events.json').read_text())
        for e in baseline:
            self.assertEqual(BY_KEY[e['key']].id, e['id'])

    def test_human_cannot_receive_automatic_country_offers(self):
        w = HumanWorld()
        for key in campaign_flow.REPORT['manual_settlements']:
            e = BY_KEY[key]
            self.assertTrue(e.manual_only, key)
            automatic = get(get(parse(compiled_event(e)), 'event'), 'trigger')
            self.assertFalse(w.test(automatic, 'JAP'), key)

    def test_early_useful_offers_are_manual_and_small_stat_bills_retired(self):
        w = HumanWorld(); w.flags.pop('JX_PACIFIC'); w.wars.clear()
        for key in campaign_flow.MANUAL_EARLY:
            e = BY_KEY[key]
            self.assertTrue(e.decision)
            automatic = get(get(parse(compiled_event(e)), 'event'), 'trigger')
            self.assertFalse(w.test(automatic, 'JAP'), key)
        for key in campaign_flow.RETIRED_EARLY:
            self.assertFalse(eligible(w, key), key)
            before = copy.deepcopy(w.resources)
            self.assertFalse(w.action(key, 0), key)
            self.assertEqual(w.resources, before)
        for key in ('tomozuru1934', 'typhoon1935'):
            self.assertFalse(BY_KEY[key].decision, key)

    def test_manual_settlement_close_leaves_no_reminder_or_effect(self):
        w = HumanWorld(); w.countries.discard('U87')
        for p in (1337, 1338, 1299): w.controlled[p] = 'JAP'
        w.addwar('JAP', 'CHI'); w.national_losses['CHI'] = 80; w.vp_losses['CHI'] = 80
        self.assertTrue(eligible(w, 'china'))
        before = copy.deepcopy((w.resources, w.flags, w.wars, w.masters))
        self.assertTrue(w.action('china', 3))
        self.assertEqual((w.resources, w.flags, w.wars, w.masters), before)
        self.assertFalse(w.queue)
        self.assertTrue(eligible(w, 'china'))
        self.assertTrue(w.action('china', 4))
        self.assertFalse(eligible(w, 'china'))

    def test_paid_start_and_duplicate_finish_cannot_charge_or_deliver_twice(self):
        w = HumanWorld(); before = w.resources['JAP'].copy()
        self.assertTrue(w.action('strategic_storage', 0))
        charged = w.resources['JAP'].copy()
        self.assertFalse(w.action('strategic_storage', 0))
        self.assertEqual(w.resources['JAP'], charged)
        w.advance(90)
        self.assertEqual(w.properties['JAP', 'stockpile', 'supplies', None], 200)
        self.assertEqual(w.resources['JAP']['money'], before['money'] - 100)
        props = dict(w.properties)
        self.assertTrue(w.dispatch('strategic_storage_finish_0'))
        self.assertEqual(dict(w.properties), props)

    def test_manual_preparation_close_does_not_schedule_a_return_popup(self):
        w = HumanWorld(); w.flags.pop('JX_PACIFIC'); w.wars.clear()
        for key in ('fx1933', 'oil1934', 'fx1936', 'neutral1939', 'army_production', 'strategic_storage'):
            e = BY_KEY[key]
            close = next(i for i, a in enumerate(e.actions) if a.name == 'Leave this proposal available')
            before = copy.deepcopy((w.resources, w.flags))
            self.assertTrue(w.action(key, close), key)
            self.assertEqual((w.resources, w.flags), before)
            self.assertFalse(w.queue, key)

    def test_paid_failed_finish_refunds_once_and_old_receiver_is_inert(self):
        w = HumanWorld(); before = w.resources['JAP'].copy()
        self.assertTrue(w.action('home_fuel', 0))
        w.controlled[1552] = 'USA'; w.advance(240)
        self.assertEqual(w.resources['JAP'], before)
        self.assertTrue(w.dispatch('home_fuel_finish_0'))
        self.assertEqual(w.resources['JAP'], before)
        self.assertFalse(any(k[1] == 'add_prov_resource' for k in w.properties))

    def test_stale_settlement_receivers_do_not_puppet_release_or_reopen_failure(self):
        w = HumanWorld(); before = copy.deepcopy((w.flags, w.masters, w.access, w.wars, w.countries))
        for suffix in ('prepare', 'create', 'commit', 'verify', 'failed', 'confirmed'):
            self.assertTrue(w.dispatch('china_' + suffix))
        self.assertEqual((w.flags, w.masters, w.access, w.wars, w.countries), before)
        self.assertFalse(w.queue)
        w.flags['JX_china_SETTLED'] = 1
        w.dispatch('china_verify')
        self.assertFalse(w.queue)

    def test_failed_settlement_retry_cannot_form_a_six_day_loop(self):
        w = HumanWorld(); w.flags['JX_china_PENDING'] = 1
        self.assertTrue(w.action('china_failed', 0))
        self.assertEqual(len(w.queue), 1)
        self.assertEqual(w.queue[0][0] - w.day, 30)
        self.assertEqual(w.queue[0][2], 'china_prepare')

    def test_every_country_all_three_terms_preserve_deliveries_after_inline_prepare(self):
        from build import source_country
        for key in campaign_flow.REPORT['manual_settlements']:
            for choice in (0, 1, 2):
                with self.subTest(country=key, terms=choice):
                    w = HumanWorld()
                    old = BY_KEY[key + '_withdraw'].country
                    tag = BY_KEY[key + '_local'].country
                    w.countries.add(old)
                    if old != tag:
                        w.countries.discard(tag); w.masters.pop(tag, None); w.groups.pop(tag, None)
                    # Model the existing national state at settlement time,
                    # rather than the 1933 colonial owner of its future land.
                    _, homeland = source_country(old)
                    for p in homeland: w.owned[p] = old
                    w.wars.clear(); w.addwar('JAP', old)
                    w.addwar('JAP', 'USA'); w.addwar('JAP', 'SOV')
                    w.national_losses[old] = 100; w.vp_losses[old] = 100
                    for p in w.owned: w.controlled[p] = 'JAP'
                    self.assertTrue(eligible(w, key))
                    self.assertTrue(w.action(key, choice))
                    w.advance(10)
                    self.assertTrue(w.flags.get('JX_' + key + '_SETTLED'))
                    self.assertTrue(w.flags.get('JX_' + key + '_ANNOUNCED'))
                    self.assertIn(('JAP', tag), w.access); self.assertIn((tag, 'JAP'), w.access)
                    self.assertEqual(w.masters.get(tag) == 'JAP', choice != 2)
                    self.assertTrue(w.atwar('JAP', 'USA')); self.assertTrue(w.atwar('JAP', 'SOV'))
                    self.assertNotIn(key + '_prepare', w.received)
                    self.assertNotIn(key + '_confirmed', w.received)

    def test_annexed_release_and_foreign_owner_transfers_keep_their_delays(self):
        from build import source_country
        for key, old, tag, owner in [('china', 'CHI', 'U87', 'JAP'),
                                     ('indonesia', 'U05', 'INO', 'HOL'),
                                     ('malaya', 'MLY', 'MLY', 'ENG'),
                                     ('cambodia', 'CMB', 'CMB', 'FRA')]:
            with self.subTest(country=key, owner=owner):
                w = HumanWorld(); w.countries.discard(old); w.countries.discard(tag)
                if owner != 'JAP':
                    w.countries.add(owner); w.addwar('JAP', owner)
                _, provinces = source_country(tag)
                for p in provinces: w.owned[p] = owner
                for p in w.owned: w.controlled[p] = 'JAP'
                self.assertTrue(eligible(w, key))
                self.assertTrue(w.action(key, 0))
                self.assertNotIn(tag, w.countries)
                self.assertTrue(any(item[2] == key + '_create' and item[0] == 1 for item in w.queue))
                self.assertTrue(any(item[2] == key + '_commit' and item[0] == 3 for item in w.queue))
                w.advance(10)
                self.assertTrue(w.flags.get('JX_' + key + '_SETTLED'))
                self.assertEqual(w.masters[tag], 'JAP')

    def test_visible_offer_tooltips_and_command_counts_stay_bounded(self):
        for e in EVENTS:
            if e.country != 'JAP' or not e.desc: continue
            for a in e.actions:
                self.assertLess(len(a.gate), 2500, e.key)
                if e.key in campaign_flow.REPORT['manual_settlements']:
                    self.assertLess(len(a.commands), 20, e.key)

    def test_regional_development_grant_and_refund_each_have_one_receipt(self):
        for key, tag in (('guangxi', 'CGX'), ('yunnan', 'CYN')):
            w = HumanWorld(); w.countries.add(tag); w.masters[tag] = 'JAP'
            w.flags[f'JX_{key}_REGIONAL_PENDING'] = 1
            before = w.resources[tag].copy()
            self.assertTrue(w.action(key + '_local'))
            self.assertEqual(w.resources[tag]['money'], before['money'] + 100)
            after = w.resources[tag].copy()
            w.dispatch(key + '_local')
            self.assertEqual(w.resources[tag], after)
            payer = w.resources['JAP'].copy()
            self.assertTrue(w.action(key + '_refund'))
            refund = w.resources['JAP'].copy()
            w.dispatch(key + '_refund')
            self.assertEqual(w.resources['JAP'], refund)
            self.assertEqual(refund['money'], payer['money'] + 100)


if __name__ == '__main__':
    unittest.main(verbosity=2)

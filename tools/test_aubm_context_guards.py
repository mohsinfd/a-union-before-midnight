"""Read-only scenario tests of the shipped India reaction scripts."""
from dataclasses import dataclass, field
from pathlib import Path
import unittest

from dh_save_spans import Node, parse
from aubm_context_guards import (
    FILES, KEEP, LAPSE, ROOT, actions, validate, transformed,
    REACTIONS, CALLBACK_GUARDS,
)


@dataclass
class State:
    wars: set = field(default_factory=set)
    alliances: set = field(default_factory=set)
    flags: set = field(default_factory=set)
    countries: set = field(default_factory=lambda: set("IND JAP CHI SIA GER ITA SOV ENG USA FRA CZE SPR SPA IRQ PER ETH".split()))
    money: int = 10000
    supplies: int = 10000
    manpower: int = 1000

    def pair(self, other, category):
        getattr(self, category).add(frozenset(("IND", other)))
        return self


def evaluate(node, state, country="IND"):
    """Only the documented subset used by this correction. Fail on unknowns."""
    if node is None:
        return True
    values = []
    for f in node.fields:
        key, value = f.key, f.value
        if key == "AND":
            result = evaluate(value, state, country)
        elif key == "OR":
            result = any(evaluate(Node(fields=[child]), state, country) for child in value.fields)
        elif key == "NOT":
            result = not evaluate(value, state, country)
        elif key == "war":
            result = frozenset(value.all("country")) in state.wars
        elif key == "alliance":
            result = frozenset(value.all("country")) in state.alliances
        elif key == "flag":
            result = value in state.flags
        elif key == "exists":
            result = value in state.countries
        elif key == "atwar":
            tag = country if value in ("yes", "no") else value
            result = any(tag in pair for pair in state.wars)
            if value == "no":
                result = not result
        elif key == "participant":
            result = any(value.get("country") in pair for pair in state.alliances)
        elif key in ("money", "supplies", "manpower"):
            result = getattr(state, key) >= float(value)
        elif key == "ai":
            result = (country != "IND") == (value == "yes")
        elif key == "puppet":
            result = False
        else:
            raise AssertionError(f"Unsupported test predicate: {key}")
        values.append(result)
    return all(values)


class ReactionContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = {}
        cls.texts = {}
        for filename in FILES:
            text = (ROOT / "mod/db/events" / filename).read_bytes().decode("cp1252")
            cls.texts[filename] = text
            for e in parse(text).all("event"):
                cls.events[int(e.get("id"))] = e

    def action(self, eid, key):
        return next(a for k, a in actions(self.events[eid]) if k == key)

    def allowed(self, eid, key, state):
        return evaluate(self.action(eid, key).get("trigger"), state, self.events[eid].get("country"))

    def test_japan_war_never_offers_neutrality(self):
        state = State().pair("JAP", "wars")
        for eid in (9280356, 9280704, 9280350, 9280353, 9270452, 9270455):
            self.assertFalse(self.allowed(eid, "action_b", state), eid)
        # A simultaneous Soviet war does not loosen those restrictions.
        state.pair("SOV", "wars")
        self.assertFalse(self.allowed(9280704, "action_b", state))

    def test_uncommitted_peace_keeps_neutral_choices(self):
        for eid in (9280356, 9280704, 9280350, 9280353, 9270452, 9270455):
            self.assertTrue(self.allowed(eid, "action_b", State()), eid)

    def test_old_orientation_does_not_override_current_relations(self):
        stale = State(flags={"ind_v3_japanese_orientation", "ind_aubm_route_japan", "ind_aubm_jp_partnership"})
        self.assertTrue(self.allowed(9280350, "action_a", stale))
        self.assertTrue(self.allowed(9280704, "action_a", stale))
        stale.flags.add("ind_aubm_commitment_japan")
        self.assertFalse(self.allowed(9280350, "action_a", stale))
        self.assertFalse(self.allowed(9280704, "action_a", stale))

    def test_never_supply_a_current_enemy(self):
        cases = ((9280350, "action_a", "CHI"), (9280350, "action_c", "JAP"),
                 (9280355, "action_a", "SOV"), (9280355, "action_c", "GER"),
                 (9280700, "action_a", "ENG"), (9280703, "action_a", "PER"),
                 (9280704, "action_a", "USA"), (9280357, "action_a", "ENG"),
                 (9270452, "action_a", "CHI"), (9270452, "action_c", "JAP"))
        for eid, key, opponent in cases:
            with self.subTest(event=eid, enemy=opponent):
                self.assertFalse(self.allowed(eid, key, State().pair(opponent, "wars")))

    def test_actual_alliance_blocks_aid_to_its_enemy(self):
        self.assertFalse(self.allowed(9280350, "action_a", State().pair("JAP", "alliances")))
        self.assertFalse(self.allowed(9280355, "action_a", State().pair("GER", "alliances")))
        self.assertFalse(self.allowed(9280355, "action_c", State().pair("SOV", "alliances")))

    def test_delayed_shipment_rechecks_war_on_each_leg(self):
        for ids, enemy in (((9280602,), "JAP"), ((9280606, 9280612), "ENG"),
                           ((9280623, 9280627), "USA"), ((9280622, 9280626), "PER")):
            for eid in ids:
                event = self.events[eid]
                for state, permitted in ((State(), True), (State().pair(enemy, "wars"), False)):
                    available = [a for _, a in actions(event) if evaluate(a.get("trigger"), state, event.get("country"))]
                    self.assertEqual(len(available), 1, eid)
                    self.assertEqual(available[0].get("name") != LAPSE, permitted, eid)
                    if not permitted:
                        self.assertEqual(available[0].all("command"), [])

    def test_alliance_shipment_lapses_after_withdrawal_or_collapse(self):
        for eid, partner in ((9280634, "ENG"), (9280635, "GER"), (9280636, "SOV"), (9280637, "JAP")):
            self.assertTrue(self.allowed(eid, "action_a", State().pair(partner, "alliances")))
            old_flags = State(flags={"ind_v3_joined_axis", "ind_v3_joined_japan", "ind_v3_joined_allies", "ind_v3_joined_comintern"})
            self.assertFalse(self.allowed(eid, "action_a", old_flags))
            old_flags.countries.remove(partner)
            self.assertFalse(self.allowed(eid, "action_a", old_flags))

    def test_no_money_or_supplies_still_has_free_safe_choice(self):
        state = State(money=0, supplies=0, manpower=0).pair("JAP", "wars").pair("ENG", "wars")
        for eid in (9280350, 9280356, 9280700, 9280704, 9280706, 9270452, 9272206):
            event = self.events[eid]
            safe = next(a for _, a in actions(event) if a.get("name") == KEEP)
            self.assertTrue(evaluate(safe.get("trigger"), state))
            self.assertTrue(all(c.get("type") == "setflag" for c in safe.all("command")))
        self.assertFalse(self.allowed(9280356, "action_a", state))
        self.assertFalse(self.allowed(9280706, "action_a", state))

    def test_raid_and_imphal_pages_do_not_invent_battles(self):
        raid = self.events[9280706]
        self.assertEqual(raid.get("name"), "Prepare for Japanese Naval Raids")
        self.assertFalse(self.allowed(9280706, "action_b", State()))
        self.assertTrue(self.allowed(9280706, "action_b", State().pair("JAP", "wars")))
        self.assertEqual(self.events[9280708].get("name"), "Plan the Imphal Front")
        self.assertIn("do not mean a battle has taken place", self.events[9280708].get("desc"))

    def test_all_owned_context_contracts(self):
        total = sum(validate(text, filename) for filename, text in self.texts.items())
        self.assertEqual(total, 76)
        self.assertEqual(len(self.events), 83)

    def test_explicit_ai_distributions_and_ui_labels(self):
        for eid, event in self.events.items():
            aa = actions(event)
            for _, action in aa:
                self.assertLessEqual(len(action.get("name").encode("cp1252")), 58, eid)
            if eid in REACTIONS:
                self.assertEqual(sum(int(a.get("ai_chance")) for _, a in aa), 100, eid)
                self.assertEqual(next(a.get("ai_chance") for _, a in aa if a.get("name") == KEEP), "0")
            elif eid in CALLBACK_GUARDS:
                self.assertEqual([a.get("ai_chance") for _, a in aa], ["100", "100"], eid)

    def test_marked_old_output_is_repaired_once(self):
        for filename, source in self.texts.items():
            text = source.replace("\r\n", "\n")
            self.assertEqual(transformed(text, filename), text)
            old = text.replace('ai_chance = 0\n\t\tname = "' + KEEP, 'ai_chance = 5\n\t\tname = "' + KEEP)
            # Old callback primaries had no explicit chance before the trigger.
            old = old.replace('action_a = {\n\t\tai_chance = 100\n', 'action_a = {\n')
            self.assertEqual(transformed(old, filename), text, filename)


if __name__ == "__main__":
    unittest.main()

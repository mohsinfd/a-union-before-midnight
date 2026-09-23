"""Battlefield contract tests, not a Darkest Hour engine simulation."""
import copy
from pathlib import Path
import unittest

from dh_save_spans import Node, parse, walk
from aubm_redesign_campaign_access import (
    transform, canonical, OPPONENT, predicate_roots, SOURCE_MODULE)
from test_aubm_liberator import State, evaluate, pair

ROOT = Path(__file__).resolve().parents[1]
PATH = "mod/db/events/aubm_v4/" + SOURCE_MODULE


def event_map(text):
    return {int(e.get("id")): e for e in parse(text).all("event")}


def actions(e):
    return [f.value for f in e.fields if (f.key or "").startswith("action")]


def battlefield(enemy="JAP"):
    s = State(flags=set(), wars={pair(("IND", enemy))})
    s.alliances.add(pair(("IND", "ENG")))  # A friendly ally is not the enemy.
    return s


class CampaignAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / PATH).read_bytes().decode("latin1")
        cls.output, cls.reviews = transform({PATH: cls.source})
        cls.before = event_map(cls.source)
        cls.after = event_map(cls.output[PATH])

    def gate(self, eid, state, action=False):
        node = actions(self.after[eid])[0] if action else self.after[eid]
        return evaluate(canonical(node.get("trigger", Node())), state)

    def test_exact_inventory_no_new_ids_and_no_other_event_edits(self):
        self.assertEqual(61, len(OPPONENT))
        self.assertEqual(set(OPPONENT), set(self.reviews))
        self.assertTrue(all(r[0]["status"] == "reviewed" for r in self.reviews.values()))
        self.assertEqual(set(self.before), set(self.after))
        for eid, event in self.before.items():
            if eid not in OPPONENT:
                other = self.after[eid]
                self.assertEqual(self.source[event.start:event.end],
                                 self.output[PATH][other.start:other.end], eid)

    def test_war_observation_needs_no_manual_optin_or_route(self):
        for eid, enemy in [(9289804, "JAP"), (9289805, "SOV")]:
            for route in [None, "allied", "german", "soviet", "japan", "sovereign"]:
                s = battlefield(enemy)
                if route:
                    s.flags.add("ind_aubm_route_" + route)
                self.assertTrue(self.gate(eid, s))
                self.assertTrue(self.gate(eid, s, action=True))
                s.wars.clear()
                self.assertFalse(self.gate(eid, s))

    def test_enemy_alliance_and_indian_puppet_excluded(self):
        for eid, enemy in [(9289804, "JAP"), (9289805, "SOV")]:
            s = battlefield(enemy)
            s.alliances.add(pair(("IND", enemy)))
            self.assertFalse(self.gate(eid, s))
            s = battlefield(enemy)
            s.puppets["IND"] = "ENG"
            self.assertFalse(self.gate(eid, s))
            s = battlefield(enemy)
            s.exists.remove("IND")
            self.assertFalse(self.gate(eid, s))

    def test_siam_nanjing_and_indochina_start_from_real_fronts(self):
        for eid, target, provinces in [
            (9297000, "SIA", (1423, 1425)),
            (9289900, "U87", (1337, 1338, 1317, 1299)),
            (9294010, "U03", (1396, 1400, 1389, 1395, 1397)),
        ]:
            s = battlefield()
            s.flags.add("ind_lib1_japan_war")
            s.exists.add(target)
            s.wars.add(pair(("IND", target)))
            s.puppets[target] = "JAP"
            s.alliances.add(pair((target, "JAP")))
            # Source trigger is the authority for the actual map IDs.
            for node in walk(self.after[eid].get("trigger")):
                for f in node.fields:
                    if f.key in {"owned", "control"}:
                        getattr(s, f.key)[int(f.value.get("province"))] = f.value.get("data")
            self.assertTrue(self.gate(eid, s), eid)
            for route in ["allied", "german", "soviet", "japan", "sovereign"]:
                variant = copy.deepcopy(s)
                variant.flags.add("ind_aubm_route_" + route)
                self.assertTrue(self.gate(eid, variant), (eid, route))
            s.wars.remove(pair(("IND", target)))
            self.assertFalse(self.gate(eid, s), eid)

    def test_japanese_hold_still_requires_every_city_and_real_war(self):
        s = battlefield()
        s.control = {1552: "IND", 1553: "IND", 1554: "IND"}
        self.assertTrue(self.gate(9289920, s))
        for province in tuple(s.control):
            bad = copy.deepcopy(s)
            del bad.control[province]
            self.assertFalse(self.gate(9289920, bad))
        s.flags.add("ind_lib1_jap_hold_earned")
        self.assertFalse(self.gate(9289920, s))

    def test_soviet_hold_keeps_deep_territorial_threshold(self):
        s = battlefield("SOV")
        s.control = {p: "IND" for p in (713, 1103, 706, 663, 1151)}
        # Two complete absent republics: Turkmenistan and Uzbekistan.
        s.owned = {p: "SOV" for p in (1097, 1098, 1099, 1100, 1101, 1102, 1103)}
        s.control.update({p: "IND" for p in s.owned})
        self.assertTrue(self.gate(9289910, s))
        for route in ["allied", "german", "soviet", "japan", "sovereign"]:
            alternative = copy.deepcopy(s)
            alternative.flags.add("ind_aubm_route_" + route)
            self.assertTrue(self.gate(9289910, alternative))
        del s.control[1097]
        self.assertFalse(self.gate(9289910, s))

    def test_cost_readiness_pending_and_terminal_guards_survive(self):
        eid = 9289903
        s = battlefield()
        s.exists.add("U87")
        s.wars.add(pair(("IND", "U87")))
        s.alliances.add(pair(("U87", "JAP")))
        s.puppets["U87"] = "JAP"
        s.flags |= {"ind_lib1_japan_war", "ind_lib1_china_hold_ready"}
        s.owned = {1337: "U87", 1317: "U87", 1299: "U87"}
        s.control = {p: "IND" for p in (1337, 1338, 1317, 1299)}
        self.assertTrue(self.gate(eid, s, action=True))
        for resource, amount in [("money", 349), ("supplies", 999)]:
            bad = copy.deepcopy(s)
            bad.resources[resource] = amount
            self.assertFalse(self.gate(eid, bad, action=True))
        for flag in ["china_pending", "china_protection_pending", "china_cooldown", "china_break"]:
            bad = copy.deepcopy(s)
            bad.flags.add("ind_lib1_" + flag)
            self.assertFalse(self.gate(eid, bad, action=True))
        s.flags.remove("ind_lib1_china_hold_ready")
        self.assertFalse(self.gate(eid, s, action=True))

    def test_protected_predicates_and_effect_payloads_unchanged(self):
        protected = {"war", "owned", "control", "puppet", "event", "money", "supplies"}
        def evidence(event):
            found = []
            for root in predicate_roots(event):
                for node in walk(root):
                    for f in node.fields:
                        if f.key in protected:
                            found.append((f.key, canonical(f.value) if isinstance(f.value, Node) else f.value))
                        if f.key == "flag" and str(f.value).startswith("ind_lib1_") and f.value != "ind_lib1_enabled":
                            found.append((f.key, f.value))
            return found
        for eid in OPPONENT:
            self.assertEqual(evidence(self.before[eid]), evidence(self.after[eid]), eid)
            for old, new in zip(actions(self.before[eid]), actions(self.after[eid])):
                for a, b in zip(old.all("command"), new.all("command")):
                    self.assertEqual(canonical(Node(fields=[f for f in a.fields if f.key != "trigger"])),
                                     canonical(Node(fields=[f for f in b.fields if f.key != "trigger"])), eid)
                self.assertEqual(len(old.all("command")), len(new.all("command")))

    def test_idempotent_and_wrong_module_untouched(self):
        again, _ = transform(self.output)
        self.assertEqual(again, self.output)
        wrong, _ = transform({"unrelated.txt": self.source})
        self.assertEqual(wrong["unrelated.txt"], self.source)
        self.assertEqual(self.source, (ROOT / PATH).read_bytes().decode("latin1"))

    def test_composes_after_diplomacy_and_cooperation(self):
        from aubm_redesign_diplomacy import transform as diplomacy
        from aubm_redesign_cooperation import transform as cooperation
        staged, _ = diplomacy({PATH: self.source})
        staged, _ = cooperation(staged)
        result, reviews = transform(staged)
        self.assertTrue(all(r[0]["status"] == "reviewed" for r in reviews.values()))
        self.assertEqual(set(event_map(staged[PATH])), set(event_map(result[PATH])))
        s = battlefield()
        event = event_map(result[PATH])[9289804]
        self.assertTrue(evaluate(canonical(event.get("trigger")), s))


if __name__ == "__main__":
    unittest.main()

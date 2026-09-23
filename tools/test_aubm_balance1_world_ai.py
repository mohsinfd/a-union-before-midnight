"""Script-contract tests, not a substitute for a native DH campaign test."""
import unittest
from aubm_balance1_world_ai import ENEMIES, EVENT_PATH, MARKER, generated_events, transform
from dh_save_spans import Node, parse, walk


def fixture():
    return {
        "db/events.txt": 'event = "db\\events\\AI\\AI_FIN.txt"\n',
        "db/events/AI/AI_FIN.txt": '''event = {
            id = 3030010 country = FIN persistent = yes
            trigger = { ai = yes NOT = { local_flag = FINHomeland }
                war = { country = SOV } NOT = { lost_national = { country = FIN value = 2 } } }
            action_a = { command = { type = ai which = "switch/FIN_Homeland.ai" } }
        }
        event = { id = 3030011 country = FIN persistent = yes
            trigger = { ai = yes NOT = { local_flag = FINNormal }
                OR = { NOT = { war = { country = SOV } } lost_national = { country = FIN value = 2 } } }
            action_a = { command = { type = ai which = "switch/FIN_Normal.ai" } }
        }''',
        "ai/switch/ITA_Homeland.ai": 'garrison = { defend_overseas_beaches = no overseas_multiplier = 0.1 province_priorities = { 377 = 20 } }',
        "ai/switch/eng_attack.ai": 'front = { recklessness = 3 min_attack_odds = 0.8 base_attack_odds = 1.1 } invasion = { enemy = 1 adjacentenemy = 0.5 }',
        "ai/switch/GER_Russia.ai": 'no_exp_forces_to = { JAP FIN SIA } garrison = { province_priorities = { 55 = 30 } }',
        "ai/switch/GER_Norway_END.ai": 'invasion = { invasion = yes }',
        "ai/switch/SOV_Germany.ai": 'garrison = { country_priorities = { GER = 150 } province_priorities = { 553 = 70 } } front = { distrib_vs_ai = op_defensive }',
        "db/events/AI/AI_SOV.txt": 'event = { id = 100 country = SOV action_a = { command = { type = ai which = "switch/SOV_Germany.ai" } } }',
        "unrelated.txt": 'This byte string is intentionally not a game script.\r\n',
    }


def pair(node):
    return frozenset(node.all("country"))


def evaluate(node, state, receiver):
    """Independent evaluator for the exact documented guard subset we emit."""
    def field(f):
        k, v = f.key, f.value
        if k == "AND": return evaluate(v, state, receiver)
        if k == "OR": return any(field(x) for x in v.fields)
        if k == "NOT": return not any(field(x) for x in v.fields)
        if k == "ai":
            return receiver in state["ai"] if v == "yes" else (receiver not in state["ai"] if v == "no" else v in state["ai"])
        if k == "exists": return v in state["exists"]
        if k == "war": return pair(v) in state["wars"]
        if k == "alliance": return pair(v) in state["alliances"]
        if k == "local_flag": return v in state["flags"]
        if k == "control": return state["control"].get(v.get("province")) == v.get("data")
        if k in ("manpower", "supplies", "oil", "money"): return state[k] >= float(v)
        raise AssertionError("Untested predicate " + str(k))
    return all(field(f) for f in node.fields)


def state():
    return dict(ai=set(ENEMIES) | {"FIN"}, exists=set(ENEMIES) | {"FIN", "IND"},
                wars=set(), alliances=set(), flags=set(), control={},
                manpower=200, supplies=10000, oil=5000, money=1000)


class WorldAITests(unittest.TestCase):
    def setUp(self):
        self.events = {e.get("id"): e for e in parse(generated_events()).all("event")}

    def active(self, eid, s):
        e = self.events[str(eid)]
        return evaluate(e.get("trigger"), s, e.get("country"))

    def test_transform_idempotent_preserves_unrelated(self):
        source = fixture()
        out, records = transform(source)
        second, again = transform(out)
        self.assertEqual(second, out)
        self.assertEqual(again, [])
        self.assertEqual(source, fixture())
        self.assertEqual(out["unrelated.txt"], source["unrelated.txt"])
        self.assertEqual(out["db/events.txt"].count("53_world_ai_balance1.txt"), 1)
        for record in records:
            self.assertIn(MARKER, out[record["path"]])

    def test_finland_does_not_abandon_defence_after_losses(self):
        out, _ = transform(fixture())
        fin = parse(out["db/events/AI/AI_FIN.txt"]).all("event")
        self.assertNotIn("lost_national", out["db/events/AI/AI_FIN.txt"])
        self.assertEqual(fin[1].get("trigger").get("NOT").get("local_flag"), "FINNormal")

    def test_priorities_merge_not_replace_historical_fronts(self):
        out, _ = transform(fixture())
        ger = parse(out["ai/switch/GER_Russia.ai"])
        self.assertEqual(ger.get("garrison").get("province_priorities").get("55"), "30")
        for p in ("483", "488", "493", "495"):
            self.assertIsNotNone(ger.get("garrison").get("province_priorities").get(p))
        self.assertNotIn("FIN", ger.get("no_exp_forces_to").atoms())
        self.assertIn("JAP", ger.get("no_exp_forces_to").atoms())
        sov = parse(out["ai/switch/SOV_Germany.ai"])
        self.assertEqual(sov.get("garrison").get("country_priorities").get("GER"), "150")
        self.assertEqual(sov.get("front").get("distrib_vs_ai"), "op_defensive")

    def test_enemy_response_guard_matrix_and_latch(self):
        for i, tag in enumerate(ENEMIES):
            s = state()
            with self.subTest(tag=tag):
                self.assertFalse(self.active(9318000 + i * 2, s))
                s["wars"].add(frozenset((tag, "IND")))
                self.assertTrue(self.active(9318000 + i * 2, s))
                s["flags"].add("aubm_b1_india_front_" + tag.lower())
                self.assertFalse(self.active(9318000 + i * 2, s))
                self.assertFalse(self.active(9318001 + i * 2, s))
                s["wars"].clear()
                self.assertTrue(self.active(9318001 + i * 2, s))
                s["flags"].clear()
                s["wars"].add(frozenset((tag, "IND")))
                s["alliances"].add(frozenset((tag, "IND")))
                self.assertFalse(self.active(9318000 + i * 2, s))
                s["alliances"].clear()
                s["exists"].remove("IND")
                self.assertFalse(self.active(9318000 + i * 2, s))
                s["exists"].add("IND")
                s["ai"].add("IND")
                self.assertFalse(self.active(9318000 + i * 2, s))
                s["ai"].remove("IND")
                s["ai"].remove(tag)
                self.assertFalse(self.active(9318000 + i * 2, s))

    def test_africa_no_port_no_ally_and_single_package(self):
        s = state()
        s["wars"] = {frozenset(("GER", "ENG")), frozenset(("ITA", "ENG"))}
        s["alliances"].add(frozenset(("GER", "ITA")))
        s["control"]["55"] = "GER"
        self.assertFalse(any(self.active(i, s) for i in range(9318020, 9318023)))
        for p in ("750", "761", "765"): s["control"][p] = "ITA"
        self.assertEqual([self.active(i, s) for i in range(9318020, 9318023)], [True, False, False])
        del s["control"]["750"]
        self.assertEqual([self.active(i, s) for i in range(9318020, 9318023)], [False, True, False])
        s["flags"].add("aubm_b1_afrika_deployed")
        self.assertFalse(any(self.active(i, s) for i in range(9318020, 9318023)))
        s["flags"].clear()
        s["exists"].remove("ITA")
        self.assertFalse(any(self.active(i, s) for i in range(9318020, 9318023)))
        s["exists"].add("ITA")
        s["supplies"] = 5999
        self.assertFalse(any(self.active(i, s) for i in range(9318020, 9318023)))

    def test_finland_support_only_continuation_war(self):
        s = state()
        s["alliances"].add(frozenset(("GER", "FIN")))
        s["control"]["517"] = "FIN"
        s["wars"].add(frozenset(("FIN", "SOV")))
        self.assertFalse(self.active(9318023, s))
        s["wars"].add(frozenset(("GER", "SOV")))
        self.assertTrue(self.active(9318023, s))
        for eid in (9318023, 9318024):
            self.assertEqual(self.events[str(eid)].get("date").get("year"), "1941")
            self.assertEqual(self.events[str(eid)].get("date").get("month"), "june")
        s["flags"].add("aubm_b1_nordland_deployed")
        self.assertFalse(self.active(9318023, s))

    def test_no_infinite_troops_or_player_menus(self):
        for event in self.events.values():
            self.assertEqual(event.get("name"), "AI_EVENT")
            self.assertIsNone(event.get("decision"))
            units = [n for n in walk(event) if n.get("type") == "add_division"]
            if units:
                self.assertEqual(event.get("persistent"), "no")
                self.assertEqual(len(units), 2)
                self.assertTrue(any(n.get("type") == "manpowerpool" for n in walk(event)))

    def test_stock_ai_switch_gets_war_guarded_response(self):
        out, _ = transform(fixture())
        e = parse(out["db/events/AI/AI_SOV.txt"]).get("event")
        commands = e.get("action_a").all("command")
        self.assertEqual(commands[0].get("which"), "switch/SOV_Germany.ai")
        self.assertEqual(commands[1].get("which"), "aubm/balance1/SOV_india_front.ai")
        self.assertIsInstance(commands[1].get("trigger"), Node)

    def test_fail_closed_missing_baseline_and_id_collision(self):
        with self.assertRaises(ValueError): transform({})
        f = fixture()
        f["db/events/foreign.txt"] = "event = {\n id = 9318000\n country = IND\n}"
        with self.assertRaises(ValueError): transform(f)


if __name__ == "__main__":
    unittest.main()

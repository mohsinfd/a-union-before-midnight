"""Static naval transaction/timing tests; no game or installed writes."""
import copy
from pathlib import Path
import unittest

from dh_save_spans import Node, parse, walk
import aubm_redesign_navy as navy

DONE = dict(zip(range(9271100, 9271111), (
    "ind_v3_naval_staff", "ind_v3_three_fleet_doctrine", "ind_v3_dockyard_act",
    "ind_v3_carrier_decision", "ind_v3_arabian_fleet", "ind_v3_bay_fleet",
    "ind_v3_carrier_keels", "ind_v3_oceanic_fleet_commissioned",
    "ind_v3_trincomalee_command", "ind_v3_naval_board_1941", "ind_v3_second_carrier")))
DONE.update({9281880: "ind_aubm_shbb_himalaya_contract", 9281881: "ind_aubm_shbb_vindhyagiri_contract"})


def state(eid):
    return dict(flags=(set(DONE.values()) | {"ind_v3_transport_1934", "ind_v3_naval_program", navy.PROGRAMMES[0]}) - {DONE[eid]},
                year=1950, month=11, day=29, elapsed={}, ai=False, exists=True,
                money=10000, supplies=10000, manpower=100, ic=200,
                technologies={3490}, owned={1511, 1517, 1533, 1493, 1497}, control={1511})


def evaluate(node, s):
    def one(key, value):
        if key in ("AND", "OR", "NOT"):
            results = [one(f.key, f.value) for f in value.fields]
            return all(results) if key == "AND" else any(results) if key == "OR" else not any(results)
        if key == "flag": return value in s["flags"]
        if key == "event": return s["elapsed"].get(int(value.get("id")), -1) >= int(value.get("days"))
        if key == "exists": return s["exists"]
        if key == "ai": return s["ai"] == (value == "yes")
        if key == "technology": return int(value) in s["technologies"]
        if key in ("owned", "control"): return int(value.get("province")) in s[key]
        if key in ("year", "month", "day", "money", "supplies", "manpower", "ic"):
            return s[key] >= float(value)
        raise AssertionError(f"Unhandled predicate {key}")
    return all(one(f.key, f.value) for f in node.fields)


class NavyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / "mod/db/events"
        cls.files = {"india_v3/32_navy.txt": (root / "india_v3/32_navy.txt").read_text(encoding="cp1252"),
                     "aubm_v4/40_special_units_and_capital_ships.txt": (root / "aubm_v4/40_special_units_and_capital_ships.txt").read_text(encoding="cp1252")}
        cls.output, cls.records = navy.transform(cls.files)
        cls.before = {int(ev.get("id")): ev for text in cls.files.values() for ev in parse(text).all("event")}
        cls.after = {int(ev.get("id")): ev for text in cls.output.values() for ev in parse(text).all("event")}

    def test_ids_effects_and_unrelated_events_preserved(self):
        self.assertEqual(set(self.before), set(self.after))
        for eid, event in self.before.items():
            if eid in navy.EDITED_IDS: continue
            self.assertEqual(navy.inner(next(t for t in self.files.values() if f"id = {eid}" in t), event),
                             navy.inner(next(t for t in self.output.values() if f"id = {eid}" in t), self.after[eid]))
        def fingerprint(command):
            return tuple((f.key, str(f.value)) for f in command.fields if not isinstance(f.value, Node))
        for eid in navy.EDITED_IDS:
            def effect_commands(ev, before=False):
                result=[]
                for action in navy.actions(ev):
                    for c in action.value.all("command"):
                        if c.get("type") == "add_brigade": continue
                        if c.get("type") == "setflag" and c.get("which") == navy.paid_flag(eid): continue
                        if eid in navy.COST_CHANGES and c.get("type") in ("money", "supplies"): continue
                        result.append(fingerprint(c))
                return result
            self.assertEqual(effect_commands(self.before[eid]), effect_commands(self.after[eid]))

    def test_exact_cost_reductions_and_no_old_threshold(self):
        for eid, (_, costs) in navy.COST_CHANGES.items():
            event = self.after[eid]
            action = next(a.value for a in navy.actions(event) if navy.substantive(a.value))
            for resource, amount in zip(("money", "supplies"), costs):
                values = [int(c.get("value")) for c in action.all("command") if c.get("type") == resource]
                self.assertEqual(values, [-amount])
                exact = state(eid)
                exact[resource] = amount
                self.assertTrue(evaluate(action.get("trigger"), exact))
                exact[resource] -= .01
                self.assertFalse(evaluate(action.get("trigger"), exact))

    def test_65_loose_brigades_removed_and_queued_hulls_identical(self):
        self.assertEqual(sum(t.count("type = add_brigade") for t in self.files.values()), 65)
        self.assertEqual(sum(t.count("type = add_brigade") for t in self.output.values()), 0)
        for eid in navy.EDITED_IDS:
            def builds(event):
                return [(c.get("which"), c.get("value"), c.get("when"), c.get("where"), c.get("name"))
                        for a in navy.actions(event) for c in a.value.all("command") if c.get("type") == "build_division"]
            self.assertEqual(builds(self.before[eid]), builds(self.after[eid]))

    def test_cancel_retry_and_completion_closure(self):
        for eid in navy.EDITED_IDS:
            event = self.after[eid]
            self.assertEqual(event.get("persistent"), "yes")
            self.assertEqual(event.get("save_date"), "yes")
            cancel = [a.value for a in navy.actions(event) if not navy.substantive(a.value)]
            self.assertEqual(len(cancel), 1)
            self.assertEqual(cancel[0].all("command"), [])
            base = state(eid)
            self.assertTrue(evaluate(event.get("decision_trigger"), base), eid)
            self.assertTrue(evaluate(cancel[0].get("trigger"), dict(base, money=0, supplies=0)))
            closed = copy.deepcopy(base)
            closed["flags"].add(DONE[eid])
            for key in ("decision", "trigger", "decision_trigger"):
                self.assertFalse(evaluate(event.get(key), closed), eid)
            for a in navy.actions(event):
                if navy.substantive(a.value):
                    self.assertFalse(evaluate(a.value.get("trigger"), closed), eid)

    def test_new_contracts_open_at_50_to_75_percent_proxy_not_before(self):
        for eid, info in navy.TIMING.items():
            event = self.after[eid]
            delays = info["days"] if isinstance(info["days"], tuple) else (info["days"],)
            schedules = info["scheduled"] if isinstance(info["scheduled"], tuple) else (info["scheduled"],)
            for i, (delay, schedule) in enumerate(zip(delays, schedules)):
                self.assertGreaterEqual(delay/schedule, .5)
                self.assertLessEqual(delay/schedule, .75)
                base = state(eid)
                base["flags"].difference_update(navy.PROGRAMMES)
                base["flags"].add(navy.PROGRAMMES[i])
                base["flags"].add(navy.paid_flag(info["previous"]))
                self.assertFalse(evaluate(event.get("decision_trigger"), base))
                base["elapsed"][info["previous"]] = delay-1
                self.assertFalse(evaluate(event.get("decision_trigger"), base))
                base["elapsed"][info["previous"]] = delay
                self.assertTrue(evaluate(event.get("decision_trigger"), base), eid)
                for action in navy.actions(event):
                    if navy.substantive(action.value) and evaluate(action.value.get("trigger"), base):
                        stale = copy.deepcopy(base)
                        stale["elapsed"][info["previous"]] = delay-1
                        self.assertFalse(evaluate(action.value.get("trigger"), stale))

    def test_legacy_contracts_keep_calendar_not_missing_date_fast_track(self):
        for eid, info in navy.TIMING.items():
            base = state(eid)
            year, month, day = info["legacy"]
            base.update(year=year-1, month=11, day=29)
            self.assertFalse(evaluate(self.after[eid].get("decision_trigger"), base), eid)
            base.update(year=year, month=month, day=day)
            self.assertTrue(evaluate(self.after[eid].get("decision_trigger"), base), eid)
            base["flags"].add(navy.paid_flag(info["previous"]))
            self.assertFalse(evaluate(self.after[eid].get("decision_trigger"), base), eid)

    def test_crew_reserve_and_exclusive_ocean_programmes(self):
        for eid, reserve in navy.QUEUE_RESERVES.items():
            base = state(eid)
            base["manpower"] = reserve
            self.assertTrue(evaluate(self.after[eid].get("decision_trigger"), base))
            base["manpower"] -= .01
            self.assertFalse(evaluate(self.after[eid].get("decision_trigger"), base))
        for i, reserve in enumerate(navy.OCEAN_RESERVES):
            base = state(9271106)
            base["flags"].difference_update(navy.PROGRAMMES)
            base["flags"].add(navy.PROGRAMMES[i])
            base["manpower"] = reserve
            self.assertTrue(evaluate(self.after[9271106].get("decision_trigger"), base))
            base["manpower"] -= .01
            self.assertFalse(evaluate(self.after[9271106].get("decision_trigger"), base))
            base["manpower"] = 100
            base["flags"].update(navy.PROGRAMMES)
            self.assertFalse(evaluate(self.after[9271106].get("decision_trigger"), base))

    def test_input_immutable_idempotent_and_drift_detected(self):
        source = dict(self.files)
        self.assertEqual(navy.transform(self.output)[0], self.output)
        self.assertEqual(self.files, source)
        tampered = dict(self.output)
        key = "india_v3/32_navy.txt"
        tampered[key] = tampered[key].replace("persistent = yes", "persistent = no", 1)
        with self.assertRaises(ValueError): navy.transform(tampered)
        self.assertEqual(set(self.records), set(navy.EDITED_IDS) | set(navy.INSPECTED_UNCHANGED_IDS))

    def test_visible_text_limits_and_engine_action_keys(self):
        for eid in navy.EDITED_IDS:
            event = self.after[eid]
            self.assertLessEqual(len(event.get("name")), 58)
            self.assertLessEqual(len(event.get("desc")), 340)
            self.assertLessEqual(len(event.get("decision_desc")), 500)
            for action in navy.actions(event):
                self.assertIn(action.key, ("action", "action_a", "action_b", "action_c", "action_d"))
                self.assertLessEqual(len(action.value.get("name")), 58)

    def test_carrier_question_cannot_spend_at_zero_queue_manpower(self):
        event = self.after[9271103]
        base = state(9271103)
        base["manpower"] = 0
        self.assertFalse(evaluate(event.get("decision_trigger"), base))
        for action in navy.actions(event):
            if navy.substantive(action.value):
                self.assertFalse(evaluate(action.value.get("trigger"), base))
        base["manpower"] = 2
        self.assertTrue(evaluate(event.get("action_c").get("trigger"), base))

    def test_fresh_earliest_overlap_precedes_original_oceanic_calendar(self):
        # DH event calendars use 12 months of 30 scripted days. Authorize
        # Arabian in March 1937, Bengal after225d, Oceanic afteranother225d.
        base = state(9271104)
        base.update(year=1937, month=1, day=29)
        self.assertFalse(evaluate(self.after[9271104].get("decision_trigger"), base))
        base.update(month=2, day=0)
        self.assertTrue(evaluate(self.after[9271104].get("decision_trigger"), base))
        for eid, absolute in ((9271105, 1937*360+60+225), (9271106, 1937*360+60+450)):
            s = state(eid)
            year, within = divmod(absolute, 360)
            month, day = divmod(within, 30)
            previous = navy.TIMING[eid]["previous"]
            s.update(year=year, month=month, day=day)
            s["flags"].add(navy.paid_flag(previous))
            s["elapsed"][previous] = 225
            self.assertTrue(evaluate(self.after[eid].get("decision_trigger"), s))
        self.assertLess(absolute, 1938*360 + 9*30)


if __name__ == "__main__":
    unittest.main()

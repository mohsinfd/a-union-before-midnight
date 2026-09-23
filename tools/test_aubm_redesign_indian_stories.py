"""Static model tests; these do not claim native DH playtesting."""
import copy
from pathlib import Path
import re
import unittest

from dh_save_spans import Node, parse, walk
import aubm_redesign_indian_stories as stories


def passes(node, state):
    def one(key, value):
        if key in ("AND", "OR", "NOT"):
            results = [one(f.key, f.value) for f in value.fields]
            return (all(results) if key == "AND" else
                    any(results) if key == "OR" else not any(results))
        if key == "flag":
            return value in state["flags"]
        if key == "ispuppet":
            return state["puppet"]
        if key == "exists":
            return value == "IND" and state["exists"]
        if key in ("ai", "atwar"):
            return state[key] == (value == "yes")
        if key in ("year", "month", *stories.STOCK.values()):
            return state[key] >= float(value)
        raise AssertionError(f"Unsupported test predicate: {key}={value}")
    return all(one(f.key, f.value) for f in node.fields)


def state_for(story):
    return dict(ai=False, atwar=story["war"], year=1942,
                month=story["months"][0], exists=True, puppet=False,
                money=5000, supplies=10000, metal=3000, oil=3000,
                manpower=100, dissent=2, flags=set())


def perform(action, state):
    result = copy.deepcopy(state)
    assert passes(action.get("trigger"), state)
    for command in action.all("command"):
        kind = command.get("type")
        if kind == "setflag":
            result["flags"].add(command.get("which"))
        else:
            result[stories.STOCK[kind]] += float(command.get("value"))
    return result


class IndianStoriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = {s["id"]: parse(stories.render(s)).get("event")
                      for s in stories.STORIES}

    def test_exact_twelve_ids_and_writing_bounds(self):
        self.assertEqual(tuple(self.events), stories.NEW_EVENT_IDS)
        self.assertEqual(len(self.events), 12)
        for event in self.events.values():
            self.assertLessEqual(len(event.get("desc")), 500)
            self.assertLessEqual(len(event.get("name")), 58)
            for key in ("action_a", "action_b", "action_c"):
                self.assertLessEqual(len(event.get(key).get("name")), 58)

    def test_only_explicit_bounded_commands(self):
        allowed = set(stories.STOCK) | {"setflag"}
        for story in stories.STORIES:
            event = self.events[story["id"]]
            for node in walk(event):
                for command in node.all("command"):
                    self.assertIn(command.get("type"), allowed)
                    if command.get("type") == "manpowerpool":
                        self.assertLessEqual(float(command.get("value")), 8)
            self.assertNotIn("ind_aubm_route", stories.render(story))
            for _, effects in story["options"]:
                self.assertTrue(any(v < 0 for v in effects.values()))
                self.assertLessEqual(effects.get("supplies", 0), 700)
                self.assertLessEqual(effects.get("oilpool", 0), 300)
                self.assertLessEqual(effects.get("money", 0), 100)

    def test_every_cost_has_stock_check_and_cannot_overdraw(self):
        for story in stories.STORIES:
            for key, (_, effects) in zip(("action_a", "action_b"), story["options"]):
                event = self.events[story["id"]]
                action = event.get(key)
                exact = state_for(story)
                for resource, amount in effects.items():
                    if amount < 0:
                        exact[stories.STOCK[resource]] = -amount
                self.assertTrue(passes(action.get("trigger"), exact))
                after = perform(action, exact)
                self.assertTrue(all(after[r] >= 0 for r in stories.STOCK.values()))
                for resource, amount in effects.items():
                    if amount < 0:
                        short = copy.deepcopy(exact)
                        short[stories.STOCK[resource]] = -amount - 0.01
                        self.assertFalse(passes(action.get("trigger"), short))

    def test_all_substantive_choices_close_story_and_other_option(self):
        for story in stories.STORIES:
            event = self.events[story["id"]]
            for choice in ("action_a", "action_b"):
                after = perform(event.get(choice), state_for(story))
                self.assertIn(stories.flag(story), after["flags"])
                for key in ("decision", "decision_trigger", "trigger"):
                    self.assertFalse(passes(event.get(key), after))
                for key in ("action_a", "action_b"):
                    self.assertFalse(passes(event.get(key).get("trigger"), after))

    def test_cancel_is_free_retryable_and_always_available_to_player(self):
        for story in stories.STORIES:
            event = self.events[story["id"]]
            self.assertEqual(event.get("persistent"), "yes")
            before = state_for(story)
            self.assertEqual(perform(event.get("action_c"), before), before)
            self.assertTrue(passes(event.get("decision_trigger"), before))
            stale = dict(before, month=11, atwar=not story["war"], money=0,
                         puppet=True, flags={stories.flag(story)})
            self.assertTrue(passes(event.get("action_c").get("trigger"), stale))

    def test_context_rechecked_even_after_opening(self):
        for story in stories.STORIES:
            event = self.events[story["id"]]
            base = state_for(story)
            mutations = [dict(atwar=not base["atwar"]), dict(puppet=True),
                         dict(exists=False), dict(ai=True), dict(year=1933),
                         dict(month=(story["months"][0]+2) % 12)]
            for mutation in mutations:
                stale = dict(base, **mutation)
                for key in ("decision", "decision_trigger", "trigger"):
                    self.assertFalse(passes(event.get(key), stale))
                for key in ("action_a", "action_b"):
                    self.assertFalse(passes(event.get(key).get("trigger"), stale))

    def test_no_old_save_flood_and_months_disclosed(self):
        for year in (1933, 1934, 1942, 1964):
            for month in range(12):
                for war in (False, True):
                    visible = 0
                    for story in stories.STORIES:
                        state = dict(state_for(story), year=year, month=month, atwar=war)
                        event = self.events[story["id"]]
                        visible += passes(event.get("decision"), state)
                        self.assertIn(story["season"], event.get("decision_desc"))
                    self.assertLessEqual(visible, 1)
                    if year == 1933:
                        self.assertEqual(visible, 0)

    def test_may_1942_snapshot_can_choose_carriers_with_no_metal(self):
        story = stories.STORIES[2]
        state = dict(state_for(story), month=4, money=1707.2875,
                     supplies=18440.4121, manpower=527.2674, dissent=0, metal=0)
        event = self.events[story["id"]]
        self.assertTrue(passes(event.get("decision_trigger"), state))
        self.assertTrue(passes(event.get("action_b").get("trigger"), state))

    def test_relief_not_wasted_at_zero_dissent(self):
        for story in stories.STORIES:
            state = dict(state_for(story), dissent=0)
            for key, (_, effects) in zip(("action_a", "action_b"), story["options"]):
                if effects.get("dissent", 0) < 0:
                    self.assertFalse(passes(self.events[story["id"]].get(key).get("trigger"), state))

    def test_append_preserves_every_existing_byte_and_is_idempotent(self):
        files = {"db/events/" + stories.SOURCE_MODULE: "# Original\r\nevent = { id = 1 }\r\n",
                 "unrelated.txt": "unchanged"}
        original = dict(files)
        result, records = stories.transform(files)
        self.assertEqual(files, original)
        self.assertTrue(result[next(iter(files))].startswith(files[next(iter(files))]))
        self.assertEqual(result["unrelated.txt"], "unchanged")
        self.assertEqual(stories.transform(result), (result, records))
        self.assertEqual(set(records), set(stories.NEW_EVENT_IDS))
        self.assertTrue(all(r[0]["dimension"] == "indian_stories" for r in records.values()))

    def test_rejects_collisions_and_missing_target(self):
        with self.assertRaises(ValueError):
            stories.transform({})
        with self.assertRaises(ValueError):
            stories.transform({stories.SOURCE_MODULE: "", "other.txt": "event = { id = 9398100 }"})

    def test_marker_cannot_claim_review_for_missing_or_changed_bodies(self):
        with self.assertRaises(ValueError):
            stories.transform({stories.SOURCE_MODULE: stories.MARKER})
        output, _ = stories.transform({stories.SOURCE_MODULE: ""})
        output[stories.SOURCE_MODULE] = output[stories.SOURCE_MODULE].replace(
            "type = supplies value = 500", "type = supplies value = 50000", 1)
        with self.assertRaises(ValueError):
            stories.transform(output)

    def test_authored_corpus_collision_free_and_parseable(self):
        root = Path(__file__).resolve().parents[1] / "mod/db/events/aubm_v4"
        files = {p.name: p.read_text(encoding="cp1252") for p in root.glob("*.txt")}
        output, records = stories.transform(files)
        ids = [int(e.get("id")) for e in parse(output[stories.SOURCE_MODULE]).all("event")]
        for event_id in stories.NEW_EVENT_IDS:
            self.assertEqual(ids.count(event_id), 1)


if __name__ == "__main__":
    unittest.main()

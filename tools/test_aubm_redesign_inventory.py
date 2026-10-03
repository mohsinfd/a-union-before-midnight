"""Contracts for honest static coverage, not a Darkest Hour engine emulator."""
import json
import unittest

try:
    from .aubm_redesign_inventory import inventory
except ImportError:
    from aubm_redesign_inventory import inventory


def event(eid, body="", country="IND"):
    return f'event = {{ id = {eid} country = {country} name = "Event {eid}" {body} }}'


class RedesignInventoryTests(unittest.TestCase):
    def test_every_id_and_module_are_covered_even_foreign_and_internal(self):
        files = {"a.txt": event(1) + event(2, "one_action = yes", "ENG"),
                 "b.txt": event(3, "trigger = { ai = yes }"), "empty.txt": "# empty"}
        report = inventory(files)
        self.assertEqual({ev["id"] for ev in report["events"]}, {1, 2, 3})
        self.assertEqual(report["coverage"]["event_occurrences"], 3)
        self.assertEqual(report["coverage"]["module_count"], 3)
        self.assertEqual(report["coverage"]["dispositions"]["pending"], 3)
        for ev in report["events"]:
            self.assertIn("UNREVIEWED", ev["disposition_reasons"][0])
            self.assertFalse(ev["human_authored_reviewed"])
            self.assertFalse(ev["engine_tested"])
        json.dumps(report)

    def test_bare_and_lettered_actions_both_count(self):
        report = inventory({"a": event(1, '''
            action = { name = "Close" }
            action_a = { name = "Next" command = { type = event which = 2 } }
            action = { name = "Pay" command = { type = money value = -50 } }
        ''') + event(2)})
        ev = report["events"][0]
        self.assertEqual(ev["action_count"], 3)
        self.assertEqual(ev["effect_class"], "effectful")
        self.assertEqual(ev["direct_links"][0]["target_id"], 2)
        self.assertEqual(ev["direct_links"][0]["action_index"], 1)
        self.assertTrue(ev["actions"][0]["empty_exit_candidate"])
        self.assertIn("direct_callback", report["events"][1]["entry_points"])

    def test_navigation_and_no_effects_do_not_imply_retirement(self):
        files = {"a": event(1, 'action = { command = { type = trigger which = 2 } }') +
                 event(2, "persistent = yes action = { command = {} }")}
        result = inventory(files)["events"]
        self.assertEqual(result[0]["effect_class"], "navigation_only")
        self.assertEqual(result[1]["effect_class"], "no_effects")
        self.assertEqual(result[1]["lifecycle"], "persistent")
        self.assertEqual(result[0]["lifecycle"], "one_time_default")
        self.assertTrue(all(ev["disposition"] == "pending" for ev in result))

    def test_ai_chance_and_nested_or_or_not_cannot_hide_indian_events(self):
        bodies = ["one_action = yes action = { ai_chance = 100 }",
                  "trigger = { OR = { ai = yes flag = example } }",
                  "trigger = { NOT = { ai = no } }",
                  "decision = { ai = yes }", ""]
        report = inventory({"a": "".join(event(i, body) for i, body in enumerate(bodies, 1))})
        self.assertTrue(all(ev["human_facing_candidate"] for ev in report["events"]))
        positive = inventory({"a": event(8, "trigger = { AND = { ai = yes } }")})["events"][0]
        self.assertTrue(positive["mandatory_positive_ai_guard"])
        self.assertEqual(positive["disposition"], "pending")

    def test_missing_country_and_id_remain_accounted_for(self):
        ev = inventory({"a": 'event = { name = "Unknown" action = {} }'})["events"][0]
        self.assertIsNone(ev["id"])
        self.assertEqual(ev["visibility"], "unknown_visibility_unreviewed")
        self.assertEqual(ev["disposition"], "pending")

    def test_duplicate_ids_are_not_silently_overwritten(self):
        report = inventory({"a": event(1), "b": event(1)})
        self.assertEqual(len(report["events"]), 2)
        self.assertEqual(report["coverage"]["unique_event_ids"], 1)
        self.assertEqual(report["duplicate_ids"], {"1": ["a#1", "b#1"]})

    def test_missing_callbacks_are_scoped_and_delays_are_retained(self):
        report = inventory({"a": event(1, 'action = { command = { type = event which = 99 when = 3 } }')})
        self.assertEqual(report["callback_missing"][0]["target_id"], 99)
        self.assertEqual(report["callback_missing"][0]["delay"], {"when": "3"})
        self.assertIn("stock/external", report["callback_missing_scope"])

    def test_callback_where_identifies_foreign_receiver_and_preserves_delay(self):
        report = inventory({"a": event(1, '''action = {
            command = { type = event which = 2 where = JAP when = 3 }
            command = { type = event which = 2 country = ENG when = 5 }
        }''') + event(2, country="JAP")})
        links = report["events"][0]["direct_links"]
        self.assertEqual(links[0]["country"], "JAP")
        self.assertEqual(links[0]["where"], "JAP")
        self.assertEqual(links[0]["delay"], {"when": "3"})
        self.assertEqual(links[1]["country"], "ENG")
        self.assertEqual(report["events"][1]["incoming_links"][0]["country"], "JAP")

    def test_saved_history_queue_and_sleep_never_create_engine_proof(self):
        report = inventory({"a": event(1, "date = { year = 1933 } decision = {}")},
                           slept_1933_ids=[1], latest_save_refs={"history_ids": [1], "queued_ids": [1]})
        ev = report["events"][0]
        self.assertTrue(ev["slept_in_1933"])
        self.assertEqual(ev["entry_points"], ["calendar", "decision", "queued_in_latest_save"])
        self.assertFalse(ev["engine_tested"])
        self.assertEqual(ev["retirement"], "not_established")
        self.assertEqual(ev["branch_closure"], "unverified")

    def test_explicit_review_and_engine_evidence_are_separate(self):
        review = {1: {"disposition": "rewrite", "reasons": ["Choices lack consequences"],
                      "human_authored_reviewed": True, "human_review_evidence": "review-notes.md"}}
        report = inventory({"a": event(1)}, review)
        self.assertTrue(report["events"][0]["human_authored_reviewed"])
        self.assertFalse(report["events"][0]["engine_tested"])
        self.assertEqual(report["coverage"]["human_authored_reviewed"], 1)
        review[1].update(engine_tested=True, engine_test_evidence=["engine-session-log.md"])
        self.assertEqual(inventory({"a": event(1)}, review)["coverage"]["engine_tested"], 1)

    def test_claims_require_explicit_evidence(self):
        for record in ({"engine_tested": True}, {"human_authored_reviewed": True},
                       {"disposition": "keep"}, {"engine_tested": "yes"}):
            with self.subTest(record=record), self.assertRaises(ValueError):
                inventory({"a": event(1)}, {1: record})

    def test_stale_review_is_pending(self):
        review = {1: {"disposition": "keep", "reasons": ["Good choices"], "source_sha256": "old",
                      "human_authored_reviewed": True, "human_review_evidence": ["notes.md"]}}
        ev = inventory({"a": event(1)}, review)["events"][0]
        self.assertEqual(ev["disposition"], "pending")
        self.assertFalse(ev["human_authored_reviewed"])
        self.assertTrue(ev["review_stale"])

    def test_bad_modules_cannot_claim_complete_coverage(self):
        with self.assertRaisesRegex(ValueError, "bad.txt"):
            inventory({"bad.txt": "event = { id = 1"})

    def test_occurrence_specific_review_and_unmatched_review_keys(self):
        report = inventory({"a": event(1), "b": event(1)},
                           {"b#1": {"disposition": "retire", "reasons": ["Duplicate navigation"]},
                            "999": {"disposition": "pending"}})
        self.assertEqual([ev["disposition"] for ev in report["events"]], ["pending", "retire"])
        self.assertEqual(report["events"][1]["retirement"], "proposed_by_review")
        self.assertEqual(report["unmatched_review_keys"], ["999"])


if __name__ == "__main__":
    unittest.main()

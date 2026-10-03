"""Tests against authored source; no game installation or source writes."""
from pathlib import Path
import unittest

from dh_save_spans import Node, parse, replace
from aubm_redesign_prose import CATALOG, actions, effect_bytes, transform

ROOT = Path(__file__).resolve().parents[1]


def events(text):
    return {int(f.value.get("id")): f.value for f in parse(text).fields
            if f.key == "event" and isinstance(f.value, Node)}


def mask_presentation(text):
    edits = []
    for event in events(text).values():
        for f in event.fields:
            if f.key in {"name", "desc", "decision_desc"}:
                edits.append((f.value_start, f.end, '"PRESENTATION"'))
        for a in actions(event):
            f = a.field("name")
            edits.append((f.value_start, f.end, '"PRESENTATION"'))
    return replace(text, edits)


class ProseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {}
        for path in (ROOT / "mod/db/events").rglob("*.txt"):
            text = path.read_bytes().decode("latin1")
            # Only parse files which may contain a bounded catalogue ID.
            if any(str(eid) in text for eid in CATALOG):
                cls.files[str(path.relative_to(ROOT))] = text
        cls.output, cls.reviews = transform(cls.files)

    def test_all_24_authored_events_are_present_and_reviewed(self):
        self.assertEqual(24, len(CATALOG))
        self.assertEqual(set(CATALOG), set(self.reviews))
        self.assertTrue(all(r[0]["status"] == "reviewed"
                            for r in self.reviews.values()), self.reviews)

    def test_every_nonpresentation_byte_is_unchanged(self):
        for path, before in self.files.items():
            after = self.output[path]
            self.assertEqual(mask_presentation(before), mask_presentation(after), path)
            old, new = events(before), events(after)
            self.assertEqual(set(old), set(new))
            for eid in old:
                self.assertEqual(effect_bytes(before, old[eid]),
                                 effect_bytes(after, new[eid]), (path, eid))
                if eid not in CATALOG:
                    self.assertEqual(before[old[eid].start:old[eid].end],
                                     after[new[eid].start:new[eid].end], eid)

    def test_idempotent_and_input_unchanged(self):
        again, review = transform(self.output)
        self.assertEqual(self.output, again)
        self.assertTrue(all(r[0]["status"] == "reviewed" for r in review.values()))
        for path, text in self.files.items():
            self.assertEqual(text, (ROOT / path).read_bytes().decode("latin1"))

    def test_presentation_limits_and_safe_quoting(self):
        for spec in CATALOG.values():
            self.assertLessEqual(len(spec["title"]), 58)
            self.assertLessEqual(len(spec["description"]), 500)
            for value in [spec["title"], spec["description"], *spec["actions"].values()]:
                self.assertNotIn('"', value)
                self.assertNotIn("\n", value)
                value.encode("ascii")
            for value in spec["actions"].values():
                self.assertLessEqual(len(value), 58)

    def test_inserted_cancel_does_not_shift_substantive_action(self):
        eid = 9289910
        path, text = next((p, t) for p, t in self.files.items() if eid in events(t))
        e = events(text)[eid]
        first = actions(e)[0]
        cancel = '\n action = { name = "Cancel - leave unchanged" }\n'
        # Insert before the action field, not inside its opening brace.
        af = next(f for f in e.fields if f.value is first)
        changed = text[:af.start] + cancel + text[af.start:]
        output, records = transform({path: changed})
        rewritten = events(output[path])[eid]
        self.assertEqual("Cancel - leave unchanged", actions(rewritten)[0].get("name"))
        self.assertEqual("Begin the 90-day hold", actions(rewritten)[1].get("name"))
        self.assertEqual("reviewed", records[eid][0]["status"])
        self.assertEqual(mask_presentation(changed), mask_presentation(output[path]))

    def test_unknown_action_leaves_entire_event_pending(self):
        eid = 9289910
        path, text = next((p, t) for p, t in self.files.items() if eid in events(t))
        changed = text.replace("Begin the 90-day consolidation record", "A new substantive choice")
        output, records = transform({path: changed})
        self.assertEqual("pending", records[eid][0]["status"])
        before, after = events(changed)[eid], events(output[path])[eid]
        self.assertEqual(changed[before.start:before.end], output[path][after.start:after.end])

    def test_missing_ids_are_pending_and_not_generated(self):
        output, records = transform({"empty.txt": "# no events\n"})
        self.assertEqual({"empty.txt": "# no events\n"}, output)
        self.assertTrue(all(r[0]["status"] == "pending" for r in records.values()))

    def test_changed_effect_cannot_receive_a_stale_prose_review(self):
        eid = 9289910
        path, text = next((p, t) for p, t in self.files.items() if eid in events(t))
        event = events(text)[eid]
        command = actions(event)[0].field("command")
        changed = replace(text, [(command.start, command.end,
            "command = { type = money value = -999 }")])
        output, records = transform({path: changed})
        self.assertEqual("pending", records[eid][0]["status"])
        before, after = events(changed)[eid], events(output[path])[eid]
        self.assertEqual(changed[before.start:before.end], output[path][after.start:after.end])


if __name__ == "__main__":
    unittest.main()

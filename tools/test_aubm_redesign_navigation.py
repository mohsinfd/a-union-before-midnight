"""Bounded navigation graph/command tests; no native UI claim."""
from pathlib import Path
import unittest
from dh_save_spans import Node, parse, walk
import aubm_redesign_navigation as nav


def index(files):
    return {int(e.get("id")): (text[e.start:e.end], e)
            for text in files.values() for e in parse(text).all("event")}


def canonical(node):
    return tuple((f.key, canonical(f.value) if isinstance(f.value, Node) else f.value)
                 for f in node.fields)


def evaluate(node, state):
    def one(key, value):
        if key in ("AND", "OR", "NOT"):
            results = [one(f.key, f.value) for f in value.fields]
            return all(results) if key == "AND" else any(results) if key == "OR" else not any(results)
        if key == "flag": return value in state["flags"]
        if key == "ai": return state["ai"] == (value == "yes")
        if key == "atwar": return bool(state["wars"]) == (value == "yes")
        if key == "year": return state["year"] >= int(value)
        if key == "exists": return value in state["exists"]
        if key == "ispuppet": return value in state["puppets"]
        if key in ("war", "alliance"):
            pair = frozenset(value.all("country"))
            return pair in state["wars" if key == "war" else "alliances"]
        raise AssertionError("Unknown navigation predicate: " + key)
    return all(one(f.key, f.value) for f in node.fields)


def state():
    return dict(flags=set(), ai=False, year=1942, exists={"IND", "JAP"},
                puppets=set(), wars=set(), alliances=set())


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / "mod/db/events"
        cls.source = {p.relative_to(root).as_posix(): p.read_text(encoding="cp1252")
                      for folder in ("india_v3", "aubm_v4") for p in (root/folder).glob("*.txt")}
        cls.output, cls.records = nav.transform(cls.source)
        cls.before, cls.after = index(cls.source), index(cls.output)

    def test_no_ids_removed_or_added_and_unrelated_nodes_unchanged(self):
        self.assertEqual(set(self.before), set(self.after))
        for eid in self.before.keys() - set(nav.REVIEWED_IDS):
            self.assertEqual(self.before[eid][0], self.after[eid][0], eid)
        self.assertEqual(len(self.records), 26)

    def test_fourteen_retired_pages_are_only_free_close(self):
        for eid in nav.RETIRED_IDS:
            event = self.after[eid][1]
            self.assertIsNone(event.get("decision"))
            self.assertIsNone(event.get("date"))
            self.assertIsNone(event.get("one_action"))
            aa = nav.actions(event)
            self.assertEqual(len(aa), 1)
            self.assertFalse(aa[0].value.all("command"))
            self.assertTrue(evaluate(aa[0].value.get("trigger"), state()))

    def test_navigation_cannot_declare_war_pay_or_record_completion(self):
        pure_pages = (*nav.RETIRED_IDS, nav.ROOT_ID, 9281012, 9289645, *nav.WAR_REVIEWS)
        for eid in pure_pages:
            for a in nav.actions(self.after[eid][1]):
                for c in a.value.all("command"):
                    self.assertEqual(c.get("type"), "event", eid)
                    self.assertNotIn(int(c.get("which")), nav.RETIRED_IDS)

    def test_every_actual_effect_and_commitment_survives(self):
        for eid in nav.REVIEWED_IDS:
            if eid in nav.SECONDARY_LEDGERS: continue
            def effects(event):
                return [canonical(c) for a in nav.actions(event) for c in a.value.all("command")
                        if c.get("type") != "event"]
            self.assertEqual(effects(self.before[eid][1]), effects(self.after[eid][1]), eid)
        # Explicit real alliance, war and relief nodes are not rewritten.
        for eid in (9281910, 9281920, 9281921, 9281922, 9281923, 9289649, 9289650):
            self.assertEqual(self.before[eid][0], self.after[eid][0])

    def test_no_callbacks_advertised_as_new_direct_decisions(self):
        for eid in nav.REVIEWED_IDS:
            if eid == nav.ROOT_ID: continue
            self.assertIsNone(self.after[eid][1].get("decision"), eid)
        event = self.after[nav.ROOT_ID][1]
        self.assertIsNotNone(event.get("decision"))
        self.assertNotIn("ind_aubm_route_", self.after[nav.ROOT_ID][0])
        self.assertNotIn("aubm_v4_union_register_opened", self.after[nav.ROOT_ID][0])
        self.assertTrue(evaluate(event.get("decision"), state()))
        early = state(); early["year"] = 1933
        self.assertFalse(evaluate(event.get("decision"), early))
        early["wars"].add(frozenset(("IND", "JAP")))
        self.assertTrue(evaluate(event.get("decision"), early))
        early["puppets"].add("IND")
        self.assertFalse(evaluate(event.get("decision"), early))

    def test_japan_access_uses_real_partner_state_not_route(self):
        event = self.after[nav.ROOT_ID][1]
        link = next(a.value for a in nav.actions(event) if any(c.get("which") == "9289645" for c in a.value.all("command")))
        base = state()
        self.assertFalse(evaluate(link.get("trigger"), base))
        base["flags"].add("ind_aubm_route_japan")
        self.assertFalse(evaluate(link.get("trigger"), base))
        base["alliances"].add(frozenset(("IND", "JAP")))
        self.assertTrue(evaluate(link.get("trigger"), base))
        base["wars"].add(frozenset(("IND", "JAP")))
        self.assertFalse(evaluate(link.get("trigger"), base))
        compact = state()
        compact["flags"].update(("ind_aubm_commitment_japan", "ind_aubm_jp_partnership"))
        self.assertTrue(evaluate(link.get("trigger"), compact))
        compact["flags"].add("ind_aubm_commitment_soviet")
        self.assertFalse(evaluate(link.get("trigger"), compact))

    def test_loop_cuts_sandbox_write_survives_without_self_popup(self):
        self.assertEqual(sum(len(r[0]["retired_links"]) for r in self.records.values()), 44)
        for eid in (*nav.JAPAN_PAGES, 9281013):
            for a in nav.actions(self.after[eid][1]):
                for c in a.value.all("command"):
                    if c.get("type") == "event":
                        self.assertNotIn(int(c.get("which")), (*nav.RETIRED_IDS, nav.ROOT_ID, 9289645, eid))
        sandbox = self.after[9281013][1]
        writes = [c for a in nav.actions(sandbox) for c in a.value.all("command") if c.get("type") == "setflag"]
        self.assertEqual([c.get("which") for c in writes], ["ind_aubm_unrestricted_sandbox"])

    def test_dead_mirror_reader_fails_closed_and_no_reward_removed(self):
        poisoned = dict(self.source)
        poisoned["new_consumer.txt"] = "event = { id = 1 trigger = { flag = ind_aubm_bespoke_secondary_allied_southern } }"
        with self.assertRaisesRegex(ValueError, "live reader"):
            nav.transform(poisoned)
        self.assertEqual(sum(r[0]["mirror_writes_retired"] for r in self.records.values()), 35)

    def test_idempotent_input_unchanged_and_supported_action_keys(self):
        again, _ = nav.transform(self.output)
        self.assertEqual(again, self.output)
        for eid in nav.REVIEWED_IDS:
            event = self.after[eid][1]
            self.assertLessEqual(len(event.get("name")), 58)
            self.assertLessEqual(len(event.get("desc")), 500)
            for a in nav.actions(event):
                self.assertIn(a.key, ("action", "action_a", "action_b", "action_c", "action_d"))

    def test_previously_board_only_effects_remain_reachable(self):
        def links(event):
            return [int(c.get("which")) for a in nav.actions(event) for c in a.value.all("command") if c.get("type") == "event"]
        def reach(indexed, roots, stop_at_effects=False):
            seen, pending = set(), list(roots)
            while pending:
                eid = pending.pop()
                if eid in seen or eid not in indexed: continue
                seen.add(eid)
                event = indexed[eid][1]
                real = any(c.get("type") != "event" for a in nav.actions(event) for c in a.value.all("command"))
                if not (stop_at_effects and real): pending.extend(links(event))
            return seen
        old_frontier = reach(self.before, nav.RETIRED_IDS, stop_at_effects=True)
        actual = {eid for eid in old_frontier if any(c.get("type") != "event"
                  for a in nav.actions(self.before[eid][1]) for c in a.value.all("command"))}
        # The five crisis offers have their own dated live trigger in authored
        # input and become direct state-driven decisions in the preceding stage.
        native_roots = {eid for eid, (_, ev) in self.after.items()
                        if ev.get("decision") is not None or
                        (ev.get("date") is not None and ev.get("trigger") is not None)}
        available = reach(self.after, native_roots | {nav.ROOT_ID})
        self.assertFalse(actual - set(nav.SECONDARY_LEDGERS) - available)
        cabinet_paths = reach(self.after, {nav.ROOT_ID})
        for eid in (9281910, 9281913, 9289646, 9289647, 9289648, 9289649):
            self.assertIn(eid, cabinet_paths)
        for eid in (9289501, 9289541, 9289581, 9289621, 9289661):
            self.assertIn(eid, native_roots)
        # Postwar settlement navigation must not disappear when peace returns.
        result_link = next(a.value for a in nav.actions(self.after[nav.ROOT_ID][1])
                           if any(c.get("which") == "9281913" for c in a.value.all("command")))
        self.assertTrue(evaluate(result_link.get("trigger"), state()))


if __name__ == "__main__":
    unittest.main()

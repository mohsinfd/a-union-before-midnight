"""Stock surrender adapter tests; never write to the installed game."""
from pathlib import Path
import unittest

from dh_save_spans import Node, parse, walk
from aubm_stock_settlement_guard import (
    apply_guard, apply_china_client_guard, apply_japan_client_guard, FALLBACK_NAME, PROTECTED,
    CLIENT_TRANSFER_TYPES,
)

FIXTURE = b'''# stock bytes outside this event must survive\r\nevent = { id = 1 country = JAP action = { name = "Other" command = { type = money value = 17 } } }\r\nevent = {\r\n id = 2011028\r\n country = JAP\r\n trigger = { war = { country = JAP country = USA } }\r\n action = { name = "Offer surrender" ai_chance = 90 command = { type = inherit which = U87 } command = { type = peace which = USA value = 1 } }\r\n action = { name = "Fight on" ai_chance = 10 command = { type = sleepevent which = 2049003 } command = { type = dissent value = 5 } }\r\n}\r\nevent = { id = 2 action = { name = "Other" } }\r\n'''


def evaluate(node, war=False, enabled=False, city=None, india=True):
    values = []
    for f in node.fields:
        k, v = f.key, f.value
        if k == "AND":
            result = evaluate(v, war, enabled, city, india)
        elif k == "OR":
            result = any(evaluate(Node(fields=[x]), war, enabled, city, india) for x in v.fields)
        elif k == "NOT":
            result = not evaluate(v, war, enabled, city, india)
        elif k == "exists":
            result = india
        elif k == "war":
            # The fixture's original US war remains true in every case.
            result = True if "USA" in v.all("country") else war
        elif k == "flag":
            result = enabled
        elif k == "control":
            result = v.get("province") == city
        else:
            raise AssertionError(k)
        values.append(result)
    return all(values)


class StockSurrenderGuardTests(unittest.TestCase):
    def test_scope_is_exact_and_idempotent(self):
        guarded = apply_guard(FIXTURE)
        self.assertEqual(apply_guard(guarded), guarded)
        old, new = parse(FIXTURE).all("event"), parse(guarded).all("event")
        for i in (0, 2):
            self.assertEqual(FIXTURE[old[i].start:old[i].end], guarded[new[i].start:new[i].end])
        self.assertNotIn(b"\n", guarded.replace(b"\r\n", b""))

    def test_only_active_indian_home_island_stake_blocks(self):
        event = next(e for e in parse(apply_guard(FIXTURE)).all("event") if e.get("id") == "2011028")
        for war, enabled, city, blocked in (
            (False, True, "1552", False), (True, False, "1552", False),
            (True, True, None, False), (True, True, "1337", False),
            (True, True, "1552", True), (True, True, "1553", True),
            (True, True, "1554", True),
        ):
            with self.subTest(war=war, enabled=enabled, city=city):
                self.assertEqual(evaluate(event.get("trigger"), war, enabled, city), not blocked)
                available = [a for a in event.all("action") if a.get("trigger") is None or evaluate(a.get("trigger"), war, enabled, city)]
                if blocked:
                    self.assertEqual(len(available), 1)
                    self.assertEqual(available[0].get("name"), FALLBACK_NAME)
                    self.assertEqual(available[0].all("command"), [])
                else:
                    self.assertEqual([a.get("name") for a in available], ["Offer surrender", "Fight on"])

    def test_command_bytes_and_amounts_are_preserved(self):
        guarded = apply_guard(FIXTURE)
        def commands(raw):
            return [raw[n.start:n.end] for n in walk(parse(raw)) if n.get("type")]
        self.assertEqual(commands(FIXTURE), commands(guarded))

    def test_releases_guard_when_india_loses_city_or_war_ends(self):
        expression = parse("trigger = { " + PROTECTED + " }").get("trigger")
        self.assertTrue(evaluate(expression, True, True, "1552"))
        self.assertFalse(evaluate(expression, True, True, None))
        self.assertFalse(evaluate(expression, False, True, "1552"))

    def test_installed_stock_parses_without_writing(self):
        path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\db\events\japan.txt")
        if not path.exists():
            self.skipTest("Installed stock fixture is unavailable")
        raw = path.read_bytes()
        updated = apply_guard(raw)
        old_commands = [raw[n.start:n.end] for n in walk(parse(raw)) if n.get("type")]
        new_commands = [updated[n.start:n.end] for n in walk(parse(updated)) if n.get("type")]
        self.assertEqual(old_commands, new_commands)
        self.assertEqual(path.read_bytes(), raw)


CHINA_FIXTURE = b'''# Preserve this outside comment\r\nevent = { id = 1 action = { command = { type = inherit which = U87 } } }\r\nevent = { id = 2012004 trigger = { flag = victory } action = { name = "Victory" command = { trigger = { exists = U87 } type = inherit which = U87 } command = { type = money value = 37 } } }\r\nevent = { id = 2012005 action = { name = "Terms" command = { trigger = { OR = { flag = korea flag = alternate } } type = make_puppet which = KOR } command = { type = make_puppet which = PRK } command = { type = make_puppet which = U03 } command = { type = inherit which = MAN } command = { type = inherit which = MEN } command = { type = end_mastery which = VIE } command = { type = secederegion which = U03 value = Indochine } } }\r\n'''


def evaluate_client(node, masters=None, flags=(), existing=()):
    masters = masters or {}
    results = []
    for field in node.fields:
        k, v = field.key, field.value
        if k == "AND":
            value = evaluate_client(v, masters, flags, existing)
        elif k == "OR":
            value = any(evaluate_client(Node(fields=[f]), masters, flags, existing) for f in v.fields)
        elif k == "NOT":
            value = not evaluate_client(v, masters, flags, existing)
        elif k == "puppet":
            subject, master = v.all("country")
            value = masters.get(subject) == master
        elif k == "flag":
            value = v in flags
        elif k == "exists":
            value = v in existing
        else:
            raise AssertionError(k)
        results.append(value)
    return all(results)


def command_nontrigger_bytes(raw):
    return [[raw[f.start:f.end] for f in n.fields if f.key != "trigger"]
            for n in walk(parse(raw)) if n.get("type")]


class ChinaClientGuardTests(unittest.TestCase):
    def test_actual_indian_client_only(self):
        updated = apply_china_client_guard(CHINA_FIXTURE)
        for event in parse(updated).all("event")[1:]:
            for action in event.all("action"):
                for command in action.all("command"):
                    if command.get("type") not in CLIENT_TRANSFER_TYPES:
                        continue
                    target = command.get("which")
                    for master in (None, "JAP", "CHI", "IND"):
                        with self.subTest(target=target, master=master):
                            self.assertEqual(evaluate_client(command.get("trigger"), {target: master}, ("korea",), ("U87",)), master != "IND")

    def test_existing_conditions_are_still_required(self):
        events = parse(apply_china_client_guard(CHINA_FIXTURE)).all("event")
        inherit = events[1].all("action")[0].all("command")[0]
        korea = events[2].all("action")[0].all("command")[0]
        self.assertFalse(evaluate_client(inherit.get("trigger")))
        self.assertFalse(evaluate_client(korea.get("trigger")))
        self.assertTrue(evaluate_client(korea.get("trigger"), flags=("alternate",)))

    def test_no_event_or_action_disable_and_effects_preserved(self):
        updated = apply_china_client_guard(CHINA_FIXTURE)
        old_events, new_events = parse(CHINA_FIXTURE).all("event"), parse(updated).all("event")
        self.assertEqual(CHINA_FIXTURE[old_events[0].start:old_events[0].end], updated[new_events[0].start:new_events[0].end])
        self.assertEqual(command_nontrigger_bytes(CHINA_FIXTURE), command_nontrigger_bytes(updated))
        for old, new in zip(old_events[1:], new_events[1:]):
            if old.get("trigger"):
                a, b = old.get("trigger"), new.get("trigger")
                self.assertEqual(CHINA_FIXTURE[a.start:a.end], updated[b.start:b.end])
            else:
                self.assertIsNone(new.get("trigger"))
            self.assertTrue(all(a.get("trigger") is None for a in new.all("action")))
        self.assertEqual(apply_china_client_guard(updated), updated)
        self.assertNotIn(b"\n", updated.replace(b"\r\n", b""))

    def test_installed_china_only_seven_explicit_client_transfers(self):
        path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\db\events\china.txt")
        if not path.exists():
            self.skipTest("Installed stock fixture is unavailable")
        raw = path.read_bytes()
        updated = apply_china_client_guard(raw)
        self.assertEqual(command_nontrigger_bytes(raw), command_nontrigger_bytes(updated))
        original_events, updated_events = parse(raw).all("event"), parse(updated).all("event")
        changed = []
        for old, new in zip(original_events, updated_events):
            if old.get("id") not in ("2012004", "2012005"):
                self.assertEqual(raw[old.start:old.end], updated[new.start:new.end])
            for a, b in zip(old.all("action"), new.all("action")):
                for x, y in zip(a.all("command"), b.all("command")):
                    if raw[x.start:x.end] != updated[y.start:y.end]:
                        changed.append((old.get("id"), x.get("type"), x.get("which")))
        from aubm_stock_settlement_guard import CHINA_MARKER,validate_china_client_guard
        validate_china_client_guard(updated)
        self.assertEqual(changed, [] if CHINA_MARKER.encode() in raw else [
            ("2012004", "inherit", "U87"), ("2012004", "inherit", "U87"),
            ("2012005", "inherit", "MAN"), ("2012005", "inherit", "MEN"),
            ("2012005", "make_puppet", "KOR"), ("2012005", "make_puppet", "PRK"),
            ("2012005", "make_puppet", "U03"),
        ])
        self.assertEqual(path.read_bytes(), raw)


class JapanClientGuardTests(unittest.TestCase):
    def test_mastery_commands_protect_only_current_indian_clients(self):
        raw = b'event = { id = 2011018 action_a = { command = { type = end_mastery which = MAN } command = { trigger = { flag = release } type = end_mastery which = MEN } command = { type = money value = 43 } } }'
        updated = apply_japan_client_guard(raw)
        self.assertEqual(apply_japan_client_guard(updated), updated)
        self.assertEqual(command_nontrigger_bytes(raw), command_nontrigger_bytes(updated))
        commands = parse(updated).all("event")[0].get("action_a").all("command")
        for command in commands[:2]:
            target = command.get("which")
            for master in (None, "JAP", "CHI", "IND"):
                self.assertEqual(evaluate_client(command.get("trigger"), {target: master}, ("release",)), master != "IND")
        self.assertFalse(evaluate_client(commands[1].get("trigger")))
        self.assertIsNone(commands[2].get("trigger"))

    def test_installed_japan_composition_changes_only_two_client_commands(self):
        path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\db\events\japan.txt")
        if not path.exists():
            self.skipTest("Installed stock fixture is unavailable")
        raw = path.read_bytes()
        updated = apply_japan_client_guard(raw)
        self.assertEqual(command_nontrigger_bytes(raw), command_nontrigger_bytes(updated))
        changed = []
        for old, new in zip(parse(raw).all("event"), parse(updated).all("event")):
            if old.get("id") != "2011018":
                self.assertEqual(raw[old.start:old.end], updated[new.start:new.end])
            for a, b in zip([f.value for f in old.fields if f.key and f.key.startswith("action")],
                            [f.value for f in new.fields if f.key and f.key.startswith("action")]):
                for x, y in zip(a.all("command"), b.all("command")):
                    if raw[x.start:x.end] != updated[y.start:y.end]:
                        changed.append((old.get("id"), x.get("type"), x.get("which")))
        from aubm_stock_settlement_guard import JAPAN_CLIENT_MARKER,validate_japan_client_guard
        validate_japan_client_guard(updated)
        self.assertEqual(changed, [] if JAPAN_CLIENT_MARKER.encode() in raw else [("2011018", "end_mastery", "MAN"), ("2011018", "end_mastery", "MEN")])
        combined = apply_japan_client_guard(apply_guard(raw))
        self.assertEqual(combined, apply_guard(apply_japan_client_guard(raw)))
        self.assertEqual(apply_japan_client_guard(apply_guard(combined)), combined)
        self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()

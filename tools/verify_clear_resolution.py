from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aubm_resolution_outcomes import MARKER, NEW_EVENT_IDS, records
from dh_save_spans import parse


def commands(event):
    return [c for action in event.all("action") for c in action.all("command")]


def main(root):
    base = Path(root) / "staged-authored" / "db" / "events" / "aubm_v4"
    modules = {
        name: (base / name).read_text(encoding="latin1")
        for name in ("46_regional_campaigns.txt", "47_global_campaign_matrix.txt", "49_bespoke_armistices.txt")
    }
    parsed = {name: {int(e.get("id")): e for e in parse(text).all("event")} for name, text in modules.items()}
    assert len(NEW_EVENT_IDS) == 456
    assert all(MARKER in text for text in modules.values())

    checked = 0
    for module, docket, tag, name, capital, foreign_id, final_id, family in records():
        events = parsed[module]
        assert docket in events and foreign_id in events and final_id in events
        docket_event, foreign_event, final_event = events[docket], events[foreign_id], events[final_id]
        labels = [a.get("name") for a in docket_event.all("action")]
        assert any("Indian protectorate" in label for label in labels)
        assert any("Independent partner" in label for label in labels)
        assert any("Continue the war" in label for label in labels)
        assert "60%" not in (docket_event.get("desc") or "")
        protect = next(a for a in docket_event.all("action") if "Indian protectorate" in a.get("name"))
        partner = next(a for a in docket_event.all("action") if "Independent partner" in a.get("name"))
        protect_commands, partner_commands = protect.all("command"), partner.all("command")
        for action_commands in (protect_commands, partner_commands):
            assert any(c.get("type") == "inherit" and c.get("which") == tag for c in action_commands)
            assert any(c.get("type") == "independence" and c.get("which") == tag and c.get("value") == "1" for c in action_commands)
            assert any(c.get("type") == "make_puppet" and c.get("which") == tag for c in action_commands)
            assert not any(c.get("type") in ("peace", "leave_alliance", "event") for c in action_commands)
        assert not any(c.get("type") == "end_mastery" for c in protect_commands)
        assert any(c.get("type") == "end_mastery" and c.get("which") == tag for c in partner_commands)
        assert any(c.get("type") == "trigger" and c.get("which") == str(foreign_id) for c in partner_commands)
        foreign_commands = commands(foreign_event)
        assert any(c.get("type") == "access" and c.get("which") == "IND" for c in foreign_commands)
        assert any(c.get("type") == "leave_alliance" for c in foreign_commands)
        final_commands = commands(final_event)
        assert not any(c.get("type") in ("peace", "inherit", "independence", "make_puppet", "leave_alliance") for c in final_commands)
        assert all(len((e.get("name") or "").encode("utf-8")) <= 58 for e in (docket_event, foreign_event, final_event))
        checked += 1

    all_ids = [eid for events in parsed.values() for eid in events]
    assert len(all_ids) == len(set(all_ids))
    for events in parsed.values():
        for event in events.values():
            assert not any(c.get("type") == "peace" for c in commands(event)), event.get("id")
    print(f"PASS: {checked} universal atomic settlement dockets; no delayed peace path; synchronous partner access verified")


if __name__ == "__main__":
    main(sys.argv[1])

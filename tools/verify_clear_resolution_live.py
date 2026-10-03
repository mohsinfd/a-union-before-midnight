from pathlib import Path
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aubm_resolution_outcomes import MARKER, NEW_EVENT_IDS, records
from aubm_victory_clarity import MARKER as VICTORY_MARKER
from dh_save_spans import Node, parse

LIVE = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1")
CANDIDATE = Path(r"C:\Users\Mohsin Dingankar\Downloads\India Ascendant\build\redesign\candidate18\staged-authored")
SAVE = LIVE / "scenarios/save games/WESTERN1_newplayIndia_1941_October_6.eug"
MODULES = ("43_wartime_settlements.txt", "45_enemy_campaigns.txt", "46_regional_campaigns.txt", "47_global_campaign_matrix.txt", "49_bespoke_armistices.txt")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_queued(node):
    for field in node.fields:
        if field.key == "event" and isinstance(field.value, Node):
            yield field.value
        if isinstance(field.value, Node):
            yield from walk_queued(field.value)


def main():
    live_events = LIVE / "db/events/aubm_v4"
    candidate_events = CANDIDATE / "db/events/aubm_v4"
    for name in MODULES:
        live, candidate = live_events / name, candidate_events / name
        assert digest(live) == digest(candidate), name
        text=live.read_text(encoding="latin1")
        assert (VICTORY_MARKER if name.startswith(("43_","45_")) else MARKER) in text

    ids = []
    module_maps = {}
    for path in live_events.glob("*.txt"):
        events = parse(path.read_bytes()).all("event")
        ids.extend(int(e.get("id")) for e in events if e.get("id"))
        if path.name in MODULES:
            module_maps[path.name] = {int(e.get("id")): e for e in events}
    assert len(ids) == len(set(ids)), "duplicate event IDs in live aubm_v4"
    assert NEW_EVENT_IDS <= set(ids)
    for module, docket, tag, name, capital, foreign_id, final_id, family in records():
        assert {docket, foreign_id, final_id} <= set(module_maps[module])

    root = parse(SAVE.read_bytes())
    countries = {c.get("tag"): c for c in root.all("country")}
    flags = root.get("globaldata").get("flags")
    relation = next(r for r in countries["IND"].get("diplomacy").all("relation") if r.get("tag") == "SIK")
    assert countries["SIK"].get("puppet") == "IND"
    assert relation.get("access") == "yes"
    assert "SIK" in root.get("globaldata").get("axis").get("participant").atoms()
    assert all("SIK" in side.get("participant").atoms()
               for war in root.get("globaldata").all("war")
               for side in (war.get("attackers"), war.get("defenders"))
               if isinstance(side, Node) and "IND" in side.get("participant").atoms())
    assert float(countries["IND"].get("dissent")) == 0.0
    assert flags.get("ind_aubm_regional_settled_sik") == "1"
    assert flags.get("ind_aubm_bespoke_armistice_outstanding") == "0"
    assert not any(e.get("tag") == "IND" and e.get("id") in ("9282288", "9282291") for e in walk_queued(root))
    print(f"PASS: live modules match candidate; {len(ids)} live AUBM IDs unique; WESTERN1 Xinjiang puppet/access/war state intact")


if __name__ == "__main__":
    main()

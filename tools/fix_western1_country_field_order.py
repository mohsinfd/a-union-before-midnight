"""Build an engine-canonical WESTERN1 copy without changing campaign state."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dh_save_spans import parse, replace

SAVE_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\scenarios\save games")
SOURCE = SAVE_DIR / "WESTERN1_newplayIndia_1941_October_6.eug"
OUTPUT = SAVE_DIR / "PLAY_WESTERN1_FIXED_India_1941_October_15.eug"
OUTPUT_CFG = OUTPUT.with_suffix(".eug.cfg")


def main():
    raw = SOURCE.read_bytes()
    root = parse(raw)
    countries = {c.get("tag"): c for c in root.all("country")}
    edits = []
    moved = []

    for tag in ("SIK", "PER"):
        country = countries[tag]
        puppet = country.field("puppet")
        anchor = country.field("breakthrough")
        assert puppet and puppet.value == "IND", (tag, "missing Indian mastery")
        assert anchor, (tag, "missing canonical puppet anchor")
        if country.fields.index(puppet) != country.fields.index(anchor) + 1:
            edits.append((puppet.start, puppet.end, b""))
            edits.append((anchor.end, anchor.end, b"\n\tpuppet = IND"))
            moved.append(tag)

    optionfile = root.get("header").field("optionfile")
    new_option = r'"scenarios\save games\PLAY_WESTERN1_FIXED_India_1941_October_15.eug.cfg"'
    edits.append((optionfile.value_start, optionfile.end, new_option.encode("ascii")))
    display_name = root.get("header").field("name")
    edits.append((display_name.value_start, display_name.end,
                  b'"PLAY WESTERN1 FIXED - India 15 October 1941"'))

    updated = replace(raw, edits)
    check = parse(updated)
    checked = {c.get("tag"): c for c in check.all("country")}
    for tag in ("SIK", "PER"):
        country = checked[tag]
        puppet_index = next(i for i, f in enumerate(country.fields) if f.key == "puppet")
        anchor_index = next(i for i, f in enumerate(country.fields) if f.key == "breakthrough")
        assert puppet_index == anchor_index + 1
        assert country.get("puppet") == "IND"
    assert all(next(f.key for f in c.fields if f.key) == "tag" for c in check.all("country"))

    OUTPUT.write_bytes(updated)
    shutil.copy2(SOURCE.with_suffix(".eug.cfg"), OUTPUT_CFG)
    print(json.dumps({
        "play_this": str(OUTPUT),
        "source_unchanged": str(SOURCE),
        "moved_to_engine_native_position": moved,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "output_sha256": hashlib.sha256(updated).hexdigest(),
        "campaign_state_changed": False,
    }, indent=2))


if __name__ == "__main__":
    main()

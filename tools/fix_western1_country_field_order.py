"""Move Xinjiang's repaired puppet field after the mandatory leading tag field."""
from datetime import datetime
from pathlib import Path
import hashlib, json, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dh_save_spans import parse, replace

SAVE=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\scenarios\save games\WESTERN1_newplayIndia_1941_October_6.eug")
ROOT=Path(__file__).resolve().parents[1]


def main():
    raw=SAVE.read_bytes(); root=parse(raw)
    sik=next(c for c in root.all("country") if c.get("tag")=="SIK")
    fields=[f for f in sik.fields if f.key]
    tag=sik.field("tag"); puppet=sik.field("puppet")
    assert puppet and puppet.value=="IND"
    if fields[0].key=="tag":
        print("Xinjiang country field order is already valid"); return
    updated=replace(raw,[(puppet.start,puppet.end,b""),(tag.end,tag.end,b"\n\tpuppet = IND")])
    check=parse(updated); cs={c.get("tag"):c for c in check.all("country")}; fixed=cs["SIK"]
    assert next(f.key for f in fixed.fields if f.key)=="tag" and fixed.get("puppet")=="IND"
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S"); backup=ROOT/"build/western-portfolio1"/("pre-country-order-fix-"+stamp)
    backup.mkdir(parents=True); backup_file=backup/SAVE.name; backup_file.write_bytes(raw); SAVE.write_bytes(updated)
    print(json.dumps({"save":str(SAVE),"backup":str(backup_file),
      "before_sha256":hashlib.sha256(raw).hexdigest(),"after_sha256":hashlib.sha256(updated).hexdigest(),
      "fix":"SIK tag is first; puppet remains IND"},indent=2))


if __name__=="__main__": main()

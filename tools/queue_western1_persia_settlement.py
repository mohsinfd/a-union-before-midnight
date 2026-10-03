"""Queue the valid Persian settlement that the old ownership gate suppressed."""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dh_save_spans import Node, parse, replace

SAVE = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\scenarios\save games\WESTERN1_newplayIndia_1941_October_6.eug")
ROOT = Path(__file__).resolve().parents[1]
EVENT_ID = "9282270"


def find_node(node, key):
    for field in node.fields:
        if field.key == key and isinstance(field.value, Node):
            return field.value
        if isinstance(field.value, Node):
            found=find_node(field.value,key)
            if found: return found


def queued(node):
    return [f.value for f in node.fields if f.key == "event" and isinstance(f.value, Node)]


def main():
    raw=SAVE.read_bytes(); root=parse(raw)
    countries={c.get("tag"):c for c in root.all("country")}
    flags=root.get("globaldata").get("flags")
    assert "PER" in countries and flags.get("ind_aubm_regional_current_per") == "1"
    assert "1080" in countries["IND"].get("controlledprovinces").atoms()
    queue=find_node(root,"queued_events"); assert queue
    if any(e.get("tag")=="IND" and e.get("id")==EVENT_ID for e in queued(queue)):
        print("Persian settlement already queued"); return
    insert=b'\n\t\tevent = { tag = IND id = 9282270 hour = 1 } '
    updated=replace(raw,[(queue.end-1,queue.end-1,insert)])
    check=parse(updated); q2=find_node(check,"queued_events")
    assert any(e.get("tag")=="IND" and e.get("id")==EVENT_ID for e in queued(q2))
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    backup=ROOT/"build/western-portfolio1"/("pre-persia-docket-"+stamp)
    backup.mkdir(parents=True); backup_file=backup/SAVE.name
    backup_file.write_bytes(raw); SAVE.write_bytes(updated)
    print(json.dumps({"save":str(SAVE),"backup":str(backup_file),
        "before_sha256":hashlib.sha256(raw).hexdigest(),
        "after_sha256":hashlib.sha256(updated).hexdigest(),
        "queued":"Persia explicit settlement docket in 1 hour",
        "other_state_unchanged":True},indent=2))


if __name__ == "__main__": main()

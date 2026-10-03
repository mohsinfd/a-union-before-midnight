"""Keep historical victory flags but remove two no-longer-valid live claims."""
from datetime import datetime
from pathlib import Path
import hashlib, json, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dh_save_spans import parse, replace

SAVE=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\scenarios\save games\WESTERN1_newplayIndia_1941_October_6.eug")
ROOT=Path(__file__).resolve().parents[1]
CLEAR=("ind_aubm_global_current_egy","ind_aubm_global_pending_egy",
       "ind_aubm_regional_current_irq","ind_aubm_regional_pending_irq")
SET=("ind_aubm_global_suspended_egy","ind_aubm_regional_suspended_irq")


def main():
    raw=SAVE.read_bytes(); root=parse(raw); flags=root.get("globaldata").get("flags"); edits=[]; additions=[]
    for key in CLEAR:
        f=flags.field(key)
        if f: edits.append((f.value_start,f.end,b"0"))
        else: additions.append(f"\n\t{key} = 0")
    for key in SET:
        f=flags.field(key)
        if f: edits.append((f.value_start,f.end,b"1"))
        else: additions.append(f"\n\t{key} = 1")
    if additions: edits.append((flags.end-1,flags.end-1,"".join(additions).encode("ascii")))
    updated=replace(raw,edits); check=parse(updated).get("globaldata").get("flags")
    assert all(check.get(k)=="0" for k in CLEAR) and all(check.get(k)=="1" for k in SET)
    assert check.get("ind_aubm_global_victory_egy")=="1" and check.get("ind_aubm_regional_victory_irq")=="1"
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S"); backup=ROOT/"build/western-portfolio1"/("pre-stale-victory-clean-"+stamp)
    backup.mkdir(parents=True); backup_file=backup/SAVE.name; backup_file.write_bytes(raw); SAVE.write_bytes(updated)
    print(json.dumps({"save":str(SAVE),"backup":str(backup_file),"before_sha256":hashlib.sha256(raw).hexdigest(),
      "after_sha256":hashlib.sha256(updated).hexdigest(),"cleared_live_claims":["Egypt","Iraq"],
      "historical_victories_preserved":True},indent=2))


if __name__=="__main__": main()

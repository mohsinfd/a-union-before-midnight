"""Apply the intended Persian protectorate directly without a peace transition."""
from datetime import datetime
from pathlib import Path
import hashlib, json, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dh_save_spans import Node, parse, replace

SAVE=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1\scenarios\save games\WESTERN1_newplayIndia_1941_October_6.eug")
ROOT=Path(__file__).resolve().parents[1]
SET=("ind_aubm_regional_settled_per","ind_aubm_bespoke_protected_per",
     "ind_aubm_bespoke_negotiated_per","ind_aubm_global_campaign_victory")
CLEAR=("ind_aubm_bespoke_armistice_outstanding","ind_aubm_bespoke_target_per",
       "ind_stage_resolution_protect_per","ind_stage_resolution_partner_per",
       "ind_stage_bespoke_full_per","ind_stage_bespoke_limited_per","ind_stage_bespoke_refused_per",
       "ind_aubm_regional_pending_per","ind_aubm_regional_current_per","ind_aubm_regional_suspended_per")


def scalar(node,key,value):
    f=node.field(key); return f.value_start,f.end,str(value).encode("latin1")


def participants(node,tag,present):
    f=node.field("participant"); atoms=f.value.atoms(); revised=[x for x in atoms if x!=tag]
    if present: revised.append(tag)
    if revised==atoms: return None
    return f.value_start,f.end,("{ "+" ".join(revised)+" }").encode("ascii")


def queued_fields(node):
    for field in node.fields:
        if field.key=="event" and isinstance(field.value,Node): yield field
        if isinstance(field.value,Node): yield from queued_fields(field.value)


def locations(node):
    out=[]
    for field in node.fields:
        if field.key in ("location","province") and not isinstance(field.value,Node): out.append((field.key,str(field.value)))
        if isinstance(field.value,Node): out.extend(locations(field.value))
    return out


def main():
    raw=SAVE.read_bytes(); root=parse(raw); countries={c.get("tag"):c for c in root.all("country")}
    india,per=countries["IND"],countries["PER"]; flags=root.get("globaldata").get("flags"); edits=[]
    before_provinces={t:((c.get("ownedprovinces").atoms() if c.get("ownedprovinces") else []),(c.get("controlledprovinces").atoms() if c.get("controlledprovinces") else [])) for t,c in countries.items()}
    before_locations=locations(root)
    if per.get("puppet") is None: edits.append((per.field("tag").end,per.field("tag").end,b"\n\tpuppet = IND"))
    elif per.get("puppet")!="IND": edits.append(scalar(per,"puppet","IND"))
    relation=next(x for x in india.get("diplomacy").all("relation") if x.get("tag")=="PER")
    if relation.get("access")!="yes": edits.append((relation.end-1,relation.end-1,b" access = yes "))
    globaldata=root.get("globaldata")
    for name in ("axis","allies","comintern"):
        alliance=globaldata.get(name); edit=participants(alliance,"PER",name=="axis")
        if edit: edits.append(edit)
    for war in globaldata.all("war"):
        sides=[war.get(k) for k in ("attackers","defenders")]
        india_side=next((s for s in sides if "IND" in s.get("participant").atoms()),None)
        if not india_side: continue
        for side in sides:
            edit=participants(side,"PER",side is india_side)
            if edit: edits.append(edit)
    additions=[]
    for key in SET:
        f=next((x for x in flags.fields if x.key==key),None)
        if f: edits.append((f.value_start,f.end,b"1"))
        else: additions.append(f"\n\t{key} = 1")
    for key in CLEAR:
        f=next((x for x in flags.fields if x.key==key),None)
        if f: edits.append((f.value_start,f.end,b"0"))
        else: additions.append(f"\n\t{key} = 0")
    if additions: edits.append((flags.end-1,flags.end-1,"".join(additions).encode("ascii")))
    removed=0
    for field in queued_fields(root):
        e=field.value
        if e.get("id") in ("9282270","9282280","9401100","9401101"):
            edits.append((field.start,field.end,b"")); removed+=1
    updated=replace(raw,edits); check=parse(updated); cc={c.get("tag"):c for c in check.all("country")}; ff=check.get("globaldata").get("flags")
    assert cc["PER"].get("puppet")=="IND" and next(f.key for f in cc["PER"].fields if f.key)=="tag"
    assert next(x for x in cc["IND"].get("diplomacy").all("relation") if x.get("tag")=="PER").get("access")=="yes"
    assert "PER" in check.get("globaldata").get("axis").get("participant").atoms()
    assert "PER" not in check.get("globaldata").get("allies").get("participant").atoms()
    after_provinces={t:((c.get("ownedprovinces").atoms() if c.get("ownedprovinces") else []),(c.get("controlledprovinces").atoms() if c.get("controlledprovinces") else [])) for t,c in cc.items()}
    assert before_provinces==after_provinces and before_locations==locations(check)
    assert all(ff.get(k)=="1" for k in SET) and all(ff.get(k)=="0" for k in CLEAR)
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S"); backup=ROOT/"build/western-portfolio1"/("pre-persia-direct-repair-"+stamp)
    backup.mkdir(parents=True); backup_file=backup/SAVE.name; backup_file.write_bytes(raw); SAVE.write_bytes(updated)
    print(json.dumps({"save":str(SAVE),"backup":str(backup_file),"before_sha256":hashlib.sha256(raw).hexdigest(),
      "after_sha256":hashlib.sha256(updated).hexdigest(),"persia":"Indian puppet; Axis member and co-belligerent",
      "indian_access":True,"queued_unsafe_events_removed":removed,"province_and_unit_positions_unchanged":True},indent=2))


if __name__=="__main__": main()

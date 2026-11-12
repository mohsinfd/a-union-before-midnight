"""Static validation of the actual installed Japan Rising build.

This checks structural/source invariants, not a simulated claim of engine play.
"""
from collections import Counter
import json
from pathlib import Path
import re
import sys
from PIL import Image

from build import TARGET,SOURCE,GAME,EVENTS,IDS,parse,get,getall,read,resolve,compiled_event,prepare_catalog


def run():
    # Compare installed content with the prepared source, not only its ID set.
    # Source-dependent province lists and completion safeguards are added here.
    prepare_catalog()
    errors=[];warnings=[]
    events=[];files=[]
    scenario=parse(read(TARGET/"scenarios/1933.eug"))
    index=parse(read(TARGET/"db/events.txt"))
    paths=[v for v in getall(index,"event")+getall(scenario,"event") if isinstance(v,str)]
    for rel in dict.fromkeys(paths):
        p=TARGET/rel.replace("\\","/")
        if not p.exists():errors.append("Missing event file "+rel);continue
        files.append(p)
        structure=[]
        try:tree=parse(read(p),structure)
        except ValueError as ex:errors.append(str(p)+": "+str(ex));continue
        if structure:errors.append(str(p)+": "+str(structure))
        for n in getall(tree,"event"):
            events.append((p,n))
    ids=Counter(get(e,"id") for _,e in events)
    errors += [f"Duplicate event {i} ({count})" for i,count in ids.items() if count>1]
    engine_ids=set(ids)
    from localisation_support import loaded_names,review as localisation_review
    from build import localisation
    names=loaded_names(TARGET,GAME,read)
    try:localisation_review(TARGET,GAME,localisation(),read)
    except AssertionError as ex:errors.append('Engine-loaded localisation: '+str(ex))
    from specialist_units import CLASSES,model_years
    for unit,info in CLASSES.items():
        for i,year in enumerate(model_years(unit)):
            for prefix in ('','_JAP'):
                key=f'MODEL{prefix}_{info["index"]}_{i}'
                if names.get(key)!=f'{info["name"]} {year}':errors.append('Missing engine-visible model name '+key)
    tech_ids=set()
    for p in (TARGET/"db/tech").glob("*.txt"):
        try:
            for tech in getall(parse(read(p)),"technology"):
                for app in getall(tech,"application"):tech_ids.add(get(app,"id"))
        except ValueError:pass
    generated=[(p,e) for p,e in events if "japan_rising" in p.parts]
    def walk(node):
        for k,v in node:
            yield k,v
            if isinstance(v,list):yield from walk(v)
    allowed_commands={
        "setflag","clrflag","local_setflag","local_clrflag","event","trigger","money","supplies","oilpool",
        "manpowerpool","construct","build_time","build_cost","industrial_modifier","tc_mod","attrition_mod",
        "gain_tech","max_organization","morale","transport_pool","escort_pool","build_division","add_corps",
        "add_division","add_brigade","activate_unit_type","deactivate_unit_type","activate_division","lock_division","unlock_division","remove_units","new_model","add_prov_resource","range","fuel_consumption",
        "dissent","leave_alliance","peace","end_puppet","country","make_puppet","independence","access",
        "non_aggression","end_non_aggression","secedeprovince","ai","addcore","removecore","headofstate",
        "headofgovernment","chiefofstaff","river_attack","urban_attack","war","end_mastery","research_mod",
        "frozen_move","frozen_defense","free_oil","alliance","inherit","trade","end_trades","naval_defense","naval_attack","hard_attack"
    }
    from specialist_units import MIRRORS
    allowed_commands.update(get(c,'type') for _,_,_,c in MIRRORS)
    allowed_commands.update({'scrap_model','free_manpower','wartime_ic_mod','repair_mod','stockpile'})
    allowed_commands.update({'energypool','metalpool','rarematerialspool','free_ic','sleepevent','set_relation','set_domestic','domestic'})
    # Verified against shipped event commands and native technology/events.
    from prewar_content import DOCUMENTED_NEW_COMMANDS
    allowed_commands.update(DOCUMENTED_NEW_COMMANDS)
    from equipment_delivery import DOCUMENTED_NEW_COMMANDS as EQUIPMENT_COMMANDS
    allowed_commands.update(EQUIPMENT_COMMANDS)
    # R12 mirrors these shipped unit-effect commands onto the registered
    # Japanese subclasses; their source/which/value parity is audited too.
    import unique_divisions
    allowed_commands.update(unique_divisions.UNIT_EFFECTS)
    for p,e in generated:
        eid=get(e,"id")
        for field in ("name","desc"):
            value=get(e,field)
            if value and value!="AI_EVENT" and value.startswith("JX_") and value not in names:
                errors.append(f"{eid}: missing localisation {value}")
        for k,v in walk(e):
            if k=="name" and isinstance(v,str) and v.startswith("JX_") and v not in names:errors.append(f"{eid}: missing action {v}")
            if k=="command" and isinstance(v,list):
                typ=get(v,"type")
                if typ and typ not in allowed_commands:errors.append(f"{eid}: unreviewed command {typ}")
                if typ in {"event","trigger"} and get(v,"which") not in engine_ids:
                    errors.append(f"{eid}: missing event target {get(v,'which')}")
                if typ=="event":
                    receiver=next((n for _,n in events if get(n,"id")==get(v,"which")),None)
                    if receiver and (get(receiver,"date") or get(receiver,"offset") or get(receiver,"trigger")):
                        errors.append(f"{eid}: scheduled event has normal trigger/date {get(v,'which')}")
                if typ=="gain_tech" and get(v,"which") not in tech_ids:errors.append(f"{eid}: invalid blueprint {get(v,'which')}")
                if typ=="ai":
                    ai=TARGET/"ai"/get(v,"which").replace("\\","/")
                    if not ai.exists():errors.append(f"{eid}: missing AI {ai}")
                if typ=="construct":
                    if get(v,"where") is None:errors.append(f"{eid}: unplaced construction")
                if typ=='inherit' and get(v,'value')!='1':errors.append(f'{eid}: inheritance does not explicitly preserve units/queue')
                if typ=='trade':
                    cancellable={str(IDS[k]) for k in ('fx1933','oil1934','fx1936')}
                    protected=get(v,'which')=='USA' and get(v,'where')=='JAP' and str(eid) not in cancellable
                    if get(v,'value')!=('1' if protected else '0') or not get(v,'when'):errors.append(f'{eid}: commercial trade protection/duration does not match its supplier policy')
                if typ in {"add_division","build_division"}:
                    unit=get(v,"value") if typ=="add_division" else get(v,"which")
                    if not (TARGET/"db/units/divisions"/(str(unit)+".txt")).exists():errors.append(f"{eid}: unknown unit {unit}")
        for art_field,folder in (("picture","gfx/events_pics"),("decision_picture","gfx/events_pics")):
            v=get(e,art_field)
            if v and not (TARGET/folder/(v+".bmp")).exists():errors.append(f"{eid}: missing art {v}")
            elif v:
                with Image.open(TARGET/folder/(v+".bmp")) as im:
                    expected=(224,48) if art_field=='decision_picture' else (400,116)
                    if im.size!=expected:errors.append(f"{eid}: wrong {art_field} dimensions {im.size}, expected {expected}")
    actual_new={get(e,"id") for _,e in generated}
    if actual_new!={str(e.id) for e in EVENTS}:errors.append("Installed new event IDs differ from catalogue")
    installed_by_id={get(e,'id'):e for _,e in generated}
    for definition in EVENTS:
        expected=get(parse(compiled_event(definition)),'event')
        if installed_by_id.get(str(definition.id))!=expected:
            errors.append(f'{definition.id} ({definition.key}): installed event differs from current compiled source')
    # Each technical country withdrawal must be performed by that country, never Japan.
    for p,e in generated:
        for a in getall(e,"action"):
            for c in getall(a,"command"):
                if get(c,"type")=="peace" and get(e,"country")=="JAP":
                    errors.append(f"{get(e,'id')}: Japan directly issues a peace command")
    # No India expansion modules or custom opening; historical IND country data is allowed.
    all_registered="\n".join(paths).lower()
    for token in ("india_overhaul","india_v3","aubm","india_compact"):
        if token in all_registered:errors.append("Forbidden India-mod import: "+token)
    if "The Proclamation of Indian Sovereignty" in read(TARGET/"db/events/UK.txt"):
        errors.append("Installed Indian independence contamination")
    rev=parse(read(TARGET/"db/revolt.txt"));u87=get(rev,"U87",[])
    if len(get(u87,"extra",[]))<50:errors.append("Chinese puppet still lacks its homeland cores")
    for tag,cap in (('INO','1647'),('CMB','1400')):
        if get(get(rev,tag,[]),'capital')!=cap:errors.append(f'{tag}: settlement/release capitals disagree')
    for model in range(5):
        for name,size in ((f'ill_div_JAP_41_{model}.bmp',(192,104)),(f'JAP_model_41_{model}.bmp',(67,44))):
            with Image.open(TARGET/'gfx/interface/models'/name) as im:
                if im.size!=size:errors.append(f'{name}: model image dimensions {im.size} != {size}')
    # Cabinet commands must select real ministers belonging to the receiver.
    ministers={}
    for p,e in generated:
        tag=get(e,'country')
        if tag not in ministers:
            candidates=list((TARGET/'db/ministers').glob('ministers_'+tag+'.csv'))
            ministers[tag]={line.split(';')[0] for source in candidates for line in read(source).splitlines() if line.split(';')[0].isdigit()}
        for a in getall(e,'action'):
            for c in getall(a,'command'):
                if get(c,'type') in {'headofstate','headofgovernment','chiefofstaff'} and get(c,'which') not in ministers[tag]:
                    errors.append(f"{get(e,'id')}: minister {get(c,'which')} does not belong to {tag}")
    all_text=read(TARGET/"config/japan_rising.csv")
    if "\xa7" in all_text:errors.append("Colour control codes in new localisation")
    for e in EVENTS:
        if e.decision and e.country=='JAP' and not e.ready.strip():
            errors.append(f'{e.key}: empty decision readiness falls back to the automatic trigger')
        if len(e.desc)>1500:warnings.append(f"{e.key}: long description ({len(e.desc)} characters), inspect in engine")
        for a in e.actions:
            if len(a.name)>72:warnings.append(f"{e.key}: long action ({len(a.name)} characters)")
    report={"result":"PASS" if not errors else "FAIL","event_files":len(files),"all_event_blocks":len(events),"new_event_blocks":len(generated),"new_decisions":sum(e.decision for e in EVENTS),"errors":errors,"warnings":warnings,"scope":"Static script, asset and dependency validation. Not engine playtesting."}
    (Path(__file__).parent/"STATIC_VALIDATION.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if not errors else 1


if __name__=="__main__":raise SystemExit(run())

"""Compile the explicit event catalogue, document it, and install an isolated mod.

All generated files derive from the catalogue/clean baseline. Existing India
installations and saves are never inputs to this builder.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
sys.path.insert(0,str(WORKSPACE / "tools"))
from audit_japan_baseline import parse, get, getall, num, TOKEN
from catalog import EVENTS, VERSION, MOD_NAME, Action, cmd, cond, control, owned, flag
import endings  # adds the major-power and Axis event catalogue
import partners  # Chinese alternatives and partner reconstruction
import early  # Historical preparation and conditional early-war choices
import activities  # Optional specialist training and operational preparations
import specialist_units  # Two separately registered Japanese specialist classes
import more_activities  # Diplomatic and geographically distinct opportunities
import release_support  # Common starter kit, including manual puppet releases
import construction_safety
import japan_personnel
import us_invasion
import snlf_cabinet  # Append after old events: preserve saved event IDs
import localisation_support
import production_programmes
import decision_banners
import model_names_and_ai
import campaign_balance
import japan_wartime  # staged manpower, wartime industry and land-air reach
import human_campaign
import force_value
import endurance_economy
import recruitment_endurance
import campaign_flow
import event_accessibility
import force_delivery_audit
import japanese_research_names
import minister_integrity
import regional_content
import prewar_content
import us_campaign_content
import final_event_integrity
import equipment_delivery
import player_copy
import unique_divisions
import unique_attachments
import unique_unit_events
import unique_art
import island_shipping
import r14_china
import r14_peace
import r14_afterwar
import r15_enemy
import r15_recovery
import r15_strategy
import enemy_transport_ai

from runtime_paths import GAME
from runtime_paths import SOURCE
TARGET = GAME / "Mods" / MOD_NAME
ART_INPUTS = {
    "naval":"exec-41d8b2b1-0209-40b3-8d47-fc6699f96b0b.png",
    "industry":"exec-fa9fb62e-b5cf-4c7c-a53b-9c52135c40ff.png",
    "asia":"exec-32b7f295-9c1e-42f7-8f97-11c3d09ec7c4.png",
    "army":"exec-b582bd2c-3881-443c-bf58-1718fb582ab8.png",
}
ART_INPUTS.update(unique_art.SOURCES)
from runtime_paths import ART_ROOT
IDS = {e.key:e.id for e in EVENTS}
IDS['activate_d_12']=snlf_cabinet.ACTIVATION_ID
PATCHES = []
PREPARED_CORES = None


def read(path):
    return path.read_text(encoding="latin1")


def write(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding="latin1",newline="\r\n")


def ascii_text(value):
    return value.replace("\u2014"," - ").replace("\u2013","-").replace("\u2019","'").replace("\u201c",'"').replace("\u201d",'"')


def resolve(text):
    def replace(m):
        key=m.group(1)
        if key not in IDS:
            raise ValueError("Unknown event reference: "+key)
        return str(IDS[key])
    return re.sub(r"@([A-Za-z0-9_]+)",replace,text)


def quote(s):
    if s is None:
        return '""'
    s=str(s)
    if re.fullmatch(r"[A-Za-z0-9_.:+-]+",s):
        return s
    return '"'+s.replace('"',"'")+'"'


def serialise(node,level=0):
    lines=[]
    for k,v in node:
        prefix="\t"*level+(str(k)+" = " if k is not None else "")
        if isinstance(v,list):
            if all(k2 is None and not isinstance(v2,list) for k2,v2 in v):
                lines.append(prefix+"{ "+" ".join(quote(v2) for _,v2 in v)+" }")
            else:
                lines.append(prefix+"{")
                lines.append(serialise(v,level+1))
                lines.append("\t"*level+"}")
        else:
            lines.append(prefix+quote(v))
    return "\n".join(lines)


def event_spans(source):
    for m in re.finditer(r"(?m)^\s*event\s*=\s*\{",source):
        depth=0
        for tok in TOKEN.finditer(source,m.start()):
            t=tok.group()
            if t.startswith("#") or t.startswith('"'):
                continue
            if t=="{":depth+=1
            elif t=="}":
                depth-=1
                if depth==0:
                    yield m.start(),tok.end(),get(parse(source[m.start():tok.end()]),"event")
                    break


def patch_event(relative,event_id,transform):
    path=TARGET/relative
    content=read(path)
    matches=[(s,t,e) for s,t,e in event_spans(content) if get(e,"id")==str(event_id)]
    if len(matches)!=1:
        raise ValueError(f"Expected one {event_id} in {relative}; found {len(matches)}")
    start,end,event=matches[0]
    transform(event)
    write(path,content[:start]+"\nevent = {\n"+serialise(event,1)+"\n}"+content[end:])
    PATCHES.append({"file":relative,"event":event_id})


def add_gate(node,key,gate):
    for i,(k,v) in enumerate(node):
        if k==key:
            node[i]=(k,v+parse(gate));return
    node.append((key,parse(gate)))


def set_value(node,key,value):
    node[:]=[(k,v) for k,v in node if k!=key]
    node.append((key,str(value)))


def source_country(tag):
    rev=parse(read(SOURCE/"db/revolt.txt"))
    n=get(rev,tag,[])
    provinces=[]
    for field in ("minimum","extra"):
        provinces.extend(int(v) for _,v in get(n,field,[]))
    return n,list(dict.fromkeys(provinces))


def province_names():
    result={}
    for line in read(GAME/"map/Map_1/province_names.csv").splitlines():
        cells=line.split(";")
        if len(cells)>1 and re.fullmatch(r"PROV\d+",cells[0]):
            result[int(cells[0][4:])]=cells[1]
    return result


def prepare_catalog():
    """Resolve source-dependent province lists before documentation or compilation."""
    global PREPARED_CORES
    if PREPARED_CORES is not None:return PREPARED_CORES
    rev=parse(read(SOURCE/"db/revolt.txt"))
    names=province_names()
    production_programmes.apply(SOURCE,names,read,parse,get,getall,num)
    for e in EVENTS:
        m=re.fullmatch(r"(.+)_land_(ENG|FRA|U05|HOL|U02)",e.key)
        if m:
            key,owner=m.groups()
            local=next(x for x in EVENTS if x.key==key+"_local")
            tag=local.country
            node,provinces=source_country(tag)
            if tag=="U87":
                provinces=[1337]+[int(v) for _,v in get(node,"claims",[])]
            e.actions[0].commands=[cond(control(p)+" "+owned(p,owner),cmd("secedeprovince",which="JAP",value=p,when=1)) for p in provinces]
        if e.key.endswith("_create"):
            # The release must never take Japanese expeditionary units.
            assert all("value = 1" in c for c in e.actions[0].commands)
    # Unit programmes must not silently consume the setup budget and then add no
    # production lines because manpower was spent before completion.
    for e in EVENTS:
        match=re.fullmatch(r"(.+)_finish_\d+",e.key)
        if not match:continue
        required=0
        for text in e.actions[0].commands:
            n=parse(resolve(text))
            if get(n,"type")!="build_division":continue
            unit=get(n,"which")
            models=specialist_units.models(unit) if unit in specialist_units.CLASSES else getall(parse(read(SOURCE/"db/units/divisions"/(unit+".txt"))),"model")
            required+=max(num(m,"manpower") for m in models)*max(1,num(n,"when",1))
        if not required:continue
        required=int(required+0.999)
        original=e.actions[0].gate
        e.actions[0].gate+=f" manpower = {required}"
        key=match.group(1)
        main=next(x for x in EVENTS if x.key==key)
        option=int(e.key.rsplit('_',1)[1])
        # A costly army alternative must not prevent funding a lighter air
        # alternative, or stop a player opening the proposal to decline it.
        main.actions[option].gate+=f" manpower = {required}"
        refund=[]
        # Both alternatives share the same setup payment.
        for text in main.actions[0].commands:
            n=parse(resolve(text))
            if get(n,"type") in {"money","supplies"} and num(n,"value")<0:
                refund.append(cmd(get(n,"type"),value=-num(n,"value")))
        refund += [cmd("clrflag",which="JX_"+key+"_PENDING"),flag(key+"_WAIT"),cmd("event",which=IDS[key+"_return"],where="JAP",when=90)]
        failure=Action("The programme cannot finish; return the funds",refund,gate=f"flag = JX_{key}_PENDING NOT = {{ AND = {{ {e.actions[0].gate} }} }}")
        if len(e.actions)>1:e.actions[1]=failure
        else:e.actions.append(failure)
        e.desc+=" If required manpower or control is missing, the setup payment is refunded."
    # Paying merely to insert normal production orders is a poor choice: the
    # player could queue those units without the setup charge. Pure order
    # alternatives therefore buy a small permanent standardisation benefit as
    # well. No free completed capital ships or fixed cheap IC costs are used.
    informed=set()
    for e in EVENTS:
        if not re.fullmatch(r"(.+)_finish_\d+",e.key):continue
        key=re.fullmatch(r"(.+)_finish_\d+",e.key).group(1)
        rewards=[parse(resolve(c)) for c in e.actions[0].commands]
        useful=[n for n in rewards if get(n,'type') not in {'setflag','clrflag'}]
        if not useful or any(get(n,'type')!='build_division' for n in useful):continue
        units=list(dict.fromkeys(get(n,'which') for n in useful))
        e.actions[0].commands += [cmd('build_time',which=u,when='on_upgrade',value=-8) for u in units]
        e.desc += " This option also reduces future "+", ".join(units)+" construction by eight days, once."
        if key not in informed:
            main=next(x for x in EVENTS if x.key==key)
            main.desc += " An option consisting only of production orders also buys an eight-day construction improvement for each ordered unit type, once."
            informed.add(key)
    # Chinese national territory excludes independent frontier states and imperial Japan.
    u87=get(rev,"U87",[])
    excluded=set()
    for tag in ("MAN","MEN","TIB","SIK"):
        _,ps=source_country(tag);excluded.update(ps)
    china_cores=[1337]+[int(v) for _,v in get(u87,"claims",[]) if int(v) not in excluded and int(v) not in {1371,1372}]
    china_cores=list(dict.fromkeys(china_cores))
    core_event=next(e for e in EVENTS if e.key=="china_cores")
    core_event.actions[0].commands=[cmd("addcore",which=p) for p in china_cores]+core_event.actions[0].commands
    # Remove conflicting imperial/frontier cores before the old Chinese state changes tag.
    japan=parse(read(SOURCE/"scenarios/1933/japan.inc"))
    imperial={int(v) for _,v in get(get(japan,"country",[]),"nationalprovinces",[])}|excluded
    withdrawal=next(e for e in EVENTS if e.key=="china_withdraw")
    pos=next(i for i,c in enumerate(withdrawal.actions[0].commands) if "type = country" in c)
    withdrawal.actions[0].commands[pos:pos]=[cmd("removecore",which=p) for p in sorted(imperial-set(china_cores))]
    # Correct Bose's actual source minister IDs; no Indian overhaul is consulted.
    india=next(e for e in EVENTS if e.key=="india_local")
    india.actions[0].commands += [cmd("headofstate",which=250069),cmd("headofgovernment",which=250070),cmd("chiefofstaff",which=250045)]
    # Give neutral China its correct cores even though it is not a Japanese puppet.
    neutral=next(e for e in EVENTS if e.key=="china_local")
    neutral.actions[0].commands += [cmd("addcore",which=p) for p in china_cores]
    # Use the Chinese partner's own cabinet after a CHI -> U87 change.
    neutral.actions[0].commands += [cond("NOT = { year = 1945 }",cmd("headofstate",which=1250002)),cond("year = 1945",cmd("headofstate",which=1250011)),cmd("headofgovernment",which=1250003),cmd("chiefofstaff",which=1250012)]
    # Regional partners receive disjoint homeland lists. Their release never
    # includes Japanese bases, Manchukuo, or another already released region.
    regional_used=set()
    for key,tag,cap in (("guangxi","CGX",1378),("yunnan","CYN",1390)):
        _,ps=source_country(tag)
        provinces=[p for p in ps if p in china_cores and p not in regional_used]
        regional_used.update(provinces)
        e=next(e for e in EVENTS if e.key==key+"_release")
        e.actions[0].commands[0:0]=[cond(owned(p,"U87"),cmd("removecore",which=p)) for p in provinces]
        e=next(e for e in EVENTS if e.key==key+"_autonomy")
        e.desc += " Homeland: "+", ".join(names.get(p,str(p)) for p in provinces)+"."
    # A limited offer and a decisive offer must not be applied concurrently.
    next(e for e in EVENTS if e.key=="china").gate += " NOT = { flag = JX_CHINA_LIMITED_PENDING }"
    # Starting the Guards programme late must pick up infantry research already
    # completed, rather than stranding the new class at its 1939 model.
    guards=next(e for e in EVENTS if e.key=='guards_finish_0')
    guards.actions[0].commands += [cond(f'technology = {tech}',cmd('new_model',which='d_01',value=model)) for tech,model in ((1120,2),(1130,3),(1140,4))]
    # Province numbers must be readable in settlement text.
    for e in EVENTS:
        if e.module=="settlements" and e.decision:
            e.desc=re.sub(r"(?<![\w])\d{3,4}(?![\w])",lambda m:f"{names.get(int(m.group()),'province')} ({m.group()})",e.desc)
    # Exact Asian settlement list. Only already-held land can transfer.
    treaty_provinces=set()
    for tag in ("IND","U87","PHI","INO","MLY","BRU","SAR","BUR","VIE","LAO","CMB"):
        node,ps=source_country(tag)
        treaty_provinces.update(ps)
        if tag=="U87":treaty_provinces.update(china_cores)
    for owner in ("USA","ENG","AST","NZL","HOL","FRA","U05"):
        e=next(e for e in EVENTS if e.key=="us_transfer_"+owner)
        e.actions[0].commands=[cond(control(p)+" "+owned(p,owner),cmd("secedeprovince",which="JAP",value=p,when=1)) for p in sorted(treaty_provinces)]
        if owner=="USA":
            e.actions[0].commands += [cond(control(p)+" "+owned(p,"USA"),cmd("secedeprovince",which="JAP",value=p,when=1)) for p in (1673,1683,1739)]
            e.actions[0].commands.append(cond("flag = JX_US_KEEP_HAWAII "+control(1734)+" "+owned(1734,"USA"),cmd("secedeprovince",which="JAP",value=1734,when=1)))
    release_support.replace_old_support()
    construction_safety.apply()
    us_invasion.apply()
    snlf_cabinet.append()
    campaign_balance.apply()
    japan_wartime.append_events()
    human_campaign.apply()
    force_value.apply()
    endurance_economy.apply()
    recruitment_endurance.apply()
    campaign_flow.apply()
    event_accessibility.apply()
    force_delivery_audit.apply()
    minister_integrity.apply()
    regional_content.append_events()
    prewar_content.append_events()
    us_campaign_content.append_events()
    unique_unit_events.append_events()
    unique_divisions.apply()
    island_shipping.apply()
    r14_china.apply()
    r14_peace.apply()
    r14_afterwar.apply()
    r14_china.append_interruption()
    r15_enemy.apply()
    r15_recovery.apply()
    r15_strategy.apply()
    final_event_integrity.apply()
    equipment_delivery.apply()
    player_copy.apply()
    IDS.update({e.key:e.id for e in EVENTS})
    PREPARED_CORES=china_cores
    return china_cores


def event_copy(e):
    if e.key=='welcome':return e.title,e.desc
    if e.desc:return e.title,e.desc
    if e.key.endswith(('_return','_reconsider')):
        return e.title,'The proposal can be considered again.'
    if e.key.endswith('_expiry'):
        return e.title,'The temporary allocation has ended.'
    return e.title,'The orders have been carried out.'


def compiled_event(e):
    hidden=not e.desc
    # Keep the engine's tooltip-suppression token only for large legacy
    # receivers. It is localised below; it is not a promise of silent execution.
    large=hidden and any(len(a.commands)>20 or len(a.gate)>3000 for a in e.actions)
    title='"AI_EVENT"' if large else "JX_"+e.key+"_NAME"
    lines=[f"# {e.key}: {e.purpose}","event = {",f" id = {e.id}"," random = no",f" country = {e.country}"," save_date = yes",f" name = {title}"]
    lines += [f" desc = JX_{e.key}_DESC"," style = 2",f' picture = "jx_{e.art}"']
    if e.persistent or e.triggered:
        lines.append(" persistent = yes")
    if e.decision:
        lines += [f" decision = {{ year = {e.year} {resolve(e.gate)} }}",f" decision_trigger = {{ {resolve(e.ready)} }}",f' decision_picture = "jx_decision_{e.art}"']
        # Conquests offer their settlement automatically, as well as through the decision panel.
        auto=resolve(e.gate)+" "+resolve(e.ready) if e.module=="settlements" and not getattr(e,'manual_only',False) else "ai = yes "+resolve(e.gate)+" "+resolve(e.ready)
        lines += [f" trigger = {{ {auto} }}"]
    elif e.gate:
        lines.append(f" trigger = {{ {resolve(e.gate)} }}")
    if not e.triggered:
        lines += [f" date = {{ day = {e.start_day} month = {e.start_month} year = {e.year} }}",f" offset = {e.offset}"," deathdate = { day = 29 month = december year = 1950 }"]
    for i,a in enumerate(e.actions):
        lines += [" action = {",f"  name = {'ACTION_NAME_OK' if not a.name else 'JX_'+e.key+'_A'+str(i)}",f"  ai_chance = {a.chance}"]
        if a.gate:lines.append("  trigger = { "+resolve(a.gate)+" }")
        for c in a.commands:
            lines.append("  command = { "+resolve(c)+" }")
        if not a.commands:lines.append("  command = { }")
        lines.append(" }")
    lines.append("}")
    return "\n".join(lines)


def localisation():
    rows=["# Japan Rising English localisation;;;;;;;;;;;X"]
    def row(key,value):
        value=ascii_text(value).replace(";",",").replace("\r","").replace("\n","\\n")
        if "\xa7" in value:raise ValueError("Colour code in "+key)
        rows.append(";".join([key,value]+[""]*9+["X"]))
    for e in EVENTS:
        title,description=event_copy(e)
        row("JX_"+e.key+"_NAME",title)
        row("JX_"+e.key+"_DESC",description)
        for i,a in enumerate(e.actions):
            if a.name:row("JX_"+e.key+"_A"+str(i),a.name)
    row("JX_1933_SCENARIO",f"Japan Rising 1933 - {VERSION}")
    row('AI_EVENT','Military orders')
    row("JX_GUARDS_0","Imperial Guards Field Division 1935")
    row("JX_GUARDS_1","Imperial Guards Field Division 1939")
    for trait,pid,position,name,desc,commands in japan_personnel.PERSONALITIES:
        row('JX_PERSONALITY_'+str(pid)+'_NAME',name)
        row('JX_PERSONALITY_'+str(pid)+'_DESC',desc)
    for unit,info in specialist_units.CLASSES.items():
        row('JX_'+unit+'_NAME',info['name'])
        row('JX_'+unit+'_SHORT',{'d_10':'Base Force','d_11':'Jungle Light','d_12':'SNLF'}[unit])
        row('JX_'+unit+'_DESC',{'d_10':'Static overseas base defence; weak on the offensive.','d_11':'Light jungle infantry; less firepower and supply demand, ordinary opposed-landing penalties.','d_12':'Mobile naval assault division: 9 manpower, lighter supply and transport loads, improved landings, reduced firepower and defence.'}[unit])
    for key,value in unique_divisions.localisation_rows()+unique_attachments.localisation_rows():
        row(key,value)
    return "\n".join(rows)+"\n"


def documentation():
    HERE.mkdir(exist_ok=True)
    records=[]
    lines=[f"# Japan Rising: executable event specification — {VERSION}","", "This catalogue is compiled into the installed event files. It lists every event, including technical receivers, cooldowns and verification. IDs and conditions below are generated from the same objects used by the build.","",f"Total: {len(EVENTS)} events; {sum(e.decision for e in EVENTS)} actionable decision entries. Counts include alternative paths and technical follow-ups; a campaign does not display them all.","", "## Cascade rules", "", "- Investment: available decision -> paid pending project -> delayed completion -> exact reward, or refund if completion conditions fail. Delay reopens after 90 days; permanent dismissal never reopens.","- Country: defeat gate -> selected terms -> defeated country's withdrawal -> release/tag change -> puppet or neutral treaty -> owned-port transfer -> final-state check -> local defence. Japan does not issue a minor-country alliance-wide peace.","- Pacific armistice: two years at war -> qualifying position -> 180-day monitored hold -> Japanese terms -> American reply -> checked land transfers -> Allied-Pacific peace -> verification -> five-year treaty expiry.","- Soviet terms: deep Siberian objectives -> Soviet reply -> occupied-border transfer -> separate-bloc eastern peace -> optional Far Eastern client. Formal Axis membership blocks this limited peace.","", "## Event index", "", "| ID | Key | Country | Module | Kind | Follow-up IDs |", "| --- | --- | --- | --- | --- | --- |"]
    for e in EVENTS:
        text=" ".join(a.commands.__str__() for a in e.actions)
        refs=sorted(set(re.findall(r"@([A-Za-z0-9_]+)",text)))
        targets=", ".join(f"{r} ({IDS[r]})" for r in refs)
        kind="decision" if e.decision else "receiver" if e.triggered else "automatic"
        lines.append(f"| {e.id} | {e.key} | {e.country} | {e.module} | {kind} | {targets} |")
        record=asdict(e);record["gate"]=resolve(e.gate);record["ready"]=resolve(e.ready);record["follows"]=refs
        record['manual_only']=getattr(e,'manual_only',False)
        for a in record["actions"]:
            a["commands"]=[resolve(x) for x in a["commands"]];a["gate"]=resolve(a["gate"])
        records.append(record)
    lines += ["", "## Exact events, gates and actions", ""]
    for e in EVENTS:
        lines += [f"### {e.id}: {e.title or e.key}","",f"Country: {e.country}. Module: {e.module}. Earliest year: {e.year}. Triggered receiver: {e.triggered}. Persistent: {e.persistent or e.triggered}.","",e.desc or "Technical follow-up; it can appear in a human campaign and has localised text.","", "```text",compiled_event(e),"```",""]
    spec="\n".join(line.rstrip() for line in "\n".join(lines).splitlines()).rstrip()+"\n"
    (HERE/"EVENT_SPEC.md").write_text(spec,encoding="utf-8")
    payload=json.dumps(records,indent=2,ensure_ascii=True)
    (HERE/"events.json").write_text(payload,encoding="utf-8")
    digest=hashlib.sha256(payload.encode()).hexdigest()
    (HERE/"SPEC_SHA256.txt").write_text(digest+"\n",encoding="ascii")
    return digest


def install_sources():
    if TARGET.exists():
        manifest=TARGET/"JAPAN_RISING_BUILD.json"
        if not manifest.exists():raise RuntimeError("Refusing to overwrite an unrelated existing mod folder: "+str(TARGET))
        return
    print("Copying the clean Blood and Iron source into "+str(TARGET),flush=True)
    shutil.copytree(SOURCE,TARGET,ignore=shutil.ignore_patterns("save games","ScreenSave*.bmp","config.eu","__pycache__"))
    (TARGET/"scenarios/save games").mkdir(parents=True,exist_ok=True)
    write(TARGET/"JAPAN_RISING_BUILD.json",json.dumps({"version":VERSION,"source":str(SOURCE),"state":"building"}))


def patch_baseline(china_cores):
    # Always render known affected sources from the clean baseline, never stack patches.
    affected=["db/events/Add_on.txt","db/events/japan.txt","db/events/USA.txt","db/events/UK.txt","db/events/Gameplay.txt","db/revolt.txt","scenarios/1933.eug","db/events.txt","db/tech/teams/teams_jap.csv","db/tech/teams/teams_U87.csv","db/tech/infantry_tech.txt","config/models.csv"]
    for rel in affected:shutil.copy2(SOURCE/rel,TARGET/rel)
    # R12 mirrors naval/air/industry effects too. Re-render every native tech
    # from clean input, so rebuilding cannot append a second set of hooks.
    for path in (SOURCE/'db/tech').glob('*.txt'):
        shutil.copy2(path,TARGET/'db/tech'/path.name)
    # The three native parents receive conversion/attachment entries below.
    # Reset them before cloning the new classes, avoiding self-conversions on
    # a second installation into the same folder.
    for unit in {info['base'] for info in unique_divisions.CLASSES.values()}:
        shutil.copy2(SOURCE/'db/units/divisions'/(unit+'.txt'),TARGET/'db/units/divisions'/(unit+'.txt'))
    # Specialist tech effects are always replayed onto clean files, never stacked.
    for name in {p for p,_,_,_ in specialist_units.MIRRORS}:
        if name!='infantry_tech.txt':shutil.copy2(SOURCE/'db/tech'/name,TARGET/'db/tech'/name)
    p=TARGET/"db/events/Add_on.txt"
    text=read(p)
    assert text.count("command = [ type = trigger which = 1000071 }")==1
    write(p,text.replace("command = [ type = trigger which = 1000071 }","command = { type = trigger which = 1000071 }"))
    PATCHES.append({"file":"db/events/Add_on.txt","fix":"Inherited malformed command bracket at original line 2587"})
    def yamamoto_ambush(n):
        changed=0
        for a in getall(n,'action')+getall(n,'action_a')+getall(n,'action_b'):
            for c in getall(a,'command'):
                if get(c,'type')=='sleepleader' and get(c,'which')=='50200':set_value(c,'which','50292');changed+=1
        assert changed==1,'Yamamoto ambush source changed unexpectedly'
    patch_event('db/events/Add_on.txt',1000212,yamamoto_ambush)
    for eid in (2011012,2011015):
        patch_event("db/events/japan.txt",eid,lambda n:(add_gate(n,"decision","NOT = { flag = JX_ACTIVE }"),add_gate(n,"trigger","NOT = { flag = JX_ACTIVE }")))
    # Historical Thai diplomacy remains available until a new settlement is
    # pending/completed. Receiver action guards also cover already queued offers.
    thai_allowed='NOT = { flag = JX_thailand_PENDING flag = JX_thailand_SETTLED }'
    def thai_diplomacy(n):
        add_gate(n,'trigger',thai_allowed)
        for a in getall(n,'action')+getall(n,'action_a')+getall(n,'action_b')+getall(n,'action_c'):
            add_gate(a,'trigger',thai_allowed)
        n.append(('action',parse('name = "This old offer no longer applies" ai_chance = 100 trigger = { OR = { flag = JX_thailand_PENDING flag = JX_thailand_SETTLED } } command = { }')))
    for eid in (2011009,2059001,2011010,2011011):patch_event('db/events/japan.txt',eid,thai_diplomacy)
    patch_event("db/events/UK.txt",2001049,lambda n:add_gate(n,"trigger","NOT = { flag = JX_ACTIVE }"))
    def guard_pacific_receiver(n):
        # Immediate trigger commands can bypass an event's ordinary trigger.
        # Guard the actions too, so a European UK surrender cannot transfer
        # unoccupied Asian land around the new country agreements.
        add_gate(n,"trigger","NOT = { flag = JX_ACTIVE }")
        for a in getall(n,'action')+getall(n,'action_a'):
            add_gate(a,'trigger','NOT = { flag = JX_ACTIVE }')
        n.append(('action',parse('name = ACTION_NAME_OK ai_chance = 100 trigger = { flag = JX_ACTIVE } command = { }')))
        set_value(n,'name','AI_EVENT')
    patch_event("db/events/UK.txt",2001050,guard_pacific_receiver)
    # The original China offer is no longer a necessary Pearl Harbor prerequisite.
    def pearl(n):
        trig=get(n,"trigger",[])
        for k,v in trig:
            if k=="OR" and isinstance(v,list) and any(k2=="event" and v2=="2011012" for k2,v2 in v):
                v.append(("flag","JX_china_SETTLED"))
                v.append(("flag","JX_CHINA_LIMITED_DONE"))
    patch_event("db/events/japan.txt",2011025,pearl)
    def embargo_trade_close(n):
        for a in getall(n,'action')+getall(n,'action_a'):
            a.append(('command',parse('trigger = { flag = JX_ACTIVE } type = end_trades which = USA where = JAP')))
    patch_event('db/events/USA.txt',2049026,embargo_trade_close)
    # The new national-surrender path must not race with the one-shot stock
    # menu or inherit its sleepevent/refusal state. Non-JX campaigns retain it.
    def guard_us_surrender(n):
        add_gate(n,'trigger','NOT = { flag = JX_ACTIVE }')
        for a in getall(n,'action')+getall(n,'action_a')+getall(n,'action_b'):
            add_gate(a,'trigger','NOT = { flag = JX_ACTIVE }')
        n.append(('action',parse('name = "Japan Rising handles these negotiations" ai_chance = 100 trigger = { flag = JX_ACTIVE } command = { }')))
    for eid in (2049046,2011031,2049047):patch_event('db/events/USA.txt',eid,guard_us_surrender)
    # China's release cores come from the actual domestic list, not Japanese national land.
    r=parse(read(TARGET/"db/revolt.txt"))
    n=get(r,"U87")
    n[:]=[(k,v) for k,v in n if k not in {"claims","extra"}]
    n.append(("extra",[(None,str(p)) for p in china_cores if p!=1337]))
    regional_used=set()
    for tag in ("CGX","CYN"):
        n=get(r,tag);cap=get(n,"capital")
        _,ps=source_country(tag)
        ps=[p for p in ps if p in china_cores and p not in regional_used]
        regional_used.update(ps)
        n[:]=[(k,v) for k,v in n if k not in {"minimum","extra","claims"}]
        n += [("minimum",[(None,cap)]),("extra",[(None,str(p)) for p in ps if str(p)!=cap])]
    # All local governments can form from their held core capital; remaining homeland is extra.
    for tag in ("MLY","INO","VIE","LAO","CMB","BUR","IND","PHI","AST","NZL","EGY","PER","IRQ"):
        n=get(r,tag)
        oldps=[v for k in ("minimum","extra") for _,v in get(n,k,[])]
        cap={"INO":"1647","CMB":"1400"}.get(tag,get(n,"capital"))
        if tag in {"INO","CMB"}:set_value(n,"capital",cap)
        n[:]=[(k,v) for k,v in n if k not in {"minimum","extra"}]
        n += [("minimum",[(None,cap)]),("extra",[(None,p) for p in dict.fromkeys(oldps) if p!=cap])]
    write(TARGET/"db/revolt.txt",serialise(r)+"\n")
    # Reduce the largest AI-versus-AI Soviet reserve package without removing human-Germany challenge.
    def sov_package(n):
        set_value(n,"save_date","yes")
        for act in getall(n,"action_a")+getall(n,"action"):
            new=[]
            for k,c in act:
                if k!="command":new.append((k,c));continue
                typ=get(c,"type")
                changes={"free_oil":("30","15"),"supplies":("200000","60000"),"money":("8000","3000")}
                if typ in changes and get(c,"value")==changes[typ][0]:
                    base=list(c);add_gate(base,"trigger","NOT = { ai = GER }")
                    altered=list(c);set_value(altered,"value",changes[typ][1]);add_gate(altered,"trigger","ai = GER")
                    new += [(k,base),(k,altered)]
                else:new.append((k,c))
            act[:]=new
    patch_event("db/events/Gameplay.txt",100,sov_package)
    for eid,prior,days in ((1000419,100,60),(1000420,1000419,90),(1000424,1000420,60)):
        def stagger(n,prior=prior,days=days):
            set_value(n,"save_date","yes")
            add_gate(n,"trigger",f"OR = {{ NOT = {{ ai = GER }} event = {{ id = {prior} days = {days} }} }}")
        patch_event("db/events/Add_on.txt",eid,stagger)
    # Better AI deployment priorities at all main German/Italian year switches.
    for p in (SOURCE/"ai").glob("*.ai"):
        if not (p.name.lower().startswith("ger_") or p.name.lower().startswith("ita_")):continue
        write(TARGET/"ai"/p.name,model_names_and_ai.axis_ai(read(p),p.name))
    # Keep Japan AI at the clean Blood and Iron baseline; this mod's Japan
    # campaign is authored for a human player.
    for p in (SOURCE/"ai").glob("jap_*.ai"):
        shutil.copy2(p,TARGET/"ai"/p.name)
    usa_ai=SOURCE/"ai/usa_1942.ai"
    shutil.copy2(usa_ai,TARGET/"ai/usa_1942.ai")
    write(TARGET/"ai/usa_1942.ai",model_names_and_ai.allied_invasion_ai(read(usa_ai),usa_ai.name))
    PATCHES.append({"file":"ai/usa_1942.ai","change":"Lower low-value isolated-island invasion priority; raise caution around defended beaches"})
    scenario=read(TARGET/"scenarios/1933.eug")
    scenario=re.sub(r'(?m)^name\s*=.*$', 'name = "JX_1933_SCENARIO"',scenario,count=1)
    write(TARGET/"scenarios/1933.eug",scenario)
    p=TARGET/'db/tech/infantry_tech.txt'
    s=read(p)
    s,count=re.subn(r'trigger\s*=\s*\{\s*country\s*=\s*GER\s*\}(\s*type\s*=\s*(?:new_model|scrap_model|activate_unit_type)\s+which\s*=\s*d_01)',r'trigger = { OR = { country = GER AND = { country = JAP flag = JX_guards_DONE } } }\1',s)
    if count<8:raise ValueError('Guards upgrade hooks not found in the expected infantry technology file')
    write(p,s)


def ai_files():
    partner='''switch = no
reinforcement = 1.0
upgrading = 0.25
max_garrison_prop = 0.35
min_garrison_prop = 0.20
max_redeploying = 0.10
exp_force_ratio = 0.0
construction = { max_factor = 0.10 }
military = {
 relative_build_scheme = no
 infantry = 64 cavalry = 3 motorized = 4 mechanized = 0 light_armor = 0 armor = 0
 paratrooper = 0 marine = 0 bergsjaeger = 8 garrison = 8 hq = 2 militia = 0
 interceptor = 6 multi_role = 0 cas = 0 tactical_bomber = 2 naval_bomber = 0 transport_plane = 0
 strategic_bomber = 0 flying_bomb = 0 flying_rocket = 0
 battleship = 0 carrier = 0 light_carrier = 0 escort_carrier = 0 heavy_cruiser = 0
 light_cruiser = 0 destroyer = 1 submarine = 0 nuclear_submarine = 0 battlecruiser = 0 transports = 2
}
'''
    write(TARGET/"ai/jx/partner_land.ai",partner)
    small=partner.replace('infantry = 64','infantry = 35').replace('garrison = 8','garrison = 45').replace('bergsjaeger = 8','bergsjaeger = 0').replace('cavalry = 3','cavalry = 0').replace('motorized = 4','motorized = 0').replace('hq = 2','hq = 0').replace('interceptor = 6','interceptor = 10').replace('tactical_bomber = 2','tactical_bomber = 0').replace('destroyer = 1','destroyer = 5').replace('transports = 2','transports = 5').replace('max_garrison_prop = 0.35','max_garrison_prop = 0.60')
    islands=partner.replace('infantry = 64','infantry = 36').replace('garrison = 8','garrison = 20').replace('bergsjaeger = 8','bergsjaeger = 4').replace('cavalry = 3','cavalry = 0').replace('motorized = 4','motorized = 0').replace('hq = 2','hq = 0').replace('interceptor = 6','interceptor = 12').replace('tactical_bomber = 2','tactical_bomber = 0').replace('naval_bomber = 0','naval_bomber = 6').replace('destroyer = 1','destroyer = 12').replace('transports = 2','transports = 10').replace('max_garrison_prop = 0.35','max_garrison_prop = 0.50')
    write(TARGET/'ai/jx/partner_small.ai',small)
    write(TARGET/'ai/jx/partner_islands.ai',islands)
    write(TARGET/"ai/jx/partner_expedition.ai",partner.replace("exp_force_ratio = 0.0","exp_force_ratio = 0.28\nexp_force_ratios = { JAP = 1.0 }"))
    write(TARGET/"ai/jx/ger_endurance.ai",'''switch = no
reinforcement = 1.0
upgrading = 0.20
min_garrison_prop = 0.20
max_garrison_prop = 0.35
max_redeploying = 0.12
military = {
 relative_build_scheme = no
 infantry = 40 cavalry = 1 motorized = 10 mechanized = 0 armor = 10 light_armor = 0
 paratrooper = 0 marine = 0 bergsjaeger = 3 garrison = 4 hq = 2 militia = 0
 interceptor = 10 multi_role = 2 cas = 6 tactical_bomber = 4 naval_bomber = 0 transport_plane = 0
 strategic_bomber = 0 flying_bomb = 0 flying_rocket = 0
 battleship = 0 carrier = 0 light_carrier = 0 escort_carrier = 0 heavy_cruiser = 0
 light_cruiser = 0 destroyer = 2 submarine = 4 nuclear_submarine = 0 battlecruiser = 0 transports = 2
}
''')
    write(TARGET/"ai/jx/ita_endurance.ai",partner.replace("infantry = 64","infantry = 58").replace("bergsjaeger = 8","bergsjaeger = 10").replace("naval_bomber = 0","naval_bomber = 4"))
    write(TARGET/"ai/jx/sov_two_front.ai",'''switch = no
reinforcement = 1.0
upgrading = 0.20
max_front_ratios = { GER = 3.0 JAP = 1.5 MAN = 1.4 }
max_garrison_prop = 0.40
min_garrison_prop = 0.20
garrison = {
 defend_overseas_beaches = yes
 country_priorities = { GER = 180 JAP = 150 MAN = 120 }
 province_priorities = { 1191 = 150 1190 = 120 1176 = 100 1169 = 120 }
}
''')


def teams_and_units():
    p=TARGET/"db/tech/teams/teams_jap.csv"
    s=read(p)
    teams=[
        (286010,"Naval Staff College - carrier coordination",7,1938,["carrier_tactics","small_taskforce_tactics","naval_artillery","large_taskforce_tactics","naval_engineering"],"naval"),
        (286011,"Maritime Escort Headquarters",6,1941,["naval_training","naval_engineering","small_taskforce_tactics","aircraft_testing","seamanship"],"industry"),
        (286012,"Naval Landing Force Training Centre",7,1937,["marine_training","small_unit_tactics","general_equipment","vehicle_engineering","training"],"army"),
        (286013,"Army Logistics Research Office",6,1937,["management","technical_efficiency","mechanics","general_equipment","training","mountain_training"],"siberia"),
        (286014,"Aviation Engine Development Bureau",7,1940,["aeronautics","mechanics","technical_efficiency","aircraft_testing","avionics"],"air"),
        (286015,"Naval Radar and Signals Group",6,1941,["electronics","mathematics","naval_engineering","aircraft_testing","management"],"pacific"),
        (286016,"Combined Arms Study Group",6,1942,["small_unit_tactics","combined_arms_focus","training","decentralized_execution","technical_efficiency"],"diplomacy"),
        (286017,"Asian Reconstruction Institute",6,1945,["industrial_engineering","management","mechanics","chemistry","electronics"],"asia"),
    ]
    for tid,name,skill,year,skills,art in teams:
        row=[str(tid),name,"jx_team_"+str(tid),str(skill),str(year),"1970"]+skills+[""]*(32-len(skills))+["x"]
        s+="\n"+";".join(row)
    write(p,s+"\n")
    teams+=japan_personnel.apply_teams(TARGET,read,write)
    japanese_research_names.apply(TARGET,read,write)
    # Strengthen real Chinese institutions without making naval/air doctrine
    # expertise appear in every team or copying the Indian player teams.
    p=TARGET/"db/tech/teams/teams_U87.csv"
    rows=read(p).splitlines();improved=[]
    for row in rows:
        cells=row.split(";")
        if cells[0].isdigit() and len(cells)>6:
            tid=int(cells[0])
            if tid in {1250001,1250002,1250005,1250006,1250007,1250008}:cells[3]="5"
            elif tid in {1250003,1250004,1250010,1250011,1250012}:cells[3]="4"
        improved.append(";".join(cells))
    write(p,"\n".join(improved)+"\n")
    write(TARGET/'config/models.csv',model_names_and_ai.model_names(read(SOURCE/'config/models.csv'),specialist_units.CLASSES,specialist_units.model_years))
    return teams


def graphics(teams):
    from PIL import Image,ImageOps
    workspace_art=HERE/"art"
    workspace_art.mkdir(exist_ok=True)
    # Additional generated art paths are supplied through a reviewed local map.
    mapping_path=HERE/"art_inputs.json"
    if mapping_path.exists():ART_INPUTS.update(json.loads(mapping_path.read_text()))
    for name,filename in ART_INPUTS.items():
        source=ART_ROOT/filename
        local_source=workspace_art/(name+".png")
        if source.exists():shutil.copy2(source,local_source)
        elif not local_source.exists():raise FileNotFoundError(source)
        img=Image.open(local_source).convert("RGB")
        event_size=Image.open(SOURCE/"gfx/events_pics/news_paper.bmp").size
        out=ImageOps.fit(img,event_size,method=Image.Resampling.LANCZOS)
        out.save(TARGET/"gfx/events_pics"/("jx_"+name+".bmp"))
        decision_size=Image.open(SOURCE/"gfx/events_pics/decision_afrika_korps.bmp").size
        template=Image.open(SOURCE/'gfx/events_pics/decision_afrika_korps.bmp')
        decision_banners.make(img,template).save(TARGET/"gfx/events_pics"/("jx_decision_"+name+".bmp"))
        obsolete=TARGET/"gfx/interface"/("jx_"+name+".bmp")
        if obsolete.exists():obsolete.unlink()
    main=Image.open(workspace_art/"naval.png").convert("RGB")
    for rel in ("gfx/load_1024.bmp","gfx/skins/JAP/fullscreen.bmp"):
        size=Image.open(SOURCE/rel).size
        ImageOps.fit(main,size,method=Image.Resampling.LANCZOS).save(TARGET/rel)
    for tid,name,skill,year,skills,art in teams:
        im=Image.open(workspace_art/(art+".png")).convert("RGB")
        # Each institution gets an independently framed, distinct source subject when available.
        ImageOps.fit(im,(96,96),method=Image.Resampling.LANCZOS,centering=(0.15+(tid%4)*0.22,0.5)).save(TARGET/"gfx/interface/pics"/("jx_team_"+str(tid)+".bmp"))
    for model in range(5):
        im=Image.open(workspace_art/"army.png").convert("RGB")
        illustration_size=Image.open(SOURCE/"gfx/interface/models/ill_div_JAP_0_0.bmp").size
        ImageOps.fit(im,illustration_size,method=Image.Resampling.LANCZOS).save(TARGET/"gfx/interface/models"/f"ill_div_JAP_41_{model}.bmp")
        # A proper sized country icon is supplied, while existing infantry sprite assets remain intact.
        icon_size=Image.open(SOURCE/"gfx/interface/models/JAP_model_0_0.bmp").size
        ImageOps.fit(im,icon_size,method=Image.Resampling.LANCZOS).save(TARGET/"gfx/interface/models"/f"JAP_model_41_{model}.bmp")


def compile_mod(digest,china_cores):
    # Do not replace files under a running player session. This is an inventory
    # query only; it never launches or closes the game.
    processes=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq Darkest Hour.exe','/FO','CSV','/NH'],capture_output=True,text=True)
    if processes.returncode:raise RuntimeError('Cannot verify whether Darkest Hour is open; installation was not changed.')
    if any(line.lower().startswith('"darkest hour.exe"') for line in processes.stdout.splitlines()):
        raise RuntimeError('Darkest Hour is open. Source changes are ready, but installation is deferred until it is closed.')
    install_sources()
    # A partial installation must never retain the previous launchable receipt.
    write(TARGET/'JAPAN_RISING_BUILD.json',json.dumps({'version':VERSION,'mod_name':MOD_NAME,
          'source':str(SOURCE),'target':str(TARGET),'state':'building'},indent=2)+'\n')
    patch_baseline(china_cores)
    groups={}
    for e in EVENTS:groups.setdefault(e.module,[]).append(e)
    for module,events in groups.items():
        write(TARGET/"db/events/japan_rising"/(module+".txt"),"\n\n".join(compiled_event(e) for e in events)+"\n")
    index=read(TARGET/"db/events.txt")
    index+="\n# Japan Rising: generated from the reviewed event catalogue\n"
    index+="\n".join(f'event = "db\\events\\japan_rising\\{m}.txt"' for m in groups)+"\n"
    write(TARGET/"db/events.txt",index)
    localisation_support.install(SOURCE,TARGET,localisation(),read,write)
    ai_files()
    campaign_balance.install_assets(SOURCE,TARGET,read,write,parse,get,serialise)
    r14_china.install(SOURCE,TARGET,read,write,parse,serialise)
    enemy_transport_ai.install(SOURCE,TARGET,read,write,parse,serialise)
    r15_enemy.install(SOURCE,TARGET,read,write,parse,serialise)
    teams=teams_and_units()
    graphics(teams)
    specialist_units.install(SOURCE,TARGET,write,serialise)
    unique_divisions.install(SOURCE,TARGET,read,write,parse,serialise)
    japan_personnel.apply_roster(SOURCE,TARGET,read,write,parse,serialise)
    force_value.apply_personnel(TARGET,read,write,parse,serialise)
    force_delivery_audit.apply_personnel(TARGET,read,write,parse,serialise)
    unique_divisions.install_personnel(TARGET,read,write,parse,serialise)
    unique_attachments.install(SOURCE,TARGET,read,write,parse,serialise)
    minister_integrity.apply_personnel(TARGET,read,write,parse,serialise)
    unique_art.install_cards(TARGET,HERE,unique_divisions.CLASSES,{})
    japan_personnel.graphics(TARGET,HERE/'art')
    docs=TARGET/"Japan Rising Documentation";docs.mkdir(exist_ok=True)
    for name in ("EVENT_SPEC.md","events.json","README.md","SPECIALIST_REVIEW.md","R9_CHANGE_REGISTER.json",
                 "READINESS_ASSESSMENT.md","CONSTRUCTION_BALANCE.md","ENDURANCE_AUDIT.md","ENDURANCE_AUDIT.json",
                 "FORCE_AUDIT.md","FORCE_TESTS.json","FLOW_AUDIT.md","FLOW_LEGACY_RECONCILIATION.md",
                 "RESEARCH_NAMES.md","R10_CHANGES.md","FORCE_DELIVERY_AUDIT.md","FORCE_DELIVERY_TESTS.json",
                 "EVENT_ACCESSIBILITY_AUDIT.md","EVENT_ACCESSIBILITY_MATRIX.json",
                 "MINISTER_INTEGRITY_AUDIT.md","MINISTER_INTEGRITY_REVIEW.json","MINISTER_INTEGRITY_ROSTER.csv",
                 "PREWAR_CONTENT.md","PREWAR_CONTENT.json","COUNTRY_CAMPAIGNS.md","REGIONAL_CONTENT_TESTS.json",
                 "US_CAMPAIGN_CONTENT.md","R11_CHANGES.md",
                 "R11_1_FINAL_AUDIT.md","PLAYER_COPY_REVIEW.md","PLAYER_COPY_REVIEW.json",
                 "EQUIPMENT_DELIVERY_AUDIT.md","EQUIPMENT_DELIVERY_REVIEW.json",
                 "R12_UNIQUE_UNITS.md","UNIQUE_DIVISIONS_AUDIT.md","UNIQUE_DIVISIONS_REVIEW.json",
                 "UNIQUE_ATTACHMENTS.md","UNIQUE_ATTACHMENTS_REVIEW.json","UNIQUE_ART_MANIFEST.json","UNIQUE_ART_INSTALL.json",
                 "UNIQUE_UNIT_EVENTS.md","UNIQUE_UNIT_COLD_AUDIT.json",
                 "R12_1_CHANGES.md","R12_1_COLD_AUDIT.json","FURTHER_JAPANESE_SPECIALISTS.md","PROGRESS.md",
                 "R13_UNITS.md","R13_ART_SOURCES.json","R13_1_CHANGES.md",
                 "ENEMY_TRANSPORT_AI_REPORT.json","ENEMY_TRANSPORT_AI_AUDIT.json",
                 "R14_CHANGES.md","R14_CHINA.md","R14_PEACE.md","R14_AFTERWAR.md",
                 "R15_README.md","R15_ENEMY.md","R15_RECOVERY.md","R15_STRATEGY.md"):
        shutil.copy2(HERE/name,docs/name)
    shutil.copy2(WORKSPACE/"JAPAN_EXPANSION_SPEC.md",docs/"DESIGN_AND_AUDIT.md")
    manifest={"version":VERSION,"mod_name":MOD_NAME,"source":str(SOURCE),"target":str(TARGET),"state":"built-awaiting-validation","spec_sha256":digest,"events":len(EVENTS),"decisions":sum(e.decision for e in EVENTS),"patches":PATCHES,"art":list(ART_INPUTS),"excluded":"All Indian overhaul/terrain/compact code and installed Indian team overrides"}
    write(TARGET/"JAPAN_RISING_BUILD.json",json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2),flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("mode",choices=["spec","install"]);args=ap.parse_args()
    cores=prepare_catalog()
    if args.mode=="spec":
        digest=documentation()
        print(json.dumps({"spec":str(HERE/"EVENT_SPEC.md"),"events":len(EVENTS),"decisions":sum(e.decision for e in EVENTS),"sha256":digest}))
    else:
        expected=(HERE/"SPEC_SHA256.txt").read_text().strip()
        current=json.dumps([asdict(e) for e in EVENTS],sort_keys=True)
        # Regenerate documentation from the same reviewed inputs before rendering the build.
        digest=documentation()
        if digest!=expected:raise RuntimeError("Catalogue changed since the written spec; run 'spec' and review it first.")
        compile_mod(digest,cores)


if __name__=="__main__":main()

"""Japan's three registered attachments: models, research and asset packaging.

No import-time event allocation or installation. install() follows the unique
division installer and reads current target tech/unit files, preserving it.
"""
from copy import deepcopy
from pathlib import Path
import csv
import json
import re
import sys
from catalog import cmd, cond, active

HERE=Path(__file__).resolve().parent
from runtime_paths import SOURCE
sys.path.insert(0,str(HERE.parent/'tools'))
from audit_japan_baseline import parse, get, getall, num

ATTACHMENTS={
    'b_01':dict(index=41,name='Type 93 Oxygen Torpedoes',short='Type 93',base='naval_torpedoes_s',
                artkey='unique_torpedo',flag='UNIQUE_B01_ACTIVE',year=1935,tech=3060,
                years=[1935,1942,1945,1948],techpairs=[(3060,0),(12000,1),(3080,2),(3780,3)],
                branch='naval',compatible=('destroyer','light_cruiser','heavy_cruiser','d_13','d_18'),
                desc='Long-range oxygen torpedoes for Japanese destroyers and cruisers. Strong surface and convoy attack, with higher ammunition and supply demand. Uses a naval attachment slot that could carry radar, AA or ASW equipment.'),
    'b_02':dict(index=42,name='Dokuritsu Konsei Mixed Brigade',short='Mixed Bde',base='police',
                artkey='unique_mixed',flag='UNIQUE_B02_ACTIVE',year=1937,tech=1100,
                years=[1937,1939,1942,1945,1948],techpairs=[(1100,0),(1110,1),(1120,2),(1130,3),(1140,4)],
                branch='land',compatible=('infantry','garrison','militia','d_19'),
                desc='An independent mixed brigade for occupation and local defence. More suppression, defensive strength and infantry firepower than Military Police, at a higher manpower and supply cost. Its marching speed is capped at four.'),
    'b_03':dict(index=43,name='Ka-Mi Naval Tank Detachment',short='Naval Tanks',base='amph_armor',
                artkey='unique_kami',flag='UNIQUE_B03_ACTIVE',year=1942,tech=2050,
                years=[1942,1944,1949],techpairs=[(2050,0),(2060,1),(1630,2)],
                branch='land',compatible=('marine','infantry','d_19'),
                desc='A compact naval tank detachment for infantry and Marine landings. Adds soft attack, defence and improved shore and river attack, with less fuel demand than a full amphibious armour brigade. Its smaller tank complement gives less anti-armour firepower and armour coverage.'),
}
REPORT={}
SKIP_TECH={'new_model','scrap_model','activate_unit_type','deactivate_unit_type'}
DOCUMENTED_NEW_COMMANDS={'activate_unit_type','deactivate_unit_type','new_model','scrap_model','setflag',
                         'build_time','build_cost','manpower','defensiveness','toughness',
                         'convoy_attack','naval_attack','sub_attack'}


def read(path):return Path(path).read_text(encoding='latin1')


def _set(node,key,value):
    node[:]=[(k,v) for k,v in node if k!=key]
    node.append((key,str(value)))


def _body(node):
    return ' '.join(str(k)+' = '+('{ '+_body(v)+' }' if isinstance(v,list) else str(v)) for k,v in node)


def models(unit):
    """Return independent native-format model nodes; never mutate the base."""
    info=ATTACHMENTS[unit]
    base=getall(parse(read(SOURCE/'db/units/brigades'/f'{info["base"]}.txt')),'model')
    result=[]
    for i,year in enumerate(info['years']):
        node=deepcopy(base[min(i,len(base)-1)])
        node[:]=[(k,v) for k,v in node if k!='equipment']
        if unit=='b_01':
            changes=dict(cost=(.65,.8,.95,1.1)[i],buildtime=100,manpower=0,
                         seaattack=(3,4,5,5)[i],convoyattack=(2,3,4,5)[i],subattack=0,
                         supplyconsumption=(.55,.65,.75,.85)[i],fuelconsumption=0,
                         distance=0,upgrade_time_factor=.5,upgrade_cost_factor=.6)
        elif unit=='b_02':
            changes=dict(cost=3+i*.25,buildtime=120+i*5,manpower=4,maxspeed=0,speed_cap=4,
                         defaultorganisation=2,suppression=8+i,defensiveness=8+i,toughness=2+i,
                         softattack=(3,4,4,5,5)[i],hardattack=(0,0,1,1,1)[i],
                         supplyconsumption=round(.45+i*.05,2),fuelconsumption=0,
                         upgrade_time_factor=.45,upgrade_cost_factor=.6)
            node.append(('equipment', [('manpower','4000'),('horses','100'),('trucks','40')]))
        else:
            changes=dict(cost=(4.5,5,5.5)[i],buildtime=140,manpower=2,maxspeed=0,speed_cap=10,
                         defaultorganisation=3,softness=-2,defensiveness=2+i,toughness=2+i,
                         softattack=4+i,hardattack=i,supplyconsumption=(.6,.65,.7)[i],
                         fuelconsumption=(1,.95,.9)[i],upgrade_time_factor=.5,upgrade_cost_factor=.65)
            node.append(('equipment',[('manpower','2000'),('medium_armor',str(40+i*8))]))
        for key,value in changes.items():_set(node,key,value)
        result.append(node)
    return result


def _normalise_effect(node,unit):
    clone=deepcopy(node)
    _set(clone,'which',unit)
    if get(clone,'type') in {'build_cost','build_time','manpower'} and get(clone,'where')=='relative':
        base=getall(parse(read(SOURCE/'db/units/brigades'/f'{ATTACHMENTS[unit]["base"]}.txt')),'model')[0]
        field={'build_cost':'cost','build_time':'buildtime','manpower':'manpower'}[get(clone,'type')]
        _set(clone,'value',round(num(base,field)*num(clone,'value')/100,6))
        clone[:]=[(k,v) for k,v in clone if k!='where']
    return clone


def _research_groups(root):
    groups={unit:{} for unit in ATTACHMENTS}
    for tree in getall(root,'technology'):
        for app in getall(tree,'application'):
            tid=int(get(app,'id'))
            for unit,info in ATTACHMENTS.items():
                effects=[_normalise_effect(c,unit) for c in getall(get(app,'effects',[]),'command')
                         if get(c,'which')==info['base'] and get(c,'type') not in SKIP_TECH]
                upgrade=next((model for tech,model in info['techpairs'] if tech==tid),None)
                if effects or upgrade is not None:groups[unit][tid]={'effects':effects,'model':upgrade}
    return groups


def _all_groups():
    groups={unit:{} for unit in ATTACHMENTS}
    for path in sorted((SOURCE/'db/tech').glob('*.txt')):
        found=_research_groups(parse(read(path)))
        for unit in groups:groups[unit].update(found[unit])
    return groups


def _ledger(unit,tid):return f'JX_UNIQUE_{unit.upper()}_TECH_{tid}'


def _guarded(node,guard):
    original=get(node,'trigger',[])
    body=[(k,v) for k,v in node if k!='trigger']
    return 'trigger = { '+guard+(' '+_body(original) if original else '')+' } '+_body(body)


def _group_commands(unit,tid,group,guard):
    if not group['effects']:return []
    commands=[_guarded(node,guard) for node in group['effects']]
    commands.append(cond(guard,cmd('setflag',which=_ledger(unit,tid))))
    return commands


def _model_commands(unit,model,guard,assume_tech=False):
    info=ATTACHMENTS[unit];tech=info['techpairs'][model][0]
    eligible=dict(latest_model_conditions(unit))[model]
    if assume_tech:eligible=eligible.replace(f'technology = {tech}', '', 1)
    receipt=f'JX_UNIQUE_{unit.upper()}_MODEL_{model}'
    live=guard+' '+eligible+f' NOT = {{ flag = {receipt} }}'
    return ([cond(live,cmd('new_model',which=unit,value=model))]+
            [cond(live,cmd('scrap_model',which=unit,value=i)) for i in range(model)]+
            [cond(live,cmd('setflag',which=receipt))])


def activation_commands(unit):
    """Replay-safe Japan-only unlock plus already-researched effect catch-up.

    Model zero is implicit in DH. Never explicitly add it. Each researched
    group has its own receipt, shared with the future technology hook.
    """
    info=ATTACHMENTS[unit]
    guard=('country = JAP '+active()+f' year = {info["year"]} technology = {info["tech"]} '
           f'NOT = {{ flag = JX_{info["flag"]} }}')
    commands=[cond(guard,cmd('activate_unit_type',which=unit))]
    for tid,group in sorted(_all_groups()[unit].items()):
        gate=guard+f' technology = {tid} NOT = {{ flag = {_ledger(unit,tid)} }}'
        commands.extend(_group_commands(unit,tid,group,gate))
    for model in range(1,len(info['years'])):commands.extend(_model_commands(unit,model,guard))
    commands.append(cond(guard,cmd('setflag',which='JX_'+info['flag'])))
    return commands


def latest_model_conditions(unit):
    info=ATTACHMENTS[unit];pairs=info['techpairs']
    return [(index,f'year = {info["years"][index]} technology = '+str(tech)+
             (' NOT = { '+' '.join(f'AND = {{ year = {info["years"][i]} technology = {t} }}' for t,i in pairs if i>index)+' }' if index<len(pairs)-1 else ''))
            for tech,index in reversed(pairs)]


def upgrade_event_specs():
    specs=[]
    for unit,info in ATTACHMENTS.items():
        for tech,model in info['techpairs'][1:]:
            guard='country = JAP '+active()+f' flag = JX_{info["flag"]}'
            latest=dict(latest_model_conditions(unit))[model]
            receipt=f'JX_UNIQUE_{unit.upper()}_MODEL_{model}'
            specs.append(dict(key=f'unique_upgrade_{unit}_{model}',unit=unit,year=info['years'][model],
                              tech=tech,model=model,gate=guard+' '+latest+f' NOT = {{ flag = {receipt} }}',
                              commands=_model_commands(unit,model,guard)))
    return specs


def apply_tech(target,read_fn,write,parse_fn,serialise):
    changed=[];effects_count=0
    for path in sorted((Path(target)/'db/tech').glob('*.txt')):
        root=parse_fn(read_fn(path));groups=_research_groups(root);touched=False
        for tree in getall(root,'technology'):
            for app in getall(tree,'application'):
                tid=int(get(app,'id'));effects=get(app,'effects',[])
                # Remove only this module's previous hooks for repeatable installs.
                previous=[(k,c) for k,c in effects if k=='command' and
                          (get(c,'which') in ATTACHMENTS or str(get(c,'which','')).startswith('JX_UNIQUE_B_') or
                           any(str(v).startswith('JX_UNIQUE_B_') for k2,v in get(c,'trigger',[]) if k2=='flag'))]
                if previous:
                    effects[:]=[(k,c) for k,c in effects if (k,c) not in previous];touched=True
                for unit,info in ATTACHMENTS.items():
                    if tid not in groups[unit]:continue
                    gate=f'country = JAP flag = JX_{info["flag"]} NOT = {{ flag = {_ledger(unit,tid)} }}'
                    commands=_group_commands(unit,tid,groups[unit][tid],gate)
                    model=groups[unit][tid]['model']
                    if model:
                        model_guard=f'country = JAP flag = JX_{info["flag"]}'
                        commands+=_model_commands(unit,model,model_guard,assume_tech=True)
                    effects.extend(('command',parse_fn(c)) for c in commands)
                    effects_count+=len(commands);touched=True
                if tid==1010:
                    # Native command supports both divisions and brigades. New
                    # countries may inherit this old tech when they are released.
                    for unit,info in ATTACHMENTS.items():
                        gate=f'OR = {{ NOT = {{ country = JAP }} NOT = {{ flag = JX_{info["flag"]} }} }}'
                        effects.append(('command',parse_fn(cond(gate,cmd('deactivate_unit_type',which=unit)))))
                    touched=True
        if touched:write(path,serialise(root)+'\n');changed.append(path.name)
    REPORT['tech']={'files':changed,'conditional_commands':effects_count,'initialisation_tech':1010}
    return REPORT['tech']


def _scenario_availability(target,read_fn,write,parse_fn,serialise):
    rows=[]
    for path in sorted((Path(target)/'scenarios/1933').glob('*.inc')):
        root=parse_fn(read_fn(path));changed=False
        for country in getall(root,'country'):
            allowed=get(country,'allowed_brigades')
            if allowed is None:allowed=[];country.append(('allowed_brigades',allowed))
            for unit in ATTACHMENTS:_set(allowed,unit,'no')
            rows.append(get(country,'tag'));changed=True
        if changed:write(path,serialise(root)+'\n')
    REPORT['initially_locked_countries']=rows


def _registry(target,read_fn,write,parse_fn,serialise):
    path=Path(target)/'db/units/brigade_types.txt'
    root=parse_fn(read_fn(path));root[:]=[(k,v) for k,v in root if k not in ATTACHMENTS]
    insert=next(i+1 for i,(k,v) in enumerate(root) if k=='b_rsv_40')
    additions=[]
    for unit,info in ATTACHMENTS.items():
        additions.append((unit,parse_fn(f'type = {info["branch"]} name = JX_{unit}_NAME short_name = JX_{unit}_SHORT '
            f'desc = JX_{unit}_DESC short_desc = JX_{unit}_DESC value = {(.9 if unit=="b_01" else .7)} list_prio = {25 if unit=="b_01" else 45 if unit=="b_02" else 105}')))
    root[insert:insert]=additions
    write(path,serialise(root)+'\n')


def _modifiers(target,read_fn,write):
    path=Path(target)/'db/units/brigade_modifiers.csv'
    rows=list(csv.reader(read_fn(path).splitlines(),delimiter=';'));header=list(rows[0])
    # Preserve every existing native/custom column; own fields may be replaced.
    remove=[i for i,name in enumerate(header) if name in ATTACHMENTS]
    if remove:
        rows=[[v for i,v in enumerate(row) if i not in remove] for row in rows];header=list(rows[0])
    end=header.index('X');result=[]
    special={
        'b_02':{'DEF_URBAN':5,'DEF_JUNGLE':5,'ATT_JUNGLE':-3,'MOV_JUNGLE':-3,'MOV_MOUNTAIN':-3},
        'b_03':{'ATT_SHORE':15,'ATT_RIVER':12,'ATT_JUNGLE':-3,'ATT_SWAMP':0},
    }
    for row in rows:
        if not row:continue
        if row[0]=='EOF':
            row=['EOF']+['']*(len(header)-1);row[end]='X'
        values=[]
        for unit,info in ATTACHMENTS.items():
            value=unit if row[0]=='MODIFIER' else '' if row[0]=='EOF' else row[header.index(info['base'])]
            value=str(special.get(unit,{}).get(row[0],value));values.append(value)
        row[end:end]=values;result.append(';'.join(row))
    write(path,'\n'.join(result)+'\n')


def _compatibility(target,read_fn,write,parse_fn,serialise):
    changed=[]
    for path in sorted((Path(target)/'db/units/divisions').glob('*.txt')):
        root=parse_fn(read_fn(path));unit=path.stem
        prior=list(root)
        # This module owns only these three allowed-attachment entries.
        root[:]=[(k,v) for k,v in root if not (k=='allowed_brigades' and v in ATTACHMENTS)]
        new=[('allowed_brigades',b) for b,info in ATTACHMENTS.items() if unit in info['compatible']]
        root[:0]=new
        if root!=prior:write(path,serialise(root)+'\n');changed.append(unit)
    REPORT['compatible_divisions']=changed


def _minister_effects(target,read_fn,write,parse_fn,serialise):
    path=Path(target)/'db/ministers/minister_personalities.txt'
    root=parse_fn(read_fn(path));mirrored=[]
    roster=Path(target)/'db/ministers/ministers_jap.csv'
    traits={r[7].casefold() for line in read_fn(roster).splitlines()
            if len(r:=line.split(';'))>7 and r[0].isdigit()} if roster.exists() else None
    for minister in getall(root,'minister'):
        if traits is not None and get(minister,'trait','').casefold() not in traits:continue
        commands=getall(minister,'command')
        for native in list(commands):
            # 'unit' modifies divisions; 'extra' modifies attachments. Group
            # commands already cover custom entries and must not be duplicated.
            if get(native,'type')!='extra':continue
            for unit,info in ATTACHMENTS.items():
                if get(native,'which')!=info['base']:continue
                clone=deepcopy(native);_set(clone,'which',unit)
                if clone not in commands:
                    minister.append(('command',clone));commands.append(clone)
                    mirrored.append((get(minister,'trait'),unit,get(native,'when','all'),get(native,'value')))
    if mirrored:write(path,serialise(root)+'\n')
    REPORT['minister_mirrors']=mirrored


def install_personnel(target,read,write,parse,serialise):
    """Safe to repeat after the final Japanese roster/personality writers."""
    return _minister_effects(target,read,write,parse,serialise)


def _assets(source,target):
    from PIL import Image,ImageOps,ImageDraw
    source=Path(source);target=Path(target)
    for name,tile in (('auxiliary.bmp',16),('auxiliarybig.bmp',20)):
        original=Image.open(source/'gfx/interface'/name)
        if original.height!=tile or original.width<41*tile:raise ValueError('Unexpected auxiliary atlas '+str(original.size))
        atlas=Image.new('RGB',(44*tile,tile));atlas.paste(original.crop((0,0,41*tile,tile)),(0,0))
        for unit,info in ATTACHMENTS.items():
            native={'b_01':21,'b_02':12,'b_03':32}[unit]
            symbol=original.crop((native*tile,0,(native+1)*tile,tile)).convert('RGB')
            # New cells retain the native symbol/category colour above a tiny
            # consistent bitmap label; old registered cells are pixel-exact.
            glyphs={'T':('111','010','010','010','010'),'9':('111','101','111','001','111'),
                    '3':('111','001','111','001','111'),'M':('101','111','111','101','101'),
                    'B':('110','101','110','101','110'),'N':('101','111','111','111','101')}
            label={'b_01':'T93','b_02':'MB','b_03':'NT'}[unit]
            draw=ImageDraw.Draw(symbol);draw.rectangle((0,tile-7,tile-1,tile-1),fill=(30,40,44))
            x=(tile-(len(label)*4-1))//2
            for letter in label:
                for y,row in enumerate(glyphs[letter]):
                    for dx,pixel in enumerate(row):
                        if pixel=='1':draw.point((x+dx,tile-6+y),fill=(255,255,230))
                x+=4
            atlas.paste(symbol,(info['index']*tile,0))
        destination=target/'gfx/interface'/name;destination.parent.mkdir(parents=True,exist_ok=True)
        atlas.save(destination,format='BMP')
    assets=[]
    for unit,info in ATTACHMENTS.items():
        art=HERE/'art'/f'{info["artkey"]}.png'
        if not art.exists():raise FileNotFoundError('Unique attachment art is required: '+str(art))
        picture=Image.open(art).convert('RGB')
        for i,year in enumerate(info['years']):
            for filename in (f'ill_bri_JAP_{info["index"]}_{i}.bmp',f'ill_bri_{info["index"]}_{i}.bmp'):
                path=target/'gfx/interface/models'/filename;path.parent.mkdir(parents=True,exist_ok=True)
                ImageOps.fit(picture,(192,104),method=Image.Resampling.LANCZOS).save(path,format='BMP');assets.append(str(path.relative_to(target)))
        event=target/'gfx/events_pics'/f'jx_{info["artkey"]}.bmp';event.parent.mkdir(parents=True,exist_ok=True)
        ImageOps.fit(picture,(400,116),method=Image.Resampling.LANCZOS).save(event,format='BMP');assets.append(str(event.relative_to(target)))
    REPORT['assets']=assets


def localisation_rows():
    rows=[]
    for unit,info in ATTACHMENTS.items():
        rows.extend([(f'JX_{unit}_NAME',info['name']),(f'JX_{unit}_SHORT',info['short']),(f'JX_{unit}_DESC',info['desc'])])
        for i,year in enumerate(info['years']):
            for nation in ('','_JAP'):rows.append((f'BRIG_MODEL{nation}_{info["index"]}_{i}',f'{info["name"]} {year}'))
    return rows


def install(source,target,read,write,parse,serialise):
    """Install only into the caller's target; no active-mod path is assumed."""
    target=Path(target)
    _registry(target,read,write,parse,serialise)
    for unit,info in ATTACHMENTS.items():
        write(target/'db/units/brigades'/f'{unit}.txt',f'# BRIG_MODEL_{info["index"]}_\n'+serialise([('model',m) for m in models(unit)])+'\n')
    _modifiers(target,read,write)
    _compatibility(target,read,write,parse,serialise)
    apply_tech(target,read,write,parse,serialise)
    _scenario_availability(target,read,write,parse,serialise)
    _minister_effects(target,read,write,parse,serialise)
    _assets(source,target)
    REPORT['models']={unit:len(info['years']) for unit,info in ATTACHMENTS.items()}
    return REPORT

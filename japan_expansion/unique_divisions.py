"""R12 Japanese full-size specialist divisions and native-effect parity.

Catalogue apply() follows existing preparation passes. install() follows the
old specialist installer; install_personnel() follows all roster writers and
precedes the final minister integrity validator. No imports mutate catalogues.
"""
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

from catalog import EVENTS, cmd, cond, flag
import specialist_units as native

SOURCE = native.SOURCE
CLASSES = {
    'd_13': dict(index=53, base='destroyer', name='Akizuki Anti-Air Escort Flotilla',
                 short='Akizuki AA', art='unique_akizuki', artkey='unique_akizuki',
                 year=1942, tech=12000, years=(1942,1945,1955),
                 techpairs=((12000,0),(3080,1),(3090,2)), base_models=(7,8,9),
                 model_names=('Akizuki AA Escort 1942','Improved AA Escort 1945','Postwar AA Escort 1955')),
    'd_14': dict(index=54, base='naval_bomber', name='Maritime Flying Boat Wing',
                 short='Flying Boat', art='unique_patrol', artkey='unique_patrol',
                 year=1938, tech=4190, years=(1938,1942,1943,1945,1949),
                 techpairs=((4190,0),(4200,1),(4210,2),(15140,3),(15150,4)), base_models=(2,3,4,5,6),
                 model_names=('H6K Maritime Patrol 1938','H8K Maritime Patrol 1942','H8K Search Patrol 1943',
                              'Long-Range Flying Boat 1945','Ocean Patrol Flying Boat 1949')),
    'd_15': dict(index=55, base='paratrooper', name='Teishin Airborne Division',
                 short='Teishin', art='unique_teishin', artkey='unique_teishin',
                 year=1942, tech=1680, years=(1942,1944,1947,1950),
                 techpairs=((1680,0),(1690,1),(1700,2),(1710,3)), base_models=(1,2,3,4),
                 model_names=('Teishin Airborne 1942','Teishin Airborne 1944','Teishin Airborne 1947','Teishin Airborne 1950')),
    'd_16': dict(index=56, base='multi_role', name='Naval Long-Range Fighter Wing',
                 short='Naval Fighter',art='unique_longfighter',artkey='unique_longfighter',
                 art_models={2:'unique_longfighter_late',3:'unique_longfighter_late'},
                 year=1940,tech=4070,years=(1940,1943,1945,1948),
                 techpairs=((4070,0),(4100,1),(4350,2),(15030,3)),base_models=(6,7,8,9),
                 model_names=('A6M Long-Range Fighter 1940','A6M Long-Range Fighter 1943',
                              'A7M Long-Range Fighter 1945','Long-Range Naval Fighter 1948')),
    'd_17': dict(index=57,base='naval_bomber',name='Long-Range Naval Attack Wing',
                 short='Naval Attack',art='unique_landattack',artkey='unique_landattack',
                 art_models={1:'unique_landattack_late',2:'unique_landattack_late',3:'unique_landattack_late',4:'unique_landattack_late'},
                 year=1938,tech=4190,years=(1938,1941,1943,1945,1949),
                 techpairs=((4190,0),(4200,1),(4210,2),(15140,3),(15150,4)),base_models=(2,3,4,5,6),
                 model_names=('G3M Naval Attack 1938','G4M Naval Attack 1941','G4M Naval Attack 1943',
                              'Improved Naval Attack 1945','Ocean Strike Wing 1949')),
    'd_18': dict(index=58,base='destroyer',name='Economical Escort Flotilla',
                 short='Matsu Escort',art='unique_matsu',artkey='unique_matsu',
                 year=1944,tech=12000,years=(1944,1945,1955),
                 techpairs=((12000,0),(3080,1),(3090,2)),base_models=(7,8,9),
                 model_names=('Matsu Escort 1944','Tachibana Escort 1945','Postwar Escort 1955')),
    'd_19': dict(index=59,base='infantry',name='Expeditionary Assault Division',
                 short='Expeditionary',art='unique_expedition',artkey='unique_expedition',
                 year=1937,tech=1100,years=(1937,1939,1942,1945,1948),
                 techpairs=((1100,0),(1110,1),(1120,2),(1130,3),(1140,4)),base_models=(9,10,11,12,13),
                 model_names=('Expeditionary Assault 1937','Expeditionary Assault 1939','Expeditionary Assault 1942',
                              'Expeditionary Assault 1945','Expeditionary Assault 1948')),
}
LEGACY_UNITS={'d_13','d_14','d_15'}
PARENT_COLUMNS={'destroyer':'DD','naval_bomber':'NAV B','paratrooper':'PARA','multi_role':'MR F','infantry':'INF'}
TERRAIN_BONUSES={'d_19':{'ATT_JUNGLE':15,'MOV_JUNGLE':15,'ATT_FOREST':10,'MOV_FOREST':10,
                       'ATT_RIVER':15,'ATT_URBAN':10}}
COUNTER_LABELS={'d_13':'AA','d_14':'P','d_15':'AB','d_16':'LR','d_17':'NA','d_18':'AS','d_19':'EX'}
MODEL_RULES = {'new_model','scrap_model','activate_unit_type','deactivate_unit_type'}
UNIT_EFFECTS = set('no_fuel_combat_mod no_supplies_combat_mod soft_attack hard_attack defensiveness toughness softness morale suppression air_attack air_defense build_cost build_time manpower speed max_organization transport_weight supply_consumption fuel_consumption speed_cap_art speed_cap_eng speed_cap_at speed_cap_aa naval_attack convoy_attack sub_attack shore_attack naval_defense surface_detection air_detection sub_detection visibility transport_capacity range max_positioning min_positioning'.split())
UNIT_EFFECTS |= {f'{terrain}_{kind}' for terrain in ('frozen','snow','blizzard','rain','storm','muddy','night','jungle','swamp','forest','hill','mountain','desert','urban','river','shore') for kind in ('attack','defense','move')}
REPORT = {}


def _read(path): return path.read_text(encoding='latin1')
def _get(node,key,default=None): return native.get(node,key,default)
def _replace(node,key,value): native.replace(node,key,value)
def _root(base): return native.parse(_read(SOURCE/'db/units/divisions'/f'{base}.txt'))
def active_flag(unit): return 'UNIQUE_'+unit.upper()+'_ACTIVE'
def _ledger(unit,tech): return 'UNIQUE_'+unit.upper()+'_TECH_'+str(tech)
def _model_ledger(unit,index): return 'UNIQUE_'+unit.upper()+'_MODEL_'+str(index)
def _gate(unit): return 'country = JAP flag = JX_'+active_flag(unit)


def models(unit):
    info=CLASSES[unit]; templates=native.getall(_root(info['base']),'model'); out=[]
    longest_range=0
    for index in info['base_models']:
        m=deepcopy(templates[index])
        changes={}
        if unit=='d_13':
            changes={'cost':round(native.num(m,'cost')*1.15,3),
                     'buildtime':round(native.num(m,'buildtime')*1.05),
                     'airattack':round(native.num(m,'airattack')*1.5,2),
                     'seaattack':round(native.num(m,'seaattack')*.8,2),
                     'convoyattack':round(native.num(m,'convoyattack')*.8,2),
                     'airdetectioncapability':native.num(m,'airdetectioncapability')+1}
        elif unit=='d_14':
            longest_range=max(longest_range,round(native.num(m,'range')*1.7))
            changes={'cost':round(native.num(m,'cost')*1.15,2),
                     'buildtime':round(native.num(m,'buildtime')*1.10),
                     'range':longest_range,
                     'surfacedetectioncapability':native.num(m,'surfacedetectioncapability')+2,
                     'navalattack':round(native.num(m,'navalattack')*.75,2),
                     'softattack':round(native.num(m,'softattack')*.75,2),
                     'hardattack':round(native.num(m,'hardattack')*.75,2)}
        elif unit=='d_15':
            changes={'cost':round(native.num(m,'cost')*1.15,2),
                     'buildtime':round(native.num(m,'buildtime')*1.10),
                     'defaultorganisation':native.num(m,'defaultorganisation')+8,
                     'morale':native.num(m,'morale')+8,
                     'supplyconsumption':round(native.num(m,'supplyconsumption')*.9,3)}
        elif unit=='d_16':
            longest_range=max(longest_range,round(native.num(m,'range')*2))
            changes={'cost':round(native.num(m,'cost')*1.05,2),'buildtime':round(native.num(m,'buildtime')*.95),
                     'range':longest_range,'airdefence':round(native.num(m,'airdefence')*1.15,2),
                     'maxspeed':round(native.num(m,'maxspeed')*.95),'fuelconsumption':round(native.num(m,'fuelconsumption')*1.1,3)}
        elif unit=='d_17':
            longest_range=max(longest_range,round(native.num(m,'range')*1.5))
            changes={'cost':round(native.num(m,'cost')*.95,2),'buildtime':round(native.num(m,'buildtime')*.95),
                     'range':longest_range,'airdefence':round(native.num(m,'airdefence')*1.25,2),
                     'fuelconsumption':round(native.num(m,'fuelconsumption')*1.15,3),
                     'softattack':round(native.num(m,'softattack')*.5,2),'hardattack':round(native.num(m,'hardattack')*.5,2)}
        elif unit=='d_18':
            changes={'cost':round(native.num(m,'cost')*.8,3),'buildtime':round(native.num(m,'buildtime')*.8),
                     'range':round(native.num(m,'range')*.65),'maxspeed':round(native.num(m,'maxspeed')*.8,2),
                     'seaattack':round(native.num(m,'seaattack')*.55,2),'convoyattack':round(native.num(m,'convoyattack')*.55,2),
                     'airattack':round(native.num(m,'airattack')*.8,2),'subattack':round(native.num(m,'subattack')*1.2,2),
                     'fuelconsumption':round(native.num(m,'fuelconsumption')*.75,3)}
        elif unit=='d_19':
            changes={'cost':round(native.num(m,'cost')*1.05,2),'buildtime':round(native.num(m,'buildtime')*.95),
                     'supplyconsumption':round(native.num(m,'supplyconsumption')*.8,3),
                     'fuelconsumption':round(native.num(m,'fuelconsumption')*.75,3),
                     'defensiveness':round(native.num(m,'defensiveness')*.9,2),
                     'hardattack':max(0,native.num(m,'hardattack')-1)}
        for key,value in changes.items(): _replace(m,key,value)
        out.append(m)
    return out


def _clone(command,base,unit):
    c=deepcopy(command); _replace(c,'which',unit)
    if _get(c,'type') in {'build_cost','build_time','manpower'} and _get(c,'where')=='relative':
        first=native.getall(_root(base),'model')[0]
        field={'build_cost':'cost','build_time':'buildtime','manpower':'manpower'}[_get(c,'type')]
        amount=round(native.num(first,field)*native.num(c,'value')/100,6)
        c[:]=[(k,v) for k,v in c if k!='where']; _replace(c,'value',f'{amount:g}')
    return c


def _applications(source=SOURCE):
    for path in sorted((source/'db/tech').glob('*.txt')):
        for tree in native.getall(native.parse(_read(path)),'technology'):
            for app in native.getall(tree,'application'):
                yield path.name,app


def _tech_effects(unit):
    base=CLASSES[unit]['base']; grouped=defaultdict(list)
    for filename,app in _applications():
        for c in native.getall(_get(app,'effects',[]),'command'):
            if _get(c,'which')==base and _get(c,'type') in UNIT_EFFECTS:
                grouped[(filename,int(_get(app,'id')))].append(_clone(c,base,unit))
    return grouped


def _trigger(command,gate):
    c=deepcopy(command); old=_get(c,'trigger',[])
    c[:]=[(k,v) for k,v in c if k!='trigger']
    return [('trigger',native.parse(gate)+old)]+c


def _model_commands(unit,index,assume_tech=False):
    if index==0:return []  # DH model zero is implicit; do not duplicate it.
    latest=native.parse(latest_model_conditions(unit)[index][1])
    if assume_tech:
        current=str(CLASSES[unit]['techpairs'][index][0])
        latest=[(k,v) for k,v in latest if not(k=='technology' and v==current)]
    return [[('trigger',latest)]+native.parse(cmd('new_model',which=unit,value=index))]+[
        native.parse(cmd('scrap_model',which=unit,value=i)) for i in range(index)]


def latest_model_conditions(unit):
    """Ascending (custom-model, year+research+no-newer-eligible predicate)."""
    info=CLASSES[unit]; rows=[]
    for tech,index in info['techpairs']:
        gate=f'year = {info["years"][index]} technology = {tech}'
        later=[f'AND = {{ year = {info["years"][i]} technology = {t} }}'
               for t,i in info['techpairs'] if i>index]
        if later:gate+=' NOT = { OR = { '+' '.join(later)+' } }'
        rows.append((index,gate))
    return rows


def upgrade_event_specs():
    """Year/technology catch-up jobs for the event-owner's automatic resolvers."""
    from build import serialise
    rows=[]
    for unit,info in CLASSES.items():
        for tech,index in info['techpairs'][1:]:
            year=info['years'][index]
            if year>1950:continue  # Retain data/tech hook beyond campaign end.
            gate=(_gate(unit)+f' year = {year} technology = {tech} '
                  f'NOT = {{ flag = JX_{_model_ledger(unit,index)} }}')
            commands=[serialise(_trigger(c,gate)) for c in _model_commands(unit,index)]
            commands.append(cond(gate,flag(_model_ledger(unit,index))))
            rows.append(dict(key=f'unique_upgrade_{unit}_{index}',unit=unit,year=year,
                             tech=tech,model=index,gate=gate,commands=commands))
    return rows


def activation_commands(unit):
    """Safe repeated call: activate once, catch up models/effects exactly once."""
    from build import serialise
    info=CLASSES[unit]
    first=('country = JAP ai = no NOT = { ispuppet = JAP } flag = JX_ACTIVE '
           f'year = {info["year"]} technology = {info["tech"]} ')
    new=first+' NOT = { flag = JX_'+active_flag(unit)+' }'
    commands=[cond(new,cmd('activate_unit_type',which=unit)),cond(new,flag(active_flag(unit)))]
    for tech,index in info['techpairs']:
        gate=(_gate(unit)+f' year = {info["years"][index]} technology = {tech} '
              f'NOT = {{ flag = JX_{_model_ledger(unit,index)} }}')
        commands += [serialise(_trigger(c,gate)) for c in _model_commands(unit,index)]
        commands.append(cond(gate,flag(_model_ledger(unit,index))))
    for (_,tech),effects in _tech_effects(unit).items():
        gate=_gate(unit)+f' technology = {tech} NOT = {{ flag = JX_{_ledger(unit,tech)} }}'
        commands += [serialise(_trigger(c,gate)) for c in effects]
        commands.append(cond(gate,flag(_ledger(unit,tech))))
    return commands


def apply():
    """Mirror Japanese event/programme concrete effects, preserving penalties."""
    if REPORT.get('catalogue_applied'):return
    from build import serialise
    count=0
    for e in EVENTS:
        if e.country!='JAP':continue
        for a in e.actions:
            old=[native.parse(c) for c in a.commands]; additions=[]
            for c in old:
                for unit,info in CLASSES.items():
                    if _get(c,'which')==info['base'] and _get(c,'type') in UNIT_EFFECTS:
                        clone=_clone(c,info['base'],unit)
                        if clone not in old and clone not in additions:additions.append(clone)
            a.commands += [serialise(c) for c in additions]; count+=len(additions)
    REPORT.update(catalogue_applied=True,programme_mirrors=count)


def localisation_rows():
    descriptions={
        'd_13':'Full Destroyer flotilla with 50% more AA firepower and 20% less surface/convoy attack. Base IC cost +15%, construction time +5%. Normal Destroyer research and crews apply. A torpedo fitting competes with other equipment for the normal attachment slot.',
        'd_14':'Full maritime search-and-strike wing: at least 70% more range, surface detection +2, and 25% less naval/ground strike. Base IC cost +15%, construction time +10%. Designed for wide sea searches and limited surface attacks; requires an airfield, fuel and supplies.',
        'd_15':'Full Airborne division with ordinary Paratrooper firepower, manpower and transport weight. Organisation and morale +8, supply use -10%, base IC cost +15%, construction time +10%. Normal transports and airborne doctrine are still required.',
        'd_16':'Full land-based naval fighter wing. Base range doubled, IC cost +5%, time -5%, speed -5%, fuel use +10%. Air-defence vulnerability +15%: higher is worse. Ordinary fighter firepower and crews; cannot operate as a carrier air group.',
        'd_17':'Full land-based naval attack wing. Base range +50%, IC cost and time -5%, ordinary naval strike and crews. Fuel use +15%, air-defence vulnerability +25% (higher is worse), ground attack halved. Less search capability than flying boats.',
        'd_18':'Affordable Matsu/Tachibana escort flotilla. Base IC cost and time -20%, ASW attack +20%, fuel -25%. Surface and convoy attack -45%, AA attack -20%, speed -20%, range -35%. A map destroyer flotilla, not convoy escort points.',
        'd_19':'Full-size expeditionary infantry with assault engineers: ordinary manpower, soft attack, speed and attachments. Supplies -20%, fuel -25%; jungle attack/movement +15, forest attack/movement +10, river attack +15, urban attack +10 percentage points. Defence -10%, hard attack -1; IC +5%, time -5%. Normal Infantry amphibious limits apply.',
    }
    return [(key,value) for unit,info in CLASSES.items()
            for key,value in (('JX_'+unit+'_NAME',info['name']),('JX_'+unit+'_SHORT',info['short']),
                              ('JX_'+unit+'_DESC',descriptions[unit]))]


def install_personnel(target,read,write,parse,serialise):
    path=target/'db/ministers/minister_personalities.txt'; root=parse(read(path))
    traits={r[7].casefold() for l in read(target/'db/ministers/ministers_jap.csv').splitlines()
            if len(r:=l.split(';'))>7 and r[0].isdigit()}
    count=0
    for m in native.getall(root,'minister'):
        if _get(m,'trait','').casefold() not in traits:continue
        commands=native.getall(m,'command')
        for c in list(commands):
            if _get(c,'type')!='unit':continue
            for unit,info in CLASSES.items():
                if _get(c,'which')==info['base']:
                    clone=deepcopy(c);_replace(clone,'which',unit)
                    if clone not in commands:m.append(('command',clone));commands.append(clone);count+=1
    write(path,serialise(root)+'\n');REPORT['minister_mirrors']=count
    return count


def _model_names(text):
    lines=text.splitlines(); additions=[]
    for unit,info in CLASSES.items():
        for index,name in enumerate(info['model_names']):
            for key in (f'MODEL_JAP_{info["index"]}_{index}',f'MODEL_{info["index"]}_{index}'):
                lines=[l for l in lines if not l.startswith(key+';')]
                additions.append(';'.join([key,name]+['']*9+['X']))
    end=next((i for i,l in enumerate(lines) if l.lstrip().upper().startswith('#EOF') or l.split(';')[0].upper()=='EOF'),len(lines))
    lines[end:end]=additions
    return '\n'.join(lines)+'\n'


def _walk(node):
    if not isinstance(node,list):return
    for k,v in node:
        yield k,v
        if isinstance(v,list):yield from _walk(v)


def _native_event_mirrors(source,target,read,write,parse,serialise):
    """Retain concrete Japanese stock-event bonuses, not only new programmes."""
    files=set()
    for registry in (source/'db/events.txt',source/'scenarios/1933.eug'):
        for k,v in _walk(parse(read(registry))):
            if k=='event' and isinstance(v,str) and v.lower().endswith('.txt'):files.add(v)
    count=0
    for relative in sorted(files):
        path=target/relative
        if not path.exists():continue
        root=parse(read(path)); changed=False
        for event in native.getall(root,'event'):
            if not isinstance(event,list) or _get(event,'country') not in {'JAP',None}:continue
            tags=[v for _,v in _get(event,'tag',[]) if isinstance(v,str)] if isinstance(_get(event,'tag'),list) else []
            if tags and 'JAP' not in tags:continue
            for key,action in event:
                if not key.startswith('action') or not isinstance(action,list):continue
                commands=[c for c in native.getall(action,'command') if isinstance(c,list)]
                additions=[]
                for c in commands:
                    for unit,info in CLASSES.items():
                        if _get(c,'which')==info['base'] and _get(c,'type') in UNIT_EFFECTS:
                            clone=_trigger(_clone(c,info['base'],unit),'country = JAP')
                            if clone not in commands and clone not in additions:additions.append(clone)
                action += [('command',c) for c in additions]
                if additions:changed=True;count+=len(additions)
        if changed:write(path,serialise(root)+'\n')
    return count


def install(source,target,read,write,parse,serialise):
    """Append to current target registries, techs and atlas after old d_12."""
    types=parse(read(target/'db/units/division_types.txt'))
    assert _get(types,'d_12') is not None
    for unit,info in CLASSES.items():
        assert _get(types,unit) is None,'Run unique installer on freshly rebuilt registry'
        definition=deepcopy(_get(types,info['base']))
        definition[:]=[(k,v) for k,v in definition if k not in {info['base'],'name','short_name','desc','short_desc','transmute','production','list_prio'}]
        definition += [('name','JX_'+unit+'_NAME'),('short_name','JX_'+unit+'_SHORT'),
                       ('desc','JX_'+unit+'_DESC'),('short_desc','JX_'+unit+'_DESC'),
                       ('transmute',info['base']),('production','no'),('list_prio',str(120+info['index']))]
        types.append((unit,definition))
        base=parse(read(target/'db/units/divisions'/f'{info["base"]}.txt'))
        content=[(k,deepcopy(v)) for k,v in base if k!='model']
        content.append(('upgrade',[('type',info['base']),('upgrade_time_factor','1.0'),('upgrade_cost_factor','1.0')]))
        write(target/'db/units/divisions'/f'{unit}.txt',serialise(content+[('model',m) for m in models(unit)])+'\n')
        # Explicit normal conversion route; full nominal cost/time factors
        # avoid a cheap obsolete-hull/airframe conversion shortcut.
        conversion=[('type',unit),('upgrade_time_factor','1.0'),('upgrade_cost_factor','1.0')]
        if conversion not in native.getall(base,'upgrade'):base.append(('upgrade',conversion))
        write(target/'db/units/divisions'/f'{info["base"]}.txt',serialise(base)+'\n')
    write(target/'db/units/division_types.txt',serialise(types)+'\n')
    path=target/'db/units/modifiers.csv'; rows=[l.split(';') for l in read(path).splitlines()]
    header=rows[0]; end=header.index('X')
    for row in rows:
        if row[0]=='EOF':continue
        values=[unit if row[0]=='MODIFIER' else
                str(float(row[header.index(PARENT_COLUMNS[info['base']])])+TERRAIN_BONUSES[unit][row[0]])
                if row[0] in TERRAIN_BONUSES.get(unit,{}) else row[header.index(PARENT_COLUMNS[info['base']])]
                for unit,info in CLASSES.items()]
        row[end:end]=values
    width=len(rows[0]); rows=[(['EOF']+['']*(width-2)+['X']) if r[0]=='EOF' else r for r in rows]
    write(path,'\n'.join(';'.join(r) for r in rows)+'\n')
    # Preserve old conditional specialist hooks; modify current target techs.
    effect_map={u:_tech_effects(u) for u in CLASSES}
    touched=set()
    for filename,_ in _applications(source):
        if filename in touched:continue
        touched.add(filename); path=target/'db/tech'/filename; root=parse(read(path))
        for tree in native.getall(root,'technology'):
            for app in native.getall(tree,'application'):
                tech=int(_get(app,'id')); effects=_get(app,'effects')
                for unit,info in CLASSES.items():
                    indices=[i for tid,i in info['techpairs'] if tid==tech]
                    for index in indices:
                        gate=(_gate(unit)+f' year = {info["years"][index]} '
                              'NOT = { flag = JX_'+_model_ledger(unit,index)+' }')
                        effects += [('command',_trigger(c,gate)) for c in _model_commands(unit,index,assume_tech=True)]
                        effects.append(('command',native.parse(cond(gate,flag(_model_ledger(unit,index))))))
                    mirrored=effect_map[unit].get((filename,tech),[])
                    if mirrored:
                        gate=_gate(unit)+' NOT = { flag = JX_'+_ledger(unit,tech)+' }'
                        effects += [('command',_trigger(c,gate)) for c in mirrored]
                        effects.append(('command',native.parse(cond(gate,flag(_ledger(unit,tech))))))
        write(path,serialise(root)+'\n')
    path=target/'config/models.csv';write(path,_model_names(read(path)))
    REPORT['native_event_mirrors']=_native_event_mirrors(source,target,read,write,parse,serialise)
    from PIL import Image,ImageDraw
    path=target/'gfx/map/hoi_counter_strip.bmp'
    with Image.open(path) as opened:
        old=opened.copy();opened.close()  # Release BMP mmap before overwriting on Windows.
    assert old.size==(53*32,34) and old.mode=='P'
    atlas=Image.new('P',((53+len(CLASSES))*32,34));atlas.putpalette(old.getpalette());atlas.paste(old,(0,0))
    # Native functional glyphs plus small 3x5 role markers, only in new cells.
    glyphs={'A':('010','101','111','101','101'),'P':('110','101','110','100','100'),
            'B':('110','101','110','101','110'),'L':('100','100','100','100','111'),
            'R':('110','101','110','101','101'),'N':('101','111','111','111','101'),
            'S':('011','100','010','001','110'),'E':('111','100','110','100','111'),
            'X':('101','101','010','101','101')}
    colours=old.getpalette(); black=min(range(256),key=lambda i:sum(colours[i*3:i*3+3])); white=max(range(256),key=lambda i:sum(colours[i*3:i*3+3]))
    registry_names=[key for key,node in types if isinstance(node,list) and key!='eyr']
    for unit,label in COUNTER_LABELS.items():
        native_index=registry_names.index(CLASSES[unit]['base'])
        index=CLASSES[unit]['index'];atlas.paste(old.crop((native_index*32,0,(native_index+1)*32,34)),(index*32,0))
        draw=ImageDraw.Draw(atlas); x=index*32+32-len(label)*4-2
        draw.rectangle((x-1,1,x+len(label)*4,6),fill=white)
        for letter in label:
            for y,bits in enumerate(glyphs[letter]):
                for dx,bit in enumerate(bits):
                    if bit=='1':draw.point((x+dx,2+y),fill=black)
            x+=4
    atlas.save(path)
    REPORT['installed_models']={u:len(models(u)) for u in CLASSES}
    REPORT['art_owner']='Parent installs event art and large/small unit cards from unique_* PNGs; this module owns only the division counter atlas.'

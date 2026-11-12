"""Japanese-only unit classes; deterministic source-derived models."""
from copy import deepcopy
from pathlib import Path
import json
from catalog import *
from activities import activity

from runtime_paths import SOURCE
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'tools'))
from audit_japan_baseline import parse,get,getall,num

CLASSES={
    'd_10':{'index':50,'name':'Naval Base Force','base':'garrison','sprite':'garrison','art':'baseforce','flag':'BASE_FORCE','year':1937,'tech':1100,'eyr':10},
    'd_11':{'index':51,'name':'Jungle Light Infantry','base':'infantry','sprite':'infantry','art':'jungleforce','flag':'JUNGLE_FORCE','year':1940,'tech':1110,'eyr':1},
    'd_12':{'index':52,'name':'Special Naval Landing Division','base':'marine','sprite':'marine','art':'snlf','flag':'SNLF_FORCE','year':1937,'tech':1590,'eyr':1},
}
YEARS=[1937,1939,1942,1945,1948]
MODEL_TECHS=[1100,1110,1120,1130,1140]
SNLF_YEARS=[1937,1940,1943,1946,1949]
SNLF_TECHS=[1590,1600,1610,1620,1630]


def model_techs(unit):return SNLF_TECHS if unit=='d_12' else MODEL_TECHS
def model_years(unit):return SNLF_YEARS if unit=='d_12' else YEARS


def read(p):return p.read_text(encoding='latin1')


def replace(n,k,v):
    n[:]=[(a,b) for a,b in n if a!=k];n.append((k,str(v)))


def models(unit):
    info=CLASSES[unit];base=getall(parse(read(SOURCE/'db/units/divisions'/(info['base']+'.txt'))),'model')
    apps=[]
    for t in getall(parse(read(SOURCE/'db/tech/infantry_tech.txt')),'technology'):
        apps+=getall(t,'application')
    result=[]
    for year in model_years(unit):
        choices=[(num(a,'year'),int(get(c,'value'))) for a in apps if num(a,'year')<=year
                 for c in getall(get(a,'effects',[]),'command')
                 if get(c,'type')=='new_model' and get(c,'which')==info['base'] and not get(c,'trigger')]
        _,idx=max(choices);m=deepcopy(base[idx])
        # Equipment is diagnostic UI metadata; remove the inherited full-division
        # headcount rather than advertising 13,000 men in an 8,000-man force.
        m[:]=[(k,v) for k,v in m if k!='equipment']
        if unit=='d_10':
            changes={'cost':4,'buildtime':100,'manpower':5,'maxspeed':0,
                     'softattack':max(1,round(num(m,'softattack')*.7)),
                     'hardattack':max(0,round(num(m,'hardattack')*.7)),
                     'defensiveness':38,'toughness':20,
                     'airattack':num(m,'airattack')+1,'airdefence':num(m,'airdefence')+2,
                     'supplyconsumption':round(num(m,'supplyconsumption')*.55,2),
                     'transportweight':5,'suppression':max(5,num(m,'suppression'))}
        elif unit=='d_11':
            changes={'cost':4,'buildtime':190,'manpower':8,'maxspeed':6,
                     'softattack':max(1,round(num(m,'softattack')*.8)),
                     'hardattack':max(0,round(num(m,'hardattack')*.75)),
                     'defensiveness':30,'toughness':35,
                     'supplyconsumption':round(num(m,'supplyconsumption')*.85,2),
                     'transportweight':7}
        else:
            changes={'cost':6,'buildtime':240,'manpower':9,'maxspeed':6,
                     'softattack':max(1,round(num(m,'softattack')*.9)),
                     'hardattack':max(0,round(num(m,'hardattack')*.85)),
                     'defensiveness':round(num(m,'defensiveness')*.85),
                     'toughness':round(num(m,'toughness')*.9),
                     'supplyconsumption':round(num(m,'supplyconsumption')*.9,2),
                     'transportweight':8}
        for k,v in changes.items():replace(m,k,v)
        result.append(m)
    return result


def mirror_effects():
    """Relevant concrete-class tech effects; group 'land' already covers both."""
    records=[]
    for p in (SOURCE/'db/tech').glob('*.txt'):
        for tree in getall(parse(read(p)),'technology'):
            for a in getall(tree,'application'):
                for c in getall(get(a,'effects',[]),'command'):
                    if get(c,'trigger') or get(c,'type') in {'new_model','scrap_model','activate_unit_type'}:continue
                    for unit,info in CLASSES.items():
                        if get(c,'which')!=info['base']:continue
                        clone=deepcopy(c);replace(clone,'which',unit)
                        records.append((p.name,int(get(a,'id')),unit,clone))
    return records


MIRRORS=mirror_effects()


def activation(unit):
    info=CLASSES[unit]
    commands=[flag(info['flag']),cmd('activate_unit_type',which=unit),cmd('new_model',which=unit,value=0)]
    for i,tech in enumerate(model_techs(unit)[1:],1):
        commands += [cond(f'technology = {tech}',cmd('new_model',which=unit,value=i)),
                     cond(f'technology = {tech}',cmd('scrap_model',which=unit,value=i-1))]
    for _,tid,u,node in MIRRORS:
        if u==unit:
            commands.append(cond(f'technology = {tid}', ' '.join(f'{k} = {v}' for k,v in node)))
    return commands


def append_events():
    for unit,info in CLASSES.items():
        # SNLF activation is appended after the established catalogue, so old
        # event IDs remain stable. Its paid programme is the recruitment offer.
        if unit=='d_12':continue
        key='introduce_'+unit
        if any(e.key==key for e in EVENTS):continue
        extra='' if unit=='d_10' else ' OR = { '+war('CHI')+' flag = JX_PACIFIC }'
        desc=('The Navy can now recruit a separate static base-defence formation: 8 manpower, '
              'higher local defence and AA, but weaker attacks and a higher IC price than a garrison. '
              'It cannot march as a field division; plan transport and strategic redeployment. '
              if unit=='d_10' else
              'A light formation can carry less and move better through jungle and swamp. It uses 11 manpower '
              'and about 85 percent of ordinary infantry supply, with lower firepower and a higher IC price. '
              'It keeps ordinary infantry penalties for opposed landings; it is not a cheap marine division. ')
        event(key,'New formations: '+info['name'],desc+
              'Accepting unlocks the class for normal production, with no free completed units. '
              'Infantry research unlocks later models through 1948. This is an optional alternate-history force structure.',
              year=info['year'],gate=active()+f' technology = {info["tech"]} NOT = {{ flag = JX_{info["flag"]} }}'+extra,
              actions=[Action('Open recruitment for this class',[fire('activate_'+unit)],chance=100)],
              art=info['art'],module='specialists')
        event('activate_'+unit,'Activate '+info['name'],'',triggered=True,
              actions=[Action('',activation(unit),gate='NOT = { flag = JX_'+info['flag']+' }',chance=100),
                       Action('',[],gate='flag = JX_'+info['flag'])],module='specialists',
              purpose='Hidden immediate activation and research catch-up. Keeps the large research-effect list out of player-facing option tooltips; guarded against duplicate application.')
    activity('base_force_orders','Men for the ports, or ships for the routes?',
        'Prepare two Naval Base Forces in normal production. Or commission 40 convoy transports '
        'and 20 convoy escorts instead. Static defenders guard a base after arrival; merchant '
        'ships sustain the routes between bases. Neither replaces the other.',
        1937,gate='flag = JX_BASE_FORCE',cash=70,stock=400,days=90,
        reward=[cmd('build_division',which='d_10',when=2)],
        alternative=('Commission merchant shipping instead',[
            cmd('transport_pool',which=-1,value=40),cmd('escort_pool',which=-1,value=20)]),
        first_label='Prepare two Naval Base Forces',art='baseforce')
    activity('jungle_force_orders','Light columns or a stronger landing force?',
        'Prepare two Jungle Light Infantry formations for a long inland campaign. Or prepare '
        'two ordinary marine divisions for opposed landings. Both are normal production orders, '
        'with their own IC, manpower and supply costs. Neither arrives at the end of this preparation period.',
        1940,gate='flag = JX_JUNGLE_FORCE technology = 1560',cash=90,stock=500,days=90,
        reward=[cmd('build_division',which='d_11',when=2)],
        alternative=('Prepare two marine divisions instead',[
            cmd('build_division',which='marine',when=2)]),
        first_label='Prepare two Jungle Light Infantry formations',art='jungleforce')


def install(source,target,write,serialise):
    types=parse(read(source/'db/units/division_types.txt'))
    assert get(types,'d_09') and get(types,'d_10') is None
    for unit,info in CLASSES.items():
        types.append((unit,parse(f'type = {info["base"]} name = JX_{unit}_NAME short_name = JX_{unit}_SHORT desc = JX_{unit}_DESC short_desc = JX_{unit}_DESC eyr = {info["eyr"]} sprite = {info["sprite"]} transmute = {info["base"]} gfx_prio = 2 value = 0.8 list_prio = {120+info["index"]} production = no')))
        brigades=['anti_air','police','engineer'] if unit=='d_10' else ['artillery','anti_air','engineer']
        if unit=='d_12':brigades.append('amph_armor')
        write(target/'db/units/divisions'/(unit+'.txt'),serialise(
            [('allowed_brigades',b) for b in brigades]+[('model',m) for m in models(unit)])+'\n')
    write(target/'db/units/division_types.txt',serialise(types)+'\n')
    lines=read(source/'db/units/modifiers.csv').splitlines();head=lines[0].split(';');out=[]
    for line in lines:
        cells=line.split(';')
        if not cells or cells[0]=='EOF':out.append(line);continue
        end=head.index('X');values=[]
        for unit,info in CLASSES.items():
            value=unit if cells[0]=='MODIFIER' else cells[head.index({'d_10':'GAR','d_11':'INF','d_12':'MAR'}[unit])]
            override={'ATT_JUNGLE':-50,'ATT_SWAMP':-45,'MOV_JUNGLE':-20,'MOV_SWAMP':-15}
            if unit=='d_11' and cells[0] in override:value=str(override[cells[0]])
            if unit=='d_12' and cells[0] in {'ATT_SHORE','ATT_RIVER'}:value=str(float(value)+5)
            values.append(value)
        cells[end:end]=values;out.append(';'.join(cells))
    # EOF also follows the expanded column count.
    out=[('EOF'+';'*(len(out[0].split(';'))-2)+'X') if x.startswith('EOF;') else x for x in out]
    write(target/'db/units/modifiers.csv','\n'.join(out)+'\n')
    # Correct one plainly malformed inherited morale value, not the whole class.
    guards=parse(read(source/'db/units/divisions/d_01.txt'));gm=getall(guards,'model')
    assert get(gm[1],'morale')=='540';replace(gm[1],'morale',50)
    write(target/'db/units/divisions/d_01.txt',serialise(guards)+'\n')
    # Existing tech files were reset from source by the builder. Clone only
    # concrete infantry/garrison effects; never activate a class abroad.
    names={'infantry_tech.txt'}|{p for p,_,_,_ in MIRRORS}
    for name in names:
        node=parse(read(target/'db/tech'/name))
        for tree in getall(node,'technology'):
            for app in getall(tree,'application'):
                tid=int(get(app,'id'));effects=get(app,'effects')
                for unit,info in CLASSES.items():
                    condition=parse(f'country = JAP flag = JX_{info["flag"]}')
                    if tid in model_techs(unit)[1:]:
                        idx=model_techs(unit).index(tid)
                        effects += [('command',[('trigger',condition),('type','new_model'),('which',unit),('value',str(idx))]),
                                    ('command',[('trigger',condition),('type','scrap_model'),('which',unit),('value',str(idx-1))])]
                    for _,mid,u,c in MIRRORS:
                        if mid==tid and u==unit:effects.append(('command',[('trigger',condition)]+deepcopy(c)))
        write(target/'db/tech'/name,serialise(node)+'\n')
    # Atlas packaging only: retain all old indexed pixels/palette, then append
    # native garrison and infantry symbols. No symbols are redrawn or generated.
    from PIL import Image,ImageOps
    original=Image.open(source/'gfx/map/hoi_counter_strip.bmp');assert original.size==(1600,34)
    atlas=Image.new('P',((50+len(CLASSES))*32,34));atlas.putpalette(original.getpalette());atlas.paste(original,(0,0))
    for slot,existing in ((50,9),(51,0),(52,7)):atlas.paste(original.crop((existing*32,0,(existing+1)*32,34)),(slot*32,0))
    atlas.save(target/'gfx/map/hoi_counter_strip.bmp')
    for unit,info in CLASSES.items():
        art=Image.open(Path(__file__).parent/'art'/(info['art']+'.png')).convert('RGB')
        for i in range(5):
            for name,size in ((f'ill_div_JAP_{info["index"]}_{i}.bmp',(192,104)),
                              (f'JAP_model_{info["index"]}_{i}.bmp',(67,44))):
                ImageOps.fit(art,size,method=Image.Resampling.LANCZOS).save(target/'gfx/interface/models'/name)


append_events()

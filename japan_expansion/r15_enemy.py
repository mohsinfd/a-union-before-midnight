"""Finite, paid Allied preparations in response to human Japanese expansion."""
from functools import lru_cache
from copy import deepcopy
from pathlib import Path
import json
from catalog import EVENTS, Action, event, cmd, cond, flag, clear, fire, later, owned, control, war
from r14_peace import guarded_action

REPORT={}
COUNTRY_NAMES={'USA':'America','AST':'Australia','ENG':'Britain'}
MIN_YEAR={'marine':1931,'infantry':1931,'interceptor':1930,'destroyer':1933,'transport':1925}
REACTIONS=(
    dict(key='hawaii',enemy='USA',title='America prepares to return to Hawaii',
         objectives=(1734,),require_all=True,hubs=((1886,'San Diego'),(1887,'Los Angeles'),(1889,'San Francisco')),
         packages=(('marine',3,'land'),('destroyer',4,'naval'),('transport',3,'naval')),
         bill=dict(manpower=60,money=200,supplies=12000,oil=4000,metal=2000),days=180,label='Pacific Return',
         summary='three Marine divisions, four Destroyer flotillas and three transport flotillas',position='Hawaii is in Japanese hands.',
         source_ai='usa_1942.ai',block='invasion',priorities={1734:100,1739:70}),
    dict(key='australia',enemy='AST',title='Australia prepares to defend its ports',
         objectives=(1726,1607,1697),require_all=False,hubs=((1704,'Brisbane'),),
         packages=(('infantry',4,'land'),('interceptor',2,'air')),
         bill=dict(manpower=58,money=75,supplies=5000,oil=1000,metal=1000),days=120,label='Australian Port Defence',
         summary='four Infantry divisions and two Interceptor wings',position='Japan or its clients now hold Rabaul, Port Moresby or Darwin.',
         source_ai='ast_1940.ai',block='garrison',priorities={1704:100,1705:100,1697:80}),
    dict(key='ocean',enemy='ENG',title='Britain gathers an Indian Ocean force',
         objectives=(1432,1511),require_all=True,hubs=((1053,'Aden'),),
         packages=(('infantry',3,'land'),('destroyer',4,'naval'),('transport',2,'naval')),
         bill=dict(manpower=50,money=125,supplies=8000,oil=3000,metal=1500),days=150,label='Eastern Fleet Reserve',
         summary='three Infantry divisions, four Destroyer flotillas and two transport flotillas',position='Japan or its clients now hold both Singapore and Colombo.',
         source_ai='eng_1941.ai',block='invasion',priorities={1511:100,1432:70}),
)


def f(s):return 'flag = JX_R15_E_'+s.upper()
def mark(s):return flag('R15_E_'+s.upper())
def unmark(s):return clear('R15_E_'+s.upper())
def no(s):return 'NOT = { AND = { '+s+' } }'
def cost_gate(bill):return ' '.join(f'{k} = {v}' for k,v in bill.items())
def resources(bill,sign):
    aliases={'manpower':'manpowerpool','oil':'oilpool','metal':'metalpool'}
    return [cmd(aliases.get(k,k),value=v*sign) for k,v in bill.items()]
def human():return 'flag = JX_ACTIVE exists = JAP NOT = { ai = JAP ispuppet = JAP }'
def enemy_context(enemy):return human()+' exists = '+enemy+' '+war(enemy)+' ai = '+enemy+' NOT = { puppet = { country = '+enemy+' country = JAP } }'
def due(key,days):return f'event = {{ id = @r15_enemy_{key}_pay days = {days} }}'


@lru_cache(None)
def model_options(unit):
    from build import SOURCE,parse,get,getall,read
    result=[]
    for path in (SOURCE/'db/tech').glob('*.txt'):
        for tree in getall(parse(read(path)),'technology'):
            for app in getall(tree,'application'):
                year=int(get(app,'year',0))
                if not MIN_YEAR[unit]<=year<=1950:continue
                for c in getall(get(app,'effects',[]),'command'):
                    if get(c,'type')=='new_model' and get(c,'which')==unit and not get(c,'trigger'):
                        result.append((year,int(get(app,'id')),int(get(c,'value'))))
    if not result:raise ValueError('No researched models for '+unit)
    return tuple(sorted(set(result),reverse=True))


def model_gates(unit):
    previous=[]
    for year,tech,model in model_options(unit):
        ready=f'year = {year} technology = {tech}'
        gate=ready+(' NOT = { OR = { '+' '.join('AND = { '+g+' }' for g in previous)+' } }' if previous else '')
        yield model,gate
        previous.append(ready)


def research_gate(row):
    return ' '.join('OR = { '+' '.join(f'AND = {{ year = {year} technology = {tech} }}' for year,tech,_ in model_options(unit))+' }' for unit,_,_ in row['packages'])


def site_gate(row,province):
    tag=row['enemy'];gate=owned(province,tag)+' '+control(province,tag)
    branches={branch for _,_,branch in row['packages']}
    for branch,facility in (('naval','naval_base'),('air','air_base')):
        if branch in branches:gate+=f' building = {{ province = {province} type = {facility} value = 1 when = now }}'
    return gate


def sites(row):return 'OR = { '+' '.join('AND = { '+site_gate(row,p)+' }' for p,_ in row['hubs'])+' }'
def ai_path(key):return '"jx/r15_'+key+'.ai"'


@lru_cache(None)
def client_controllers(province):
    from build import SOURCE,parse,get,read
    tags=[]
    for tag,node in parse(read(SOURCE/'db/revolt.txt')):
        if not isinstance(node,list) or tag=='JAP':continue
        provinces={int(v) for kind in ('minimum','extra') for _,v in get(node,kind,[]) if str(v).isdigit()}
        if province in provinces:tags.append(tag)
    return tuple(sorted(set(tags)))


def imperial_control(province):
    clauses=[control(province)]
    for tag in client_controllers(province):
        clauses.append('AND = { exists = '+tag+' puppet = { country = '+tag+' country = JAP } '+control(province,tag)+' NOT = { '+war(tag)+' } }')
    return 'OR = { '+' '.join(clauses)+' }'


def threat_gate(row):
    terms=' '.join(imperial_control(p) for p in row['objectives'])
    return terms if row['require_all'] else 'OR = { '+terms+' }'


def formations(row,province,city):
    tag=row['enemy'];commands=[];names=[];previous_branch=None
    for unit,count,branch in row['packages']:
        if branch!=previous_branch:
            commands.append(cmd('add_corps',which='"'+row['label']+' - '+city+' '+branch.title()+'"',value=branch,where=province))
        previous_branch=branch
        for i in range(1,count+1):
            name=f'{row["label"]} {unit.title()} {i} - {city}'
            names.append(name)
            for model,gate in model_gates(unit):
                commands += [cond(gate,cmd('add_division',which='"'+name+'"',value=unit,when=model)),
                             cond(gate,cmd('damage_division',which='"'+name+'"',value=tag,where=-100))]
    return commands,names


def apply():
    if REPORT:return REPORT
    before={e.key:e.id for e in EVENTS};added=[];all_names=[]
    for row in REACTIONS:
        row['threat']=threat_gate(row)
        key=row['key'];tag=row['enemy'];prefix='r15_enemy_'+key
        base=enemy_context(tag)+' year = 1941 flag = JX_PACIFIC'
        threat=base+' '+row['threat']+' NOT = { '+f(key+'_seen')+' }'
        event(prefix+'_threat',row['title'],
              row['position']+' The enemy will assess the position for 30 days. '
              'If it can fund the order and still has a safe assembly base, it can begin raising '+row['summary']+'. '
              'These forces have not arrived yet.',
              gate=threat,persistent=True,offset=3,year=1941,art='pacific',module='r15_enemy',actions=[
                  guarded_action('Prepare for the enemy response',[mark(key+'_seen'),later(prefix+'_assess',30,tag)],threat)])
        open_order=f(key+'_seen')+' NOT = { '+f(key+'_ordered')+' '+f(key+'_closed')+' }'
        assessed=f'event = {{ id = @{prefix}_threat days = 30 }}'
        plan=open_order+' '+assessed+' '+base+' '+row['threat']+' NOT = { '+f(key+'_plan')+' }'
        event(prefix+'_assess',row['title'],'',country=tag,triggered=True,year=1941,module='r15_enemy',actions=[
            guarded_action('',[mark(key+'_plan'),cmd('ai',which=ai_path(key))],plan),Action('',[],gate=no(plan),chance=100)])
        ready=open_order+' '+assessed+' '+f(key+'_plan')+' '+base+' '+row['threat']+' '+cost_gate(row['bill'])+' '+research_gate(row)+' '+sites(row)
        event(prefix+'_pay',row['title'],'',country=tag,triggered=True,year=1941,module='r15_enemy',actions=[
            guarded_action('',resources(row['bill'],-1)+[mark(key+'_ordered'),cmd('ai',which=ai_path(key)),later(prefix+'_finish',row['days'],tag),later(prefix+'_ordered',1),later(prefix+'_missing',row['days']+1)],ready),
            Action('',[],gate=no(ready),chance=100)])
        # A cash-poor government keeps its plan and can fund the finite order
        # later. It receives no invented budget and no repeated Japanese popup.
        pay=EVENTS[-1];pay.triggered=False;pay.persistent=True;pay.gate=ready;pay.offset=7
        abandoned=open_order+' '+assessed+' '+no(base+' '+row['threat'])
        event(prefix+'_abandoned',row['title'],'',gate=abandoned,persistent=True,year=1941,offset=3,module='r15_enemy',actions=[
            guarded_action('',[mark(key+'_closed'),mark(key+'_not_funded'),later(prefix+'_cancelled',1)],abandoned)])
        notice=f(key+'_ordered')+' NOT = { '+f(key+'_order_told')+' }'
        text=(COUNTRY_NAMES[tag]+' has paid for '+row['summary']+'. Training and fitting-out take '+str(row['days'])+
              ' days. New equipment must be researched, and a safe assembly base must remain available. '
              'A continuing Japanese war is required; otherwise the enemy receives its payment back. The order is finite.')
        event(prefix+'_ordered',row['title'],text,triggered=True,year=1941,art='army',module='r15_enemy',actions=[
            guarded_action('We have time to change our preparations',[mark(key+'_order_told')],notice),Action('',[],gate=no(notice),chance=100)])
        pending=f(key+'_ordered')+' NOT = { '+f(key+'_closed')+' }'
        elapsed=due(key,row['days']);valid=pending+' '+elapsed+' '+base+' '+research_gate(row)+' '+sites(row)
        actions=[];previous=[]
        for province,city in row['hubs']:
            gate=valid+' '+site_gate(row,province)+' '+''.join(no(s)+' ' for s in previous)
            additions,names=formations(row,province,city);all_names+=names
            actions.append(guarded_action('',additions+[cmd('ai',which=ai_path(key)),mark(key+'_formed'),mark(key+'_site_'+str(province)),mark(key+'_closed'),later(prefix+'_arrived',1)],gate))
            previous.append(site_gate(row,province))
        actions += [guarded_action('',resources(row['bill'],1)+[mark(key+'_refunded'),mark(key+'_closed'),later(prefix+'_cancelled',1)],pending+' '+elapsed+' '+no(valid)),
                    Action('',[],gate=no(pending+' '+elapsed),chance=100)]
        event(prefix+'_finish',row['title'],'',country=tag,triggered=True,year=1941,module='r15_enemy',actions=actions)
        told=f(key+'_formed')+' NOT = { '+f(key+'_arrival_told')+' }'
        event(prefix+'_arrived',row['title'],
              COUNTRY_NAMES[tag]+' has completed '+row['summary']+'. They formed at the stated rear base with their newest researched equipment. '
              'They need normal organisation recovery, oil and supplies. Their fleets and missions remain under the enemy command.',
              triggered=True,year=1941,art='army',module='r15_enemy',actions=[
                  guarded_action('The enemy force is ready at '+city,[mark(key+'_arrival_told')],told+' '+f(key+'_site_'+str(p))) for p,city in row['hubs']]+[
                  Action('',[],gate=no(told),chance=100)])
        cancelled=f(key+'_closed')+' NOT = { '+f(key+'_formed')+' '+f(key+'_cancel_told')+' }'
        event(prefix+'_cancelled',row['title'],
              'This exceptional enemy order produced no new formations. Its budget or safe bases were unavailable, '
              'the war changed, or the government ceased to exist. If a surviving government had already paid, its full investment was returned. '
              'Normal enemy production and operations continue.',
              triggered=True,year=1941,art='pacific',module='r15_enemy',actions=[
                  guarded_action('Continue the campaign',[mark(key+'_cancel_told')],cancelled),Action('',[],gate=no(cancelled),chance=100)])
        gone=pending+' '+elapsed+' NOT = { exists = '+tag+' }'
        event(prefix+'_missing',row['title'],'',triggered=True,year=1941,module='r15_enemy',actions=[
            guarded_action('',[mark(key+'_closed'),mark(key+'_government_gone'),later(prefix+'_cancelled',1)],gone),
            Action('',[],gate=no(gone),chance=100)])
    added=[e.key for e in EVENTS if e.key not in before]
    assert len(all_names)==len(set(all_names)), 'Reinforcement names collide across hubs/orders'
    assert all(next(e.id for e in EVENTS if e.key==k)==v for k,v in before.items())
    REPORT.update(applied=True,added=added,formations_names=all_names,reactive_families=3,old_ids_preserved=len(before))
    return REPORT


def install(source,target,read,write,parse,serialise):
    """Partial native-format plans, keeping unrelated active AI settings intact."""
    rows=[]
    for row in REACTIONS:
        raw=parse(read(Path(source)/'ai'/row['source_ai']))
        block=deepcopy(next(v for k,v in raw if k==row['block']))
        field='target' if row['block']=='invasion' else 'province_priorities'
        old=next((v for k,v in block if k==field),None)
        if old is None:old=[];block.append((field,old))
        for province,value in row['priorities'].items():
            old[:]=[(k,v) for k,v in old if str(k)!=str(province)];old.append((str(province),str(value)))
        path=Path(target)/'ai/jx'/('r15_'+row['key']+'.ai')
        # Native ENG1914_Senussi.ai demonstrates an invasion block containing
        # only target. Do not reset distances, fleet controls or military ratios.
        write(path,'# Finite preparation after Japanese gains; native AI may replace this plan.\n'+serialise([(row['block'],[(field,old)])])+'\n')
        rows.append(dict(country=row['enemy'],path=str(path.relative_to(target)),source=row['source_ai'],block=row['block'],priorities=row['priorities']))
    return rows

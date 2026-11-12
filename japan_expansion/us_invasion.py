"""Retryable US national surrender, isolated from one-shot stock events.

Retains the inherited demand levels, allocation priorities and national-war
withdrawal. Explicit provincial receipts precede peace; no success on a failed
handover. Appended after R4 events so existing IDs cannot move.
"""
import csv
from catalog import *

REPORT={}
PORTS=(1886,1887,1889,1874)
PREFIX='US_INV_'


def f(s):return 'flag = JX_'+PREFIX+s
def sf(s):return flag(PREFIX+s)
def cf(s):return clear(PREFIX+s)
def allof(s):return 'AND = { '+s+' }'
def no(s):return 'NOT = { '+allof(s)+' }'


def apply():
    from build import SOURCE,GAME,parse,get,getall,read,serialise
    if REPORT:return
    by={e.key:e for e in EVENTS}
    source=getall(parse(read(SOURCE/'db/events/USA.txt')),'event')
    response=next(e for e in source if get(e,'id')=='2049047')
    native_actions=getall(response,'action')[:4]
    maprows=[r for r in csv.DictReader(read(GAME/'map/Map_1/Province.csv').splitlines(),delimiter=';') if r['Id'].isdigit()]
    position=' OR = { '+' '.join(control(p) for p in PORTS)+' }'
    military=war('USA')+' lost_national = { country = USA value = 40 }'+position
    open_gate=active()+' '+pacific()+' '+military+' NOT = { '+f('PENDING')+' '+f('WAIT')+' '+f('DONE')+' '+f('DISMISSED')+' flag = JX_US_PENDING }'
    main=by['us_mainland'];main.persistent=True
    main.gate=open_gate
    main.desc='From 1943, America must have lost 40 percent of its national provinces and Japan must hold San Diego, Los Angeles, San Francisco or Seattle. Choose peace terms, wait 90 days, or dismiss this proposal. American acceptance ends its existing alliance wars, including a German war. This is a national surrender, not the separate Pacific armistice.'
    main.actions=[Action('Choose our peace terms',[fire('us_national_terms')],chance=100),
                  Action('Keep fighting; ask again in 90 days',[sf('WAIT'),later('us_inv_return',90)]),
                  Action('Fight to annexation; dismiss these terms',[sf('DISMISSED')])]
    menu=by['us_national_terms'];menu.desc='White peace returns occupied American land. Pacific terms concede US-owned Pacific islands. Overseas withdrawal adds strategic bases and ends listed aid and access agreements. The strongest terms add Alaska and eligible West Coast areas. California requires its whole map area; Oregon and Washington require the whole Washington area.\n\nOnly American-owned land in American or Japanese hands can be awarded. Other countries keep their property. Occupied US land outside the treaty returns under peace, including German occupations outside any agreed German concessions. America leaves its alliance wars; the surviving USA is not puppeted. Refusal allows another offer in 90 days.'
    menu.art='pacific';menu.actions=[]
    level_gates=['','','','OR = { area = { area = "California" country = JAP } area = { area = "Washington" country = JAP } }']
    labels=['White peace; return occupied US land',
            'Demand American Pacific islands',
            'Demand overseas withdrawal and strategic bases',
            'Demand overseas withdrawal and eligible West Coast areas']
    claims={};plan=[]
    for level,a in enumerate(native_actions):
        gate=military+' '+level_gates[level]
        menu.actions.append(Action(labels[level],[sf('PENDING'),sf('LEVEL_'+str(level)),later('us_inv_offer',1,'USA')],gate=open_gate+' '+level_gates[level],chance=100 if level==1 else 0))
        # Expand the original ordered allocation clauses using this map. First
        # eligible recipient wins; third-party occupations are never taken.
        entries=[]
        for c in getall(a,'command'):
            typ=get(c,'type')
            if not str(typ).startswith('secede'):continue
            dest=get(c,'which');value=get(c,'value')
            ps=[int(value)] if typ=='secedeprovince' else [int(r['Id']) for r in maprows if r['Area' if typ=='secedearea' else 'Region']==value]
            assert ps,(typ,value)
            condition=serialise(get(c,'trigger',[])).replace('\n',' ')
            for p in ps:entries.append((p,dest,condition));claims[p,dest]=True
        plan.append(entries)
    menu.actions += [Action('Not yet; ask again in 90 days',[sf('WAIT'),later('us_inv_return',90)],gate=open_gate),
                     Action('Continue to total conquest; dismiss negotiations',[sf('DISMISSED')],gate=open_gate),
                     Action('Our position changed; close these terms',[cf('PENDING')],gate=no(open_gate))]
    # The limited armistice must not be started during national negotiations.
    by['us_peace'].gate+=' NOT = { '+f('PENDING')+' }'
    pending=f('PENDING');live=pending+' '+military
    event('us_inv_return','American peace terms can be reconsidered','',triggered=True,
          actions=[Action('',[cf('WAIT')])],module='usa_invasion')
    def delayed():return [cf('PENDING'),cf('ACCEPTED'),cf('SNAPSHOT_READY'),cf('VERIFIED'),sf('WAIT'),later('us_inv_return',90)]+[cf('LEVEL_'+str(i)) for i in range(4)]
    offer_actions=[]
    for level,chance in enumerate((73,70,67,63)):
        valid=live+' '+f('LEVEL_'+str(level))+' '+level_gates[level]+' NOT = { '+f('ACCEPTED')+' }'
        offer_actions += [Action('Accept the stated surrender terms',[sf('ACCEPTED'),fire('us_inv_snapshot')],gate=valid+' NOT = { '+f('REFUSED_TWICE')+' }',chance=chance),
                          Action('Continue the war',[cond(f('REFUSED_ONCE'),sf('REFUSED_TWICE')),sf('REFUSED_ONCE'),later('us_inv_refused',1)],gate=valid+' NOT = { '+f('REFUSED_TWICE')+' }',chance=100-chance),
                          Action('Accept after repeated defeats',[sf('ACCEPTED'),fire('us_inv_snapshot')],gate=valid+' '+f('REFUSED_TWICE'),chance=100)]
    valid_any='OR = { '+' '.join(allof(live+' '+f('LEVEL_'+str(i))+' '+level_gates[i]) for i in range(4))+' }'
    offer_actions.append(Action('The offer no longer applies',delayed(),gate=pending+' NOT = { '+f('ACCEPTED')+' } '+no(valid_any),chance=100))
    event('us_inv_offer','Japan demands an American surrender','Japan has established a mainland invasion. Accept the selected territorial terms and withdraw from our alliance wars, or refuse and keep fighting. A renewed offer is possible after 90 days. After two refusals, another qualifying offer is accepted.',country='USA',triggered=True,actions=offer_actions,art='pacific',module='usa_invasion')
    event('us_inv_refused','America refuses our terms','The war continues. These peace terms return after 90 days if America still meets the defeat requirements. After two refusals, the next qualifying offer will be accepted.',triggered=True,actions=[Action('Continue the campaign',delayed(),gate=pending,chance=100)],art='pacific',module='usa_invasion')
    accepted=pending+' '+f('ACCEPTED')
    expected=lambda p,t:f('LAND_'+str(p)+'_'+t)
    assigned=lambda p:f('CLAIM_'+str(p))
    # Reset only our previous attempt's snapshots. Never touch unrelated flags.
    resets=[cf('LAND_'+str(p)+'_'+t) for p,t in sorted(claims)]+[cf('CLAIM_'+str(p)) for p in sorted({p for p,t in claims})]+[cf('TRY_1'),cf('TRY_2'),cf('PEACE_ISSUED'),cf('VERIFIED')]
    snapshots=[]
    for level,entries in enumerate(plan):
        for p,dest,condition in entries:
            eligible=accepted+' '+f('LEVEL_'+str(level))+' '+owned(p,'USA')+' exists = '+dest+' OR = { '+control(p,'USA')+' '+control(p)+' } NOT = { '+assigned(p)+' } '+condition
            snapshots += [cond(eligible,sf('LAND_'+str(p)+'_'+dest)),cond(eligible,sf('CLAIM_'+str(p)))]
    event('us_inv_snapshot','Record the agreed American provinces','',country='USA',triggered=True,
          actions=[Action('',[sf('SNAPSHOT_READY')]+resets+snapshots+[fire('us_inv_land')],gate=accepted+' NOT = { '+f('SNAPSHOT_READY')+' }',chance=100)],module='usa_invasion')
    land=[];requirements=[]
    for p,dest in sorted(claims):
        ex=expected(p,dest)
        land.append(cond(accepted+' '+ex+' '+owned(p,'USA')+' exists = '+dest+' OR = { '+control(p,'USA')+' '+control(p)+' }',cmd('secedeprovince',which=dest,value=p,when=1)))
        requirements.append('OR = { NOT = { '+ex+' } '+owned(p,dest)+' }')
    delivered=' '.join(requirements)
    event('us_inv_land','Hand over the agreed American provinces','',country='USA',triggered=True,
          actions=[Action('',land+[later('us_inv_check',1)],gate=accepted,chance=100)],module='usa_invasion')
    # Large ownership checks stay in hidden command bodies, never in a visible
    # option's hover text. This avoids the old huge-tooltip failure pattern.
    checks=[cf('LAND_FAILED'),cf('VERIFIED')]+[
        cond(expected(p,dest)+' NOT = { '+owned(p,dest)+' }',sf('LAND_FAILED')) for p,dest in sorted(claims)]
    event('us_inv_check','Check the American handover','',triggered=True,actions=[
        Action('',checks+[fire('us_inv_result')],gate=accepted,chance=100)],module='usa_invasion')
    event('us_inv_result','Act on the American handover check','',triggered=True,actions=[
        Action('',[sf('VERIFIED'),fire('us_inv_peace')],gate=accepted+' NOT = { '+f('LAND_FAILED')+' '+f('PEACE_ISSUED')+' }',chance=100),
        Action('',[sf('VERIFIED'),fire('us_inv_signed')],gate=accepted+' NOT = { '+f('LAND_FAILED')+' } '+f('PEACE_ISSUED'),chance=100),
        Action('',[sf('TRY_1'),later('us_inv_land',2,'USA')],gate=accepted+' '+f('LAND_FAILED')+' NOT = { '+f('TRY_1')+' '+f('PEACE_ISSUED')+' }',chance=100),
        Action('',[sf('TRY_2'),later('us_inv_land',2,'USA')],gate=accepted+' '+f('LAND_FAILED')+' '+f('TRY_1')+' NOT = { '+f('TRY_2')+' '+f('PEACE_ISSUED')+' }',chance=100),
        Action('',[later('us_inv_failed',1)],gate=accepted+' '+f('LAND_FAILED')+' OR = { '+f('TRY_2')+' '+f('PEACE_ISSUED')+' }',chance=100)],module='usa_invasion')
    peace_actions=[]
    for level,a in enumerate(native_actions):
        commands=[]
        for c in getall(a,'command'):
            if str(get(c,'type')).startswith('secede') or get(c,'type')=='clrflag':continue
            commands.append(serialise(c).replace('\n',' '))
        peace_actions.append(Action('',[sf('PEACE_ISSUED')]+commands+[later('us_inv_check',2)],gate=accepted+' '+f('LEVEL_'+str(level))+' '+f('VERIFIED')+' NOT = { '+f('PEACE_ISSUED')+' }',chance=100))
    event('us_inv_peace','America signs the national surrender','',country='USA',triggered=True,actions=peace_actions,module='usa_invasion')
    event('us_inv_signed','America accepts the terms of defeat','The agreed American provinces have changed ownership and America is no longer at war with Japan. America has withdrawn from its alliance wars. Other countries retain their own wars. Occupied American land outside the treaty returns under peace. The surviving USA is not our puppet. Overseas-withdrawal terms may later provoke American separatists; a breakup is not guaranteed.',triggered=True,actions=[
        Action('The American campaign is won',[sf('DONE'),cf('PENDING'),cf('ACCEPTED'),cmd('dissent',value=-2)],gate=accepted+' '+f('PEACE_ISSUED')+' '+f('VERIFIED')+' NOT = { '+war('USA')+' }',chance=100),
        Action('The treaty did not complete; keep the matter open',delayed(),gate=accepted+' OR = { '+war('USA')+' NOT = { '+f('VERIFIED')+' } }',chance=100)],art='pacific',module='usa_invasion')
    event('us_inv_failed','The American handover could not be completed','America accepted, but the agreed ownership could not be verified. Before peace, delivery is tried at most three times. No victory is recorded and this notice does not order peace or restart a war. Check the ownership and control map. Any land already ceded stays ceded. Another offer is possible in 90 days if the war and defeat requirements still hold.',triggered=True,actions=[Action('Close this notice; reconsider in 90 days',delayed(),gate=accepted,chance=100)],art='pacific',module='usa_invasion')
    REPORT.update(stock_response=2049047,protected_native_ids=[2049046,2011031,2049047],ports=PORTS,
                  allocations=[len(x) for x in plan],province_recipient_pairs=len(claims),
                  expected_clauses=len(requirements),military_gate=military,transfer_requirements=delivered,
                  claims=[list(x) for x in sorted(claims)],helper_events=10)

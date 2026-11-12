"""Automatic, free first issues for six Japanese classes, appended after R11.

Class/model/bonus implementations belong to unique_divisions and
unique_attachments. This module owns only once-only introduction/grant flow.
"""
from catalog import EVENTS, Action, event, active, owned, control, flag, clear, fire, cmd, cond

REPORT = {}
HOME_PORTS = ((1552,'Tokyo'),(1554,'Hiroshima'),(1555,'Kobe'),(1550,'Yokohama'))
HOME_AIRFIELDS = ((1552,'Tokyo'),(1554,'Hiroshima'),(1557,'Nagoya'),(1549,'Sendai'))
FORMATION_NAMES = {
    'd_13':'1st Akizuki Air-Defence Flotilla',
    'd_14':'Yokohama Maritime Flying Boat Wing',
    'd_15':'1st Teishin Airborne Division',
    'd_16':'Tainan Long-Range Fighter Wing',
    'd_17':'Genzan Naval Attack Wing',
    'd_18':'43rd Matsu Escort Flotilla',
    'd_19':'1st Expeditionary Assault Division',
}
CONTEXT = {
    'd_13':'Akizuki-class escorts bring dedicated anti-aircraft cover to the fleet. They exchange some surface firepower for that role.',
    'd_14':'Large flying boats give Japan a long-range maritime search force. H6K equipment enters service from 1938; H8K equipment follows from 1942 when its research is complete.',
    'd_15':'Teishin training begun in 1941 produces an airborne formation for service from 1942. Airborne missions still require transport aircraft and the normal mission conditions.',
    'd_16':'Land-based naval fighters extend air cover over distant approaches. They keep ordinary fighter firepower, with greater range but less speed and protection. They cannot be based on carriers.',
    'd_17':'Long-range land-based naval bombers retain full naval striking power. They cost less to construct but use more fuel and are more vulnerable than standard naval bombers. Flying boats remain better maritime search aircraft.',
    'd_18':'Matsu and Tachibana escorts put rapid replacement ahead of fleet speed and heavy torpedo armament. They are ordinary map flotillas for escort and anti-submarine operations, not convoy escort points.',
    'd_19':'This expeditionary division combines full infantry strength with assault engineers and a lighter support train. It improves jungle, forest, river and urban operations while using fewer supplies, at the cost of some defence and anti-armour strength. This organisation is an alternative development for Japan.',
    'b_01':'The Type 93 oxygen torpedo gives eligible Japanese destroyers and cruisers a specialised surface-attack loadout. It uses an attachment slot and carries its normal ammunition and supply demand.',
    'b_02':'Independent mixed brigades combine infantry and supporting detachments for security and local defence. These are attachments for eligible land formations, not separate map divisions.',
    'b_03':'Ka-Mi naval tank detachments support eligible infantry and Marine assault formations. They still require oil and ordinary supply; they do not replace the assault division.',
}


def negate(gate):return 'NOT = { AND = { '+gate+' } }'
def done(unit):return 'UNIQUE_INTRO_'+unit.upper()+'_DONE'
def progress(unit):return 'UNIQUE_INTRO_'+unit.upper()+'_IN_PROGRESS'
def site_gate(p,kind):
    return owned(p)+' '+control(p)+(f' building = {{ province = {p} type = {kind} value = 1 when = now }}' if kind else '')


def latest_conditions(info):
    """Highest researched model whose advertised service year has arrived."""
    pairs=info['techpairs'];years=info['years'];out=[]
    for tech,index in pairs:
        gate=f'year = {years[index]} technology = {tech}'
        later=['AND = { year = '+str(years[j])+' technology = '+str(t)+' }' for t,j in pairs if j>index]
        if later:gate+=' NOT = { '+' '.join(later)+' }'
        out.append((index,gate))
    return out


def transaction_commands(commands,guard):
    """Recheck execution eligibility, including cached/deferred human actions."""
    from build import parse,get,serialise
    result=[]
    for command in commands:
        node=parse(command)
        old=get(node,'trigger',[])
        combined=parse(guard)+old
        result.append(serialise([('trigger',combined)]+[(k,v) for k,v in node if k!='trigger']))
    return result


def append_events():
    if REPORT:return REPORT
    import unique_divisions as divisions
    import unique_attachments as attachments
    before={e.key:e.id for e in EVENTS}
    entries={**divisions.CLASSES,**attachments.ATTACHMENTS}
    intros=[];helpers=[]
    upgrades=[]
    legacy=set(attachments.ATTACHMENTS)|divisions.LEGACY_UNITS
    # Append the R13 batch only after all 29 original R12 events: preserve IDs.
    for batch in (legacy,set(entries)-legacy):
        for unit in sorted(batch,key=lambda u:(entries[u]['year'],u)):
            info=entries[unit];division=unit in divisions.CLASSES
            owner=divisions if division else attachments
            year=info['year'];name=info['name'];art=info.get('artkey',info.get('art'))
            if unit=='d_14':art='unique_patrol_early'
            if not art:raise ValueError('Missing introduction art for '+unit)
            key='unique_intro_'+unit;helper='unique_activate_'+unit
            core=active()+f' year = {year} technology = {info["tech"]} NOT = {{ flag = JX_{done(unit)} }}'
            root_idle=f' NOT = {{ flag = JX_{progress(unit)} }}'
            if division:
                branch='naval' if info['base']=='destroyer' else ('air' if info['base'] in {'naval_bomber','multi_role'} else 'land')
                kind='naval_base' if branch=='naval' else (None if info['base']=='infantry' else 'air_base')
                sites=HOME_PORTS if branch=='naval' else HOME_AIRFIELDS
                availability='OR = { '+' '.join('AND = { '+site_gate(p,kind)+' }' for p,_ in sites)+' }'
                core+=' '+availability
                text=(CONTEXT[unit]+' One initially recruited formation joins at an operational Japanese home '+
                      ('port' if branch=='naval' else ('assembly area' if kind is None else 'airfield'))+'. Its equipment uses the latest researched model whose service year has arrived. '
                      'The first formation is already funded and recruited: this issue takes no money, manpower or supplies from the national pool. '
                      'Further formations require normal production, crews and maintenance. If no listed home base is usable, the issue waits until one is ready.')
                actions=[];receivers=[];previous=[]
                for p,city in sites:
                    site=site_gate(p,kind)
                    gate=core+' '+site+' '+' '.join(negate(g) for g in previous)
                    commands=owner.activation_commands(unit)+[cmd('add_corps',which='"'+FORMATION_NAMES[unit]+'"',value=branch,where=p)]
                    commands += [cond(g,cmd('add_division',which='"'+FORMATION_NAMES[unit]+'"',value=unit,when=model)) for model,g in latest_conditions(info)]
                    commands += [cmd('damage_division',which='"'+FORMATION_NAMES[unit]+'"',value='JAP',where=-100),flag(done(unit))]
                    execution=gate+' flag = JX_'+progress(unit)
                    commands=transaction_commands(commands,execution)
                    commands += [cond('flag = JX_'+done(unit),clear(progress(unit)))]
                    receivers.append(Action('',commands,gate=execution,chance=100))
                    actions.append(Action('Receive '+name+' at '+city,
                                   transaction_commands([flag(progress(unit))],gate+root_idle)+
                                   [cond(gate+' flag = JX_'+progress(unit),fire(helper))],gate=gate+root_idle,chance=100))
                    previous.append(site)
            else:
                text=(CONTEXT[unit]+' The first two attachments enter the deployment pool, ready for eligible Japanese formations. '
                      'They use the latest researched equipment whose service year has arrived. This first issue is already funded and recruited; '
                      'it takes no money, manpower or supplies from the national pool. Additional attachments use normal production and operating costs.')
                commands=owner.activation_commands(unit)
                for model,g in latest_conditions(info):
                    commands += [cond(g,cmd('add_brigade',value=unit,when=model)) for _ in range(2)]
                execution=core+' flag = JX_'+progress(unit)
                commands += [flag(done(unit))]
                commands=transaction_commands(commands,execution)+[cond('flag = JX_'+done(unit),clear(progress(unit)))]
                receivers=[Action('',commands,gate=execution,chance=100)]
                actions=[Action('Receive the first two '+name+' attachments',
                                transaction_commands([flag(progress(unit))],core+root_idle)+
                                [cond(execution,fire(helper))],gate=core+root_idle,chance=100)]
            event(key,name+' enters Japanese service',text,year=year,offset=3,persistent=True,
                  gate=core+root_idle,actions=actions,art=art,module='unique_unit_introductions')
            activation=core+' flag = JX_'+progress(unit)
            receivers.append(Action('',[cond('flag = JX_'+progress(unit),clear(progress(unit)))],
                                    gate=negate(activation),chance=0))
            event(helper,name+' - service research', '',triggered=True,
                  actions=receivers,art=art,module='unique_unit_introductions',
                  purpose='Atomic activation, research catch-up, full first issue and completion. Root only requests it; deferred acknowledgement never closes its own eligibility.')
            intros.append(key);helpers.append(helper)

        for owner in (divisions,attachments):
            for spec in owner.upgrade_event_specs():
                if spec['year']>1950 or spec['unit'] not in batch:continue
                unit=spec['unit'];info=entries[unit]
                gate=spec['gate']
                event(spec['key'],info['name']+' - equipment in service','',year=spec['year'],offset=7,persistent=True,
                      gate=gate,actions=[Action('',spec['commands'],gate=gate,chance=100)],
                      art=info.get('artkey',info.get('art')),module='unique_unit_upgrades',
                      purpose='Once-only year/technology catch-up for an already activated Japanese class; no grant or charge.')
                upgrades.append(spec['key'])
    assert all(next(e.id for e in EVENTS if e.key==key)==value for key,value in before.items())
    REPORT.update(introductions=intros,activation_helpers=helpers,upgrade_resolvers=upgrades,
                  original_ids=before,added_ids={e.key:e.id for e in EVENTS if e.key not in before},
                  free_divisions=len(divisions.CLASSES),free_attachments=6)
    return REPORT

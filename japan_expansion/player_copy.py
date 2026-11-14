"""Final text-only editorial pass for Japan Rising's in-game English.

Call after every catalogue/mechanics pass. Developer explanations belong in
the reports; the game presents the situation, bill and concrete consequences.
No IDs, commands, dates, flags, gates or action order are changed here.
"""
import re
from catalog import EVENTS

REPORT = {}
BANNED = re.compile(r'\b(?:AI|dashboard|console|callback|receiver|receipt|scripted|engine|native|manual|template|legacy|retired|packet|package|docket|ledger|ahistorical|counterfactual|playtest|replay)\b',re.I)


def _clean(text):
    replacements = (
        ('aircraft and engine works', 'aircraft motor works'),
        ('common engine, airframe and repair-parts production', 'common motor, airframe and repair-parts factories'),
        ('Unit construction stays in your hands; this programme adds no formations or queue entries.', 'Place construction orders through Production.'),
        ('New formations arrive at their existing allowed maximum strength. Organisation follows normal deployment, and later damage or mobilisation can still reduce strength.',
         'New formations are delivered at full strength. Allow time for organisation to recover before operations. Mobilisation laws still apply.'),
        ('A current airfield of at least level one is required at funding and receipt; losing it returns the full bill.',
         'Keep at least one operational airfield level in Manila until the aircraft arrive, or the investment will be returned.'),
        ('A current naval base of at least level one is required at funding and receipt; losing it returns the full bill.',
         'Keep at least one operational naval-base level at Soerabaja until the ships arrive, or the investment will be returned.'),
        ('A dedicated AI allows limited overseas contributions', 'Chinese liaison officers can prepare a limited expeditionary force'),
        ('an AI preference is not a guarantee that every division embarks immediately', 'the government will retain most troops for home defence'),
        ('ordinary AI trade decisions', 'commercial policy'),
        ('Oil over the engine limit still decays.', 'Oil above the storage limit is lost.'),
        ('The engine groups oil and supplies together.', 'The expansion covers both oil and supplies.'),
        ('Native national recruitment', 'National recruitment'),
        ('The native mobilisation laws still govern their own effects.', 'National mobilisation laws remain in force.'),
        ('Native energy-to-oil conversion', 'Coal-to-oil conversion'),
        ('native conversion', 'coal-to-oil conversion'),
        ('not convoy counters or production-queue entries', 'ready for naval service'),
        ('the final queue price and time', 'the final production cost and time'),
        ('no empty queue orders are inserted', 'equipment and manpower must still be provided'),
        ('fund the reinforcement slider to use it', 'assign IC to reinforcement to use it'),
        ('at funding and receipt', 'when ordered and delivered'),
        ('check storage before ordering', 'allow enough room in the oil reserve before ordering'),
        ('physical IC', 'IC'),
        ('finite national stocks', 'captured stores'),
        ('finite Japanese stock deliveries', 'Japanese reserve deliveries'),
        ('finite captured-stock reward', 'captured stores'),
        ('finite recovered reserve', 'recovered reserve'),
        ('finite recruitment or operating stocks', 'recruitment and operating reserves'),
        ('one-time support package', 'initial support'),
        ('one-time merchant contract', 'merchant contract'),
        ('convoy batch', 'convoy reserve'),
        ('one package only', 'Choose one proposal'),
        ('One package only', 'Choose one proposal'),
        ('merchant package', 'merchant contract'),
        ('other package', 'other reserve'),
        ('chosen package', 'agreed support'),
        ('selected package', 'agreed support'),
        ('selected campaign reserve', 'campaign reserve'),
        ('selected support', 'support'),
        ('selected Chinese aid', 'Chinese aid'),
        ('selected works', 'new works'),
        ('selected work', 'new work'),
        ('paid inputs', 'investment'),
        ('paid input', 'investment'),
        ('all inputs', 'the investment'),
        ('finite reserve', 'reserve'),
        ('finite 50-manpower recruitment reserve', '50-manpower recruitment reserve'),
        ('finite recruitment reserve', 'recruitment reserve'),
        ('finite', 'limited'),
        ('static garrisons', 'local garrisons'),
        ('static detachments', 'local detachments'),
        ('small, static', 'small local'),
        ('Small, static', 'Small local'),
    )
    for old,new in replacements:text=text.replace(old,new)
    # Remove development-history explanations and promises about software
    # behavior; exact consequences are supplied by the overrides below.
    drop = (
        r'[^.!?\n]*(?:retired custom classes|former experimental classes|three experimental specialist classes|custom class|experimental unit class)[^.!?\n]*[.!?]?',
        r'[^.!?\n]*(?:quarterly reminders|manual decision|automatic victory award|cannot repeatedly supply refunds or rewards|no alternative reward is substituted)[^.!?\n]*[.!?]?',
        r'[^.!?\n]*This is an economic choice, not a change of government[.!?]?',
        r'[^.!?\n]*Neither creates divisions or duplicates the separate bridgehead convoy programme[.!?]?',
        r'[^.!?\n]*These are actual ships,[^.!?\n]*[.!?]?',
        r'[^.!?\n]*not a permanent strategy selection[.!?]?',
        r'[^.!?\n]*No buildings, land, cores or completed divisions are granted[.!?]?',
        r'[^.!?\n]*No aircraft, research, oil or supply consumption is granted for free[.!?]?',
    )
    for pattern in drop:text=re.sub(pattern,'',text,flags=re.I)
    # Keep unfamiliar mechanical words out of ordinary narrative. Remaining
    # occurrences are audited rather than silently deleting numerical effects.
    substitutions = {'package':'reserve','packet':'cargo','receipt':'delivery',
                     'template':'design','scripted':'planned','native':'national',
                     'engine':'production','manual':'optional','ahistorical':'ambitious',
                     'counterfactual':'alternative','callback':'report','receiver':'report',
                     'dashboard':'Decisions panel','console':'staff office','docket':'proposal',
                     'ledger':'reserve register','legacy':'earlier','retired':'withdrawn',
                     'playtest':'campaign','replay':'repeat','AI':'government'}
    for old,new in substitutions.items():text=re.sub(r'\b'+old+r'\b',new,text,flags=re.I)
    text=re.sub(r'[ \t]{2,}',' ',text)
    text=re.sub(r' *\n *','\n',text)
    text=re.sub(r'\n{3,}','\n\n',text)
    return text.strip()


def _set(by,key,desc=None,title=None):
    e=by.get(key)
    if e is not None:
        if desc is not None:e.desc=desc
        if title is not None:e.title=title


def _prewar(by):
    import prewar_content
    for spec in prewar_content.programmes():
        source=by.get(spec.key)
        if source is None:continue
        story=spec.story
        story=story.replace('This is an economic choice, not a change of government.','')
        story=story.replace('Both require fuel-consuming trials rather than a new production discount.', 'Both require fuel-consuming trials.')
        story=story.replace('This is preparation with ordinary Marine divisions; it opens no experimental unit class.', 'The trials prepare standard Marine divisions for future operations.')
        story=story.replace('This allocates new factory investment: existing factories are not moved or removed.', 'The investment will build new factories.')
        results=[c.result for c in spec.choices]
        if spec.key=='prewar_rural_works':
            results[0]='Nagoya gains 3 IC. Its 25-manpower civilian workforce is assigned when funding begins.'
            results[1]='The national reserve gains 40 manpower. Dissent rises by 1.'
        elif spec.key=='prewar_medical_service':
            results[0]='Trickle-back efficiency rises by 25 percentage points, returning more wounded men to the manpower pool.'
            results[1]='Medical examinations and reserve training release 50 manpower. Dissent rises by 1.'
        elif spec.key=='prewar_navigation_trials':
            results[0]='Naval bombers gain 300 km range and 2 surface detection.'
            results[1]='Tokyo and Hiroshima each gain 2 AA levels.'
        elif spec.key=='prewar_factory_dispersion':
            results[0]='Sendai gains 2 IC and 4 AA levels.'
            results[1]='Tokyo gains 4 IC. No additional AA is included.'
        elif spec.key=='prewar_landing_trials':
            results[0]='The maximum amphibious assault size increases by 1 division before the severe stacking penalty. Marines gain 5 maximum organisation.'
            results[1]='Marines gain 12 percentage points of shore attack and 8 of river attack. The assault-size limit is unchanged.'
        bills=[]
        for i,choice in enumerate(spec.choices):
            bill=', '.join(f'{v:,} {k}' for k,v in choice.costs.items())
            bills.append(f'{choice.label}\nCost: {bill}.\nCompletion: {spec.days} days. {results[i]}')
            finish=by.get(spec.key+f'_finish_{i}')
            if finish:
                finish.desc='The work is complete. '+results[i]+' If the required facilities are no longer available, the investment will be returned.'
                if spec.key=='prewar_rural_works' and i==0:
                    finish.desc='The Nagoya workshops are complete: +3 IC. The 25-manpower workforce was assigned when construction began. If the site can no longer support the work, the investment and workforce will be returned.'
                finish.actions[0].name=('Open the new works' if choice.buildings else 'Put the new arrangements into effect')
                finish.actions[1].name='Cancel the work and return the investment'
        source.desc=story.strip()+'\n\n'+'\n\n'.join(bills)
        source.desc+='\n\nFund one proposal before the Pacific war or war with America or Britain. Work already under way may finish during war. Keep the named sites under Japanese control and supplied; if the work cannot proceed, the investment is returned.'


def _fuel(by):
    import endurance_economy
    for key,year,cash,stock,metal,days,mine,options in endurance_economy.STAGES:
        place='Kushiro' if mine==1544 else 'Sapporo'
        parts=[]
        for i,(energy,steel,rare,oil) in enumerate(options):
            minerals=f'{place}: energy +{energy}, metal +{steel}, rare materials +{rare} daily.'
            production=minerals+f' Tokyo: oil +{oil} daily. Yokohama: energy -20 daily.'
            parts.append(('Balanced industry: ' if i==0 else 'Fuel and coal priority: ')+production)
            _set(by,f'{key}_finish_{i}',
                 f'The {place} complex is ready. '+production+
                 ' Production depends on control of the sites and resource transport. If the works cannot be commissioned, the investment is returned.')
        _set(by,key,'Expand coal extraction, mineral processing, recycling and fuel production. Choose one allocation.\n\n'+
             '\n\n'.join(parts)+f'\n\nCost: {cash} money, {stock:,} supplies and {metal:,} metal; retain at least 500 metal in reserve. Completion: {days} days. '
             'These are provincial output increases before resource efficiency. Fuel priority leaves fewer minerals for factories. '
             'Coal-to-oil conversion consumes the same energy reserve. The works remain with their provinces if the territory is lost; '
             'losing a required site before completion returns the investment.')
    for key,amount in [('fuel_batch_delivery_0',6000),('fuel_batch_delivery_1',12000),('endurance_small_fuel_delivery',1500)]:
        _set(by,key,f'The conversion works have prepared {amount:,} oil. Accept it only if there is enough room in the oil reserve. '
             f'Delivery is available while current oil is below {amount:,}; otherwise cancel and recover the energy, supplies and money. '
             f'The next conversion order can be placed in {90 if amount>=12000 else 45} days.')
        if key in by:by[key].actions[1].name='Cancel delivery and return the investment'
    _set(by,'wartime_fuel_batch',
         'Order a wartime coal-to-oil conversion.\n\nSmall: 3,000 energy, 200 supplies and 25 money for 1,500 oil.\n'
         'Standard: 12,000 energy, 800 supplies and 100 money for 6,000 oil.\n'
         'Large: 24,000 energy, 1,600 supplies and 200 money for 12,000 oil.\n\n'
         'Delivery takes 45 days. Small and standard orders then need 45 days of recovery; large orders need 90 days. One order may be under way at a time. '
         'Keep at least 9,000 energy after payment. Standard orders require strategic storage and the home fuel works; '
         'large orders require strategic storage and the wartime expansion. Current oil must be below the chosen delivery size. '
         'Check room in the oil reserve before accepting delivery; cancellation returns the investment. Industry and fuel conversion continue to use energy during the wait.')
    _set(by,'strategic_storage',
         "Expand Japan's strategic oil and supply depots. After 90 days, the national oil-and-supply storage modifier rises by 200 percentage points in peace and war. "
         'The actual storage limit still follows national demand. Oil above that limit is lost, so cancel surplus imports when the tanks are full.\n\nCost: 100 money and 800 supplies.')
    _set(by,'strategic_storage_finish_0',
         'The strategic depots are ready. Oil-and-supply storage modifier: +200 percentage points in peace and war. '
         'The storage limit follows national demand; keep imports within available capacity.')


def _settlements(by):
    for e in list(by.values()):
        if e.module!='settlements':continue
        if e.decision:
            e.desc=e.desc.split('\n\nThis settlement is offered')[0]
            e.desc+='\n\nConsider these terms when ready, or retain the present occupation.'
        elif e.key.endswith('_verify'):
            e.title=e.title.replace('agreement confirmed','the settlement')
            e.desc=('Our envoys report on the agreed government, reciprocal military access and Japanese bases. '
                    'Japan will help establish local defence and shipping where manpower and port facilities permit. '
                    "The agreement leaves Japan's other wars in force.")
            for a in e.actions:
                if a.name=='The agreement is incomplete; review the problem':a.name='The terms have not yet been fulfilled'
        elif e.key.endswith('_confirmed'):
            e.desc=("The agreement is in force. The new government accepts the agreed access and base arrangements. "
                    "Japan's other wars continue.")
        elif e.key.endswith('_failed'):
            e.desc=('Our envoys cannot yet confirm the agreed government, access or Japanese bases. Continue negotiations '
                    'in 30 days at no additional cost, or retain the present position. Territory already ceded remains with its present owner.')


def _special(by):
    _set(by,'welcome',
         'Japan enters 1933 with a powerful fleet, limited industrial resources and competing demands from the Army and Navy. '
         'Invest in factories, shipping, training and reserves to prepare for conflict in China and across the Pacific. '
         "Choose Japan's future alliances and peace terms from the position we build.\n\n"
         'Garrisons defend local bases, Mountain Infantry handle difficult terrain and Marines lead opposed landings. '
         'Production priorities and regional agreements can support the forces you build.')
    for key in ('china_expedition','china_expedition_finish_0','china_expedition_finish_1'):
        if key not in by:continue
        if key.endswith('_0'):
            text='The Chinese liaison mission is ready. China can offer part of its army for overseas operations while retaining most troops for home defence.'
        elif key.endswith('_1'):
            text='The Chinese home-defence programme is ready. China will concentrate its forces on defending its own territory.'
        else:
            text=('Prepare a Chinese expeditionary force for overseas service, or help China strengthen its home defence. '
                  'Most Chinese troops remain responsible for their own front.\n\nCost: 180 money and 1,000 supplies. Completion: 180 days.')
        _set(by,key,text)
    for key in ('china_exp_ai','india_exp_ai'):
        _set(by,key,'Liaison officers will consider a limited overseas force. Most troops remain assigned to home defence.')
    _set(by,'us_refused',
         'America will continue the war. Another offer is possible in six months if the military position still qualifies. '
         'After two refusals, maintaining that position again will bring America to negotiations.')
    _set(by,'us_inv_check',title='The American territorial handover')
    _set(by,'us_inv_result',title='The American handover report')
    _set(by,'us_inv_failed',
         'America accepted the terms, but the territorial handover remains incomplete. Land already ceded stays with its present owner. '
         'If the war continues and the defeat conditions still hold, another offer is possible in 90 days.')
    _set(by,'national_callup_1941',
         'The wider war brings 160 manpower into the replacement pool. For five years, recruitment adds another 0.65 manpower daily, '
         'about 237 per year. Wartime IC rises by 12%. Allocate equipment, supplies and reinforcement spending to put these recruits into service. '
         'National mobilisation laws remain in force.')
    _set(by,'national_mobilization_end',
         'The five-year recruitment supplement has ended. Its extra 0.65 daily manpower is removed. National recruitment continues, '
         'and recruits already called up remain available.')
    _set(by,'army_production_finish_0',
         'The infantry workshops are ready. Infantry construction: -1 IC and -43.5 days. Mountain Infantry: -1.2 IC and -43.5 days. '
         'Marines: -1.6 IC and -63 days. These reductions apply to future production orders.')
    for key in ('army_production_finish_1','naval_production_finish_0','naval_production_finish_1'):
        if key in by:
            by[key].desc=by[key].desc.replace('; no empty queue orders are inserted','').replace('Order the forces through normal production','Place the new orders through Production')
    names={'infantry':'Infantry','bergsjaeger':'Mountain Infantry','marine':'Marines',
           'motorized':'Motorised Infantry','cavalry':'Cavalry','armor':'Armour',
           'carrier':'Fleet carriers','light_carrier':'Light carriers','cag':'Carrier air groups',
           'light_cag':'Light carrier air groups','destroyer':'Destroyers','light_cruiser':'Light cruisers','submarine':'Submarines'}
    for key,cash,stock,days,intro,labels in (
        ('army_production',150,900,180,'Expand the workshops that equip the Army. Choose the formations to receive priority.',
         ('Infantry, mountain troops and Marines','Motorised troops, cavalry and armour')),
        ('naval_production',220,1200,240,'Expand the shipyards and their specialist suppliers. Choose which ships receive priority.',
         ('Carriers and their air groups','Escorts and submarines')),
    ):
        if key not in by:continue
        descriptions=[]
        for i,label in enumerate(labels):
            finish=by.get(f'{key}_finish_{i}')
            if finish is None:continue
            effects={};tc=0
            for command in finish.actions[0].commands:
                match=re.search(r'\btype = (build_cost|build_time)\b.*?\bwhich = (\w+)\b.*?\bvalue = (-?[\d.]+)',command)
                if match:
                    kind,unit,value=match.groups();effects.setdefault(unit,{})[kind]=float(value)
                bonus=re.fullmatch(r'type = tc_mod value = (-?[\d.]+)',command)
                if bonus:tc+=float(bonus[1])
            lines=[f'{names.get(unit,unit)}: {values.get("build_cost",0):g} IC, {values.get("build_time",0):g} days'
                   for unit,values in effects.items()]
            text='; '.join(lines)+'.'
            if tc:text+=f' Transport capacity +{tc:g}%.'
            descriptions.append(label+'\n'+text)
            finish.desc=label+' tooling is ready. '+text+' These reductions apply to future production orders.'
        by[key].desc=intro+'\n\n'+'\n\n'.join(descriptions)+f'\n\nCost: {cash} money and {stock:,} supplies. Completion: {days} days. '
        by[key].desc+='Research, manpower, equipment and operating resources remain necessary. Technology, ministers and gearing affect the final production price and time.'
    # The regional descriptions already carry their bills. Remove the
    # development comparisons and treaty non-effects from those narratives.
    for e in by.values():
        if e.module=='country_campaigns':
            e.desc=e.desc.replace('Manila can support more than a flag on the map.',
                                  "Manila's airfields can base fighters over Luzon or maritime patrols over the surrounding seas.")
            e.desc=e.desc.replace('Garrisons cannot march; these are ordinary formations, not the retired custom classes.', 'Garrisons cannot march.')
            e.desc=e.desc.replace('These are actual ships, not convoy counters or production-queue entries.', 'The ships enter service at Soerabaja.')
            e.desc=e.desc.replace('One package only. Losing the required position before delivery returns all inputs. Declining changes no borders, alliance or peace terms.',
                                  'Choose one proposal. Losing the required position before delivery returns the investment.')
            e.desc=e.desc.replace(' The setup bill was paid earlier. The chosen package is now due.', ' The agreed support is ready; its cost has already been paid.')
        if e.key.startswith('cs_'):
            if e.key.endswith('_start'):e.title='Construction orders'
            elif e.key.endswith('_verify'):e.title='Construction report'
            elif e.key.endswith('_refund'):
                e.title='Construction cancelled'
                e.desc='The contracted facilities could not be completed. The investment is returned. The proposal may be reconsidered in 90 days if the sites are available.'
                if len(e.actions)>1:e.actions[1].name='Acknowledge the cancellation'
    _set(by,'late_air_finish_0',
         'The aircraft and electronics mission has returned with blueprints for contemporary fighter and radar research.')
    regional_deliveries={
        'cn_shanghai_holding':('Two Garrison divisions are ready to defend Shanghai.','One Infantry division is ready at Shanghai.'),
        'cn_wuhan_choice':('Two Mountain Infantry divisions are ready at Wuhan.','The evacuation service returns 30 manpower and 1,500 supplies to Japan.'),
        'ph_manila_air':('Two Interceptor wings are ready at Manila.','Two Naval Bomber wings are ready at Manila.'),
        'ph_island_agreement':('Two Infantry divisions are ready at Tokyo for later deployment.',
                               'The merchant contract delivers 160 convoy transports, 40 escorts and 4,000 supplies to Japan.'),
        'in_java_shipyards':('Two Destroyers enter service at Soerabaja.','One Light Cruiser enters service at Soerabaja.'),
        'in_indonesian_exports':('The export mission delivers 12,000 oil to Japan. Allow enough room in the oil reserve.',
                                  'The export mission delivers 2,000 rare materials, 4,000 metal and 60 convoy transports to Japan.'),
        'my_singapore_yards':('The spare-parts service begins: reinforcement efficiency +20 percentage points for 360 days. Assign IC to reinforcement to use it.',
                              'The merchant reserve delivers 200 convoy transports, 60 escorts and 4,000 supplies to Japan.'),
        'my_malayan_exports':('The export mission delivers 2,000 rare materials and 4,000 metal to Japan.',
                              'The export mission delivers 16,000 energy and 6,000 supplies to Japan.'),
        'american_base':('The bridgehead reserve is ready: 120 convoy transports, 40 escorts and 2,000 supplies.',
                          'The replacement service is ready: 4,000 supplies and transport capacity +5%.'),
    }
    for key,choices in regional_deliveries.items():
        for i,text in enumerate(choices):
            _set(by,f'{key}_finish_{i}',text+' If the required position is no longer secure, the investment is returned.')
    _set(by,'american_base',
         'A foothold at San Diego, Los Angeles, San Francisco or Seattle opens a support programme for the American front. '
         'Choose an escorted supply route or a replacement service.\n\n'
         'Supply route: 120 convoy transports, 40 escorts and 2,000 supplies.\n'
         'Replacement service: 4,000 supplies and transport capacity +5%.\n\n'
         'Cost: 180 money and 1,000 supplies. Completion: 90 days. Retain a qualifying port until delivery or recover the investment. '
         'Supplies enter the national reserve; convoys must carry them to the front.')
    _set(by,'usc_commitment',
         'The American campaign has lasted 180 days, and Japanese forces still hold a Pacific coast port. '
         'Prepare replacements for an inland offensive, or strengthen the coastal position.\n\n'
         'Inland offensive: 50 manpower and 4,000 supplies.\nCoastal position: 8,000 supplies and 2,000 oil.\n\n'
         'Cost: 250 money and 4,000 supplies. Completion: 60 days. The American war and a qualifying coastal foothold must continue until delivery; '
         'otherwise the investment is returned. Peace negotiations and later campaign decisions remain available.')
    _set(by,'usc_replacements',
         'The mainland foothold needs replacements and equipment. Choose 50 manpower for reinforcement and recruitment, '
         'or a 6,000-supply operating reserve.\n\nCost: 200 money and 2,500 supplies. Completion: 60 days. '
         'The American war and a qualifying coastal foothold must continue until delivery; otherwise the investment is returned.')
    # Completion notices describe the funded outcome, rather than asking the
    # player to pay or choose again after the original transaction.
    for key,options in {
        'usc_replacements':('The American campaign reserve is ready: 50 manpower.','The American operating reserve is ready: 6,000 supplies.'),
        'usc_commitment':('The inland offensive reserve is ready: 50 manpower and 4,000 supplies.',
                          'The coastal reserve is ready: 8,000 supplies and 2,000 oil.'),
    }.items():
        for i,text in enumerate(options):_set(by,f'{key}_finish_{i}',text+' If the required foothold or war no longer exists, the investment is returned.')


def _mechanics():
    return [(e.key,e.id,e.country,e.gate,e.ready,e.year,e.start_month,e.start_day,e.offset,e.persistent,e.triggered,e.decision,
             [(a.gate,list(a.commands),a.chance) for a in e.actions]) for e in EVENTS]


def apply():
    if REPORT:return REPORT
    before=_mechanics()
    old={e.key:(e.title,e.desc,tuple(a.name for a in e.actions)) for e in EVENTS}
    by={e.key:e for e in EVENTS}
    _special(by);_prewar(by);_fuel(by);_settlements(by)
    for e in EVENTS:
        e.title=_clean(e.title);e.desc=_clean(e.desc)
        for a in e.actions:a.name=_clean(a.name)
    assert before==_mechanics(), 'Player copy must never change campaign mechanics'
    changed=[e.key for e in EVENTS if old[e.key]!=(e.title,e.desc,tuple(a.name for a in e.actions))]
    remaining=[{'key':e.key,'field':field,'term':m.group(),'text':value}
               for e in EVENTS for field,value in [('title',e.title),('desc',e.desc)]+[(f'action{i}',a.name) for i,a in enumerate(e.actions)]
               for m in BANNED.finditer(value)]
    REPORT.update(changed_events=changed,changed_count=len(changed),remaining=remaining,
                  mechanics_unchanged=True,minister_copy='Command-derived descriptions retained; no development terminology.')
    return REPORT

"""Country-specific operational choices, appended after the R10 catalogue.

One transaction per offer, no grand-strategy flags or peace commands. Each
alternative reserves its own complete bill and rechecks the map on delivery.
"""
from pathlib import Path
import json
from catalog import *

PROGRAMMES = []
MODELS = {}


def negate(gate):
    return 'NOT = { AND = { ' + gate + ' } }'


def relation(tag, key):
    return ('exists = ' + tag + ' NOT = { ' + war(tag) + ' } OR = { '
            + puppet(tag) + ' AND = { flag = JX_' + key + '_NEUTRAL '
            'flag = JX_' + key + '_SETTLED access = { country = ' + tag + ' country = JAP } } }')


def models():
    if MODELS:
        return
    from build import SOURCE, parse, read, get, getall, num
    apps = [a for p in (SOURCE / 'db/tech').glob('*.txt')
            for tree in getall(parse(read(p)), 'technology') for a in getall(tree, 'application')]
    for unit, year in [('garrison', 1931), ('infantry', 1936), ('bergsjaeger', 1935),
                       ('interceptor', 1939), ('naval_bomber', 1938),
                       ('destroyer', 1938), ('light_cruiser', 1938), ('transport', 1936)]:
        options = [(num(a, 'year'), int(get(c, 'value')), int(get(a, 'id')))
                   for a in apps if num(a, 'year') <= year
                   for c in getall(get(a, 'effects', []), 'command')
                   if get(c, 'type') == 'new_model' and get(c, 'which') == unit and not get(c, 'trigger')]
        chosen = max(options)
        template = getall(parse(read(SOURCE / 'db/units/divisions' / (unit + '.txt'))), 'model')[chosen[1]]
        MODELS[unit] = {'year': int(chosen[0]), 'model': chosen[1], 'tech': chosen[2],
                        'mp': num(template, 'manpower')}


def formation(unit, count, site, label, branch='land'):
    models()
    m = MODELS[unit]
    commands = [cmd('add_corps', which='"' + label + '"', value=branch, where=site)]
    commands += [cmd('add_division', which='"' + label + (' ' + str(i + 1) if count > 1 else '') + '"',
                     value=unit, when=m['model']) for i in range(count)]
    return commands, count * m['mp'], f'technology = {{ country = JAP value = {m["tech"]} }}'


def stock(label, cash, supplies_cost, days, awards, *, mp=0, metal=0, energy=0, oil=0, gate=''):
    return dict(label=label, cash=cash, stock=supplies_cost, days=days, awards=awards,
                mp=mp, metal=metal, energy=energy, oil=oil, gate=gate)


def unit_choice(label, cash, supplies_cost, days, unit, count, site, name, branch='land', extra_gate='', **extra):
    awards, mp, tech = formation(unit, count, site, name, branch)
    return stock(label, cash, supplies_cost, days, awards, mp=mp, gate=tech+' '+extra_gate, **extra)


def programme(key, title, story, year, context, choices, art='army'):
    gate = active() + ' ' + context + ' ' + no_state(key)
    actions, copy = [], []
    for i, option in enumerate(choices):
        costs = [('money', option['cash']), ('supplies', option['stock']),
                 ('manpowerpool', option['mp']), ('metalpool', option['metal']),
                 ('energypool', option['energy']), ('oilpool', option['oil'])]
        names = {'manpowerpool': 'manpower', 'metalpool': 'metal', 'energypool': 'energy', 'oilpool': 'oil'}
        bill = ', '.join(f'{v:g} {names.get(k,k)}' for k,v in costs if v)
        copy.append(f'{i + 1}. {option["label"]}: {bill}; {option["days"]} days.')
        pay = [cmd(k, value=-v) for k,v in costs if v]
        refund = [cmd(k, value=v) for k,v in costs if v]
        need = ' '.join(f'{names.get(k,k)} = {v:g}' for k,v in costs if v)
        selected = f'flag = JX_{key}_CHOICE_{i}'
        pending = (f'flag = JX_{key}_PENDING NOT = {{ flag = JX_{key}_DONE }} ' + selected
                   + f' event = {{ id = @{key} days = {option["days"]} }}')
        valid = human() + ' ' + context + ' ' + option['gate']
        finish = key + '_finish_' + str(i)
        actions.append(Action(option['label'], pay + [flag(key + '_PENDING'), flag(key + '_CHOICE_' + str(i)),
                              later(finish, option['days'])], gate=gate + ' ' + need + ' ' + option['gate'], chance=100 if i == 0 else 0))
        terminal = [clear(key + '_PENDING'), clear(key + '_CHOICE_' + str(i))]
        event(finish, title + ' - ready', story + ' The setup bill was paid earlier. The chosen package is now due.',
              triggered=True, module='country_campaigns', art=art,
              actions=[Action('Put the selected package into service', option['awards'] + terminal + [flag(key + '_DONE')], gate=pending + ' ' + valid, chance=100),
                       Action('Conditions changed; return every paid input', refund + terminal, gate=pending + ' ' + negate(valid)),
                       Action('', [], gate=negate(pending))])
    actions += [Action('Leave this offer available', [], gate=gate),
                Action('Dismiss this offer permanently', [flag(key + '_DISMISSED')], gate=gate)]
    text = story + '\n\n' + '\n'.join(copy) + '\nOne package only. Losing the required position before delivery returns all inputs. Declining changes no borders, alliance or peace terms.'
    e = event(key, title, text, year=year, decision=True, persistent=True, gate=gate,
              actions=actions, art=art, module='country_campaigns')
    e.manual_only = True
    PROGRAMMES.append({'key': key, 'id': e.id, 'year': year, 'title': title, 'context': context,
                       'story': story, 'choices': choices})


def append_events():
    if PROGRAMMES:
        return
    models()
    programme('cn_shanghai_holding', 'China: who holds Shanghai?',
        'The landing force is needed farther inland. Choose two ordinary 1931-model Garrison divisions to hold the port, '
        'or one ordinary 1936 Infantry division that can follow the advance. Both arrive equipped in Shanghai. '
        'Garrisons cannot march; these are ordinary formations, not the retired custom classes.',
        1937, war('CHI') + ' ' + control(1338), [
            unit_choice('Hold Shanghai with two Garrisons', 160, 2000, 120, 'garrison', 2, 1338, 'Shanghai Port Defence'),
            unit_choice('Raise one mobile Infantry division', 200, 2800, 180, 'infantry', 1, 1338, 'Shanghai Infantry')])

    programme('cn_wuhan_choice', 'China: beyond Wuhan',
        'Wuhan opens the approach to the interior. Fund two ordinary 1935 Mountain Infantry divisions at Wuhan for rough-country fighting, '
        'or a casualty evacuation service that returns 30 manpower and 1,500 supplies to Japan once. '
        'The evacuation award is a finite recovered reserve, not daily recruitment.',
        1938, war('CHI') + ' ' + control(1317), [
            unit_choice('Train two Mountain Infantry divisions', 220, 4000, 180, 'bergsjaeger', 2, 1317, 'Wuhan Mountain Group'),
            stock('Recover 30 manpower and 1500 supplies', 140, 3000, 120, [cmd('manpowerpool', value=30), supplies(1500)])])

    programme('ph_manila_air', 'Philippines: aircraft for the new front',
        'Manila can support more than a flag on the map. Choose two ordinary Interceptor wings to contest the air, '
        'or two Naval Bomber wings to patrol the surrounding seas. They deploy equipped at Manila using the listed prewar models; '
        'research, the manpower bill and normal oil/supply use remain necessary. Keep Japanese control until delivery.',
        1941, pacific() + ' ' + control(1565), [
            unit_choice('Deploy two Interceptor wings at Manila', 220, 3200, 150, 'interceptor', 2, 1565, 'Manila Fighter Group', 'air', metal=500, oil=500),
            unit_choice('Deploy two Naval Bomber wings at Manila', 260, 4000, 180, 'naval_bomber', 2, 1565, 'Manila Maritime Air Group', 'air', metal=600, oil=800)], art='air')

    programme('ph_island_agreement', 'Philippines: soldiers or shipping?',
        'After an agreement, decide how the islands fit the next campaign. With a Philippine puppet, fund two Japanese 1936 Infantry divisions '
        'at Tokyo for later deployment. Any friendly treaty government can instead support a one-time merchant contract: '
        '160 convoy transports, 40 escorts and 4,000 Japanese supplies. Neutral terms remain neutral; no war is inherited by this programme.',
        1941, pacific() + ' ' + relation('PHI', 'philippines'), [
            unit_choice('Raise two Infantry divisions at Tokyo', 300, 4200, 210, 'infantry', 2, 1552, 'Philippine Expedition Reserve', extra_gate=puppet('PHI')+' '+control(1552)),
            stock('Buy the inter-island merchant package', 200, 1800, 120,
                  [cmd('transport_pool', which=-1, value=160), cmd('escort_pool', which=-1, value=40), supplies(4000)])], art='pacific')
    programme('in_java_shipyards', 'Indonesia: put Soerabaja to work',
        'Use Soerabaja as a funded naval workshop. Commission two ordinary Destroyers or one Light Cruiser, '
        'with models no later than 1938, at this port. These are actual ships, not convoy counters or production-queue entries. '
        'They require their normal crews, fuel and maintenance. Japan must retain control of Soerabaja until completion.',
        1941, pacific() + ' ' + control(1653), [
            unit_choice('Commission two Destroyers at Soerabaja', 260, 4200, 240, 'destroyer', 2, 1653, 'Soerabaja Escort Flotilla', 'naval', metal=1200, oil=600),
            unit_choice('Commission one Light Cruiser at Soerabaja', 300, 5000, 300, 'light_cruiser', 1, 1653, 'Soerabaja Patrol Cruiser', 'naval', metal=1600, oil=800)], art='naval')

    friendly_java = 'OR = { ' + control(1647) + ' AND = { ' + relation('INO','indonesia') + ' ' + control(1647,'INO') + ' } }'
    friendly_oil = 'OR = { ' + control(1636) + ' AND = { ' + relation('INO','indonesia') + ' ' + control(1636,'INO') + ' } }'
    programme('in_indonesian_exports', 'Indonesia: what leaves the islands?',
        'Batavia and Palembang can support one large export mission. Choose a 12,000-oil cargo, or 2,000 rare materials, '
        '4,000 metal and 60 convoy transports. Deliveries enter Japan\'s national reserve, not a local depot. '
        'The oil choice requires Japanese oil below 12,000 at funding and receipt; check storage before ordering. '
        'Friendly puppet or neutral treaty control is accepted. This creates no continuing resource bonus.',
        1941, pacific() + ' ' + friendly_java + ' ' + friendly_oil, [
            stock('Order the 12000-oil cargo', 260, 2800, 150, [cmd('oilpool', value=12000)], energy=4000, gate='NOT = { oil = 12000 }'),
            stock('Order minerals and merchant hulls', 260, 2800, 150,
                  [cmd('rarematerialspool', value=2000), cmd('metalpool', value=4000), cmd('transport_pool', which=-1, value=60)])], art='economy')

    expiry_gate = 'flag = JX_SINGAPORE_REPAIR_ACTIVE'
    event('my_singapore_repair_end', 'The Singapore spare-parts contract ends', '', triggered=True,
          actions=[Action('', [cmd('repair_mod', value=-20), clear('SINGAPORE_REPAIR_ACTIVE')], gate=expiry_gate, chance=100),
                   Action('', [], gate=negate(expiry_gate))], module='country_campaigns', art='naval')
    programme('my_singapore_yards', 'Malaya: Singapore after the fighting',
        'Singapore offers a choice between a spare-parts service and merchant replacements. The service adds 20 percentage points '
        'to Japan\'s reinforcement efficiency for 360 days, across land, air and naval forces; fund the reinforcement slider to use it. '
        'It restores no sunk ships. The other package supplies 200 convoy transports, 60 escorts and 4,000 supplies once. '
        'Japan must retain control of Singapore until the work finishes.',
        1941, pacific() + ' ' + control(1432), [
            stock('Fund a one-year spare-parts service', 180, 3000, 90,
                  [cmd('repair_mod', value=20), flag('SINGAPORE_REPAIR_ACTIVE'), later('my_singapore_repair_end',360)], metal=1500, oil=1000),
            stock('Replace merchant ships and operating stocks', 220, 2400, 150,
                  [cmd('transport_pool', which=-1, value=200), cmd('escort_pool', which=-1, value=60), supplies(4000)], metal=1000)], art='naval')

    friendly_malaya = 'OR = { ' + control(1438) + ' AND = { ' + relation('MLY','malaya') + ' ' + control(1438,'MLY') + ' } }'
    programme('my_malayan_exports', 'Malaya: rubber, tin and a working economy',
        'Holding Kuala Lumpur, or trading with a friendly Malayan treaty government, opens one funded export programme. '
        'Choose 2,000 rare materials and 4,000 metal for factories and shipbuilding, or 16,000 energy and 6,000 supplies '
        'for fuel conversion and a long campaign. These are finite Japanese stock deliveries. '
        'No occupation, puppet, neutrality or base term is changed by either choice.',
        1941, pacific() + ' ' + friendly_malaya, [
            stock('Buy rubber and metal stocks', 220, 2200, 150, [cmd('rarematerialspool', value=2000), cmd('metalpool', value=4000)]),
            stock('Buy fuel feedstock and campaign supplies', 220, 2200, 150, [cmd('energypool', value=16000), supplies(6000)])], art='economy')

    # Existing Chinese partner offers should follow the actual conquest, not
    # sit idle until 1941/42 after an early settled campaign.
    by = {e.key:e for e in EVENTS}
    for key, year in [('china_mission',1938), ('china_expedition',1939), ('china_rebuild',1939)]:
        by[key].year = year
    pending = 'flag = JX_china_mission_PENDING NOT = { flag = JX_china_mission_DONE }'
    live = human()+' '+puppet('U87')
    for i,key in enumerate(('china_mission_aid','china_mission_unit')):
        selected = f'flag = JX_R11_CHINESE_AID_{i}'
        by['china_mission'].actions[i].commands.append(flag('R11_CHINESE_AID_'+str(i)))
        receipt = 'R11_CHINESE_AID_RECEIPT_'+str(i)
        recipient = by[key]
        awards = [supplies(1500),money(100)] if i==0 else [cmd('manpowerpool', value=35),supplies(3000)]
        receiver_guard = pending+' '+selected+' '+puppet('U87')+' NOT = { flag = JX_'+receipt+' }'
        recipient.actions = [Action('Receive the funded Chinese aid',awards+[flag(receipt)],gate=receiver_guard,chance=100),
                             Action('',[],gate=negate(receiver_guard))]
        finish = by['china_mission_finish_'+str(i)]
        finish_guard = pending+' '+selected
        terminal = [clear('china_mission_PENDING'),clear('R11_CHINESE_AID_'+str(i))]
        finish.actions = [
            Action('Deliver the selected Chinese aid',[fire(key)]+terminal+[flag('china_mission_DONE')],gate=finish_guard+' '+live,chance=100),
            Action('The relationship changed; refund the mission',[money(120),supplies(1500)]+terminal,gate=finish_guard+' '+negate(live)),
            # Old queued missions lack the new branch marker. Return their bill
            # once instead of guessing the selected aid or trapping the save.
            Action('Return the superseded mission payment',[money(120),supplies(1500),clear('china_mission_PENDING')],
                   gate=pending+' NOT = { flag = JX_R11_CHINESE_AID_0 flag = JX_R11_CHINESE_AID_1 }'),
            Action('',[],gate='OR = { '+negate(pending)+f' flag = JX_R11_CHINESE_AID_{1-i} '+' }')]
    by['china_mission_unit'].title = 'Chinese army replacements and equipment'
    by['china_mission_unit'].desc = 'The paid Japanese mission provides 35 Chinese manpower and 3,000 Chinese supplies for ordinary recruitment and reinforcement. No unfunded production order is inserted.'
    by['china_mission'].actions[1].name = 'Fund 35 Chinese manpower and 3000 supplies'
    desc = ('Support the actual Chinese puppet from 1938. After 60 days the economic mission sends China 1,500 supplies and 100 money; '
            'the military mission sends 35 Chinese manpower and 3,000 supplies for its existing army. '
            'Neither creates an unfunded build order or transfers manpower to Japan. Cost: 120 money and 1,500 supplies. '
            'China must remain a Japanese puppet, or the payment returns.')
    by['china_mission'].desc = desc
    by['china_mission_finish_0'].desc = by['china_mission_finish_1'].desc = desc + ' The chosen aid is now due.'

    # The 1933 Philippines are US-owned, and the Commonwealth can be absent or
    # reannexed later. The original generic colonial owner list omitted USA.
    # Release only already occupied Philippine provinces, never make US peace.
    from build import source_country
    _, provinces = source_country('PHI')
    old = 'OR = { '+owned(1565)+' '+war('ENG')+' '+war('FRA')+' '+war('U05')+' '+war('HOL')+' }'
    new = old[:-2]+' '+war('USA')+' }'
    ph = by['philippines']
    assert old in ph.gate
    ph.gate = ph.gate.replace(old,new)
    for a in ph.actions:
        a.gate = a.gate.replace(old,new)
    occupation = ('flag = JX_philippines_PENDING NOT = { flag = JX_philippines_SETTLED exists = PHI } '
                  'exists = USA '+war('USA')+' '+control(1565))
    event('philippines_land_USA','Philippines: occupied American territory changes hands','',country='USA',triggered=True,
          actions=[Action('',[cond(owned(p,'USA')+' '+control(p),cmd('secedeprovince',which='JAP',value=p,when=1)) for p in sorted(set(provinces))],
                          gate=occupation,chance=100),Action('',[],gate=negate(occupation))],module='settlements',
          purpose='Missing owner case: absent Commonwealth during a Japanese-American war. Only occupied Philippine land transfers; USA remains at war.')
    for a in ph.actions[:3]:
        j=next(i for i,c in enumerate(a.commands) if 'type = setflag which = JX_philippines_PENDING' in c)
        a.commands.insert(j+1,cond(occupation,fire('philippines_land_USA')))
    # The old retry preparation must use the same checked transfer.
    by['philippines_prepare'].actions[0].commands.insert(0,cond(occupation,fire('philippines_land_USA')))


def documentation(path):
    lines = ['# R11 country campaign choices', '',
             'Eight new country-specific decisions plus three earlier Chinese partner offers. Existing settlement/peace machinery is retained. No new alliance route is selected.', '',
             '| Decision | Earliest | Requirements | Alternatives |', '| --- | --- | --- | --- |']
    requirements = {
        'cn_shanghai_holding':'War with Nationalist China; Japan holds Shanghai',
        'cn_wuhan_choice':'War with Nationalist China; Japan holds Wuhan',
        'ph_manila_air':'Pacific war begun; Japan holds Manila',
        'ph_island_agreement':'Pacific war begun; Philippine puppet or settled neutral treaty with access',
        'in_java_shipyards':'Pacific war begun; Japan holds Soerabaja',
        'in_indonesian_exports':'Pacific war begun; Japan or friendly Indonesian treaty government holds Batavia and Palembang',
        'my_singapore_yards':'Pacific war begun; Japan holds Singapore',
        'my_malayan_exports':'Pacific war begun; Japan or friendly Malayan treaty government holds Kuala Lumpur',
    }
    for p in PROGRAMMES:
        lines.append('| '+p['title']+' | '+str(p['year'])+' | '+requirements[p['key']]+' | '+' / '.join(x['label'] for x in p['choices'])+' |')
    lines += ['', 'Every funded choice has its own selected-branch marker, complete upfront bill, due-date map/research recheck, exact refund and final one-time receipt. Closing schedules no reminder; dismissal is permanent for that offer only.', '',
              'Unit models and manpower costs are read from the clean Blood and Iron technologies/templates. Unit funding reserves that model\'s complete manpower. Units are issued as normal equipped formations, with ordinary combat and maintenance; no zero-progress production order or retired custom class is used. Native mobilisation and engine deployment behaviour remain runtime checks.', '',
              'Friendly neutral treaties qualify only for stated civilian/merchant programmes. No new declaration, alliance, mastery, core, province transfer or peace command is issued. Physical supplies/resources enter the national pool; convoy delivery remains the player\'s responsibility.', '',
              'Chinese aid opens from 1938, expedition/home-defence choice and reconstruction from 1939, once the actual puppet exists. Chinese military aid now grants 35 local manpower and 3,000 supplies instead of inserting an unfunded infantry order.', '',
              'An absent Philippine Commonwealth can now be released from occupied American-owned Philippine territory during a Japanese-American war. Only Japanese-held Philippine provinces transfer; American peace is not issued. Both puppet and protected-neutral outcomes have been checked.']
    for p in PROGRAMMES:
        lines += ['', '## '+p['title'], '', p['story'], '', '| Choice | Full upfront bill | Wait |', '| --- | --- | --- |']
        for c in p['choices']:
            bill=', '.join(f'{c[k]:g} {label}' for k,label in [('cash','money'),('stock','supplies'),('mp','manpower'),('metal','metal'),('energy','energy'),('oil','oil')] if c[k])
            lines.append('| '+c['label']+' | '+bill+' | '+str(c['days'])+' days |')
    Path(path).write_text('\n'.join(lines)+'\n', encoding='utf-8')

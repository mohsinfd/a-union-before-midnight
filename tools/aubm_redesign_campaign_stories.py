"""Four finite non-Japanese campaigns, with player-owned start and ending.

No automatic wars, foreign concessions, delayed callbacks or perpetual menus.
One expedition can be open at a time. Abandoning spends the opportunity, so
restarting cannot farm the opening benefit. This is staged, not native-tested.
"""
from pathlib import PurePosixPath
from dh_save_spans import parse
from aubm_redesign_route_finish import CURRENT
from aubm_redesign_focus_outcomes import deployed, control

MARKER = '# AUBM_STAGED_CAMPAIGN_STORIES_V1'
MODULE = '51_bespoke_route_arcs.txt'
NEW_EVENT_IDS = tuple(range(9398500, 9398508))
BUSY = 'ind_story_campaign_open'
BASE = 'ai = no exists = IND NOT = { ispuppet = IND } year = 1937'


def flag(name): return 'flag = ' + name
def absent(name): return 'NOT = { flag = ' + name + ' }'
def war(tag): return f'war = {{ country = IND country = {tag} }}'
def peace(tag): return 'NOT = { ' + war(tag) + ' }'
def cmd(effect): return 'command = { type = ' + effect + ' }'
def setflag(name): return cmd('setflag which = ' + name)
def clear(name): return cmd('clrflag which = ' + name)
def all_of(*rules): return 'AND = { ' + ' '.join(rules) + ' }'
def any_of(*rules): return 'OR = { ' + ' '.join(rules) + ' }'


GER_BROKEN = any_of('NOT = { exists = GER }',
    all_of('exists = GER', 'NOT = { control = { province = 163 data = GER } }',
           'NOT = { control = { province = 195 data = GER } }'))
REGIONAL_WAR = any_of(*(war(t) for t in ('PER', 'AFG', 'IRQ', 'ENG')))
REGIONAL_WIN = any_of(*(flag('ind_aubm_regional_victory_' + t) for t in ('per', 'afg', 'irq')),
                      flag('ind_aubm_britain_limited_victory'))

CAMPAIGNS = [
    dict(key='mediterranean', family='allied', id=9398500,
         title='The Monsoon Soldiers Go West',
         desc='Letters from the Mediterranean ask when the Indian army is coming. Delhi can send a fighting expedition or take responsibility for the sea road. Pay 300 money and 800 supplies to begin. The expedition needs six Indian land divisions in both Rome and Athens; the sea road needs six in both Suez and Rome. Indian or allied control counts. No war is declared. Only one new campaign can be open.',
         start=any_of(war('GER'), war('ITA')),
         choices=('Send the fighting expedition', 'Keep the Mediterranean road open'),
         goals=(all_of(deployed(419), deployed(377)), all_of(deployed(900), deployed(419))),
         ending='The Long Road Home',
         enddesc='Once your deployment objective is met, decide what comes home. A permanent transport service gives +4 transport capacity. A veterans programme returns 35 manpower and cuts dissent by 3. Expedition: six divisions each in Rome and Athens. Sea road: six each in Suez and Rome. Keep fighting Germany or Italy. Indian or allied control counts; foreign territory does not become Indian.',
         rewards=(('Keep the transport service: +4 TC', ('tc_mod value = 4',)),
                  ('Bring veterans home: +35 manpower, -3 dissent', ('manpowerpool value = 35', 'dissent value = -3')))),
    dict(key='eurasian', family='german', id=9398502,
         title='The Maps on the German Table',
         desc='Berlin draws arrows beyond the Caucasus. Indian officers draw the supply roads back home. Pay 300 money and 800 supplies. Choose the oil road: Baku, Astrakhan and Stalingrad; or the inland road: Tashkent and Omsk. India must control every objective while fighting the USSR. If Germany loses Berlin and Vienna, a smaller Indian foothold unlocks a costly rescue ending. No German claim is settled here.',
         start=war('SOV'), choices=('Take the oil road', 'Build the inland supply road'),
         goals=(all_of(control(713), control(706), control(663)), all_of(control(1103), control(1138))),
         ending='Our War Does Not End in Berlin',
         enddesc='Oil road: control Baku, Astrakhan and Stalingrad. Inland road: Tashkent and Omsk. Keep fighting the USSR. Victory gives a choice: +4 transport capacity and 1,500 oil, or two factories each in Bombay and Calcutta. If Germany loses Berlin and Vienna first, hold Baku or Tashkent to rescue the expedition: 500 money for 20 manpower, no victory reward. India must own and control both cities for factories.',
         rewards=(('Keep the road: +4 TC, +1,500 oil', ('tc_mod value = 4', 'oilpool value = 1500')),
                  ('Bring industry home: four factories', ('construct which = ic where = 1517 value = 2', 'construct which = ic where = 1447 value = 2')))),
    dict(key='reconstruction', family='soviet', id=9398504,
         title='What Comes After the Red Flags?',
         desc='Indian engineers travelling with the anti-fascist armies see ruined stations and empty workshops. Pay 300 money and 800 supplies to prepare for the peace. Choose a scientific mission in Berlin and Vienna, or railway teams in Rome and Athens: six Indian land divisions in each city, under Indian or allied control. Finish while fighting Germany, or after peace if Germany no longer exists.',
         start=war('GER'), choices=('Send the scientific mission north', 'Send railway teams to the Mediterranean'),
         goals=(all_of(deployed(163), deployed(195)), all_of(deployed(419), deployed(377))),
         ending='The Engineers Ask Who Is in Charge',
         enddesc='Deploy six Indian divisions each in Berlin and Vienna for science, or Rome and Athens for railways. Remain a Soviet partner and fight Germany, unless Germany no longer exists. Then choose Indian laboratories: +3 research, costing 500 money and 1 dissent; or military workshops: +4 supply production, costing 1,500 supplies. Neither changes your alliance or grants Moscow authority over Indian peace terms.',
         rewards=(('Indian laboratories: $500, +1 dissent; +3 research', ('money value = -500', 'dissent value = 1', 'research_mod value = 3')),
                  ('Military workshops: 1,500 supplies; +4 supply output', ('supplies value = -1500', 'industrial_modifier which = supplies value = 4')))),
    dict(key='western', family='sovereign', id=9398506,
         title='An Ocean Without a Patron',
         desc='Delhi needs no great-power invitation to look west. Pay 300 money and 800 supplies. The sea road requires Indian control of Aden, Suez and Mombasa while at war. The landward alternative requires recorded victories over both Persia and Afghanistan, followed by peace with both. Neither choice declares war, transfers territory or makes a neighbour an Indian puppet.',
         start=REGIONAL_WAR, choices=('Build the western sea road', 'Settle the continental frontier'),
         goals=(all_of('atwar = yes', control(1053), control(900), control(842)),
                all_of(flag('ind_aubm_regional_victory_per'), flag('ind_aubm_regional_victory_afg'), peace('PER'), peace('AFG'))),
         ending='The Shipping Lists Arrive in Delhi',
         enddesc='Stay independent. Sea road: control Aden, Suez and Mombasa while at war. Frontier: recorded victories over Persia and Afghanistan, then peace with both. Success offers +5 transport capacity for 1,000 oil, or two factories each in Bombay and Calcutta for 600 money. India must own and control both factory cities. No foreign government changes here. The next order comes from Delhi.',
         rewards=(('Run the network: 1,000 oil; +5 TC', ('oilpool value = -1000', 'tc_mod value = 5')),
                  ('Place Indian orders: $600; four factories', ('money value = -600', 'construct which = ic where = 1517 value = 2', 'construct which = ic where = 1447 value = 2')))),
]


def names(c):
    root = 'ind_story_' + c['key']
    return root + '_started', root + '_pending', root + '_done', (root + '_a', root + '_b')


def affordability(effects):
    rules = []
    stocks = {'money': 'money', 'supplies': 'supplies', 'oilpool': 'oil'}
    for effect in effects:
        e = parse('type = ' + effect)
        kind, value = e.get('type'), int(e.get('value'))
        if kind in stocks and value < 0:
            rules.append(stocks[kind] + ' = ' + str(-value))
        if kind == 'construct':
            p = e.get('where')
            rules += [f'owned = {{ province = {p} data = IND }}', f'control = {{ province = {p} data = IND }}']
    return ' '.join(rules)


def start_gate(c):
    started, _, _, _ = names(c)
    return ' '.join((BASE, CURRENT[c['family']], c['start'], absent(started), absent(BUSY)))


def victory_gate(c):
    started, pending, done, choices = names(c)
    context = CURRENT[c['family']]
    # A German collapse must not erase an Indian campaign already undertaken.
    if c['family'] == 'german':
        context = any_of(all_of(context), all_of(GER_BROKEN, peace('GER'), war('SOV')))
    active_war = {'allied': any_of(war('GER'), war('ITA')),
                  'german': war('SOV'),
                  'soviet': any_of(war('GER'), 'NOT = { exists = GER }'),
                  'sovereign': 'exists = IND'}[c['family']]
    goals = [all_of(flag(choice), absent(choices[1-i]), c['goals'][i]) for i, choice in enumerate(choices)]
    return ' '.join((BASE, flag(started), flag(pending), absent(done), context, active_war, any_of(*goals)))


def rescue_gate(c):
    started, pending, done, _ = names(c)
    return ' '.join((BASE, flag(started), flag(pending), absent(done), GER_BROKEN,
                     peace('GER'), war('SOV'), any_of(control(713), control(1103)), 'money = 500',
                     'NOT = { AND = { ' + victory_gate(c) + ' } }'))


def action(label, guard, effects):
    return 'action = { name = "' + label + '" ai_chance = 0 trigger = { ' + guard + ' }\n' + '\n'.join(effects) + '\n}'


def event(eid, title, desc, visible, ready, aa):
    # Manual decisions only: no polling dates, automatic header trigger, or
    # queued event command. Every effect-bearing action rechecks its context.
    return '\n'.join(('event = {', f'id = {eid} country = IND random = no persistent = yes',
        'name = "' + title + '"', 'desc = "' + desc + '"',
        'style = 2 picture = "india_v3_armed_forces"',
        'decision = { ' + visible + ' }', 'decision_trigger = { ' + ready + ' }', *aa, '}'))


def render(c):
    started, pending, done, choices = names(c)
    gate = start_gate(c)
    paid = gate + ' money = 300 supplies = 800'
    opening = [action(label, paid, [setflag(started), setflag(pending), setflag(BUSY), setflag(choices[i]),
                  cmd('money value = -300'), cmd('supplies value = -800')]) for i, label in enumerate(c['choices'])]
    opening.append(action('Not now - keep this campaign available', 'ai = no', []))
    finish = [setflag(done), clear(pending), clear(BUSY)]
    ending = [action(label, victory_gate(c) + ' ' + affordability(effects),
                     [*map(cmd, effects), *finish]) for label, effects in c['rewards']]
    if c['family'] == 'german':
        ending.append(action('Rescue the expedition: $500; +20 manpower', rescue_gate(c),
                      [cmd('money value = -500'), cmd('manpowerpool value = 20'), *finish]))
    visible = 'ai = no exists = IND ' + flag(pending) + ' ' + absent(done)
    ending += [action('Leave the plan open - no cost', 'ai = no', []),
               action('End this campaign permanently - no refund', visible, finish)]
    return (event(c['id'], c['title'], c['desc'], gate, paid, opening) + '\n\n' +
            event(c['id'] + 1, c['ending'], c['enddesc'], visible, visible, ending))


def transform(files):
    output = dict(files)
    matches = [p for p in files if PurePosixPath(p.replace('\\', '/')).name == MODULE]
    if len(matches) != 1: raise ValueError('Campaign stories need one loaded module 51')
    path = matches[0]
    addition = '\n\n'.join(render(c) for c in CAMPAIGNS)
    if MARKER in files[path]:
        if addition not in files[path]: raise ValueError('Marked campaign story drift')
    else:
        ids = {int(e.get('id')) for text in files.values() for e in parse(text).all('event')}
        if ids.intersection(NEW_EVENT_IDS): raise ValueError('Campaign story ID collision')
        output[path] += '\n\n' + MARKER + '\n' + addition + '\n'
    records = {eid: [dict(dimension='campaign_stories', status='reviewed', engine_tested=False,
                detail='Finite optional non-Japanese campaign; one active card; costs, objectives and once-only ending rechecked.')]
               for eid in NEW_EVENT_IDS}
    return output, records

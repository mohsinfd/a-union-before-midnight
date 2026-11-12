"""Append-only continental campaign encounters for human Japan versus AI USA.

Append last, before the builder refreshes IDs. Existing war/peace menus and
territorial ownership are never changed. No installation or import side effect.
"""
from catalog import *

REPORT = {}
PORTS = ((1886, 'San Diego'), (1887, 'Los Angeles'), (1889, 'San Francisco'), (1874, 'Seattle'))
COAST_HUBS = ((1908, 'Denver'), (1896, 'Salt Lake City'), (1900, 'Phoenix'), (1914, 'Kansas City'))
INLAND_HUBS = ((1914, 'Kansas City'), (1832, 'Chicago'), (1809, 'Washington'))
INFANTRY_MP = 13
WAVE_SIZE = 6
WAVE_SUPPLIES = 2400


def no(gate): return 'NOT = { AND = { ' + gate + ' } }'
def f(name): return 'flag = JX_USC_' + name.removeprefix('USC_')
def mark(name): return flag('USC_' + name.removeprefix('USC_'))
def unmark(name): return clear('USC_' + name.removeprefix('USC_'))


def coastline():
    return 'OR = { ' + ' '.join(control(p) for p, _ in PORTS) + ' }'


def human_front():
    return active() + ' ai = USA year = 1941 exists = USA ' + war('USA') + ' ' + coastline()


def us_front():
    # The documented ai=TAG predicate checks that country's controller, unlike
    # ai=no, which would test the American receiver itself.
    return ('ai = yes year = 1941 NOT = { ai = JAP ispuppet = JAP } flag = JX_ACTIVE exists = JAP exists = USA '
            + war('USA') + ' ' + coastline())


def age(days): return f'event = {{ id = @usc_landing days = {days} }}'


def guarded_actions(gate, choices):
    return [Action(label, rewards, gate=gate, chance=100 if i == 0 else 0)
            for i, (label, rewards) in enumerate(choices)]


def milestone(key, title, text, gate, choices):
    live = human_front() + ' ' + gate + ' NOT = { ' + f(key.upper() + '_DONE') + ' }'
    actions = guarded_actions(live, [(label, commands + [mark(key.upper() + '_DONE')]) for label, commands in choices])
    event(key, title, text, year=1941, offset=3, persistent=True,
          gate=live, actions=actions, module='us_campaign_content', art='pacific')


def project(key, title, text, context, days, cash, stock, choices):
    live = human_front() + ' ' + context + ' ' + no_state(key)
    actions = []
    transaction = 'flag = JX_' + key + '_PENDING NOT = { flag = JX_' + key + '_DONE }'
    due = f'event = {{ id = @{key} days = {days} }}'
    for i, (label, rewards) in enumerate(choices):
        selected = key + '_CHOICE_' + str(i)
        pending = transaction + ' flag = JX_' + selected + ' ' + due
        terminal = [clear(key + '_PENDING'), clear(selected)]
        finish = key + '_finish_' + str(i)
        actions.append(Action(label, [money(-cash), supplies(-stock), flag(key + '_PENDING'), flag(selected), later(finish, days)],
                              gate=live + f' money = {cash} supplies = {stock}', chance=100 if i == 0 else 0))
        event(finish, title + ' - reserve ready',
              text + ' The payment was already taken. The same front and milestone conditions are checked again before delivery.',
              triggered=True, module='us_campaign_content', art='army', actions=[
                  Action('Receive the selected campaign reserve', rewards + [flag(key + '_DONE')] + terminal,
                         gate=pending + ' ' + human_front() + ' ' + context, chance=100),
                  Action('The front no longer qualifies; recover both payments',
                         [money(cash), supplies(stock)] + terminal + [flag(key + '_WAIT'), later(key + '_return', 90)],
                         gate=pending + ' ' + no(human_front() + ' ' + context)),
                  Action('Recover the superseded unselected programme payment',
                         [money(cash), supplies(stock), clear(key + '_PENDING'), flag(key + '_WAIT'), later(key + '_return',90)],
                         gate=transaction+' '+due+f' NOT = {{ flag = JX_{key}_CHOICE_0 flag = JX_{key}_CHOICE_1 }}'),
                  Action('', [], gate='OR = { '+no(transaction)+' '+no(due)+f' flag = JX_{key}_CHOICE_{1-i}'+' }'),
              ])
    actions += [Action('Leave this campaign choice available', [], gate=live),
                Action('Dismiss this campaign programme permanently', [flag(key + '_DISMISSED')], gate=live)]
    event(key, title, text, year=1941, gate=live, decision=True, persistent=True,
          actions=actions, module='us_campaign_content', art='army')
    event(key + '_return', title + ' - available again', '', triggered=True,
          actions=[Action('', [clear(key + '_WAIT')])], module='us_campaign_content')


def american_wave(key, title, description, context, hubs):
    live = us_front() + ' ' + context + ' NOT = { ' + f(key.upper() + '_DONE') + ' }'
    usable = 'OR = { technology = 1110 technology = 1100 }'
    funded = f'manpower = {INFANTRY_MP * WAVE_SIZE} supplies = {WAVE_SUPPLIES} ' + usable
    previous = []
    actions = []
    for p, city in hubs:
        site = owned(p, 'USA') + ' ' + control(p, 'USA')
        priority = ' '.join(no(g) for g in previous)
        gate = live + ' ' + funded + ' ' + site + ' ' + priority
        commands = [cmd('manpowerpool', value=-INFANTRY_MP * WAVE_SIZE), supplies(-WAVE_SUPPLIES),
                    cmd('add_corps', which='"Continental Reserve - ' + city + '"', value='land', where=p)]
        for i in range(1, WAVE_SIZE + 1):
            name = '"Continental Reserve Division ' + str(i) + ' - ' + city + '"'
            commands += [cond('technology = 1110', cmd('add_division', which=name, value='infantry', when=10)),
                         cond('NOT = { technology = 1110 } technology = 1100', cmd('add_division', which=name, value='infantry', when=9))]
        commands += [mark(key.upper() + '_FORMED'), mark(key.upper() + '_DONE'), later(key + '_notice', 1)]
        actions.append(Action('Form six reserve divisions at ' + city, commands, gate=gate, chance=100))
        previous.append(site)
    any_site = 'OR = { ' + ' '.join('AND = { ' + site + ' }' for site in previous) + ' }'
    actions.append(Action('Authorize a limited recruitment and equipment budget instead',
                          [cmd('manpowerpool', value=40), supplies(2000), mark(key.upper() + '_BUDGET'), mark(key.upper() + '_DONE'), later(key + '_notice', 1)],
                          gate=live + ' ' + no(funded + ' ' + any_site), chance=100))
    event(key, title, description, country='USA', gate=live, year=1941, offset=3,
          persistent=True, actions=actions, module='us_campaign_content', art='army')
    # Explicit Japanese notice describes which concrete response actually ran.
    notice_live = human_front() + ' ' + f(key.upper() + '_DONE') + ' NOT = { ' + f(key.upper() + '_TOLD') + ' }'
    event(key + '_notice', title,
          'American recruitment is responding to the invasion. If its budget and a safe staging city were available, six infantry divisions formed there, costing America 78 manpower and 2,400 supplies. Otherwise America authorized a finite 40-manpower and 2,000-supply budget instead; no formations were created. The divisions use the 1939 model only with American technology 1110, otherwise researched 1936 equipment. This response can occur once. Existing American forces remain in service.',
          triggered=True, module='us_campaign_content', art='army', actions=[
              Action('Six American reserve divisions have entered service', [mark(key.upper() + '_TOLD')],
                     gate=notice_live + ' ' + f(key.upper() + '_FORMED'), chance=100),
              Action('America funded recruitment and stocks; no new divisions yet', [mark(key.upper() + '_TOLD')],
                     gate=notice_live + ' ' + f(key.upper() + '_BUDGET'), chance=100),
              Action('', [], gate=no(notice_live)),
          ])


def append_events():
    if REPORT:
        return REPORT
    before = {e.key: e.id for e in EVENTS}
    captured = 'OR = { ' + ' '.join('AND = { ' + owned(p, 'USA') + ' ' + control(p) + ' }' for p, _ in PORTS) + ' }'
    milestone('usc_landing', 'A foothold on the American mainland',
        'Japanese troops have taken San Diego, Los Angeles, San Francisco or Seattle while America still owns the port. Choose what the captured stores support: 3,500 supplies, or 1,500 supplies and 1,000 oil. These are finite national stocks; normal convoys must carry them forward and ordinary storage limits apply. America can organize a continental reserve response. Holding one port does not satisfy the existing national surrender or Pacific armistice requirements. This opening reward is paid once, including after a lost port is recaptured.',
        captured, [('Secure the equipment and ration stores', [supplies(3500)]),
                   ('Prioritise captured fuel and service stores', [supplies(1500), cmd('oilpool', value=1000)])])

    american_wave('usc_coast_response', 'America calls a continental defence reserve',
        'A Japanese landing threatens the continental United States. Six reserve infantry divisions cost 78 American manpower and 2,400 supplies and require a safe American-owned, American-controlled staging city. Prefer Denver, Salt Lake City, Phoenix, then Kansas City. Use researched 1939 equipment, or researched 1936 equipment. If manpower, supplies, research or a safe city are missing, authorize one finite 40-manpower and 2,000-supply budget instead. This neither changes wars nor replaces the existing American army.',
        f('USC_LANDING_DONE'), COAST_HUBS)

    project('usc_replacements', 'A replacement reserve for the American campaign',
        'After the first mainland port is secured, fund a reserve for the forces already fighting there. Pay 200 money and 2,500 supplies; work takes 60 days. Choose a finite 50-manpower recruitment reserve for normal reinforcement and production, or a 6,000-supply operating reserve. Neither creates divisions or duplicates the separate bridgehead convoy programme. The American war, at least one named coastal port and the opening landing milestone must still qualify at delivery, or both payments return. Choosing either leaves later campaign and peace choices available.',
        f('USC_LANDING_DONE'), 60, 200, 2500,
        [('Recruit continental-campaign replacements', [cmd('manpowerpool', value=50)]),
         ('Prepare equipment, rations and repair stocks', [supplies(6000)])])

    california = ' '.join(control(p) for p in (1886, 1887, 1888, 1889)) + ' ' + age(90)
    milestone('usc_california', 'The California corridor is in Japanese hands',
        'Japan holds San Diego, Los Angeles, Sacramento and San Francisco, at least 90 days after the first mainland landing. Connecting these centres makes captured stores usable as one finite campaign reserve. Choose 12,000 energy, 8,000 metal and 1,500 rares for industry, or 6,000 supplies and 1,500 oil for current operations. Stocks enter Japan\'s national pools and still need shipping; the cities remain with their legal owners. This is not an annexation or a peace settlement, and it awards nothing a second time.',
        california, [('Recover industrial feedstocks', [cmd('energypool', value=12000), cmd('metalpool', value=8000), cmd('rarematerialspool', value=1500)]),
                     ('Recover the coastal operating reserve', [supplies(6000), cmd('oilpool', value=1500)])])

    interior = 'OR = { ' + ' '.join(control(p) for p in (1893, 1896, 1908)) + ' }'
    american_wave('usc_inland_response', 'America organizes a second continental reserve',
        'At least 60 days after the first landing, Japanese control of Las Vegas, Salt Lake City or Denver triggers a second and final six-division emergency reserve. It costs another 78 American manpower and 2,400 supplies, deploying only at American-owned and controlled Kansas City, Chicago or Washington. Researched 1939 infantry is preferred; researched 1936 infantry is the fallback. Missing resources, research or a safe city instead authorize one finite 40-manpower and 2,000-supply budget. No units appear in enemy territory.',
        f('USC_LANDING_DONE') + ' ' + age(60) + ' ' + interior, INLAND_HUBS)

    project('usc_commitment', 'Push inland or sustain limited aims?',
        'The American campaign has lasted 180 days and Japan still holds a listed Pacific coast port. Pay 250 money and 4,000 supplies for a 60-day reserve. Preparing a larger inland campaign delivers 50 manpower and 4,000 supplies; sustaining a limited coastal position delivers 8,000 supplies and 2,000 oil. These are finite recruitment or operating stocks, not a permanent strategy selection. Neither starts peace, changes borders, cancels later replacements nor disables the existing surrender and armistice offers. The same war and coastal foothold must still exist at delivery or both payments return.',
        f('USC_LANDING_DONE') + ' ' + age(180), 60, 250, 4000,
        [('Prepare recruits and equipment for the inland campaign', [cmd('manpowerpool', value=50), supplies(4000)]),
         ('Sustain the coastal forces and keep limited aims possible', [supplies(8000), cmd('oilpool', value=2000)])])

    enduring = us_front() + ' ' + f('USC_LANDING_DONE') + ' ' + age(180) + ' NOT = { ' + f('ENDURANCE_DONE') + ' }'
    event('usc_endurance', 'America funds a long continental war',
        'After 180 days of a continuing Japanese mainland foothold, America releases one finite continental recruitment and procurement reserve: 60 manpower, 9,000 supplies and 5,000 oil. No divisions, industrial modifiers, free daily resources or new wars are created. This is a single emergency budget, not an annually repeating rescue.',
        country='USA', gate=enduring, year=1941, offset=5, persistent=True, module='us_campaign_content', art='industry',
        actions=[Action('Release the finite continental reserve', [cmd('manpowerpool', value=60), supplies(9000), cmd('oilpool', value=5000), mark('ENDURANCE_DONE'), later('usc_endurance_notice', 1)], gate=enduring, chance=100)])
    notice = human_front() + ' ' + f('ENDURANCE_DONE') + ' NOT = { ' + f('ENDURANCE_TOLD') + ' }'
    event('usc_endurance_notice', 'America is funding a longer war',
        'The American emergency budget has released 60 manpower, 9,000 supplies and 5,000 oil, once. It creates no divisions immediately, but the existing army can reinforce and continue operations. Japan\'s 180-day commitment reserve is an optional decision. Choosing limited aims leaves the existing armistice and national-defeat requirements unchanged; neither peace offer is automatically granted by this notice.',
        triggered=True, module='us_campaign_content', art='army', actions=[Action('Review the campaign and its remaining objectives', [mark('ENDURANCE_TOLD')], gate=notice, chance=100), Action('', [], gate=no(notice))])

    milestone('usc_plains', 'The American staging belt has been breached',
        'Japan holds Denver and Kansas City at least 180 days after the first American landing. Those staging centres provide a final finite captured-stock reward: 15,000 energy, 6,000 metal and 2,000 rares, or 9,000 supplies and 4,500 oil. Choose the stores your campaign can use and check national storage limits before taking fuel. Nothing transfers provincial ownership, cores or surviving American units. The existing national surrender still requires its own military conditions. This reward cannot repeat after recapture.',
        control(1908) + ' ' + control(1914) + ' ' + age(180),
        [('Recover the inland industrial stocks', [cmd('energypool', value=15000), cmd('metalpool', value=6000), cmd('rarematerialspool', value=2000)]),
         ('Recover the inland campaign fuel and supply stocks', [supplies(9000), cmd('oilpool', value=4500)])])

    assert all(next(e.id for e in EVENTS if e.key == key) == value for key, value in before.items())
    added = [e for e in EVENTS if e.key not in before]
    assert all(len(e.desc) < 1100 for e in added), 'Keep continental event copy readable'
    REPORT.update(added=[e.key for e in added], substantive=['usc_landing','usc_coast_response','usc_replacements','usc_california','usc_inland_response','usc_commitment','usc_endurance','usc_plains'],
                  ids={e.key:e.id for e in added},
                  ports=PORTS, coastal_hubs=COAST_HUBS, inland_hubs=INLAND_HUBS,
                  infantry_models={'1939':10,'1936':9}, manpower_per_division=INFANTRY_MP, max_reserve_divisions=12)
    return REPORT

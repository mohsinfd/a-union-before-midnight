"""BALANCE1: bounded fresh-campaign playtest repairs, applied to installed text.

No I/O, deployment, save migration, economy or world-AI changes. Existing event
flags and diplomacy guards survive. This is script validation, not native QA.
"""
import json
import re
from dh_save_spans import Node, parse, replace, walk

MARKER = '# AUBM_BALANCE1_PLAYTEST_V1'
NEW_IDS = {9318100, 9318101, 9318102, 9318103}
LOCKED_IDS = (9057, 9058, 9060, 9061, 9063, 9065, 9067, 9069)
# Explicit zero-based models verified against starting Indian technology.
# Avoid relying on undocumented add_division when = -1 model selection.
AIRFIELD_MODELS = {'interceptor': 7, 'tactical_bomber': 5,
                   'transport_plane': 0, 'garrison': 4, 'militia': 4}
NORTH_PATH = 'db/events/aubm_v4/42_wartime_theatres.txt'
READY = 'ind_balance1_north_held'
PENDING = 'ind_balance1_north_counting'
BROKEN = 'ind_balance1_north_broken'
UNLOCKED = 'ind_balance1_state_forces_released'
NORTH_GATE = '''OR = {
 AND = { control = { province = 713 data = IND } control = { province = 706 data = IND } control = { province = 663 data = IND } }
 AND = { control = { province = 1103 data = IND } control = { province = 1099 data = IND } control = { province = 504 data = IND } control = { province = 1151 data = IND } }
}'''
HOLD_CONTEXT = 'war = { country = IND country = SOV }\n' + NORTH_GATE


def cmd(kind, **args):
    return 'command = { type = ' + kind + ''.join(f' {k} = {v}' for k, v in args.items()) + ' }'


def unlock_commands():
    return '\n'.join(f'command = {{ trigger = {{ division_exists = {{ type = 12700 id = {i} }} }} type = unlock_division which = 12700 value = {i} }}' for i in LOCKED_IDS) + '\n' + cmd('setflag', which=UNLOCKED)


class Edit:
    def __init__(self, text):
        self.text, self.e = text, parse(text).all('event')[0]
        self.edits = []

    def set(self, node, key, value):
        f = node.field(key)
        self.edits.append((f.value_start, f.end, json.dumps(value) if isinstance(value, str) else str(value)))

    def body(self, node, value):
        self.edits.append((node.start, node.end, value))

    def append(self, node, value):
        self.edits.append((node.end - 1, node.end - 1, '\n' + value + '\n'))

    def action(self, letter):
        return self.e.get('action_' + letter)

    def number(self, letter, kind, value, which=None):
        matches = [c for c in self.action(letter).all('command') if c.get('type') == kind and (which is None or c.get('which') == which)]
        if len(matches) != 1:
            raise ValueError(f'Expected one {self.e.get("id")}/{letter}/{kind}/{which}, got {len(matches)}')
        self.set(matches[0], 'value', value)

    def label(self, letter, value):
        self.set(self.action(letter), 'name', value)

    def desc(self, value):
        assert len(value) <= 520
        self.set(self.e, 'desc', value)

    def finish(self):
        self.append(self.e, MARKER)
        return replace(self.text, self.edits)


def political(eid, x):
    """Reduce punitive dissent gaps; rewards are mostly one-off or specialist."""
    if eid == 9270101:
        x.number('a', 'dissent', 1); x.number('c', 'dissent', 1)
        x.number('c', 'manpowerpool', -5); x.number('c', 'money', 350)
        x.label('a', 'Land reform: recruits and roads; +1 dissent')
        x.label('b', 'Irrigation: better roads and -2 dissent')
        x.label('c', 'Property settlement: 350 money; +1 dissent')
        x.desc('The villages need land, water and credit. Land reform brings 45 recruits and two roads, but causes unrest. Irrigation costs more and eases dissent while improving four roads. A property settlement raises 350 money, but loses five recruits and adds one dissent. Choose which burden India can carry.')
    elif eid == 9271301:
        x.number('b', 'dissent', 0); x.number('b', 'money', -100)
        x.label('b', 'Recruit provincial administrators: manpower and transport')
    elif eid == 9271302:
        x.number('a', 'dissent', -2); x.number('b', 'dissent', 1)
        x.number('b', 'money', 150)
        x.desc('The princes can join by agreement or by law. Guarantees cost 200 money, ease dissent by two and bring roads and 15 recruits. Statutory integration brings 150 money, 30 recruits and a more professional army, but consumes 300 supplies and adds one dissent. Both complete accession.')
    elif eid == 9271303:
        x.number('a', 'dissent', -2); x.number('b', 'dissent', 0)
        x.label('a', 'Plural safeguards: -2 dissent; 150 money')
        x.label('b', 'Common civil code: 30 recruits and research; 75 money')
        x.desc('Delhi must make citizenship work across faiths and provinces. Plural safeguards buy immediate calm and improve Afghan relations. A common civil code brings 30 recruits and one research point, without a dissent penalty. Both allow the later citizenship bill; neither changes India\'s alliances.')
    elif eid == 9271304:
        x.number('a', 'dissent', 0); x.number('a', 'manpowerpool', 45)
        x.desc('Ambedkar wants equal access to schools, public service and the army. Enforceable rights cost 200 money and bring 45 recruits without added dissent. Provincial grants cost 150 money, bring 15 recruits and ease dissent by one. One choice favours recruitment; the other immediate calm.')
    elif eid == 9271305:
        x.number('a', 'dissent', -2); x.number('b', 'dissent', 0)
        x.append(x.action('b'), cmd('manpowerpool', value=20))
        x.desc('Burma stays in the Union under either plan. Autonomy costs 225 money, eases dissent by two and improves roads and transport capacity. Shared eastern command costs 300 supplies, brings 20 recruits, strengthens Rangoon\'s road and moves India toward intervention. Neither choice releases Burma.')
    elif eid == 9280300:
        x.number('b', 'dissent', -1)
        x.append(x.action('b'), cmd('manpowerpool', value=10))
        x.append(x.action('c'), cmd('dissent', value=-1))
        x.desc('Geneva offers influence, not an alliance. Collective security improves western relations and intervention. Speaking for colonial peoples brings ten volunteers but angers Britain and France. Guarding sovereignty brings 150 money and reduces intervention. Each choice eases dissent by one; all later alliances remain open.')
    elif eid == 9280301:
        x.number('a', 'dissent', -1)
        x.number('b', 'supplies', -250)
        x.number('c', 'dissent', 0)
        x.append(x.action('c'), cmd('money', value=120))
        x.desc('London offers three ways to settle the break. Commercial terms buy better relations and one less dissent for 120 money. Defence cooperation costs 100 money and 250 supplies for staff support and intervention. A clean break keeps 120 money and increases freedom, but damages British relations. No choice joins a bloc.')


def military(eid, x):
    if eid == 9270300:
        x.number('a', 'dissent', 0)
        x.number('c', 'dissent', 1)
        x.append(x.action('b'), cmd('morale', which='infantry', value=2))
        x.label('b', 'Two infantry, one HQ and better infantry recovery')
        x.label('c', 'Two cavalry and two infantry; armoured research staff')
        x.desc('Citizen service brings four infantry divisions and a net 36 recruits, but reduces professionalism. The professional force brings two infantry, an HQ and better infantry morale. The mobile force brings two cavalry and two infantry with specialist equipment; these are not tank divisions. Choose one force, not a permanent diplomatic route.')
    elif eid == 9271202:
        x.append(x.action('a'), cmd('max_organization', which='hq', value=3))
        x.number('b', 'money', -175)
        x.append(x.action('b'), cmd('morale', which='bergsjaeger', value=3) + '\n' + cmd('morale', which='marine', value=3))
        x.label('a', 'General staff: research and stronger headquarters')
        x.label('b', 'Branch schools: mountain and marine recovery')
        x.desc('The general staff school improves research, headquarters organisation and the Delhi-Quetta roads. Branch schools cost less money, improve three training roads and give mountain troops and marines three morale. Quetta-Delhi\'s mountain research team is available under either choice.')
    elif eid == 9271203:
        x.number('b', 'domestic', 1, 'professional_army')
        x.number('b', 'money', -100); x.number('b', 'supplies', -300)
        x.append(x.action('b'), cmd('morale', which='infantry', value=2))
        x.append(x.action('a').get('trigger'), 'money = 250 supplies = 650')
        x.append(x.action('b').get('trigger'), 'money = 100 supplies = 300')
        x.append(x.e.get('trigger'), 'OR = { AND = { money = 250 supplies = 650 manpower = 45 } AND = { money = 100 supplies = 300 manpower = 20 } }')
        x.label('b', 'Two infantry and one HQ; professional training')
        x.desc('The large programme delivers four infantry and an HQ for 250 money, 650 supplies and 45 manpower. The cadre programme delivers two infantry and an HQ for 100 money, 300 supplies and 20 manpower; it improves professionalism and infantry morale. Smaller now means a stronger training base, not a penalty.')
    elif eid == 9271001:
        x.append(x.action('a'), cmd('max_organization', which='air', value=2))
        x.label('a', 'Central schools: trained crews and +2 air organisation')
        x.label('b', 'Provincial reserve: more bases and eight recruits')
        x.desc('Central schools cost 175 money, 250 supplies and five manpower. They improve Bangalore and Poona airbases and add two air organisation. Provincial clubs cost 200 supplies, bring eight recruits and improve Calcutta, Bombay and Lahore bases. Training quality or a wider network: neither delivers aircraft.')
    elif eid == 9280111:
        x.number('a', 'dissent', 0); x.number('a', 'manpowerpool', -6)
        x.number('b', 'manpowerpool', 15)
        x.number('c', 'manpowerpool', -10)
        x.label('a', 'One army: organisation and professional service')
        x.label('b', 'Territorial army: recruits and faster recovery')
        x.label('c', 'Cadre army: save money, train a smaller force')
        x.desc('Every option releases the inherited state troops for field service. One army gains four organisation and ten annual recruits. Territorials gain three morale, 15 immediate and 15 annual recruits. A cadre army returns 250 money and gains five organisation, but takes ten manpower and brings only five annual recruits.')
        for letter in 'abc': x.append(x.action(letter), unlock_commands())


def airfield(x):
    # All packages have aircraft, bases and two guards. No mobile militia windfall.
    packs = [
        ('a', 350, 900, 27, 'Defended hubs: one interceptor and two AA guards', 'garrison', 'anti_air', ['interceptor'], [1459, 1447], 'ind_v4_airfield_guard_battalions'),
        ('b', 450, 1200, 27, 'Forward air group: interceptor, bomber and two guards', 'militia', 'police', ['interceptor', 'tactical_bomber'], [1459, 1517], 'ind_v4_mobile_airfield_security'),
        ('c', 250, 700, 23, 'Dispersed bases: one transport wing and two guards', 'militia', None, ['transport_plane'], [1459, 1533], 'ind_v4_provincial_airfield_guards'),
    ]
    visible = x.e.get('decision')
    x.append(visible, 'owned = { province = 1459 data = IND } control = { province = 1459 data = IND }')
    gate = '{ OR = { ' + ' '.join(f'AND = {{ money = {m} supplies = {s} manpower = {mp} }}' for _, m, s, mp, *_ in packs) + ' } }'
    x.body(x.e.get('decision_trigger'), gate)
    x.desc('Early aircraft, usable bases and ground guards must arrive together. Choose a ready-to-deploy package: defended hubs, a forward combat group, or dispersed bases with air transport. Each brings two security divisions. Aircraft are 1930 fighters, 1932 bombers or 1926 transports; later upgrades need funding. Move guards to conquered airfields yourself.')
    for letter, money, supplies, mp, label, unit, brigade, wings, bases, flag in packs:
        pieces = [f'action_{letter} = {{ trigger = {{ money = {money} supplies = {supplies} manpower = {mp} owned = {{ province = 1459 data = IND }} control = {{ province = 1459 data = IND }} }} ai_chance = {40 if letter == "a" else 30} name = {json.dumps(label)}',
                  cmd('money', value=-money), cmd('supplies', value=-supplies), cmd('manpowerpool', value=-mp)]
        for n, province in enumerate(bases):
            pieces.append(f'command = {{ trigger = {{ owned = {{ province = {province} data = IND }} control = {{ province = {province} data = IND }} NOT = {{ building = {{ province = {province} type = air_base value = 9 }} }} }} type = construct which = air_base where = {province} value = 2 }}')
            pieces.append(cmd('add_corps', which=json.dumps(f'Airfield Guard Group {n + 1}'), value='land', where=1459))
            pieces.append(cmd('add_division', which=json.dumps(f'{n + 1} Indian Airfield Guard Division'), value=unit, when=AIRFIELD_MODELS[unit], **({'where': brigade} if brigade else {})))
        pieces.append(cmd('add_corps', which='"Indian Airfield Support Group"', value='air', where=1459))
        for n, wing in enumerate(wings):
            pieces.append(cmd('activate_unit_type', which=wing))
            pieces.append(cmd('add_division', which=json.dumps(f'{n + 1} Indian Airfield {wing.replace("_", " ").title()} Wing'), value=wing, when=AIRFIELD_MODELS[wing]))
        pieces.extend([cmd('setflag', which=flag), cmd('setflag', which='ind_v4_airfield_security'), '}'])
        f = x.e.field('action_' + letter)
        x.edits.append((f.start, f.end, '\n'.join(pieces)))


def hidden(eid, trigger, commands, persistent=True):
    return f'''event = {{
 {MARKER}
 id = {eid} country = IND random = no
 {'persistent = yes' if persistent else ''}
 name = "AI_EVENT" desc = "AI_EVENT" style = 0
 {('trigger = { ' + trigger + ' } date = { day = 0 month = january year = 1933 } offset = 1 deathdate = { day = 29 month = december year = 1964 }') if trigger is not None else ''}
 action_a = {{ name = "Record current orders" {commands} }}
}}
'''


def northern_helpers():
    arm = f'flag = ind_aubm_wartime_framework NOT = {{ flag = ind_aubm_national_northern_current }} NOT = {{ flag = {READY} }} NOT = {{ flag = {PENDING} }} {HOLD_CONTEXT}'
    invalidate = f'OR = {{ flag = {PENDING} flag = {READY} }} NOT = {{ flag = {BROKEN} }} NOT = {{ AND = {{ {HOLD_CONTEXT} }} }}'
    complete = f'command = {{ trigger = {{ flag = {PENDING} NOT = {{ flag = {BROKEN} }} {HOLD_CONTEXT} }} type = setflag which = {READY} }}\n' + cmd('clrflag', which=PENDING) + '\n' + cmd('clrflag', which=BROKEN)
    return '\n'.join([
        hidden(9318100, arm, cmd('setflag', which=PENDING) + '\n' + cmd('event', which=9318102, where='IND', when=60)),
        hidden(9318101, invalidate, f'command = {{ trigger = {{ flag = {PENDING} }} type = setflag which = {BROKEN} }}\n' + cmd('clrflag', which=READY)),
        hidden(9318102, None, complete),
    ])


PATH_IDS = {
    'db/events/india_v3/10_politics.txt': {9270101},
    'db/events/india_v3/12_society.txt': {9271301, 9271302, 9271303, 9271304, 9271305},
    'db/events/india_v3/30_military.txt': {9270300},
    'db/events/india_v3/33_command_research.txt': {9271202, 9271203},
    'db/events/india_v3/31_air_force.txt': {9271001},
    'db/events/aubm_v4/05_union_integration.txt': {9280111},
    'db/events/aubm_v4/10_world_reactions.txt': {9280300, 9280301, 9280303},
    'db/events/aubm_v4/15_operational_command.txt': {9280152, 9280162},
    'db/events/india_v3/46_world_reactions.txt': {9270450},
    NORTH_PATH: {9281932, 9281942, 9281954, 9281955},
}


def transform(files):
    out, records = dict(files), {}
    # Refuse incomplete/conflicting application; no silent skip of registered files.
    for path in PATH_IDS:
        if path not in files: raise ValueError('Missing playtest source: ' + path)
    existing = {int(e.get('id')) for p in PATH_IDS for e in parse(files[p]).all('event') if e.get('id')}
    if existing & NEW_IDS:
        expected = set().union(*PATH_IDS.values()) | NEW_IDS
        marked = {int(e.get('id')) for p in PATH_IDS for e in parse(files[p]).all('event')
                  if MARKER in files[p][e.start:e.end]}
        if not expected <= existing or not expected <= marked:
            raise ValueError('Partial BALANCE1 playtest overlay or ID collision')
        return out, {}
    # IDs also checked across non-target registered event files, without parsing CSV/AI.
    for p, text in files.items():
        if p.startswith('db/events/') and any(re.search(r'\bid\s*=\s*' + str(i) + r'\b', text) for i in NEW_IDS):
            raise ValueError('BALANCE1 event ID collision in ' + p)
    for path, ids in PATH_IDS.items():
        changes, found = [], set()
        for ev in parse(files[path]).all('event'):
            eid = int(ev.get('id'))
            if eid not in ids: continue
            found.add(eid)
            # Include the event keyword, not just its Node braces.
            x = Edit('event = ' + files[path][ev.start:ev.end])
            political(eid, x); military(eid, x)
            if eid == 9280152: airfield(x)
            elif eid == 9280162:
                x.desc('The Airfield Security Act established the first aircraft and guards. This separate expansion orders additional wings through the normal production queue. Keep their IC funded. Doctrine-first orders no aircraft. Every choice is one-off; none repeats the earlier package.')
            elif eid == 9280303:
                x.desc('Tokyo proposes closer ties. Opening talks, setting conditions or trading changes relations but joins no alliance. If India is not ready to decide, defer without cost: later strategic talks remain available. An active war with Japan or another signed strategic compact rules out this early offer.')
                x.append(x.e.get('trigger'), 'NOT = { war = { country = IND country = JAP } }\n' + '\n'.join(f'NOT = {{ flag = ind_aubm_commitment_{r} }}' for r in ('allied', 'german', 'soviet', 'japan')) + '\n' + '\n'.join(f'NOT = {{ alliance = {{ country = IND country = {t} }} }}' for t in ('ENG', 'GER', 'SOV', 'JAP')))
                # Keep early_japan_policy unset: the existing late-opening trigger
                # explicitly allows NOT early_japan_policy. Setting it with no
                # channel would permanently close every Japan opening.
                x.append(x.e, 'action_d = { ai_chance = 0 name = "Not now - keep every option open" ' + cmd('setflag', which='ind_balance1_japan_deferred') + ' }')
            elif eid == 9270450:
                x.label('a', 'Support sanctions - 300 money')
                x.label('b', 'Offer mediation - 225 money')
                x.label('c', 'Send observers - 500 supplies, +2 dissent')
                x.desc('Italy has attacked Ethiopia. Sanctions cost 300 money: Rome absorbs them 65% of the time and reroutes trade 35%. Mediation costs 225 money, with a 25% chance of an armistice. Observers cost 500 supplies and two dissent, returning an Italian technical report. These odds are fixed.')
            elif eid == 9281932:
                x.desc('Northern recognition needs a sustained offensive: hold Baku, Astrakhan and Stalingrad; or Samarkand, Tashkent, Alma-Ata and Sverdlovsk. Keep the required centres for 60 days while at war with the USSR. This opens provisional talks, not Soviet surrender. A separate deep-victory settlement decides sovereignty.')
            elif eid == 9281942:
                x.body(x.e.get('trigger'), '{ flag = ind_aubm_wartime_framework NOT = { flag = ind_aubm_national_northern_victory } flag = ' + READY + ' ' + HOLD_CONTEXT + ' }')
                x.desc('The northern offensive has held its required centres for 60 days. India has earned provisional regional talks, not Soviet capitulation. Final peace, independence and puppets still require their own deeper victory conditions. This recognition grants its reward once.')
            elif eid == 9281954:
                x.body(x.e.get('trigger'), '{ flag = ind_aubm_national_northern_current NOT = { ' + NORTH_GATE + ' } }')
                x.set(x.e, 'name', 'Northern Command Loses Its Strategic Hold')
                x.desc('A required northern centre has been lost. The campaign achievement stays on record, but provisional talks are suspended. Recover and hold the required centres for 60 days to reopen them. No territory or peace is granted here.')
                x.append(x.action('a'), cmd('clrflag', which=READY))
            elif eid == 9281955:
                x.body(x.e.get('trigger'), '{ flag = ind_aubm_national_northern_suspended flag = ' + READY + ' ' + HOLD_CONTEXT + ' }')
                x.desc('Indian forces have restored the required northern centres and held them for 60 days. Provisional talks reopen. The original recognition reward is not paid again; final Soviet settlement remains a separate matter.')
            patched = x.finish()
            if len(parse(patched).all('event')) != 1: raise ValueError('Invalid rewritten event')
            changes.append((ev.start, ev.end, patched[len('event = '):]))
            records[eid] = [dict(dimension='playtest_balance1', status='reviewed', path=path, native_playtested=False)]
        if found != ids: raise ValueError(f'Missing event IDs in {path}: {ids - found}')
        out[path] = replace(files[path], changes)
    out[NORTH_PATH] += '\n' + northern_helpers()
    out['db/events/aubm_v4/05_union_integration.txt'] += '\n' + hidden(9318103,
        f'flag = ind_v3_started atwar = yes NOT = {{ flag = {UNLOCKED} }}', unlock_commands(), persistent=False)
    records['mountain_team'] = [dict(status='already_present', detail='250027 has mountain_training from 1933; both Army Oath choices wake it. No duplicate team or global skill inflation.')]
    return out, records

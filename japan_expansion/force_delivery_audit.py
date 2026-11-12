"""Retire rejected custom recruitment; deliver a visible civil-works cabinet.

Final catalogue pass, after force_value and any event-accessibility passes.
Personnel pass follows japan_personnel.apply_roster and force_value.apply_personnel.
All class registrations/models stay installed for old-save/index compatibility.
"""
import re

from catalog import EVENTS, Action, cmd
import japan_personnel
import specialist_units as sp

RETIRED = ('d_10', 'd_11', 'd_12')
RECRUITMENT = ('introduce_d_10', 'introduce_d_11', 'snlf_open_recruitment',
               'base_force_orders', 'jungle_force_orders', 'snlf')
IMPOSSIBLE = 'ai = yes ai = no'
CIVIL_TRAIT = 'jx civil construction'
CIVIL_COMMANDS = [
    ('province', 'infra', 'time', -.12),
    ('province', 'infra', 'cost', -.12),
    ('province', 'ic', 'time', -.05),
    ('province', 'ic', 'cost', -.05),
    ('unit', 'navy', 'time', .04),
]
CIVIL_DESC = (
    'Civil works: infrastructure construction IC cost and time -12 percent; '
    'factory construction IC cost and time -5 percent; naval division '
    'construction time +4 percent. Active only while this minister is appointed. '
    'This alternate Fujiwara profile is available from 1937. The original '
    'Administrative Genius profile has different effects. Compare new orders '
    'for the same province and model; this policy does not grant IC output, '
    'repair damaged buildings or change resources automatically.')
REPORT = {}


def configure_personality():
    for i, entry in enumerate(japan_personnel.PERSONALITIES):
        trait, pid, position, name, desc, commands = entry
        if trait == CIVIL_TRAIT:
            japan_personnel.PERSONALITIES[i] = (
                trait, pid, position, 'Civil works: cheaper and faster construction',
                CIVIL_DESC, list(CIVIL_COMMANDS))
            return
    raise RuntimeError('Missing Fujiwara civil-works personality')


def _replace_unit(text):
    for unit, base in (('d_10', 'garrison'), ('d_11', 'infantry'), ('d_12', 'marine')):
        text = re.sub(r'\bwhich\s*=\s*' + unit + r'\b', 'which = ' + base, text)
    return text


def apply():
    if REPORT.get('catalogue_applied'):
        return
    configure_personality()
    by = {e.key: e for e in EVENTS}
    missing = set(RECRUITMENT) - by.keys()
    if missing:
        raise RuntimeError('force_delivery_audit must follow full catalogue: ' + str(missing))
    retired = []
    for key in RECRUITMENT:
        e = by[key]
        e.gate = e.ready = IMPOSSIBLE
        e.title = 'Legacy recruitment retired'
        e.desc = ('This former custom-unit recruitment is retired. New campaigns '
                  'use ordinary Infantry, Mountain Infantry, Marines and Garrisons '
                  'through their normal technology and production. No purchase is required here.')
        e.purpose = 'Retired custom-unit offer; ID preserved, unreachable in new campaigns.'
        e.actions = [Action('', [], chance=100)]
        retired.append({'key': key, 'id': e.id})
    for unit in RETIRED:
        e = by['activate_' + unit]
        e.gate = e.ready = IMPOSSIBLE
        e.title = 'Retired recruitment receiver'
        e.desc = ''
        e.purpose = 'Compatibility receiver only. Direct callers cannot reactivate a retired class.'
        # Triggered events can ignore their event trigger. Every action itself
        # must be harmless, including a direct dispatch from a legacy caller.
        for a in e.actions:
            a.gate = ''
            a.commands = [cmd('deactivate_unit_type', which=unit)]
            a.name = ''
    # Normal unit slots and retained model indices are untouched. A new game's
    # opening action explicitly keeps these three registrations non-producible.
    welcome = by['welcome'].actions[0]
    welcome.commands += [cmd('deactivate_unit_type', which=u) for u in RETIRED]
    by['welcome'].desc += ('\n\nThe three experimental specialist classes are retired. '
                          'Use normal Garrisons for local defence, Mountain Infantry '
                          'for difficult land terrain and full Marines for opposed landings. '
                          'The infantry production priority supports all three mobile '
                          'classes: Infantry, Mountain Infantry and Marines.')

    # Preserve already-paid old programme receivers, but route any useful
    # construction/combat benefits to normal types. No native model ID remap.
    for e in EVENTS:
        if e.key.startswith('activate_'):
            continue
        for a in e.actions:
            converted = []
            for text in a.commands:
                node = sp.parse(text)
                if sp.get(node, 'type') in {'new_model', 'scrap_model', 'activate_unit_type'} and sp.get(node, 'which') in RETIRED:
                    continue
                if sp.get(node, 'type') == 'trigger' and sp.get(node, 'which') in {'@activate_' + u for u in RETIRED}:
                    continue
                # This old rehearsal already grants +3 to ordinary Marines.
                # Its additional conditional SNLF award must not become a
                # second award to that same native class during retirement.
                if (e.key == 'landing_rehearsal_finish_0'
                        and sp.get(node, 'type') == 'river_attack'
                        and sp.get(node, 'which') == 'd_12'):
                    continue
                # Retirement/deactivation remains aimed at the retired class.
                converted.append(text if sp.get(node, 'type') == 'deactivate_unit_type' else _replace_unit(text))
            a.commands = converted

    # Price standard Marines from their own baseline; inheriting the old light
    # class's rebate would under-deliver the stated 20% cost / 15% base time.
    a = by['army_production_finish_0'].actions[0]
    a.commands = [c for c in a.commands if not (
        sp.get(sp.parse(c), 'which') == 'infantry' and
        sp.get(sp.parse(c), 'type') in {'build_cost', 'build_time'} and
        sp.num(sp.parse(c), 'value') in {-.8, -28.5})]
    marine = sp.getall(sp.parse(sp.read(sp.SOURCE / 'db/units/divisions/marine.txt')), 'model')[0]
    rebates = {'build_cost': round(sp.num(marine, 'cost') * .20, 2),
               'build_time': round(sp.num(marine, 'buildtime') * .15, 2)}
    a.commands[:0] = [cmd(kind, which='marine', when='on_upgrade', value=-value)
                       for kind, value in rebates.items()]
    by['army_production'].actions[0].name = 'Equip infantry, mountain troops and full Marines'
    by['army_production'].desc = (
        'Choose one funded army production priority. Infantry warfare supports '
        'ordinary Infantry, Mountain Infantry and full Marine divisions: Infantry '
        '-1 IC / -43.5 days; Mountain Infantry -1.2 IC / -43.5 days; Marines '
        '-1.6 IC / -63 days. The mobile alternative retains its listed reductions '
        'for Motorised Infantry, Cavalry and Armour and adds 10 percent transport '
        'capacity. These are fixed baseline reductions for future normal orders; '
        'research and manpower remain necessary. All three former experimental '
        'classes are retired.\n\nSetup: 150 money and 900 supplies; completion: 180 days.')
    by['army_production_finish_0'].desc = (
        'Infantry, Mountain Infantry and full Marine production tooling is ready. '
        'Infantry -1 IC / -43.5 days; Mountain Infantry -1.2 IC / -43.5 days; '
        'Marines -1.6 IC / -63 days. These fixed reductions apply to future normal '
        'orders. No custom class, completed formation or research is granted.')
    REPORT.update(catalogue_applied=True, retired=retired,
                  marine_priority=rebates, civil_trait=CIVIL_COMMANDS)


def apply_personnel(target, read, write, parse, serialise):
    """Update final generated files, after roster and legacy parity patches."""
    path = target / 'db/ministers/minister_personalities.txt'
    root = parse(read(path))
    ministers = [m for m in sp.getall(root, 'minister') if sp.get(m, 'trait') == CIVIL_TRAIT]
    if len(ministers) != 1:
        raise RuntimeError('Expected one civil-works personality')
    m = ministers[0]
    m[:] = [(k, v) for k, v in m if k != 'command']
    for typ, which, when, value in CIVIL_COMMANDS:
        m.append(('command', [('type', typ), ('which', which), ('when', when), ('value', str(value))]))
    write(path, serialise(root) + '\n')
    roster = target / 'db/ministers/ministers_jap.csv'
    rows = []
    found = False
    for line in read(roster).splitlines():
        r = line.split(';')
        if r[0] == '286122':
            assert r[7] == CIVIL_TRAIT
            r[2] = 'Fujiwara Ginjiro (Civil Works)'
            found = True
            line = ';'.join(r)
        rows.append(line)
    if not found:
        raise RuntimeError('Missing alternate Fujiwara appointment 286122')
    write(roster, '\n'.join(rows) + '\n')
    REPORT['personnel_applied'] = True

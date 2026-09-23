"""Pure staged Nepal retry and verified, delayed national integration.

Source/installed event collision scan for 9398200-06: no matches, 2026-09-10.
Installed 1933/nepal.inc and db/revolt.txt both list only Kathmandu 1457.
Engine event commands.txt documents inherit, addcore (156-162), and queued
events/delays/save representation (702-708). Queued targets below have NO
event trigger/date/offset; every effect is action-guarded. Engine execution,
inherit success and save/reload queue persistence still require native tests.
"""
from dataclasses import dataclass
import re
from dh_save_spans import Node, parse, replace
from aubm_redesign_diplomacy import actions, gate
from generate_aubm_liberator import action, event

NEW_EVENT_IDS = frozenset(range(9398200, 9398207))
CORE_PROVINCES = (1457,)
RETRY_MONEY, RETRY_SUPPLIES, RETRY_DISSENT = 650, 1000, 2
RETRY_DAYS, CORE_DAYS = 360, 1080
CONQUEST_DAYS = 1460
CONQUEST_MONEY, CONQUEST_SUPPLIES, CONQUEST_DISSENT = 900, 1500, 3
MARKER = '# AUBM_STAGED_NEPAL_V1'
P = 'ind_stage_nepal_'
PENDING, ACCEPTED, REJECTED = P + 'offer_pending', P + 'accepted', P + 'rejected'
COOLDOWN, VERIFY = P + 'retry_cooldown', P + 'merge_verifying'
FAILED, CORE_PENDING, DUE, CORED = P + 'merge_failed', P + 'core_pending', P + 'core_due', P + 'cored'
INTEGRATED = 'ind_v3_nepal_integrated'
LIVE = ('exists = IND exists = NEP NOT = { atwar = IND } NOT = { atwar = NEP } '
        'NOT = { ispuppet = IND } NOT = { war = { country = IND country = NEP } } '
        'OR = { NOT = { ispuppet = NEP } puppet = { country = NEP country = IND } '
        'AND = { puppet = { country = NEP country = ENG } '
        'NOT = { war = { country = IND country = ENG } } } }')
OPEN = LIVE + ' NOT = { flag = ' + INTEGRATED + ' } NOT = { flag = ' + VERIFY + ' }'
TERRITORY = ('NOT = { exists = NEP } owned = { province = 1457 data = IND } '
             'control = { province = 1457 data = IND }')


def setf(f): return 'setflag which = ' + f
def clear(f): return 'clrflag which = ' + f
def call(eid, days=1, tag='IND'): return f'event which = {eid} where = {tag} when = {days}'
def flag(f): return 'flag = ' + f
def no(g): return 'NOT = { AND = { ' + g + ' } }'
def cmds(items): return '\n'.join('command = { type = ' + x + ' }' for x in items)


def lapse(valid):
    cleanup = cmds([clear(PENDING), clear(ACCEPTED), clear(REJECTED), setf(FAILED)])
    return ('\n action = { trigger = { ' + flag(PENDING) + ' ' + no(valid) +
        ' } ai_chance = 100 name = "Close the overtaken Nepal offer; no merger"\n' + cleanup + '\n }\n'
        'action = { trigger = { NOT = { flag = ' + PENDING + ' } } ai_chance = 100 '
        'name = "Close the unrelated or completed Nepal reply" }\n')


def generated():
    retry = (OPEN + ' OR = { flag = ind_v3_nepal_refused ' + flag(FAILED) + ' } '
             'NOT = { flag = ' + PENDING + ' } NOT = { flag = ' + COOLDOWN + ' }')
    cost = f'money = {RETRY_MONEY} supplies = {RETRY_SUPPLIES}'
    reply = flag(PENDING) + ' ' + OPEN
    verified = flag(VERIFY) + ' ' + TERRITORY + ' NOT = { flag = ' + INTEGRATED + ' }'
    core = flag(CORE_PENDING) + ' ' + flag(INTEGRATED) + ' ' + TERRITORY + ' NOT = { flag = ' + CORED + ' }'
    finish = flag(DUE) + ' ' + flag(INTEGRATED) + ' ' + TERRITORY + ' NOT = { flag = ' + CORED + ' }'
    conquered = (TERRITORY + ' NOT = { ispuppet = IND } NOT = { flag = ' + INTEGRATED +
                 ' } NOT = { flag = ' + VERIFY + ' } NOT = { flag = ' + CORE_PENDING +
                 ' } NOT = { flag = ' + CORED + ' }')
    bodies = [
        event(9398200, 'Reopen the Nepal Federation Offer',
            'Kathmandu may reconsider a stronger offer. Invest 650 money and 1000 supplies, accepting 2 dissent: Nepal accepts 65% or refuses 35%. A refusal allows another offer after 360 game days. A completed merger begins 1080 days toward national status. Costs are not refunded if talks lapse.',
            [action('Renew the offer: pay 650 money and 1000 supplies',
                'money value = -650', 'supplies value = -1000', 'dissent value = 2',
                clear(FAILED), clear(ACCEPTED), clear(REJECTED), setf(PENDING),
                'setflag which = ind_v3_nepal_offered', call(9398201, 2, 'NEP'), gate=retry + ' ' + cost),
             action('Cancel - close without changes')], gate=retry, decision=True),
        event(9398201, 'Nepal Considers the Renewed Federal Settlement',
            'Delhi promises investment and protection for local institutions. Kathmandu can enter the federation or retain its sovereignty. Refusal leaves the door open to another funded offer after 360 game days.',
            [action('Accept the funded constituent settlement (65%)', setf(ACCEPTED),
                    'trigger which = 9270415', gate=reply, chance=65),
             action('Remain sovereign (35%)', setf(REJECTED), 'relation which = IND value = -20',
                    'trigger which = 9270416', gate=reply, chance=35)], country='NEP'),
        event(9398202, 'Talks with Kathmandu Can Resume',
            'A year has passed since Nepal refused the offer. Delhi may return with a new appropriation when both countries are at peace.',
            [action('Reopen the diplomatic door', clear(COOLDOWN), gate=flag(COOLDOWN)),
             action('The diplomatic door is already open', gate=no(flag(COOLDOWN)))]),
        event(9398203, 'Nepal Joins the Union',
            'Kathmandu passes into Indian administration. The Nepalese contribution brings 20 manpower and 1 dissent. Federal integration will take 1080 game days; Kathmandu gains national status only while India owns and controls it. If the merger failed, no benefit or integration clock begins.',
            [action('Welcome Nepal and begin federal integration', clear(VERIFY), clear(FAILED),
                    setf(INTEGRATED), 'dissent value = 1', 'manpowerpool value = 20',
                    setf(CORE_PENDING), call(9398204, CORE_DAYS), gate=verified),
             action('The merger has not taken effect; keep talks possible',
                    clear(VERIFY), setf(FAILED), gate=flag(VERIFY) + ' ' + no(verified)),
             action('Kathmandu has already been welcomed', gate=no(flag(VERIFY)))]),
        event(9398204, 'Kathmandu and Delhi',
            'The agreed integration period has passed: three years after a voluntary merger, or four after a funded occupation settlement. Kathmandu can now become a national province. If Nepal has returned or India lacks ownership or control, completion waits until the territorial settlement is restored.',
            [action('Grant national status to Kathmandu', 'addcore which = 1457', setf(CORED), clear(CORE_PENDING), gate=core),
             action('Wait until Kathmandu is securely within India', clear(CORE_PENDING), setf(DUE),
                    gate=flag(CORE_PENDING) + ' ' + no(core)),
             action('Kathmandu already has its settlement', gate=no(flag(CORE_PENDING)))]),
        event(9398205, 'Complete Kathmandu Federal Integration',
            'The agreed integration period has already passed. Kathmandu is again owned and controlled by India, and Nepal has not been restored. Complete national integration without a second waiting period or another charge.',
            [action('Make Kathmandu a national province', 'addcore which = 1457', setf(CORED), clear(DUE), gate=finish),
             action('Cancel - close without changes')], gate=finish, decision=True),
        event(9398206, 'Build a Lasting Settlement in Nepal',
            f'Conquest alone does not make Kathmandu a national province. Invest {CONQUEST_MONEY} money and {CONQUEST_SUPPLIES} supplies, accepting {CONQUEST_DISSENT} dissent, in a federal settlement. After {CONQUEST_DAYS} game days, Kathmandu can gain national status if Nepal remains absent and India owns and controls the province.',
            [action(f'Integrate Nepal: pay {CONQUEST_MONEY} money and {CONQUEST_SUPPLIES} supplies',
                f'money value = -{CONQUEST_MONEY}', f'supplies value = -{CONQUEST_SUPPLIES}', f'dissent value = {CONQUEST_DISSENT}',
                clear(PENDING), clear(ACCEPTED), clear(REJECTED), setf(INTEGRATED),
                setf(CORE_PENDING), call(9398204, CONQUEST_DAYS),
                gate=conquered + f' money = {CONQUEST_MONEY} supplies = {CONQUEST_SUPPLIES}'),
             action('Cancel - close without changes')], gate=conquered, decision=True),
    ]
    bodies[1] = bodies[1][:-1] + lapse(reply) + '}'
    return '\n\n'.join(b.replace('event = {', 'event = {\n ' + MARKER, 1)
                          .replace('year = 1940', 'year = 1935') for b in bodies)


@dataclass(frozen=True)
class HimalayanPolicy:
    name: str
    capital: str
    tag: str
    province: int
    base: int
    ordinary: int
    grand: int
    accepted_event: int
    refused_event: int
    followup: int
    retry_chance: int
    manpower: int
    merger_dissent: int

    def render(self, text):
        """Specialize our own Nepal template, never arbitrary source events."""
        mapping = {str(9398200+i): str(self.base+i) for i in range(7)}
        mapping.update({'9270415': str(self.accepted_event), '9270416': str(self.refused_event),
                        '1457': str(self.province), 'NEP': self.tag})
        text = re.sub(r'\b(?:' + '|'.join(mapping) + r')\b', lambda m: mapping[m[0]], text)
        for old, new in [('Nepalese', self.name + 'ese' if self.name == 'Bhutan' else 'Nepalese'),
                         ('Nepal', self.name), ('nepal', self.name.lower()), ('Kathmandu', self.capital)]:
            text = text.replace(old, new)
        text = text.replace('65%', str(self.retry_chance)+'%').replace('35%', str(100-self.retry_chance)+'%')
        text = text.replace('ai_chance = 65', 'ai_chance = '+str(self.retry_chance))
        text = text.replace('ai_chance = 35', 'ai_chance = '+str(100-self.retry_chance))
        text = text.replace('manpowerpool value = 20', 'manpowerpool value = '+str(self.manpower))
        text = text.replace('dissent value = 1', 'dissent value = '+str(self.merger_dissent))
        text = text.replace('20 manpower and 1 dissent', f'{self.manpower} manpower and {self.merger_dissent:+d} dissent')
        return text.replace('AUBM_STAGED_NEPAL_V1', 'AUBM_STAGED_'+self.tag+'_V1')


NEPAL = HimalayanPolicy('Nepal', 'Kathmandu', 'NEP', 1457, 9398200, 9270414, 9270424, 9270415, 9270416, 9270418, 65, 20, 1)
BHUTAN = HimalayanPolicy('Bhutan', 'Thimphu', 'BHU', 1456, 9398210, 9270411, 9270419, 9270412, 9270413, 9270417, 80, 5, -1)


def transform_country(files: dict[str, str], policy):
    # Local aliases keep the shared lifecycle independent for both kingdoms.
    # Nepal's public constants remain stable for existing callers/tests.
    render = policy.render
    ids = frozenset(range(policy.base, policy.base+7))
    marker = MARKER if policy == NEPAL else render(MARKER)
    pending, accepted, rejected, cooldown, verify = map(render, (PENDING, ACCEPTED, REJECTED, COOLDOWN, VERIFY))
    opened = render(OPEN)
    output, records, target = dict(files), {}, None
    all_events = [(path, ef, text) for path, text in files.items()
                  for ef in parse(text).fields if ef.key == 'event']
    for path, ef, text in all_events:
        eid = int(ef.value.get('id'))
        if eid in ids and marker not in text[ef.start:ef.end]:
            raise ValueError('Nepal reserved event collision: ' + str(eid))
    existing = {int(ef.value.get('id')) for _, ef, _ in all_events} & ids
    if existing and existing != ids:
        raise ValueError('Incomplete generated Nepal event set')
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event': continue
            eid = int(ef.value.get('id'))
            if eid not in (9270410, policy.ordinary, policy.grand, policy.accepted_event, policy.refused_event, policy.followup): continue
            if eid == policy.accepted_event: target = path
            raw = text[ef.start:ef.end]
            if marker in raw: continue
            ev = parse(raw).get('event')
            changes, extra, keys = [], '', []
            if eid == 9270410 and policy == BHUTAN:
                # A paid dual offer must actually be available to both courts.
                # Independent callbacks still allow one acceptance and one refusal.
                dual = (opened + ' NOT = { flag = ' + pending + ' } '
                        'NOT = { flag = ind_v3_bhutan_refused } NOT = { flag = ' + cooldown + ' } '
                        + OPEN + ' NOT = { flag = ' + PENDING + ' } '
                        'NOT = { flag = ind_v3_nepal_refused } NOT = { flag = ' + COOLDOWN + ' }')
                changes.append(gate(ev.get('action_d'), dual))
            if eid in (9270410, policy.followup):
                for af in actions(ev):
                    for cf in af.value.fields:
                        if cf.key != 'command' or cf.value.get('type') != 'trigger' or cf.value.get('which') not in (str(policy.ordinary), str(policy.grand)):
                            continue
                        valid = (opened + ' NOT = { flag = ' + pending + ' } '
                                 'NOT = { flag = ind_v3_' + policy.name.lower() + '_refused } '
                                 'NOT = { flag = ' + cooldown + ' }')
                        if not (eid == 9270410 and af.key == 'action_d'):
                            changes.append(gate(af.value, valid))
                        # In the grand dual offer only Nepal-specific commands
                        # change; Bhutan's offer, costs and effects are untouched.
                        # Queue first, then create its token in the same action.
                        # This keeps the grand offer's Bhutan branch intact and
                        # prevents an existing Nepal token from re-dispatching.
                        # One-day delivery ensures the token exists on arrival.
                        replacement = ('command = { trigger = { ' + valid +
                            ' } type = event which = ' + cf.value.get('which') + ' where = ' + policy.tag + ' when = 1 }\n' +
                            '\n'.join('command = { trigger = { ' + valid + ' } type = ' + x + ' }'
                                for x in [clear(accepted), clear(rejected), setf(pending)]))
                        changes.append((cf.start, cf.end, replacement))
                        keys.append(af.key)
            else:
                pf = next((f for f in ev.fields if f.key == 'persistent'), None)
                if not pf: changes.append((ev.start + 1, ev.start + 1, '\n persistent = yes\n'))
                if eid in (policy.ordinary, policy.grand):
                    valid = flag(pending) + ' ' + opened
                    for af in actions(ev):
                        changes.append(gate(af.value, valid))
                        changes.append((af.value.start + 1, af.value.start + 1,
                            '\n' + cmds([setf(accepted if af.key == 'action_a' else rejected)]) + '\n'))
                        keys.append(af.key)
                    extra = render(lapse(valid))
                elif eid == policy.accepted_event:
                    valid = flag(pending) + ' ' + flag(accepted) + ' ' + opened
                    a = ev.get('action_a'); changes.append(gate(a, valid)); keys = ['action_a']
                    for cf in a.fields:
                        if cf.key == 'command' and cf.value.get('type') != 'inherit':
                            changes.append((cf.start, cf.end, ''))
                    changes.append((a.end - 1, a.end - 1, '\n' + render(cmds([
                        clear(PENDING), clear(ACCEPTED), clear(REJECTED), setf(VERIFY), call(9398203)])) + '\n'))
                    extra = render(lapse(valid))
                else:
                    valid = flag(pending) + ' ' + flag(rejected) + ' ' + opened
                    keys = []
                    for af in actions(ev):
                        changes.append(gate(af.value, valid))
                        for cf in af.value.fields:
                            if cf.key == 'command' and cf.value.get('type') == 'addcore':
                                f = cf.value.field('type'); changes.append((f.value_start, f.end, 'addclaim'))
                        changes.append((af.value.end - 1, af.value.end - 1,
                            '\n' + render(cmds([clear(PENDING), clear(REJECTED), clear(ACCEPTED),
                                          setf(COOLDOWN), call(9398202, RETRY_DAYS)])) + '\n'))
                        keys.append(af.key)
                    extra = render(lapse(valid))
                if eid in (policy.accepted_event, policy.refused_event):
                    f = ev.field('desc')
                    note = (' No immediate national province is granted. A verified voluntary '
                            'merger starts 1080 game days before Kathmandu can become a core.' if eid == policy.accepted_event else
                            ' Another funded Nepal offer becomes available after 360 game days. '
                            'Military enforcement grants a claim, not immediate national status. '
                            'After annexation, a separate expensive five-year integration project is available.')
                    changes.append((f.value_start, f.end, '"' + f.value + render(note) + '"'))
            changes.append((ev.end - 1, ev.end - 1, '\n' + marker + '\n' + extra))
            edits.append((ef.start, ef.end, replace(raw, changes)))
            records[eid] = [{'dimension': 'nepal_merger', 'status': 'CORRECTED_SCRIPT', 'actions': keys,
                'path': path, 'detail': policy.name + ': shared offer ownership, repeatable replies and verified '
                'merger; premature cores removed. The other kingdom has independent tokens and outcomes.'}]
        output[path] = replace(text, edits)
    if target is None: raise ValueError('Authored Nepal merger event 9270415 is required')
    if not existing: output[target] += '\n\n' + (generated() if policy == NEPAL else render(generated())) + '\n'
    for eid in ids:
        records[eid] = [{'dimension': 'nepal_merger', 'status': 'CORRECTED_SCRIPT', 'actions': [], 'path': target,
            'detail': 'Funded retry: 650 money/1000 supplies/+2 dissent, 65% acceptance. '
            'Refusal cooldown 360 days; verified voluntary merger starts 1080-day queued '
            'national-status follow-up for Kathmandu 1457. Post-annexation integration costs '
            '1500 money/2500 supplies/+5 dissent and takes1800 days. Matured ownership recovery is supported.'},
            {'dimension': 'nepal_merger', 'status': 'UNRESOLVED', 'actions': [], 'path': target,
             'detail': 'New-game primary. Native inheritance/queue persistence and same-offer retry '
             'generations need engine validation. Existing cores are not removed from saves. '
             'British-puppet Nepal is retained as eligible under the authored 1933 context when '
             'nonhostile; third-party master consent/engine consequences are not certified. '
             'Core delay counts elapsed time after the verified merger or paid annexation '
             'settlement, not continuous control. Military conquest alone never awards a core.'}]
    for text in output.values(): parse(text)
    if policy != NEPAL:
        for entries in records.values():
            for record in entries:
                record['dimension'] = 'bhutan_merger'
                record['detail'] = render(record['detail'])
    return output, records


def transform(files):
    return transform_country(files, NEPAL)

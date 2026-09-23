"""Pure authored-source corrections for two bounded cooperation defects.

Input precedes B1 compilation; output never writes files or invents event IDs.
The retry reset additionally clears B1's historical completion flag for staged
compatibility. No promise of native callback delivery, retry execution or
campaign completeness follows from these script transformations.
"""
from dh_save_spans import Node, parse, replace
from aubm_redesign_diplomacy import actions, gate, COMPACTS

MARKER = '# AUBM_STAGED_COOPERATION_V1'
DONE = 'ind_cleanup1_done_9281455'
PARTNERS = {'CHI': ('china', 'JAP'), 'SIA': ('siam', 'JAP'),
            'PER': ('persia', 'SOV'), 'AFG': ('afghan', 'SOV')}
EAST_VALID = (
    'exists = SOV NOT = { ispuppet = IND } '
    'NOT = { war = { country = IND country = SOV } } '
    'NOT = { alliance = { country = IND country = JAP } } '
    'NOT = { alliance = { country = SOV country = JAP } } '
    'NOT = { flag = ind_aubm_commitment_japan } '
    'NOT = { flag = ind_aubm_jp_partnership } '
    'OR = { flag = ind_v4_sov_equal_compact flag = ind_v4_sov_supervised_compact '
    'flag = ind_v4_sov_autonomous_socialism flag = ind_v4_sov_technical_only } '
    'OR = { war = { country = IND country = JAP } '
    'war = { country = CHI country = JAP } war = { country = SOV country = JAP } } '
    'NOT = { flag = ind_v4_sov_east_requested } '
    'NOT = { flag = ind_v4_sov_east_deferred } '
    'NOT = { flag = ind_v4_sov_east_active }')


def partner(tag):
    """Actual bilateral acceptance, including the legacy consultative contracts."""
    name, _ = PARTNERS[tag]
    legacy = (' AND = { flag = ind_v42_delhi_pact_consultative '
              'flag = ind_v42_' + name + '_accepts_delhi_pact }') if tag in ('CHI', 'SIA') else ''
    return ('exists = ' + tag + ' NOT = { ispuppet = ' + tag + ' } '
            'NOT = { war = { country = IND country = ' + tag + ' } } '
            'OR = { flag = ind_v43_nam_' + name + '_partner '
            'alliance = { country = IND country = ' + tag + ' }' + legacy + ' }')


def crisis_partner(tag):
    enemy = PARTNERS[tag][1]
    return (partner(tag) + ' war = { country = ' + tag + ' country = ' + enemy +
            ' } NOT = { war = { country = IND country = ' + enemy + ' } }')


INDEPENDENT = ('NOT = { ispuppet = IND } ' +
    ' '.join('NOT = { alliance = { country = IND country = ' + tag + ' } }'
             for tag in ('ENG', 'USA', 'GER', 'ITA', 'SOV', 'JAP')) + ' ' +
    ' '.join('NOT = { flag = ' + flag + ' }' for flags in COMPACTS.values() for flag in flags))
CRISIS_VALID = ('year = 1937 ' + INDEPENDENT + ' OR = { ' +
    ' '.join('AND = { ' + crisis_partner(tag) + ' }' for tag in PARTNERS) +
    ' } NOT = { flag = ind_aubm_bespoke_partner_crisis_sovereign_resolved }')


def transform(files: dict[str, str]):
    """Return (new mapping, per-event lists of action/dimension review records)."""
    output, reviews = dict(files), {}
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != 'event':
                continue
            eid = int(ef.value.get('id'))
            if eid not in (9281446, 9281455, 9281456, 9281457, 9281458, 9281459, 9289661) and not 9281502 <= eid <= 9281537:
                continue
            raw = text[ef.start:ef.end]
            ev = parse(raw).get('event')
            records, changes = [], []

            def record(keys, detail, status='CORRECTED_SCRIPT'):
                records.append({'dimension': 'cooperation', 'status': status,
                                'actions': list(keys), 'detail': detail, 'path': path})

            if MARKER in raw:
                record([], 'Already transformed.', 'ALREADY_APPLIED')
                reviews[eid] = records
                continue
            if eid == 9281455:
                decision = ev.get('decision')
                if not isinstance(decision, Node):
                    raise ValueError('9281455 requires authored decision')
                changes.append((decision.start, decision.end, '{ ' + EAST_VALID + ' }'))
                changes.append(gate(ev.get('action_a'), EAST_VALID))
                pf = next((f for f in ev.fields if f.key == 'persistent'), None)
                changes.append((pf.value_start, pf.end, 'yes') if pf else
                               (ev.start + 1, ev.start + 1, '\n persistent = yes\n'))
                record(['action_a'], 'Request is repeatable only after requested/deferred '
                       'clear, never after active cooperation. Current Soviet nonhostility '
                       'and absence of Japanese alignment replace historical orientation '
                       'vetoes. Existing Soviet cooperation policy, war context, costs and '
                       'reply remain; India need not be at peace.')
            elif eid == 9281446:
                # A timed refusal reset is bookkeeping, even after policy changes.
                # Require its own deferred record so an unrelated call cannot
                # clear an active request. Active outcome itself is never erased.
                valid = 'flag = ind_v4_sov_east_deferred'
                for af in actions(ev):
                    if af.key not in ('action_a', 'action_b'):
                        continue
                    tr = af.value.get('trigger')
                    predicate = valid if af.key == 'action_a' else 'NOT = { ' + valid + ' }'
                    changes.append((tr.start, tr.end, '{ ' + predicate + ' }'))
                a = ev.get('action_a')
                changes.append((a.end - 1, a.end - 1,
                    '\n command = { type = clrflag which = ' + DONE + ' }\n'))
                record(['action_a', 'action_b'], 'Deferred review clears requested/deferred '
                       'and B1 done compatibility regardless of current route; no deferred '
                       'record gives an effect-free exit. Existing active/rank/reward state '
                       'is preserved; elapsed-year callback timing is unchanged.')
            elif eid == 9289661:
                tr = ev.get('trigger')
                changes.append((tr.start, tr.end, '{ ' + CRISIS_VALID + ' }'))
                for af in actions(ev):
                    if af.value.all('command'):
                        changes.append(gate(af.value, CRISIS_VALID))
                    for c in af.value.all('command'):
                        if c.get('type') == 'relation' and c.get('which') in PARTNERS:
                            old = c.get('trigger')
                            # Support reaches only the accepted partner currently
                            # fighting its relevant enemy, not every past contact.
                            new = ('{ flag = ind_aubm_bespoke_partner_crisis_sovereign_limited_support ' +
                                   crisis_partner(c.get('which')) + ' }')
                            changes.append((old.start, old.end, new))
                record([a.key for a in actions(ev)], 'Opportunity and support use v43 '
                       'country acceptance, actual alliance, or CHI/SIA legacy accepted '
                       'consultative pact. Generic Delhi Pact proves no country acceptance. '
                       'Removed global sovereign-route/autonomous-socialism veto; current '
                       'great-power alliances, puppet status and treaty commitments enforce '
                       'independence. Regional alliances remain eligible. Costs, rewards, '
                       'enemy pairings and terminal flag are preserved.')
                record(['action_b'], 'Existing menu review still consumes crisis resolution '
                       'before a war choice; fixing intent versus completion is outside '
                       'this bounded accepted-partner correction.', 'UNRESOLVED')
            else:
                record([a.key for a in actions(ev)], 'Delayed reply left unchanged: shared '
                       'request writers, pending ownership, country disappearance and retry '
                       'delivery are not fully specified. No partial success-only guard '
                       'introduced without a recoverable failure/cancel lifecycle.', 'UNRESOLVED')
            if changes:
                extra = ''
                # Only the player-invoked request gets a free close button.
                # A no-effect exit on the persistent calendar crisis would
                # leave its polling trigger true and reopen the popup.
                if eid == 9281455 and not any(not a.value.all('command') for a in actions(ev)):
                    extra = ('\n action = { trigger = { ai = no } ai_chance = 0 '
                             'name = "Cancel - close without changes" }\n')
                changes.append((ev.end - 1, ev.end - 1, '\n' + MARKER + '\n' + extra))
                updated = replace(raw, changes)
                parse(updated)
                edits.append((ef.start, ef.end, updated))
            reviews[eid] = records
        output[path] = replace(text, edits)
    return output, reviews

"""Human campaign flow: manual offers and finite, guarded transactions.

Apply after human_campaign.apply(). Existing IDs are untouched. The renderer
honours Event.manual_only for settlement offers; other decisions already use
the builder's human-manual rule. No installation or import-time mutation.
"""
import re
from catalog import EVENTS, Action, flag, later

REPORT = {}
RETIRED_EARLY = {
    'allocations1933', 'deck1935', 'colleges1936', 'rail1937',
    'materials1938', 'nomonhan1939', 'instructors1940',
}
MANUAL_EARLY = {'fx1933', 'oil1934', 'fx1936', 'neutral1939', 'procurement1937'}


def _and(gate):
    return 'AND = { ' + gate + ' }'


def _guard(event, gate):
    """Guard real actions, leaving an inert action for stale queued events."""
    for action in event.actions:
        action.gate = (gate + ' ' + action.gate).strip()
    event.actions.append(Action('', [], gate='NOT = { ' + _and(gate) + ' }'))


def apply():
    if REPORT:
        return REPORT
    by = {e.key: e for e in EVENTS}
    ids = {e.key: e.id for e in EVENTS}

    # The three service priorities replace a string of tiny additional bills.
    # Expiry/finish receivers remain usable for pending work in older saves.
    for key in sorted(RETIRED_EARLY):
        e = by[key]
        e.gate = e.ready = 'ai = yes ai = no'
        e.purpose = 'Retired small-stat preparation offer; existing receivers retained.'
        for action in e.actions:
            action.gate = e.gate + ' ' + action.gate
    for key in sorted(MANUAL_EARLY):
        e = by[key]
        e.decision = True
        e.manual_only = True
        e.desc += '\n\nThis is an optional decision. Open it when needed; leaving it available costs nothing.'
        for action in e.actions:
            if any(f'which = @'+key+'_reconsider ' in c for c in action.commands):
                action.name = 'Leave this proposal available'
                action.commands = []

    settlements = [e for e in EVENTS if e.module == 'settlements' and e.decision]
    for offer in settlements:
        key = offer.key
        pending = f'flag = JX_{key}_PENDING NOT = {{ flag = JX_{key}_SETTLED }}'
        offer.manual_only = True
        offer.desc += '\n\nThis settlement is offered in the Decisions panel. Leave it there while continuing the campaign, or dismiss it permanently. Ignoring it causes no payment, peace or puppet release.'
        # A close button need not schedule a quarterly reminder for a manual card.
        offer.actions[3].name = 'Leave these terms available; continue the campaign'
        offer.actions[3].commands = []
        for action in offer.actions:
            action.gate = (offer.gate + ' ' + action.gate).strip()

        for suffix in ('prepare', 'create', 'withdraw', 'withdraw_existing',
                       'commit', 'local', 'verify', 'failed'):
            target = by.get(key + '_' + suffix)
            if target:
                _guard(target, pending)

        # Stale verification previously re-opened failure after success, and a
        # late local receiver could puppet/reconfigure a no-longer-pending state.
        confirmed = by[key + '_confirmed']
        _guard(confirmed, f'flag = JX_{key}_SETTLED NOT = {{ flag = JX_{key}_ANNOUNCED }}')

        # Re-enter the preparation stage so withdrawals/releases are retried too.
        # A manually selected retry waits a month instead of a six-day pop-up loop.
        failed = by[key + '_failed']
        failed.actions[0].name = 'Retry the same agreement in 30 days'
        failed.actions[0].commands = [later(key + '_prepare', 30)]
        failed.desc = ('The agreed government, reciprocal access or reserved base could not be verified. '
                       'Check ownership and diplomacy before retrying. A retry applies the same terms after 30 days; '
                       'it charges no fee and does not repeat the one-time national support package. '
                       'Stopping leaves the present borders and relationships in place and dismisses this settlement.')

        # Execute preparation in the already-open terms event. Foreign-owner
        # withdrawals/transfers stay immediate; create/commit retain their
        # original one-/three-day delays and command order.
        preparation = by[key + '_prepare'].actions[0].commands
        for action in offer.actions[:3]:
            expanded = []
            for command in action.commands:
                if 'type = event which = @' + key + '_prepare ' in command:
                    expanded.extend(preparation)
                else:
                    expanded.append(command)
            action.commands = expanded

        # The verification window can itself confirm the result. The legacy
        # confirmation receiver remains registered for old queued events.
        verify = by[key + '_verify']
        verify.title = confirmed.title
        verify.desc = confirmed.desc + ' If the check fails, the agreement remains incomplete and the next notice explains how to retry or stop.'
        verify.actions[0].name = 'The agreement is in force'
        verify.actions[0].commands = [c for c in verify.actions[0].commands
                                     if 'type = event which = @' + key + '_confirmed ' not in c]
        verify.actions[0].commands.append(flag(key + '_ANNOUNCED'))
        verify.actions[1].name = 'The agreement is incomplete; review the problem'

    # Recheck the complete offer at payment time, including pending/dismissal.
    # A delayed finish always has an inert response once the transaction closes.
    paid = []
    for e in EVENTS:
        if not re.fullmatch(r'.+_finish_\d+', e.key):
            continue
        parent = by.get(e.key.rsplit('_finish_', 1)[0])
        if not parent:
            continue
        key = parent.key
        live = f'flag = JX_{key}_PENDING NOT = {{ flag = JX_{key}_DONE }}'
        _guard(e, live)
        if key in paid:
            continue
        paid.append(key)
        for action in parent.actions:
            if parent.decision and any('type = setflag which = JX_' + key + '_WAIT' in c for c in action.commands):
                action.name = 'Leave this proposal available'
                action.commands = []
            action.gate = (parent.gate + ' ' + action.gate).strip()

    # The regional development grant was not protected by the national starter
    # receipt: replaying its local event gave another 100 money/1000 supplies.
    for key, tag in (('guangxi', 'CGX'), ('yunnan', 'CYN')):
        live = f'flag = JX_{key}_REGIONAL_PENDING NOT = {{ flag = JX_{key}_REGIONAL_DONE }}'
        for suffix in ('release', 'commit', 'confirmed', 'refund'):
            _guard(by[key + '_' + suffix], live)
        local = by[key + '_local']
        receipt = f'FLOW_{key}_GRANT_DONE'
        _guard(local, live + f' NOT = {{ flag = JX_{receipt} }} puppet = {{ country = {tag} country = JAP }}')
        local.actions[0].commands.append(flag(receipt))
        main = by[key + '_autonomy']
        for action in main.actions:
            action.gate = (main.gate + ' ' + main.ready + ' ' + action.gate).strip()

    assert ids == {e.key: e.id for e in EVENTS}, 'Flow edits must preserve every existing event ID'
    REPORT.update(manual_settlements=[e.key for e in settlements],
                  manual_early=sorted(MANUAL_EARLY), retired_early=sorted(RETIRED_EARLY),
                  guarded_paid_projects=paid, regional_grant_receipts=['guangxi', 'yunnan'])
    return REPORT

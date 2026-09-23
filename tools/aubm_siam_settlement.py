"""Siam's exit from Japan: opponent-side withdrawal, then verified protection.

No Indian peace command is permitted in this chain. Script contracts cannot
prove engine war-list mutation; the staged checks fail closed if it differs.
"""
from generate_aubm_liberator import (
    action, event, CANCEL, flag, setf, clear, no, all_of, any_of,
    war, owned, control, puppet, later,
)
from aubm_liberator_v2 import age
from aubm_liberator_v3 import TAGS

BASE = 9297000
HOLD_DAYS = 21
HUBS = (1423, 1425)  # Bangkok and Chiang Mai: installed Map_1 province_names.csv.
ROUTE = all_of('exists = IND', no('ispuppet = IND'),
    no('alliance = { country = IND country = JAP }'),
    any_of(*(f'flag = ind_aubm_route_{r}' for r in ('sovereign', 'allied', 'german', 'soviet'))))
TOKYO = any_of(puppet('SIA', 'JAP'), 'alliance = { country = SIA country = JAP }')
POSITION = all_of(*(owned(p, 'SIA') for p in HUBS), *(control(p, 'IND') for p in HUBS))
VALID = all_of(ROUTE, 'exists = SIA', war('JAP'), war('SIA'), TOKYO, POSITION)
UNATTACHED = all_of('exists = SIA', no('ispuppet = SIA'),
    *(no(f'alliance = {{ country = SIA country = {t} }}') for t in TAGS if t != 'SIA'))
FREE_POSITION = all_of(*(owned(p, 'SIA') for p in HUBS),
    *(any_of(control(p, 'IND'), control(p, 'SIA')) for p in HUBS))
DETACHED = all_of(ROUTE, war('JAP'), UNATTACHED, no('atwar = SIA'), FREE_POSITION)
LEGACY_FLAGS = ('regional_armistice_target_sia', 'regional_pending_sia',
    'regional_current_sia', 'regional_retry_sia', 'regional_suspended_sia')


def legacy_cleanup():
    return tuple(f'clrflag which = ind_aubm_{f}' for f in LEGACY_FLAGS)


def render_events():
    start = all_of(VALID, no(flag('siam_hold_watch')), no(flag('siam_break_pending')),
        no(flag('siam_detached')), no(flag('siam_protected')))
    interrupted = all_of(flag('siam_hold_watch'), no(VALID),
        no(flag('siam_break_pending')), no(flag('siam_detached')), no(flag('siam_protected')))
    ready = all_of(VALID, flag('siam_hold_watch'), age(BASE, HOLD_DAYS), no(flag('siam_hold_ready')))
    offer = all_of(VALID, flag('siam_hold_ready'), no(flag('siam_break_pending')),
        no(flag('siam_detached')), no(flag('siam_protected')))
    response = all_of(VALID, flag('siam_break_pending'), flag('siam_hold_ready'))
    verify = all_of(DETACHED, flag('siam_break_pending'))
    confirmed = all_of(ROUTE, war('JAP'), puppet('SIA', 'IND'), no(war('SIA')),
        flag('siam_detached'), no(flag('siam_protected')))
    return [
        event(BASE, 'Siam: Secure Bangkok and Chiang Mai',
            'India holds Bangkok and Chiang Mai. Hold both for 21 days while fighting Siam and Japan to demand a new Siamese government under Indian protection. Losing either city restarts the count.',
            [action('Begin the 21-day hold', setf('siam_hold_watch'), gate=start)],
            gate=start, automatic=True, offset=1, save_date=True),
        event(BASE+1, 'Siam: The Hold Has Ended',
            'The required cities or war conditions have changed. A new 21-day hold is needed before India can impose terms.',
            [action('Restart the count when both cities are secure', clear('siam_hold_watch'), clear('siam_hold_ready'), gate=interrupted)],
            gate=interrupted, automatic=True, offset=1),
        event(BASE+2, 'Siam: Terms Are Ready',
            'Bangkok and Chiang Mai have been held for 21 days. India may demand that Siam leave Japan and become an Indian puppet. Keep both cities until the Siamese government accepts the terms.',
            [action('Open the Siam peace offer', setf('siam_hold_ready'), gate=ready)],
            gate=ready, automatic=True, offset=1),
        event(BASE+3, 'Siam: End Japanese Rule',
            'Siam will end Japanese rule, leave Japan\'s alliance and its inherited wars, then become an Indian puppet. Siam keeps its land and units; India gains control of its foreign policy and military access. India\'s war with Japan must continue before protection is confirmed. No Indian peace order is issued. You may keep fighting instead.',
            [action('Demand an Indian puppet government', setf('siam_break_pending'),
                *legacy_cleanup(), later(BASE+4, 'SIA', 1), gate=offer), CANCEL],
            gate=offer, decision=True),
        event(BASE+4, 'Siam Leaves Japan',
            'Indian forces hold Bangkok and Chiang Mai. The government accepts Indian protection. End Japanese control and withdraw Siam from Japan\'s alliance and its inherited wars. Indian protection follows only after the withdrawal is checked.',
            [action('Accept Indian protection and leave Japan', 'end_puppet', 'leave_alliance when = 1',
                later(BASE+5, 'IND', 1), gate=response, chance=100),
             action('The terms no longer apply', clear('siam_break_pending'), clear('siam_hold_watch'),
                clear('siam_hold_ready'), gate=no(response), chance=100)], country='SIA'),
        event(BASE+5, 'Siam: Confirm Indian Protection',
            'Check that Siam is free of all masters, alliances and wars, and that India is still fighting Japan. If those checks pass, Siam becomes an Indian puppet and grants India access. If they fail, no peace or puppet order is issued.',
            [action('Confirm Siam as an Indian puppet', clear('siam_break_pending'), setf('siam_detached'),
                'make_puppet which = SIA', later(BASE+6, 'SIA', 1), later(BASE+7, 'IND', 2),
                gate=verify, chance=100),
             action('The withdrawal could not be confirmed', clear('siam_break_pending'),
                clear('siam_hold_watch'), clear('siam_hold_ready'), gate=no(verify), chance=100)]),
        event(BASE+6, 'Siam: Indian Military Access',
            'Siam is now an Indian puppet. Grant India military access. This creates no new war or alliance.',
            [action('Grant Indian access', 'access which = IND',
                gate=all_of(puppet('SIA', 'IND'), flag('siam_detached')), chance=100),
             action('No protected government was formed', gate=no(all_of(puppet('SIA', 'IND'), flag('siam_detached'))), chance=100)],
            country='SIA'),
        event(BASE+7, 'Siam Is Under Indian Protection',
            'Siam is confirmed as an Indian puppet and India remains at war with Japan. Siam keeps its territory and armed forces. Normal puppet obligations apply. The Siam campaign is complete; India may continue its war against Japan.',
            [action('Record the Siam settlement', setf('siam_protected'), clear('siam_detached'),
                clear('siam_hold_watch'), clear('siam_hold_ready'), *legacy_cleanup(),
                'setflag which = ind_aubm_regional_settled_sia',
                'setflag which = ind_aubm_regional_protected_sia',
                'setflag which = ind_aubm_regional_victory_sia', gate=confirmed, chance=100),
             action('Protection is not confirmed; no reward is recorded', clear('siam_detached'),
                clear('siam_hold_watch'), clear('siam_hold_ready'), gate=no(confirmed), chance=100)]),
        event(BASE+8, 'Siam: Close an Abandoned Offer',
            'Siam no longer exists. Close the unfinished offer without changing any war, territory or government.',
            [action('Close the offer', clear('siam_break_pending'), clear('siam_detached'),
                clear('siam_hold_watch'), clear('siam_hold_ready'))],
            gate=all_of(no('exists = SIA'), any_of(flag('siam_break_pending'), flag('siam_detached'))),
            automatic=True, offset=1),
    ]

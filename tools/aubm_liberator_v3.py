"""LIBERATOR3: route cleanup, reactive intervention and readable campaign state.

All new events live in the already save-loaded settlement module. Country
watchers use the documented, country-relative `attack = JAP` predicate: merely
being at war with Japan is not evidence that Japan was the aggressor.
"""
from pathlib import Path
import re

from generate_aubm_liberator import (
    ROOT, ACTIVE, HUMAN, P, action, event, CANCEL, flag, setf, clear, no,
    all_of, any_of, war, owned, control, puppet, independent, later,
)
from aubm_liberator_v2 import (
    CHINA_DEEP, SOV_DEEP, JAP_DEEP, CA_MIN, COMPLETE, hold_events, age,
    conditional, peaceful_free, client,
)

BASE = 9294000
AI_FILE = 'aubm/japan/JAP_india_rupture.ai'
INDO_PROVINCES = (1395, 1396, 1397, 1399, 1403)
INDO_LEVERAGE = all_of(ACTIVE, war('JAP'), war('U03'),
    puppet('U03', 'JAP'), 'alliance = { country = U03 country = JAP }',
    *(owned(p, 'U03') for p in INDO_PROVINCES),
    *(control(p, 'IND') for p in INDO_PROVINCES))
INDO_READY = all_of(INDO_LEVERAGE, flag('indo_hold_ready'))
INDO_PARTNER = all_of(flag('indo_settled'), no(war('U03')),
    any_of(client('U03'), all_of(independent('U03'), flag('indo_sovereign'))),
    *(owned(p, 'U03') for p in (1395, 1399)),
    *(any_of(control(p, 'U03'), control(p, 'IND')) for p in (1395, 1399)))


def country_tags():
    # IDs survive future country-table additions and ordering changes.
    return [s for s in (ROOT/'tools/data/liberator3_country_ids.txt').read_text().splitlines()
            if s and not s.startswith('#')]


TAGS = country_tags()


def witnessed_war(tag):
    return all_of(flag('aggression_live_'+tag.lower()), f'exists = {tag}',
        f'war = {{ country = JAP country = {tag} }}')


AGGRESSION = any_of(*(witnessed_war(t) for t in TAGS))
INTERVENE = all_of(ACTIVE, 'exists = JAP', no(war('JAP')), AGGRESSION)


def ai_cleanup():
    eligible = all_of('ai = yes', 'exists = IND', 'flag = ind_aubm_jp_rupture',
        no('flag = ind_aubm_jp_partnership'), no('alliance = { country = IND country = JAP }'),
        no(flag('japan_ai_released')))
    renewed = all_of('flag = ind_aubm_jp_partnership', no('flag = ind_aubm_jp_rupture'),
        flag('japan_ai_released'))
    # This cleanup is not tied to the opt-in campaign or to peace. It repairs
    # diplomatic exits on every route, once per actual partnership lifecycle.
    return [event(BASE, 'Japan Resumes Independent Operational Planning',
        'The Indian partnership has ended. Remove its protection, front-passivity and naval-area exclusions. This changes AI planning only: no war, alliance, units or resources are created.',
        [action('Clear obsolete partnership restrictions',
            f'ai which = "{AI_FILE}"', setf('japan_ai_released'), gate=eligible)],
        gate=eligible, country='JAP', automatic=True, offset=1).replace('year = 1940', 'year = 1933'),
        event(BASE+1, 'A New Tokyo Partnership Has Its Own AI Lifecycle',
        'A newly valid partnership may use its own theatre instructions. A later rupture will again release those restrictions.',
        [action('Arm cleanup for the new partnership', clear('japan_ai_released'), gate=renewed)],
        gate=renewed, country='JAP', automatic=True, offset=1).replace('year = 1940', 'year = 1933')]


def aggression_events():
    out = []
    for n, tag in enumerate(TAGS):
        armed, live = 'aggression_armed_'+tag.lower(), 'aggression_live_'+tag.lower()
        pair_war = f'war = {{ country = JAP country = {tag} }}'
        peace = all_of(ACTIVE, 'exists = IND', no(pair_war),
            any_of(no(flag(armed)), flag(live)))
        attacked = all_of(ACTIVE, flag(armed), pair_war, 'attack = JAP')
        out += [event(9295000+n*2, f'Indian Observation: {tag} at Peace with Japan',
            'Record a peaceful baseline. A war already in progress when this programme starts is not relabelled as new Japanese aggression.',
            [action('Record peace; clear this old aggression notice', setf(armed), clear(live), gate=peace)],
            country=tag, gate=peace, automatic=True, offset=1),
            event(9295001+n*2, f'Indian Observation: Japan Attacks {tag}',
            'A country previously observed at peace is now fighting a war initiated by Japan. Record this fact for an optional Indian intervention; do not enter India into the war.',
            [action('Record Japanese aggression; India remains free to wait', clear(armed), setf(live), gate=attacked)],
            country=tag, gate=attacked, automatic=True, offset=1)]
    notice = all_of(INTERVENE, no(flag('aggression_notified')))
    clear_notice = all_of(flag('aggression_notified'), no(AGGRESSION))
    out += [event(BASE+2, 'Japan Has Started a New War: India May Respond',
        'The observation programme has verified fresh Japanese aggression. India has NOT declared war and has joined no alliance. The Respond to Japanese Aggression decision is available while a witnessed war continues. You may wait indefinitely; there is no deadline or automatic mobilisation.',
        [action('Remain neutral for now; review the decision when ready', setf('aggression_notified'), gate=notice)],
        gate=notice, automatic=True, offset=1),
        event(BASE+3, 'The Witnessed Japanese Wars Have Ended',
        'Close the old notification. Only a newly observed Japanese attack can open another aggression notice.',
        [action('Close the old notice', clear('aggression_notified'), gate=clear_notice)],
        gate=clear_notice, automatic=True, offset=1),
        event(BASE+4, 'Respond to Japanese Aggression',
        'Optional sovereign intervention, not membership of the Allies. Confirming declares war on Japan, with its alliance and puppet obligations applying, and adds 2 scripted dissent. India retains every existing war, including a Soviet war. Japan must have initiated a newly witnessed, still ongoing war. Cancel preserves neutrality. The confirmation page declares no war until you select its explicit declaration.',
        [CANCEL, action('Review declaration: Japan and its war system; +2 dissent', later(BASE+5, days=0), gate=INTERVENE)],
        gate=INTERVENE, decision=True),
        event(BASE+5, 'Confirm: Independent Indian War Against Japan',
        'DECLARE WAR NOW: India attacks Japan in response to verified Japanese aggression elsewhere. Scripted cost: +2 dissent. Japan\'s allies and puppets can enter through normal engine rules. India does not join Britain, America or another coalition and does not end any Soviet or other existing Indian war. Cancel does nothing. If the witnessed war or your sovereign status has ended, declaration is unavailable.',
        [CANCEL, action('Declare war on Japan now: +2 dissent', 'dissent value = 2',
            'war which = JAP', setf('japan_war'), setf('reactive_intervention'), gate=INTERVENE)])]
    return out


def indochina():
    out = hold_events(BASE+10, 'indo_hold', 'Break Japan\'s Indochinese Client',
        INDO_LEVERAGE, 30, 'Hold Hanoi, Dong Hoi, Da Nang, Saigon and Can Tho, all legally owned by the Japanese puppet U03, while fighting both U03 and Japan.')
    offer = all_of(INDO_READY, no(flag('indo_pending')), no(flag('indo_cooldown')),
        no(flag('indo_consent')), no(flag('indo_settled')),
        no('flag = ind_aubm_universal_armistice_outstanding'))
    live = all_of(INDO_READY, flag('indo_pending'), no('flag = ind_aubm_universal_armistice_outstanding'))
    free = all_of(ACTIVE, flag('indo_consent'), peaceful_free('U03'),
        *(owned(p, 'U03') for p in INDO_PROVINCES),
        *(control(p, 'U03') for p in INDO_PROVINCES), no(flag('indo_settled')))
    credit = ('setflag which = ind_aubm_sea_land_indochina_japan_occupation_seen',
              'setflag which = ind_aubm_sea_land_indochina_liberated',
              'setflag which = ind_aubm_sea_land_indochina_liberated_current')
    out += [event(BASE+13, 'Indochina: End Japanese Puppet Rule',
        'Five provinces held for 30 days: demand U03 leave Tokyo. Cost: 200 money, 750 supplies. Reply in three days: 80% accept, 20% refuse; retry after 90 days. Acceptance preserves U03 and its army, ends Japanese mastery and inherited alliance wars, and returns its occupied territory through peace. India keeps fighting Japan. Then choose independence or an Indian puppet. No automatic Vietnam/Laos/Cambodia release. Opening a generic peace file invalidates this paid offer.',
        [CANCEL, action('Demand Tokyo withdrawal: 80%; pay 200 and 750 supplies',
            'money value = -200', 'supplies value = -750', setf('indo_pending'),
            later(BASE+14, 'U03', 3), gate=all_of(offer, 'money = 200', 'supplies = 750'))],
        gate=offer, decision=True),
        event(BASE+14, 'Indochina: Delhi Offers an Exit from Tokyo',
        'Delhi has sustained control over the Vietnamese strategic corridor. Acceptance removes Japanese mastery and leaves Tokyo\'s alliance and inherited wars. Our government and surviving forces remain; Delhi will then ratify independent partnership or the offered Indian protection. India does not leave its own Japanese war.',
        [action('Accept withdrawal and the proposed Indian settlement', clear('indo_pending'),
            clear('indo_hold_watch'), clear('indo_hold_ready'), setf('indo_consent'),
            'end_puppet', 'leave_alliance when = 1', 'access which = IND', gate=live, chance=80),
         action('Refuse; continue the war', clear('indo_pending'), setf('indo_cooldown'),
            later(BASE+16, days=90), gate=live, chance=20),
         action('Leverage lost or another peace file opened', clear('indo_pending'), gate=no(live), chance=100)],
        country='U03'),
        event(BASE+15, 'Indochina: Choose the Post-Japanese Government',
        'U03 has left Tokyo and recovered the five provinces. INDEPENDENT PARTNER: sovereignty, access, +1 TC, -1 dissent. INDIAN PUPPET: Indian mastery, +2 TC, +3 dissent; normal puppet obligations apply. Either counts as ONE southern partner while its relationship and hubs survive. India\'s other wars continue. Cancel postpones freely. A separate Vietnam petition remains possible after independent recognition. Neither choice releases Laos or Cambodia automatically.',
        [CANCEL,
         action('Independent Indochina: +1 TC, -1 dissent', setf('indo_settled'),
            setf('indo_sovereign'), clear('indo_consent'), *credit,
            'guarantee which = IND where = U03', 'tc_mod value = 1', 'dissent value = -1', gate=free),
         action('Indian puppet Indochina: +2 TC, +3 dissent', setf('indo_settled'),
            clear('indo_consent'), *credit, 'make_puppet which = U03', 'tc_mod value = 2',
            'dissent value = 3', gate=free)], gate=free, decision=True),
        event(BASE+16, 'Indochina: A New Offer May Be Prepared',
        'The 90-day refusal interval has ended. The offer still needs the full current campaign leverage.',
        [action('End the Indochinese refusal interval', clear('indo_cooldown'), gate=flag('indo_cooldown'))]),
        event(BASE+17, 'Indochina: Close an Invalid Pending Offer',
        'A required city, war, puppet relationship or Indian route changed. Clear only the pending offer; no peace or reward is issued.',
        [action('Close this invalid request', clear('indo_pending'), gate=all_of(flag('indo_pending'), no(live)))],
        gate=all_of(flag('indo_pending'), no(live)), automatic=True, offset=1)]
    clock = all_of(ACTIVE, flag('indo_settled'), client('U03'), no(flag('indo_client_clock')))
    review = all_of(ACTIVE, flag('indo_client_clock'), client('U03'),
        no('atwar = U03'), no(war('JAP')), age(BASE+18, 730))
    out += [event(BASE+18, 'Indochina: Protectorate Review Clock Starts',
        'An actual Indian puppet has been verified. After two years and peace for U03 and with Japan, full independence becomes optional. Retaining protection adds no new recurring penalty.',
        [action('Record the actual protectorate', setf('indo_client_clock'), gate=clock)],
        gate=clock, automatic=True, save_date=True),
        event(BASE+19, 'Indochina: Optional Full Independence',
        'End Indian mastery and guarantee U03. A separate alliance, if one exists, remains. Southern-partner credit can survive under sovereignty; no original reward is paid again. Cancel retains the puppet.',
        [CANCEL, action('Grant independence; retain the sovereign partnership',
            'end_mastery which = U03', 'guarantee which = IND where = U03', setf('indo_sovereign'), gate=review)],
        gate=review, decision=True)]
    return out


def status(label, gate=''):
    return action('STATUS: '+label, gate=gate)


def city_lines(provinces):
    return [a for p, name in provinces for a in (
        status(name+' secured by India', control(p, 'IND')),
        status(name+' still required', no(control(p, 'IND'))))]


def clock_lines(key, base, days):
    watch, ready = flag(key+'_watch'), flag(key+'_ready')
    result = [status('Hold is not currently running', all_of(no(watch), no(ready))),
              status('Hold complete; keep leverage until acceptance', ready)]
    for start in range(0, days, 30):
        end = min(start+30, days)
        gate = all_of(watch, no(ready), age(base, start), no(age(base, end)))
        result.append(status(f'Hold underway: days {start}-{end-1} of {days}', gate))
    result.append(status('Hold due: daily verification pending', all_of(watch, no(ready), age(base, days))))
    return result


INFO = ('STATUS lines are read-only and close this page. Holds use 30-day bands; incomplete holds reset on daily checks. ')


def progress():
    menu = all_of(HUMAN, flag('enabled'))
    pages = [
        (BASE+31, 'China: Cities and Settlement Status',
         'An independent three-city deal ends access to the stronger puppet demand. For a puppet, add Chongqing and hold all four cities for 60 days. Japan and U87 must both be enemies and U87 must still be Tokyo\'s puppet.',
         city_lines(((1337,'Nanjing'),(1338,'Shanghai'),(1317,'Wuhan'),(1299,'Chongqing'))) +
         clock_lines('china_hold',9289900,60) + [
             status('Chinese reply pending',any_of(flag('china_pending'),flag('china_protection_pending'))),
             status('Refused: 90-day retry interval active',flag('china_cooldown')),
             status('Consent received: ratify the protectorate decision',flag('china_protection_consent')),
             status('Chinese Indian protectorate established',flag('china_protectorate'))]),
        (BASE+32, 'USSR: Strategic Cities and Hold Status',
         'Baku, Tashkent, Astrakhan and Stalingrad plus ONE of Sverdlovsk, Omsk or Moscow are required. Also occupy two COMPLETE Soviet-owned republic territories; use the republic checklist. Limited frontier peace creates no republics.',
         city_lines(((713,'Baku'),(1103,'Tashkent'),(706,'Astrakhan'),(663,'Stalingrad'))) + [
             status('One required interior hub secured',any_of(*(control(p,'IND') for p in (1151,1138,572)))),
             status('Still need Sverdlovsk, Omsk or Moscow',no(any_of(*(control(p,'IND') for p in (1151,1138,572)))))] +
         clock_lines('sov_hold',9289910,90) + [
             status('Soviet reply pending',all_of('flag = ind_aubm_local_armistice_outstanding','flag = ind_aubm_local_armistice_target_sov')),
             status('Soviet retry interval active','flag = ind_aubm_local_armistice_retry_sov'),
             status('Deep protected settlement achieved',flag('sov_deep_settled'))]),
        (BASE+33, 'USSR: Complete Republic Checklist',
         'Need any TWO complete, absent republics: every minimum province legally Soviet-owned and controlled by India. Turkmenistan: 1097-1098; Uzbekistan: 1099-1103; Tajikistan: 1104-1105; Kyrgyzstan: 1106-1107; Kazakhstan: 498,500,504-507. A capital alone is insufficient. Already-existing states cannot be gifted by Moscow.',
         [a for (tag, _), requirement in zip(CA_MIN.items(), COMPLETE) for a in (
             status(tag+': complete and eligible',requirement),
             status(tag+': incomplete or already exists',no(requirement)))]),
        (BASE+34, 'Japan: Optional Home-Island Campaign',
         'The home-island campaign is OPTIONAL. Hold Tokyo, Osaka and Hiroshima for 60 days while fighting Japan, then obtain the FULL Japanese armistice or eliminate Japan to unlock the paid investment. Limited peace alone does not qualify.',
         city_lines(((1552,'Tokyo'),(1553,'Osaka'),(1554,'Hiroshima'))) + clock_lines('jap_hold',9289920,60) + [
             status('Historical home-island hold earned',flag('jap_hold_earned')),
             status('Postwar home-island investment paid',flag('jap_legacy'))]),
        (BASE+35, 'Indochina: Japanese-Client Settlement Status',
         'This branch applies to U03 as a JAPANESE PUPPET, not friendly colonial liberation. Secure all five listed provinces for 30 days. Submit the withdrawal offer, await consent, then choose sovereign partnership or Indian protection. A generic limited U03 peace does not itself grant this settlement.',
         city_lines(((1395,'Hanoi'),(1396,'Dong Hoi'),(1397,'Da Nang'),(1399,'Saigon'),(1403,'Can Tho'))) +
         clock_lines('indo_hold',BASE+10,30) + [
             status('Indochinese reply pending',flag('indo_pending')),
             status('Refused: 90-day retry interval active',flag('indo_cooldown')),
             status('Consent received: choose the new government',flag('indo_consent')),
             status('Live southern partner secured',INDO_PARTNER)]),
        (BASE+36, 'Southern Peace: Campaign and Partner Checklist',
         'Complete the Southeast Asian operational theatre (two land achievements plus one sea lane, or one land plus two sea lanes), end the Japan war and retain TWO distinct live regional partners. Indochina and Vietnam are ONE regional slot, never two. China may be a consenting Indian puppet. Suez and invading Japan itself are optional.',
         [status('Operational theatre achieved','flag = ind_aubm_sea_theatre_achieved'),
          status('Operational theatre still required',no('flag = ind_aubm_sea_theatre_achieved')),
          status('Japan war is still ongoing',war('JAP')),
          status('Japan war has ended',all_of(flag('japan_war'),no(war('JAP')))),
          status('Southern peace dividend recorded',flag('southern_peace'))]),
    ]
    from generate_aubm_liberator import REGIONS, partner_gate, CHINA_FREE
    for r in REGIONS:
        gate=all_of(flag(r.key+'_reward'),partner_gate(r))
        if r.key=='indochina': gate=any_of(gate,INDO_PARTNER)
        pages[-1][3].extend([status(r.title+': live partner',gate),status(r.title+': partner not yet secured',no(gate))])
    china = any_of(all_of(flag('china_reward'),CHINA_FREE),all_of(flag('china_protectorate'),client('U87')))
    pages[-1][3].extend([status('China: live partner',china),status('China: partner not yet secured',no(china))])
    # Keep each page small enough for the game's smaller window sizes. Navigation
    # is immediate, user-driven and acyclic; Cancel has no callback at all.
    original={eid:(title,desc,lines) for eid,title,desc,lines in pages}
    def part(eid,source,title,lines):
        return (eid,title,original[source][1],lines)
    c=original[BASE+31][2];s=original[BASE+32][2];r=original[BASE+33][2]
    j=original[BASE+34][2];i=original[BASE+35][2];south=original[BASE+36][2]
    pages=[part(BASE+40,BASE+31,'China: Four Cities',c[:8]),
           part(BASE+41,BASE+31,'China: Hold and Negotiations',c[8:]),
           part(BASE+42,BASE+32,'USSR: Four Southern Hubs',s[:8]),
           part(BASE+43,BASE+32,'USSR: Interior Hub, Hold and Negotiations',s[8:]),
           part(BASE+44,BASE+33,'Republics: Turkmenistan, Uzbekistan, Tajikistan',r[:6]),
           part(BASE+45,BASE+33,'Republics: Kyrgyzstan and Kazakhstan',r[6:]),
           part(BASE+46,BASE+34,'Japan: Three Home-Island Cities',j[:6]),
           part(BASE+47,BASE+34,'Japan: Hold and Peace Dividend',j[6:]),
           part(BASE+49,BASE+35,'Indochina: Saigon and Can Tho',i[6:10]),
           part(BASE+50,BASE+35,'Indochina: Hanoi, Dong Hoi and Da Nang',i[:6]),
           part(BASE+51,BASE+35,'Indochina: Hold and Negotiations',i[10:]),
           part(BASE+52,BASE+36,'Southern Peace: Theatre and Japanese War',south[:5]),
           part(BASE+53,BASE+36,'Southern Partners: Malaya and Indonesia',south[5:9]),
           part(BASE+54,BASE+36,'Southern Partners: Indochina/Vietnam and China',south[9:11]+south[-2:]),
           part(BASE+55,BASE+36,'Southern Partners: The Philippines',south[11:13])]
    menus=[(BASE+31,'China Progress',[(BASE+40,'Four-city checklist'),(BASE+41,'Hold and negotiations')]),
           (BASE+32,'Soviet Progress',[(BASE+42,'Four southern hubs'),(BASE+43,'Interior hub, hold and negotiations'),(BASE+33,'Complete republic territories')]),
           (BASE+33,'Soviet Republic Checklist',[(BASE+44,'Turkmenistan, Uzbekistan and Tajikistan'),(BASE+45,'Kyrgyzstan and Kazakhstan')]),
           (BASE+34,'Japanese Home-Island Progress',[(BASE+46,'Three-city checklist'),(BASE+47,'Hold and postwar investment')]),
           (BASE+35,'Southern Campaign Progress',[(BASE+48,'Indochina: five-province checklist'),(BASE+51,'Indochina: hold and negotiations'),(BASE+36,'Southern peace and partners')]),
           (BASE+48,'Indochina Province Checklist',[(BASE+50,'Hanoi, Dong Hoi and Da Nang'),(BASE+49,'Saigon and Can Tho')]),
           (BASE+36,'Southern Peace and Partners',[(BASE+52,'Theatre achievement and Japanese war'),(BASE+53,'Malaya and Indonesia'),(BASE+54,'Indochina/Vietnam and China'),(BASE+55,'The Philippines')])]
    out = [event(BASE+30, 'LIBERATOR3 - Campaign Progress Board',
        'Installed campaign revision: LIBERATOR3 / COMMAND-RESERVE1. This is a read-only progress board, available at peace and war. Current status appears as labelled lines on each page. No page starts a war, spends resources, changes your route or opens a looping cabinet. New commanders are already in new campaigns; existing campaigns need the separately repaired save.',
        [CANCEL]+[action(title,later(eid,days=0)) for eid,title in
            ((BASE+31,'China'),(BASE+32,'Soviet Union'),(BASE+34,'Japan: optional home-island campaign'),(BASE+35,'Indochina and the southern peace'))],gate=menu,decision=True)]
    out += [event(eid,title,'Read-only pages. Navigation is immediate and spends no resources or game days. Cancel closes without returning to the War Cabinet.',
        [CANCEL]+[action(label,later(target,days=0)) for target,label in links]) for eid,title,links in menus]
    out += [event(eid,title,INFO+desc,[CANCEL]+lines) for eid,title,desc,lines in pages]
    return out


def revise_pack(blocks):
    out=[]
    for b in blocks:
        eid=int(re.search(r'\bid = (\d+)',b)[1])
        if eid in (9289800,9289801,9289880): b=b.replace('LIBERATOR2','LIBERATOR3')
        if eid==9289801:
            b=re.sub(r'(?m)^\tdesc = .*$', '\tdesc = "This guide changes no resources or route. Use the LIBERATOR3 Campaign Progress Board for current cities, hold periods and negotiations. Fresh Japanese aggression is observed only after a peaceful baseline. Respond to Japanese Aggression offers optional, confirmed intervention; it never enters India automatically. The Long-War Objectives guide explains the stronger Chinese and Soviet settlements. Sovereign treaties and Indian puppet choices have different obligations."',b)
        if eid==9289850:
            b=re.sub(r'(?m)^\tdesc = .*$', '\tdesc = "Hold Nanjing, Shanghai and Wuhan against Japan and its Nanjing puppet. Cost: 250 money, 750 supplies; 60% accept, 40% refuse. ACCEPTANCE MAKES CHINA INDEPENDENT and ends its inherited alliance wars, not India\'s Japan war. WARNING: this removes access to the stronger Indian-puppet demand. For a puppet, cancel, add Chongqing and hold all four cities for 60 days. U87 and its units survive; Chiang is not restored and Japanese-owned Shanghai is not ceded."',b)
            b=b.replace('Offer sovereignty and a separate Chinese peace', 'Choose independent China; forgo the puppet demand')
        if eid==9289905:
            b=b.replace('Honour the Chinese break as full independence', 'Choose full independence; forgo this puppet ratification')
        if eid==9289802:
            b=re.sub(r'(?m)^\tdesc = .*$', '\tdesc = "Friendly-owner path: retake Japanese-occupied hubs, earn liberation credit, restore release territory, petition the owner, then offer an equal treaty. Enemy U03 path: defeat Japan\'s puppet across five provinces for 30 days, negotiate its Tokyo exit and choose its new status. Indochina and Vietnam share ONE partner slot. Southern peace needs the operational theatre, peace with Japan and two live regional partners. Vietnam does not include Laos or Cambodia."',b)
        out.append(b)
    return out


def render_events():
    return ai_cleanup()+aggression_events()+indochina()+progress()

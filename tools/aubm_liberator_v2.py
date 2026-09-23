"""Long-war settlements; kept in save-loaded module 43. No save migration.

Native saved event dates measure consolidation. Daily checks revoke an active
hold, while completed achievement flags are historical and cannot pay twice.
Only enumerated legacy events are patched; other routes retain their gates.
"""
from itertools import combinations
from pathlib import Path
import re

from aubm_menu_safety import event_spans
from generate_aubm_liberator import (
    ACTIVE, P, CA, CHINA_LEVERAGE, CHINA_FREE, CHINA_RETURN,
    action, event, CANCEL, flag, setf, clear, no, all_of, any_of,
    control, owned, war, puppet, independent, later,
)

LEGACY_IDS = {9282036, 9282037, 9282038, 9282040, 9282043, 9282044, 9282046}
CA_MIN = {
    'TRK': (1097,1098), 'UZB': (1099,1100,1101,1102,1103),
    'TAJ': (1104,1105), 'KYG': (1106,1107), 'KAZ': (498,500,504,505,506,507),
}
SOV_HUBS = all_of(*(control(p,'IND') for p in (713,1103,706,663)),
    any_of(*(control(p,'IND') for p in (1151,1138,572))))
COMPLETE = [all_of(no(f'exists = {t}'), *(owned(p,'SOV') for p in ps),
    *(control(p,'IND') for p in ps)) for t,ps in CA_MIN.items()]
SOV_DEEP = all_of(ACTIVE, war('SOV'), SOV_HUBS,
    any_of(*(all_of(a,b) for a,b in combinations(COMPLETE,2))))
SOV_READY = all_of(SOV_DEEP, flag('sov_hold_ready'))
CHINA_DEEP = all_of(CHINA_LEVERAGE, owned(1299,'U87'), control(1299,'IND'))
JAP_DEEP = all_of(ACTIVE, war('JAP'), *(control(p,'IND') for p in (1552,1553,1554)))


def age(eid, days): return f'event = {{ id = {eid} days = {days} }}'
def conditional(gate, command): return f'trigger = {{ {gate} }} type = {command}'
def client(tag): return all_of(f'exists = {tag}', puppet(tag,'IND'), no(war(tag)))
def peaceful_free(tag):
    return all_of(independent(tag), no(f'atwar = {tag}'),
        *(no(f'alliance = {{ country = {tag} country = {t} }}') for t in ('ENG','GER','SOV','USA')))


def hold_events(base, key, title, valid, days, requirements):
    start = all_of(valid, no(flag(key+'_watch')), no(flag(key+'_earned')))
    bad = all_of(flag(key+'_watch'), no(flag(key+'_earned')), no(valid))
    mature = all_of(valid, flag(key+'_watch'), age(base,days), no(flag(key+'_ready')))
    # A historical Japanese victory is retained after peace. China and Soviet
    # readiness are only current negotiating leverage, not permanent bypasses.
    return [event(base, title+': Consolidation Begins',
        f'{requirements} Maintain these conditions for {days} days. Daily checks reset this attempt if a requirement fails. This starts a record; it does not sign peace or grant territory.',
        [action(f'Begin the {days}-day consolidation record', setf(key+'_watch'), gate=start)],
        gate=start, automatic=True, offset=1, save_date=True),
        event(base+1, title+': Consolidation Interrupted',
        'The required front, territory or independent Indian route was lost. Current negotiating readiness is removed. A new attempt starts from day zero; no old conquest reward is replayed.',
        [action('Reset the incomplete consolidation record', clear(key+'_watch'), clear(key+'_ready'), gate=bad)],
        gate=bad, automatic=True, offset=1),
        event(base+2, title+': Sustained Victory Recorded',
        f'The {days}-day consolidation is complete. {requirements} This unlocks the stated settlement or postwar choice; it does not compel peace. Keep current negotiating positions until terms are accepted.',
        [action('Record the sustained campaign result', setf(key+'_ready'),
            *([setf(key+'_earned')] if key=='jap_hold' else []), gate=mature)],
        gate=mature, automatic=True, offset=1)]


def render_events(_context=None):
    out = hold_events(9289900,'china_hold','Four-City Chinese Campaign', CHINA_DEEP,60,
        'Hold Nanjing, Shanghai, Wuhan and Chongqing while fighting Japan and its Nanjing puppet.')
    out += hold_events(9289910,'sov_hold','Beyond the Soviet Southern Frontier', SOV_DEEP,90,
        'Hold Baku, Tashkent, Astrakhan and Stalingrad, plus Sverdlovsk, Omsk or Moscow, and two complete Soviet-owned republic territories.')
    out += hold_events(9289920,'jap_hold','The Japanese Home-Island Campaign', JAP_DEEP,60,
        'Hold Tokyo, Osaka and Hiroshima as India while at war with Japan.')

    offer = all_of(CHINA_DEEP, flag('china_hold_ready'), no(flag('china_pending')),
        no(flag('china_protection_pending')), no(flag('china_cooldown')), no(flag('china_break')))
    live = all_of(CHINA_DEEP, flag('china_hold_ready'), flag('china_protection_pending'))
    confirm = all_of(ACTIVE, flag('china_protection_consent'), peaceful_free('U87'),
        *(owned(p,'U87') for p in CHINA_RETURN), *(control(p,'U87') for p in CHINA_RETURN),
        no(flag('china_protectorate')))
    out += [event(9289903, 'Chinese Settlement: Demand an Indian Protectorate',
        'After the four-city 60-day campaign, demand an Indian puppet government. Cost: 350 money and 1,000 supplies. Acceptance 80%, refusal 20%, retry in 90 days. Consent first removes China from Tokyo and its inherited wars. A separate Indian decision then establishes the puppet. India does not leave its Japanese war. U87 and its units survive; this is not Chiang or annexation.',
        [action('Demand an Indian puppet: 80% acceptance', 'money value = -350', 'supplies value = -1000',
            setf('china_protection_pending'), later(9289904,'U87',3),
            gate=all_of(offer,'money = 350','supplies = 1000')), CANCEL], gate=offer, decision=True),
        event(9289904, 'Nanjing: The Indian Protectorate Terms',
        'India has held four strategic cities for 60 days. Accepting ends Japanese mastery and leaves Tokyo and its inherited alliance wars. Delhi may then establish an Indian puppet relationship. The existing Chinese state survives. Refusal keeps the Japanese relationship; India can offer again after 90 days.',
        [action('Accept the proposed Indian protectorate', clear('china_protection_pending'), clear('china_hold_watch'), clear('china_hold_ready'), setf('china_protection_consent'),
            setf('china_break'), 'end_puppet', 'leave_alliance when = 1', 'access which = IND', gate=live, chance=80),
         action('Refuse; remain with Tokyo', clear('china_protection_pending'), setf('china_cooldown'), later(9289853,days=90), gate=live,chance=20),
         action('The proposed settlement is no longer valid', clear('china_protection_pending'), gate=no(live),chance=100)],country='U87'),
        event(9289905, 'Ratify the Chinese Protectorate',
        'China has left Tokyo, is at peace, and has recovered Nanjing and Wuhan. Ratify to make U87 an Indian puppet: +3 dissent, +4 TC and 2,000 supplies once. Puppet obligations apply; this is not an equal treaty. No explicit alliance or war command is issued. India remains in its current wars. After two years and peace with Japan, you may grant full independence without replaying rewards. Cancel postpones ratification.',
        [action('Make China an Indian puppet: +3 dissent', setf('china_protectorate'), clear('china_protection_consent'),
            setf('china_reward'), 'make_puppet which = U87', 'tc_mod value = 4', 'supplies value = 2000', 'dissent value = 3',gate=confirm),
         action('Honour the Chinese break as full independence', clear('china_protection_consent'), 'guarantee which = IND where = U87',gate=confirm), CANCEL],
        gate=confirm,decision=True),
    ]
    # Start the two-year clock from an observed puppet, not a cancellable menu.
    for n,tag in enumerate(('U87',)+CA):
        mark = 9289940+n*2
        earned = flag('china_protectorate') if tag=='U87' else all_of(flag('sov_deep_settled'), client(tag))
        record = all_of(ACTIVE, earned, client(tag), no(flag(f'client_clock_{tag.lower()}')))
        free = all_of(ACTIVE, client(tag), flag(f'client_clock_{tag.lower()}'), age(mark,730),
            no(war('JAP' if tag=='U87' else 'SOV')), no(f'atwar = {tag}'))
        out += [event(mark, f'{tag}: Protectorate Review Clock Starts',
            'An actual Indian puppet relationship has been verified. Full independence becomes an optional decision after two years and peace for this state and its former imperial opponent. No automatic release, upkeep event or repeated loyalty payment follows.',
            [action('Record the start of the constitutional review',setf(f'client_clock_{tag.lower()}'),gate=record)],
            gate=record,automatic=True,save_date=True),
            event(mark+1, f'{tag}: Optional Full Independence',
            'This Indian puppet has completed its two-year review and is at peace; India is no longer fighting its former imperial opponent. Granting independence ends Indian mastery and guarantees the state. It does not dissolve a separate alliance or replay conquest rewards. Cancel retains the puppet with no new cost. Future cooperation is diplomacy, not continued Indian ownership.',
            [action('End Indian puppet rule; guarantee independence', f'end_mastery which = {tag}',
                f'guarantee which = IND where = {tag}',setf(f'client_freed_{tag.lower()}'),gate=free), CANCEL], gate=free,decision=True)]

    sov_live = all_of(SOV_READY, 'flag = ind_aubm_local_armistice_target_sov',
        'flag = ind_aubm_local_armistice_outstanding', 'flag = ind_aubm_local_soviet_protected_terms')
    out += [event(9289914, 'Moscow: The Deep Central Asian Settlement',
        'India has sustained a major inland offensive, not merely raided the frontier. Accept 80%: transfer only complete occupied Soviet republic territories for separate Indian puppet states. Refuse 20%: continue the war, with a 90-day retry. No free five-state release and no compulsory base-rights counteroffer. India need not annex Russia or occupy Moscow if it has reached the Urals or Omsk.',
        [action('Accept the earned protected-republic settlement',setf('sov_deep_accepted'),
            later(9282046,'SOV'),later(9282043,days=3),gate=sov_live,chance=80),
         action('Refuse the Indian terms',later(9282045,days=3),gate=sov_live,chance=20),
         action('The Indian proposal has lost its required leverage',later(9282045,days=1),gate=no(sov_live),chance=100)],country='SOV')]

    live_ca = [all_of(any_of(client(t), all_of(independent(t),flag(f'client_freed_{t.lower()}'))),
        *(owned(p,t) for p in ps), *(control(p,t) for p in ps)) for t,ps in CA_MIN.items()]
    two_ca = any_of(*(all_of(a,b) for a,b in combinations(live_ca,2)))
    sov_peace = all_of(ACTIVE, flag('sov_deep_accepted'), no(war('SOV')),
        'flag = ind_aubm_settlement_central_asia_protected',two_ca,no(flag('sov_deep_settled')))
    out += [event(9289915,'Central Asia: An Indian-Protected Political Order',
        'The Soviet war has ended and at least two complete republics actually exist as Indian puppets. The new sphere is a political result, not direct Indian annexation. Its development programme is now available. Each verified republic receives an optional independence review after two years. Other Indian wars need not end.',
        [action('Record the achieved Central Asian settlement',setf('sov_deep_settled'),gate=sov_peace)],gate=sov_peace,automatic=True)]
    development = all_of(ACTIVE, flag('sov_deep_settled'), two_ca, no(war('SOV')), no(flag('sov_legacy')))
    paid = all_of(development,'money = 500','supplies = 2000')
    out += [event(9289916,'Central Asian Victory: Choose the Lasting Investment',
        'A deep Soviet victory created a surviving Indian-protected region. Invest 500 money and 2,000 supplies once. Choose frontier logistics (+8 TC and +5 supply output), or Indian industrial development (+2 base IC each in Delhi, Bombay and Calcutta). These are alternatives, not stacking prizes. The normal reconstruction grant remains separate. No Soviet factories or manpower are magically inherited.',
        [action('Frontier network: +8 TC and +5 supply output',setf('sov_legacy'),'money value = -500','supplies value = -2000',
            'tc_mod value = 8','industrial_modifier which = supplies value = 5',gate=paid),
         action('Indian industry: +6 base IC across three cities',setf('sov_legacy'),'money value = -500','supplies value = -2000',
            *(conditional(all_of(owned(p,'IND'),control(p,'IND')),f'construct which = ic where = {p} value = 2') for p in (1459,1517,1447)),
            gate=all_of(paid,*(all_of(owned(p,'IND'),control(p,'IND')) for p in (1459,1517,1447)))),CANCEL],gate=development,decision=True)]

    jap_peace = all_of(ACTIVE,flag('jap_hold_earned'),no(war('JAP')),
        any_of('flag = ind_aubm_armistice_japan',no('exists = JAP')),no(flag('jap_legacy')))
    paid = all_of(jap_peace,'money = 500','supplies = 2000')
    out += [event(9289923,'After the Home-Island War: The Indian Peace Dividend',
        'India held Tokyo, Osaka and Hiroshima for 60 days, then secured the full Japanese armistice or Japan ceased to exist. Invest 500 money and 2,000 supplies once. Choose a blue-water logistics system (+8 TC, +5 supply output, +2 research), or rebuild Indian industry (+2 base IC each in Delhi, Bombay and Calcutta). This is Indian development, not annexation of Japan or fabricated Japanese reparations. A limited peace alone does not qualify.',
        [action('Blue-water future: logistics and research',setf('jap_legacy'),'money value = -500','supplies value = -2000',
            'tc_mod value = 8','industrial_modifier which = supplies value = 5','research_mod value = 2',gate=paid),
         action('Industrial future: +6 base IC in India',setf('jap_legacy'),'money value = -500','supplies value = -2000',
            *(conditional(all_of(owned(p,'IND'),control(p,'IND')),f'construct which = ic where = {p} value = 2') for p in (1459,1517,1447)),
            gate=all_of(paid,*(all_of(owned(p,'IND'),control(p,'IND')) for p in (1459,1517,1447)))),CANCEL],gate=jap_peace,decision=True)]

    # Independent missions build on actual prior settlements. No third country's
    # sovereignty changes because China or the USSR lost a war elsewhere.
    tib = all_of(ACTIVE, client('TIB'), owned(1289,'TIB'),control(1289,'TIB'),no(war('TIB')))
    west = all_of(ACTIVE,*(all_of(no(war(t)),any_of(
        all_of(client(t),owned(p,t),control(p,t)),all_of(owned(p,'IND'),control(p,'IND'))))
        for t,p in (('PER',1085),('AFG',2171))))
    for base,key,title,valid,desc,tc,supply,cost in (
        (9289930,'tib_mission','The Himalayan Protectorate',tib,
         'Tibet must actually be an Indian puppet and hold Lhasa. Use its existing settlement docket after your Tibetan campaign; choose Protect Tibet after annexation. China cannot give you Tibet.',3,2,200),
        (9289934,'west_mission','The Independent Western Corridor',west,
         'Tehran and Kabul must be secure under their Indian puppet governments or direct Indian ownership, with India at peace with both states. This is an optional Persian-Afghan campaign, independent of Japan and the USSR.',5,3,300),
    ):
        out += hold_events(base,key,title,valid,90,desc)
        gate = all_of(valid,flag(key+'_ready'),no(flag(key+'_paid')))
        out += [event(base+3,title+': Fund a Working Settlement',
            f'After 90 days of stable control, invest {cost} money and 1,000 supplies. Gain +{tc} TC and +{supply} supply output once. {desc} No declaration, annexation or new puppet relationship is hidden in this investment. Japan, Soviet and Suez outcomes are not prerequisites.',
            [action('Fund the secured regional network',setf(key+'_paid'),setf(key+'_earned'),f'money value = -{cost}',
                'supplies value = -1000',f'tc_mod value = {tc}',f'industrial_modifier which = supplies value = {supply}',
                gate=all_of(gate,f'money = {cost}','supplies = 1000')),CANCEL],gate=gate,decision=True)]

    invalid = all_of(flag('china_protection_pending'),no(all_of(CHINA_DEEP,flag('china_hold_ready'))))
    out += [event(9289952,'Close an Invalid Chinese Protection Offer',
        'The recipient, four-city front, or independent Indian route no longer supports the dispatched proposal. Clear its pending state without a refund or diplomatic change.',
        [action('Close the invalid proposal',clear('china_protection_pending'),gate=invalid)],gate=invalid,automatic=True,offset=1),
        event(9289953,'LIBERATOR2 - Long-War Objectives and Endings',
        'Limited peace is an exit, not total victory. China: four cities for 60 days unlock an 80% puppet offer; three cities retain the lighter sovereign offer. USSR: four southern hubs, one interior hub and two complete republics for 90 days. Japan: home-island occupation is optional, with its own lasting dividend. Tibet and the western corridor are independent missions. Read the next page for exact Soviet hubs. Cancel always closes this guide.',
        [action('Read the exact deep Soviet requirements',later(9289954)),action('Read the independent missions',later(9289955)),CANCEL],
        gate=all_of(flag('enabled'),'ai = no'),decision=True),
        event(9289954,'LIBERATOR2 - The Soviet Defeat Threshold',
        'Baku, Tashkent, Astrakhan AND Stalingrad; ALSO Sverdlovsk OR Omsk OR Moscow. Hold these and at least two complete Soviet-owned republic territories for 90 days. Protected terms: 80% accept, 20% refuse, 90-day retry. Only fully occupied republics transfer, not all five automatically. The existing +6 dissent cost of creating puppets remains. A frontier victory still permits a limited base-rights peace; you may reject that counteroffer.',[CANCEL]),
        event(9289955,'LIBERATOR2 - Independent Missions and Reviews',
        'Tibet: after annexation, choose Protect Tibet in its settlement docket, then secure Lhasa for 90 days and invest for a Himalayan logistics reward. West: secure Tehran and Kabul under India or its puppets, end those wars, hold 90 days and invest. Neither requires Japan, the USSR or Suez. Chinese and Central Asian puppets have an optional independence review after two years and the relevant peace; retaining them is free of new scripted penalties.',[CANCEL])]
    return out


def revise_pack(blocks, _context=None):
    replacements = {
        9289800: ('LIBERATOR2 - India\'s Independent Campaigns',
            'Optional extension for existing saves and fresh campaigns from 1940. Stay sovereign and choose your wars. Earn Chinese protection, deeper Soviet republic settlements, and lasting development after major or independent campaigns. Suez remains optional. Enabling changes no history, resources or alliances and declares no war. The LIBERATOR2 Long-War Objectives guide gives the exact new requirements.'),
        9289801: ('LIBERATOR2 - Liberation Campaign Guide',
            'This guide changes no resources or route. The separate LIBERATOR2 Long-War Objectives decision explains the stronger puppet settlements and deeper Soviet threshold. These pages cover the existing sovereign liberation options. Neutral India does not automatically fight when Japan attacks Britain or America. Treaties preserve independence; protectorate choices explicitly create Indian puppets.'),
        9289803: ('Liberation Guide: Wider Objectives',
            'China: three cities allow an independent exit from Tokyo; adding Chongqing and holding all four for 60 days unlocks the stronger Indian puppet offer. Shanghai stays a Japanese ownership question. Tibet is a separate settlement, not a Chinese gift. Suez is optional. Use the LIBERATOR2 Long-War Objectives decision for new northern and independent missions.'),
        9289808: ('Liberation Guide: Northern Peace and Replacements',
            'Baku plus Tashkent or Astrakhan earns a frontier milestone, not a republic settlement. LIBERATOR2 requires a sustained inland offensive for Central Asian releases; see its Long-War Objectives guide. During a Japan or Soviet war, 100 divisions and fewer than 400 manpower allow a paid extra class: +180 manpower for 900 supplies, 100 money and +1 dissent, once per year. Existing reserves remain separate.'),
    }
    result=[]
    for b in blocks:
        eid=int(re.search(r'\bid = (\d+)',b)[1])
        if eid in replacements:
            name,desc=replacements[eid]
            b=re.sub(r'(?m)^\tname = "[^"]*"',f'\tname = "{name}"',b,count=1)
            b=re.sub(r'(?m)^\tdesc = "[^"]*"',f'\tdesc = "{desc}"',b,count=1)
        if eid==9289852:
            # A protection offer cannot collect the sovereign reward in the
            # gap between withdrawal and Indian puppet ratification.
            b=b.replace(no(flag('china_reward')),all_of(no(flag('china_reward')),no(flag('china_protection_consent'))))
        if eid==9289851:
            b=b.replace('command = { type = end_puppet }',
                'command = { type = '+clear('china_hold_watch')+' }\n\t\tcommand = { type = '+clear('china_hold_ready')+' }\n\t\tcommand = { type = end_puppet }')
        if eid==9289880: b=b.replace('LIBERATOR1','LIBERATOR2')
        result.append(b)
    return result


def patch_legacy(raw):
    """Idempotent, allowlisted edits; byte-preserve all other legacy events."""
    text=raw.decode('cp1252')
    baseline_text=(Path(__file__).parent/'fixtures/liberator2_legacy43.txt').read_text(encoding='cp1252')
    baseline={i:baseline_text[s:e] for s,e,i in event_spans(baseline_text)}
    changes=[]
    for start,end,eid in event_spans(text):
        if eid not in LEGACY_IDS: continue
        block=text[start:end]
        if '# LIBERATOR2_LEGACY' not in block and block.replace('\r\n','\n') != baseline[eid]:
            raise ValueError(f'Unreviewed legacy change in {eid}; preserve it and review before rebuilding')
        b=baseline[eid]
        b=b.replace('\trandom = no','\t# LIBERATOR2_LEGACY: deeper opt-in settlement and explicit refusal\n\trandom = no',1)
        normal_or_deep=any_of(no(ACTIVE),SOV_READY)
        if eid==9282036:
            b=re.sub(r'(?m)^\tdesc = .*$', '\tdesc = "Fixed odds: base rights 45/40/15, no republics; sovereign terms 55/30/15. Protected terms: 25/45/30 normally, or 80% accept / 20% refuse in LIBERATOR2 after its deep 90-day campaign. LIBERATOR2 republic terms need Baku, Tashkent, Astrakhan, Stalingrad, one interior hub and two complete republics. Protected creation adds 6 dissent. Only complete Soviet-owned occupied territories can transfer. Counteroffers can be rejected."',b)
            for label in ('a','b'):
                anchor=f'\taction_{label} = {{\n\t\ttrigger = {{ '
                b=b.replace(anchor,anchor+normal_or_deep+' ',1)
            b=b.replace('command = { type = clrflag which = ind_aubm_major_armistice_terms_dispatching }',
                'command = { type = clrflag which = ind_aubm_major_armistice_terms_dispatching }\n\t\tcommand = { '+conditional(ACTIVE,clear('sov_deep_accepted'))+' }\n\t\tcommand = { '+conditional(ACTIVE,clear('sov_deep_transferred'))+' }',2)
            b=b.replace('name = "Protected republics: 25/45/30"','name = "Demand Indian puppet republics; see terms above"')
            b=b.replace('command = { type = event which = 9282038 where = SOV when = 3 }',
                f'command = {{ trigger = {{ {no(ACTIVE)} }} type = event which = 9282038 where = SOV when = 3 }}\n'
                f'\t\tcommand = {{ trigger = {{ {ACTIVE} }} type = event which = 9289914 where = SOV when = 3 }}')
        elif eid in (9282037,9282038):
            live=any_of(no(ACTIVE),all_of(SOV_READY,'flag = ind_aubm_local_armistice_outstanding','flag = ind_aubm_local_armistice_target_sov'))
            for letter in 'abc': b=b.replace(f'\taction_{letter} = {{',f'\taction_{letter} = {{\n\t\ttrigger = {{ {live} }}',1)
            b=b.replace('name = "Accept the sovereign settlement"','name = "Accept the sovereign settlement"\n\t\tcommand = { '+conditional(ACTIVE,setf('sov_deep_accepted'))+' }')
            b=b[:-1]+f'\taction_d = {{ trigger = {{ {no(live)} }} ai_chance = 100 name = "The proposed terms are no longer valid" command = {{ type = event which = 9282045 where = IND when = 1 }} }}\n}}'
        elif eid==9282046:
            valid=any_of(no(ACTIVE),all_of(SOV_READY,flag('sov_deep_accepted'),'flag = ind_aubm_local_armistice_outstanding'))
            b=b.replace('\taction_a = {',f'\taction_a = {{\n\t\ttrigger = {{ {valid} }}',1)
            b=b.replace('\t\tname = "Transfer only complete, verified republic territories"',
                '\t\tname = "Transfer only complete, verified republic territories"\n\t\tcommand = { '+conditional(ACTIVE,setf('sov_deep_transferred'))+' }\n\t\tcommand = { '+conditional(ACTIVE,clear('sov_hold_watch'))+' }\n\t\tcommand = { '+conditional(ACTIVE,clear('sov_hold_ready'))+' }')
            b=b[:-1]+f'\taction_b = {{ trigger = {{ {no(valid)} }} name = "The transfer is no longer authorised" command = {{ type = event which = 9282045 where = IND when = 1 }} }}\n}}'
        elif eid in (9282040,9282043):
            valid=any_of(no(ACTIVE),all_of(war('SOV'),flag('sov_deep_accepted'),flag('sov_deep_transferred'),
                'flag = ind_aubm_local_armistice_outstanding','flag = ind_aubm_local_armistice_target_sov'))
            original=re.search(r'\taction_a = \{\n\t\ttrigger = \{ (.*) \}\n',b)[1]
            success=all_of(valid,original)
            b=re.sub(r'(\taction_a = \{\n)\t\ttrigger = \{ .* \}\n',lambda m:m[1]+f'\t\ttrigger = {{ {success} }}\n',b,count=1)
            b=re.sub(r'(\taction_b = \{\n)\t\ttrigger = \{ .* \}\n',lambda m:m[1]+f'\t\ttrigger = {{ {no(success)} }}\n',b,count=1)
        elif eid==9282044:
            b=re.sub(r'(?m)^\tdesc = .*$', '\tdesc = "Moscow offers LIMITED PEACE and transit rights, with NO republics or Indian puppets. Ratifying ends the Soviet war and therefore this war\'s deeper republic campaign. India\'s Japanese and other wars continue. Accept to send these narrower terms for ratification, or reject and keep fighting toward the larger settlement. Existing access is not a territorial victory."',b)
            b=b[:-1]+'\taction_b = {\n\t\tname = "Reject the limited peace; keep fighting"\n'+''.join(
                f'\t\tcommand = {{ type = clrflag which = ind_aubm_{f} }}\n' for f in (
                    'local_armistice_target_sov','local_armistice_outstanding','local_soviet_sovereign_terms',
                    'local_soviet_protected_terms','local_soviet_base_terms'))+(
                '\t\tcommand = { type = setflag which = ind_aubm_local_armistice_retry_sov }\n'
                '\t\tcommand = { type = setflag which = ind_aubm_local_armistice_retry_pending }\n'
                '\t\tcommand = { type = event which = 9282054 where = IND when = 90 }\n\t}\n}')
        changes.append((start,end,b))
    for s,e,b in reversed(changes): text=text[:s]+b+text[e:]
    return text.encode('cp1252')

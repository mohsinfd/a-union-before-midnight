"""Earned, consent-based British decolonisation; one attempt per country.

Britain ends its own mastery. India never issues another country's diplomatic
commands. Recognition requires observed sovereignty, not an acceptance flag.
One-use requests avoid retry/callback generation ambiguity. Native QA pending.
"""
from pathlib import PurePosixPath
from dh_save_spans import parse
from aubm_redesign_route_finish import CURRENT
from aubm_redesign_campaign_stories import all_of, any_of, flag, absent, cmd, setflag, clear

MARKER = '# AUBM_STAGED_DECOLONISATION_V1'
NEW_EVENT_IDS = tuple(range(9398600, 9398609))
COUNTRIES = (('EGY', 'Egypt'), ('IRQ', 'Iraq'), ('OMN', 'Oman'))
BUSY = 'ind_decolonisation_talks_open'
PROOF = any_of(flag('ind_lib1_suez_reward'),
               flag('ind_aubm_bespoke_focus_culminated_allied_continental'))


def names(tag):
    return {k: 'ind_decol_' + tag.lower() + '_' + k
            for k in ('started','pending','funded','responded','accepted','closed','recognised')}


def peaceful(tag):
    return ' '.join('NOT = { atwar = ' + t + ' }' for t in ('IND','ENG',tag))


def context(tag):
    # CURRENT[allied] can refer to an American compact: Britain must also be
    # sovereign, friendly and the actual current master of the target.
    return ' '.join((CURRENT['allied'], 'exists = ENG NOT = { ispuppet = ENG }',
        'NOT = { war = { country = IND country = ENG } }', 'exists = ' + tag,
        'puppet = { country = ' + tag + ' country = ENG }', peaceful(tag), PROOF))


def offer(tag):
    n=names(tag)
    return 'ai = no year = 1937 ' + context(tag) + ' ' + absent(n['started']) + ' ' + absent(BUSY)


def reply(tag):
    n=names(tag)
    return ' '.join((flag(n['started']),flag(n['pending']),absent(n['closed']),
                     absent(n['responded']),context(tag)))


def recognised(tag):
    n=names(tag)
    return ' '.join(('ai = no exists = IND NOT = { ispuppet = IND }',
        flag(n['started']),flag(n['pending']),flag(n['responded']),flag(n['accepted']),
        absent(n['closed']),absent(n['recognised']), 'exists = ' + tag,
        'NOT = { ispuppet = ' + tag + ' }',
        'NOT = { war = { country = IND country = ' + tag + ' } }'))


def action(label, guard, effects=(), chance=0):
    return ('action = { name = "' + label + '" ai_chance = ' + str(chance) +
            ' trigger = { ' + guard + ' }\n' + '\n'.join(effects) + '\n}')


def event(eid, country, title, desc, actions, decision=None):
    fields = ['event = {',f'id = {eid} country = {country} random = no persistent = yes',
              'name = "' + title + '"','desc = "' + desc + '"',
              'style = 2 picture = "india_v3_armed_forces"']
    if decision:
        fields += ['decision = { ' + decision + ' }','decision_trigger = { ' + decision + ' }']
    return '\n'.join([*fields,*actions,'}'])


def render(tag, name, base):
    n=names(tag); request=offer(tag); valid=reply(tag)
    openings=[]
    for funded,cost,odds in ((False,250,60),(True,750,80)):
        effects=[cmd('money value = -' + str(cost)),setflag(n['started']),setflag(n['pending']),setflag(BUSY)]
        if funded: effects.append(setflag(n['funded']))
        effects.append(cmd(f'event which = {base+1} where = ENG when = 2'))
        openings.append(action(f'Press the case: ${cost}; {odds}% British acceptance',request+f' money = {cost}',effects))
    openings.append(action('Not now - leave this opportunity open','ai = no'))
    opening=event(base,'IND','A Free '+name+' at the Peace Table',
        f'India has earned a hearing through the defence of Suez or its Allied continental campaign. Ask Britain to free {name}. Spend 250 money for 60% acceptance, or 750 for 80%. This is a non-refundable diplomatic campaign, not an investment payment. One attempt per country. All three countries must be at peace. Independence does not make {name} Indian or force it out of its alliance.',openings,request)
    replies=[]
    for funded,odds in ((False,60),(True,80)):
        gate=valid+' '+(flag(n['funded']) if funded else absent(n['funded']))
        replies += [action('End British mastery over '+name,gate,
            [setflag(n['responded']),setflag(n['accepted']),cmd('end_mastery which = '+tag)],odds),
            action('Refuse the Indian proposal',gate,[setflag(n['responded'])],100-odds)]
    replies.append(action('The proposal is no longer valid', 'NOT = { AND = { '+valid+' } }',chance=100))
    response=event(base+1,'ENG','Delhi Asks Britain to Free '+name,
        f'Indian service in the Allied cause has become a demand at the peace table. Delhi asks Britain to end its mastery over {name}. Acceptance grants sovereignty, not Indian rule, and does not itself change alliances or military access. Britain may refuse. The Indian delegation has already paid its own campaigning costs.',replies)
    pending='ai = no exists = IND '+flag(n['pending'])+' '+absent(n['closed'])
    finish=[setflag(n['closed']),clear(n['pending']),clear(BUSY)]
    review=event(base+2,'IND','The Answer on '+name,
        f'Britain has been asked to free {name}. Claim recognition only after Britain accepts and {name} exists without any puppet master: -2 dissent and +30 relations. A signature alone is not enough. If Britain refuses, conditions change or the reply never arrives, you may close the talks. Fees are never refunded. Closing before the British reply prevents a late release; a completed release is not reversed.',
        [action('Welcome a sovereign '+name,recognised(tag),
            [setflag(n['recognised']),cmd('dissent value = -2'),cmd('relation which = '+tag+' value = 30'),*finish]),
         action('Wait - leave the talks open','ai = no'),
         action('Close these talks permanently; no refund',pending,finish)],pending)
    return '\n\n'.join((opening,response,review))


def transform(files):
    out=dict(files)
    paths=[p for p in files if PurePosixPath(p.replace('\\','/')).name=='51_bespoke_route_arcs.txt']
    if len(paths)!=1: raise ValueError('Decolonisation requires loaded module 51')
    path=paths[0]
    text='\n\n'.join(render(tag,name,9398600+3*i) for i,(tag,name) in enumerate(COUNTRIES))
    if MARKER in files[path]:
        if text not in files[path]: raise ValueError('Decolonisation content drift')
    else:
        ids={int(e.get('id')) for t in files.values() for e in parse(t).all('event')}
        if ids.intersection(NEW_EVENT_IDS): raise ValueError('Decolonisation ID collision')
        out[path]+='\n\n'+MARKER+'\n'+text+'\n'
    return out,{eid:[dict(dimension='decolonisation',status='reviewed',engine_tested=False,
                detail='One-use British reply; observed sovereign outcome; cancel closes late callback ownership. Native end_mastery unverified.')]
                for eid in NEW_EVENT_IDS}

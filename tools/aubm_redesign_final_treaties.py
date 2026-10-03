"""Finite German, Soviet and Ocean settlements using foreign consent.

One live proposal across this family, one attempt per subject. Foreign commands
execute in the foreign country. Indian ratification observes real state first.
No wars, peace, alliance switches, automatic annexations or retry queues.
"""
from itertools import combinations
from pathlib import PurePosixPath
from dh_save_spans import parse
from aubm_redesign_decolonisation import action, event
from aubm_redesign_campaign_stories import all_of, any_of, flag, absent, cmd, setflag, clear
from aubm_redesign_route_finish import CURRENT

MARKER='# AUBM_STAGED_FINAL_TREATIES_V1'
NEW_EVENT_IDS=tuple(range(9398700,9398719))
BUSY='ind_final_treaty_pending'
CHARTER='ind_ocean_charter_completed'
TALKS=[
    dict(key='baku',tag='GER',name='Baku',family='german',province=713,base=9398700),
    dict(key='tashkent',tag='GER',name='Tashkent',family='german',province=1103,base=9398703),
    dict(key='moscow',tag='SOV',name='Moscow',family='soviet',base=9398706),
    dict(key='egypt',tag='EGY',name='Egypt',family='sovereign',base=9398709),
    dict(key='oman',tag='OMN',name='Oman',family='sovereign',base=9398712),
    dict(key='persia',tag='PER',name='Persia',family='sovereign',base=9398715),
]


def names(t):
    return {k:'ind_treaty_'+t['key']+'_'+k for k in ('started','pending','alternative','responded','accepted','closed','ratified')}


def bilateral(kind,a,b):return f'{kind} = {{ country = {a} country = {b} }}'
def peace(tag):return 'NOT = { atwar = '+tag+' }'
def territory(p,tag):return f'owned = {{ province = {p} data = {tag} }} control = {{ province = {p} data = {tag} }}'
def nap(tag):return cmd(f'non_aggression which = {tag} where = IND when = 1800')


def partner_live(t):
    tag=t['tag']
    return ' '.join(('exists = '+tag,'NOT = { ispuppet = '+tag+' }',
                     'NOT = { '+bilateral('war','IND',tag)+' }',peace('IND'),peace(tag)))


def relationship(t):return CURRENT[t['family']]+' '+partner_live(t)


def leverage(t):
    if t['family']=='german':
        return any_of(flag('ind_aubm_bespoke_focus_culminated_german_eurasian'),
                      flag('ind_aubm_soviet_major_victory'))
    if t['family']=='soviet':
        return any_of(flag('ind_aubm_bespoke_focus_culminated_soviet_antifascist'),
                      flag('ind_aubm_germany_major_victory'))
    return any_of(flag('ind_aubm_national_western_victory'),flag('ind_aubm_britain_limited_victory'),
                  flag('ind_aubm_bespoke_focus_culminated_sovereign_ocean'),
                  flag('ind_aubm_bespoke_focus_culminated_sovereign_continental'))


def context(t):
    extra=territory(t['province'],'GER') if t['family']=='german' else ''
    return relationship(t)+' '+leverage(t)+' '+extra


def opening(t):
    return 'ai = no year = 1937 '+context(t)+' '+absent(names(t)['started'])+' '+absent(BUSY)


def reply(t):
    n=names(t)
    return ' '.join((flag(n['started']),flag(n['pending']),absent(n['closed']),absent(n['responded']),context(t)))


def observed(t,alternative):
    tag=t['tag'];terms=bilateral('non_aggression',tag,'IND')
    if t['family']=='german':
        return territory(t['province'],'IND') if not alternative else bilateral('access',tag,'IND')+' '+terms
    if t['family']=='soviet':
        if alternative:return bilateral('access',tag,'IND')+' '+terms
        return ('NOT = { '+bilateral('access','IND',tag)+' } NOT = { '+bilateral('access',tag,'IND')+' } '+terms)
    terms+=' '+bilateral('access',tag,'IND')
    if not alternative:terms+=' '+bilateral('guarantee',tag,'IND')
    return terms


def ratify(t,alternative):
    n=names(t)
    return ' '.join(('ai = no',relationship(t),flag(n['started']),flag(n['pending']),flag(n['responded']),
        flag(n['accepted']),absent(n['closed']),absent(n['ratified']),
        flag(n['alternative']) if alternative else absent(n['alternative']),observed(t,alternative)))


def foreign_effects(t,alternative):
    tag=t['tag']
    if t['family']=='german' and not alternative:return [cmd(f'secedeprovince which = IND value = {t["province"]}')]
    if t['family']=='soviet' and not alternative:
        return [cmd('end_access which = IND'),cmd('end_access which = IND when = 1'),nap(tag)]
    effects=[cmd('access which = IND'),nap(tag)]
    if t['family']=='sovereign' and not alternative:effects.append(cmd(f'guarantee which = {tag} where = IND'))
    return effects


def indian_effects(t,alternative):
    if t['family']=='german':
        return [cmd('relation which = GER value = 20')]
    if t['family']=='soviet':
        return ([cmd('access which = SOV'),cmd('research_mod value = 2')] if alternative
                else [cmd('dissent value = -2')])
    effects=[cmd('access which = '+t['tag'])]
    if not alternative:effects.append(cmd('guarantee which = IND where = '+t['tag']))
    return effects


def prose(t):
    if t['family']=='german':
        return ('Whose Flag Flies over '+t['name']+'?',
            f'After India earns its Soviet campaign victory, a German-held {t["name"]} can become a dispute at the peace table. Pay 500 money to ask for the province (50% acceptance), or military access and a five-year non-aggression pact (80%). Both countries must be at peace. Fees are not refunded. One attempt for this city; a refusal does not start a war.',
            ('Ask Germany to cede the city: $500; 50%', 'Accept access, not ownership: $500; 80%'),
            (50,80),
            'Check the answer against the map. A territorial settlement needs Indian ownership and control. The limited settlement needs actual German access and the pact. Ratification gives +20 relations; it cannot conjure a failed transfer. Closing stops an unanswered proposal, but never reverses a completed transfer or treaty.')
    if t['family']=='soviet':
        return ('Delhi Draws a Line for Moscow',
            'After an earned anti-fascist victory, decide how close Moscow should remain. Pay 500 money. Separate military zones (70%): Moscow ends access in both directions and signs a five-year non-aggression pact; India gains -2 dissent on verification. Joint workshops (85%): reciprocal access and the same pact; +2 research on ratification. Existing alliances and compacts are not rewritten. Fees are not refunded.',
            ('Separate military zones: $500; 70%', 'Joint workshops and reciprocal access: $500; 85%'),
            (70,85),
            'Separate zones must show no military access in either direction and a real pact before India receives -2 dissent. Workshops require Soviet access and the pact; ratifying grants Soviet access to India and +2 research once. Neither option ends an alliance or changes the old compact. Alliance members may still move through allied territory regardless of access treaties.')
    return ('A Place for '+t['name']+' in the Ocean League',
        f'An independent India with a western or Ocean campaign victory can invite sovereign {t["name"]}. Both must be at peace. Pay 500 money for a mutual-defence agreement (70% acceptance) or a commercial partnership (85%). Both give reciprocal military access and a five-year non-aggression pact. Defence adds guarantees both ways. Two verified members unlock the Ocean charter. No alliance or puppet is created; fees are not refunded.',
        ('Mutual defence and port access: $500; 70%', 'Commercial partnership and port access: $500; 85%'),
        (70,85),
        'The partner must actually grant access and sign the pact. A defence agreement also needs its guarantee of India. Ratifying gives reciprocal access and, for defence, an Indian guarantee. Two current verified partners can found the Ocean charter. This is a league of sovereign states, not annexation. Closing cannot revoke rights already granted.')


def render(t):
    n=names(t);base=t['base'];title,desc,labels,odds,reviewdesc=prose(t)
    aa=[]
    for alternative in (False,True):
        effects=[cmd('money value = -500'),setflag(n['started']),setflag(n['pending']),setflag(BUSY)]
        if alternative:effects.append(setflag(n['alternative']))
        effects.append(cmd(f'event which = {base+1} where = {t["tag"]} when = 2'))
        aa.append(action(labels[int(alternative)],opening(t)+' money = 500',effects))
    aa.append(action('Not now - leave this offer open','ai = no'))
    start=event(base,'IND',title,desc,aa,opening(t))
    aa=[];valid=reply(t)
    for alternative in (False,True):
        gate=valid+' '+(flag(n['alternative']) if alternative else absent(n['alternative']))
        aa += [action('Accept the proposed terms',gate,[setflag(n['responded']),setflag(n['accepted']),*foreign_effects(t,alternative)],odds[int(alternative)]),
               action('Refuse - no concession',gate,[setflag(n['responded'])],100-odds[int(alternative)])]
    aa.append(action('The proposal has been overtaken','NOT = { AND = { '+valid+' } }',chance=100))
    foreign=event(base+1,t['tag'],'The Indian Proposal: '+t['name'],desc,aa)
    visible='ai = no exists = IND '+flag(n['pending'])+' '+absent(n['closed'])
    finish=[setflag(n['closed']),clear(n['pending']),clear(BUSY)]
    aa=[action('Ratify the verified '+('limited' if alt else 'primary')+' terms',ratify(t,alt),
        [*indian_effects(t,alt),setflag(n['ratified']),*finish]) for alt in (False,True)]
    aa += [action('Wait - leave the talks open','ai = no'),action('Close permanently - no refund',visible,finish)]
    return '\n\n'.join((start,foreign,event(base+2,'IND','The Agreement with '+t['name'],reviewdesc,aa,visible)))


def member(t,defence=False):
    n=names(t);tag=t['tag']
    rule=' '.join((flag(n['ratified']),partner_live(t),bilateral('access',tag,'IND'),
                   bilateral('access','IND',tag),bilateral('non_aggression',tag,'IND')))
    if defence:rule+=' '+absent(n['alternative'])+' '+bilateral('guarantee',tag,'IND')+' '+bilateral('guarantee','IND',tag)
    return rule


def charter_gate(defence=False):
    partners=[t for t in TALKS if t['family']=='sovereign']
    pairs=[all_of(all_of(member(a,defence)),all_of(member(b,defence))) for a,b in combinations(partners,2)]
    return 'ai = no '+CURRENT['sovereign']+' '+absent(CHARTER)+' '+any_of(*pairs)


def charter():
    return event(9398718,'IND','An Indian Ocean Charter',
        'Two sovereign partners have put their agreements into effect. Choose once. Shipping federation: 800 money for +5 transport capacity and +3 supply production. Defence council: two mutual-defence partners and 1,000 supplies for +3 naval organisation and +2 research. No countries merge or inherit wars. Non-aggression pacts last five years; access and guarantees have no scripted expiry. Indian institutional gains are permanent.',
        [action('Shipping federation: $800; +5 TC, +3 supply output',charter_gate()+' money = 800',
            [cmd('money value = -800'),cmd('tc_mod value = 5'),cmd('industrial_modifier which = supplies value = 3'),setflag(CHARTER)]),
         action('Defence council: 1,000 supplies; +3 naval org, +2 R&D',charter_gate(True)+' supplies = 1000',
            [cmd('supplies value = -1000'),cmd('max_organization which = naval value = 3'),cmd('research_mod value = 2'),setflag(CHARTER)]),
         action('Not now - leave the charter open','ai = no')],charter_gate())


def transform(files):
    out=dict(files);paths=[p for p in files if PurePosixPath(p.replace('\\','/')).name=='51_bespoke_route_arcs.txt']
    if len(paths)!=1:raise ValueError('Final treaties require loaded module 51')
    path=paths[0];text='\n\n'.join([*(render(t) for t in TALKS),charter()])
    if MARKER in files[path]:
        if text not in files[path]:raise ValueError('Final treaty drift')
    else:
        ids={int(e.get('id')) for content in files.values() for e in parse(content).all('event')}
        if ids.intersection(NEW_EVENT_IDS):raise ValueError('Final treaty ID collision')
        out[path]+='\n\n'+MARKER+'\n'+text+'\n'
    return out,{eid:[dict(dimension='final_treaties',status='reviewed',engine_tested=False,
        detail='One-use consent, observed foreign effect, current treaty membership and capped ending; native verification pending.')]
        for eid in NEW_EVENT_IDS}

"""R14: consent, explicit terms, and recoverable peace transactions.

Call after the existing catalogue is prepared, before final integrity/copy passes.
Imports do not mutate files or the catalogue. Existing IDs are never changed.
"""
import re
from catalog import EVENTS, Action, event, cmd, flag, clear, later, fire, cond, control, owned, war, active, pacific, puppet

REPORT = {}
_SERIAL = 0
OBJECTIVES=set()
AUTHORITIES=set()
PARTNERS = tuple('GER ITA MAN MEN U87 IND SIA PHI INO AST NZL FIN ROM HUN BUL SPA SPR PER IRQ EGY TUR USA SOV CHI CGX CYN CSX SIK PRI HOL ENG FRA'.split())
INDEPENDENT = 'NOT = { alliance = { country = JAP country = GER } }'
SOV_PROVINCES = (1191,1190,1189,1188,1187,1186,1185,1184,1183,1182,1176,1541)


def f(s): return 'flag = JX_' + s
def no(s): return 'NOT = { AND = { ' + s + ' } }'
def allied(t): return 'alliance = { country = JAP country = ' + t + ' }'


def coalition(p, consent=False):
    alternatives = [control(p)]
    for t in PARTNERS:
        authority = (' OR = { '+puppet(t)+' '+f('R14_CONSENT_'+t)+' }') if consent else ''
        alternatives.append('AND = { '+allied(t)+' NOT = { '+war(t)+' } '+control(p,t)+authority+' }')
    return 'OR = { '+' '.join(alternatives)+' }'


def objective(p):
    OBJECTIVES.add(int(p))
    return 'OR = { '+control(p)+' '+f('R14_CAPTURE_'+str(p))+' }'


def authority(p):
    AUTHORITIES.add(int(p))
    return f('R14_AUTH_'+str(p))


def expanded(gate):
    return re.sub(r'flag\s*=\s*JX_R14_CAPTURE_(\d+)\b',lambda m:coalition(int(m[1])),gate)


def widen(gate, consent=False):
    return re.sub(r'control\s*=\s*\{\s*province\s*=\s*(\d+)\s+data\s*=\s*(?:JAP|-3)\s*\}',
                  lambda m: authority(int(m[1])) if consent else objective(int(m[1])),gate)


def protected(command, gate):
    """Guard at command execution too: an already-open action can become stale."""
    command=command.strip()
    if command.startswith('trigger = {'):
        start=command.index('{');depth=0
        for end in range(start,len(command)):
            depth += (command[end]=='{')-(command[end]=='}')
            if depth==0:
                gate='AND = { '+gate+' } AND = { '+command[start+1:end]+' }'
                command=command[end+1:].strip()
                break
    return cond(gate,command)


def actions(e, choices, fallback='Close this notice'):
    e.actions = choices
    used = 'OR = { '+' '.join('AND = { '+a.gate+' }' for a in choices)+' }'
    e.actions.append(Action(fallback, [], gate=no(used), chance=100))


def guarded_action(name, commands, gate, chance=100):
    # The engine can cache a selected action. Acquire a private execution receipt
    # only if its full gate still holds, then execute this batch against that
    # receipt. Rechecking the original gate on every command is wrong: its own
    # setflag/peace commands intentionally change that gate during the batch.
    global _SERIAL
    _SERIAL += 1
    receipt='R14_EXEC_'+str(_SERIAL)
    return Action(name,[protected(flag(receipt),gate)]+[protected(c,f(receipt)) for c in commands]+[clear(receipt)],gate=gate,chance=chance)


def apply():
    global PARTNERS
    if REPORT: return REPORT
    from build import parse, get, resolve, source_country
    by = {e.key:e for e in EVENTS}
    original_ids = {e.key:e.id for e in EVENTS}
    released={e.country for e in EVENTS if e.module=='settlements' and e.key.endswith('_local') and e.country!='JAP'}
    PARTNERS=tuple(dict.fromkeys(PARTNERS+tuple(sorted(released-set(PARTNERS)))))

    # One visible diplomatic agreement, rather than one card for every ally.
    candidates = ['AND = { exists = '+t+' '+allied(t)+' NOT = { '+war(t)+' '+puppet(t)+' '+f('R14_CONSENT_'+t)+' '+f('R14_REFUSED_'+t)+' } }' for t in PARTNERS]
    eg = active()+' '+pacific()+' OR = { '+' '.join(candidates)+' }'
    agreement = event('r14_allied_occupation','Agree with our allies over occupied land',
        'Ask our allies to let Japan settle enemy territory held by their troops. An ally may refuse. The agreement never gives Japan that ally\'s own national territory. A puppet follows Japanese policy.\n\nWithout an agreement, allied victories can still count towards defeating an existing enemy government, but allied-held colonial land cannot be used to create a Japanese client.',
        decision=True,persistent=True,gate=eg,year=1937,art='diplomacy',module='diplomacy',actions=[
            guarded_action('Ask the allied governments',[cond(c, later('r14_consent_'+t,1,t)) for t,c in zip(PARTNERS,candidates)],eg),
            Action('Leave this proposal available',[],gate=eg)])
    agreement.manual_only=True
    available=f('R14_ALLIED_AVAILABLE')
    agreement.gate=active()+' '+pacific()+' '+available
    for i,a in enumerate(agreement.actions):
        if a.commands:
            event('r14_allied_occupation_commit_'+str(i),'Send the allied proposals','',triggered=True,module='diplomacy',actions=[guarded_action('',a.commands,eg),Action('',[],gate=no(eg),chance=100)])
            a.commands=[fire('r14_allied_occupation_commit_'+str(i))]
        a.gate=agreement.gate
    event('r14_allied_available','Allied negotiations become available','',gate='flag = JX_ACTIVE OR = { AND = { '+available+' '+no(eg)+' } AND = { NOT = { '+available+' } '+eg+' } }',persistent=True,offset=1,module='diplomacy',actions=[
        guarded_action('',[flag('R14_ALLIED_AVAILABLE')],eg+' NOT = { '+available+' }'),
        guarded_action('',[clear('R14_ALLIED_AVAILABLE')],available+' '+no(eg))])
    for t in PARTNERS:
        live=allied(t)+' NOT = { '+war(t)+' '+f('R14_CONSENT_'+t)+' '+f('R14_REFUSED_'+t)+' }'
        event('r14_consent_'+t,'Allied terms for occupied enemy land',
              'Japan asks permission to include enemy-owned land held by our forces in its country settlements. Our own sovereign territory is excluded. Refusal leaves our occupations untouched and can be reconsidered after six months.',
              country=t,triggered=True,art='diplomacy',module='diplomacy',actions=[
                  guarded_action('Agree to Japanese settlements of enemy land',[flag('R14_CONSENT_'+t)],live,70),
                  guarded_action('Retain control of our occupations',[flag('R14_REFUSED_'+t),later('r14_consent_return_'+t,180,t)],live,30),
                  Action('The request no longer applies',[],gate=no(live),chance=100)])
        event('r14_consent_return_'+t,'The allied proposal can be reconsidered','',country=t,triggered=True,module='diplomacy',actions=[Action('',[clear('R14_REFUSED_'+t)])])

    # Existing defeated states can surrender after coalition victory. Transfers
    # are narrower: owner must remain an opponent; independent occupiers consent.
    roots=[e for e in list(EVENTS) if e.module=='settlements' and e.decision and e.key!='china']
    for root in roots:
        key=root.key; old=root.gate
        root.gate=widen(root.gate)
        for i,a in enumerate(root.actions):
            a.gate=widen(a.gate)
            if i<3:a.commands=[clear('R14_'+key+'_WITHDRAWING'),clear('R14_'+key+'_CREATED')]+a.commands
        root.actions=[guarded_action(a.name,a.commands,a.gate,a.chance) for a in root.actions]
        root.desc += '\n\nOur allies\' captures count towards defeat. Their own territory stays theirs. Enemy colonial land held by an independent ally can be allocated only with that ally\'s agreement; reserved Japanese bases still require prior Japanese occupation.'
        recipient=by[key+'_local'].country
        authorised='OR = { '+f('R14_'+key+'_WITHDRAWING')+' '+f('R14_'+key+'_CREATED')+' '+puppet(recipient)+' }'
        for e in list(EVENTS):
            if not e.key.startswith(key+'_'): continue
            if '_land_' in e.key:
                live=f(key+'_PENDING')+' NOT = { '+f(key+'_SETTLED')+' } '+war(e.country)
                for a in e.actions:
                    a.gate=(live+' '+a.gate).strip()
                    a.commands=[protected(widen(c,True).replace('when = 1','when = 2'),live) for c in a.commands]
                e.actions.append(Action('',[],gate=no(live),chance=100))
            elif e.key==key+'_create':
                # Match the actual release capital, including the two explicit
                # builder corrections to the old B&I revolt definitions.
                capital={'indonesia':1647,'cambodia':1400}.get(key,int(get(source_country(recipient)[0],'capital')))
                creation=[]
                for a in e.actions:
                    if not a.commands:continue
                    cg=a.gate+' '+owned(capital)+' '+control(capital)
                    replacement=guarded_action(a.name,[flag('R14_'+key+'_CREATED')]+a.commands,cg,a.chance)
                    a.gate=replacement.gate;a.commands=replacement.commands
                    creation.append(cg)
                anycreate='OR = { '+' '.join('AND = { '+g+' }' for g in creation)+' }'
                e.actions.append(guarded_action('',[later(key+'_failed',1)],f(key+'_PENDING')+' '+no(anycreate)))
            elif e.key in (key+'_commit',key+'_local',key+'_merge'):
                for a in e.actions:
                    if not a.commands:continue
                    replacement=guarded_action(a.name,a.commands,a.gate+' '+authorised,a.chance)
                    a.gate=replacement.gate;a.commands=replacement.commands
                e.actions.append(guarded_action('',[later(key+'_failed',1)],f(key+'_PENDING')+' '+no(authorised)))
            elif e.key in (key+'_withdraw',key+'_withdraw_existing'):
                live=f(key+'_PENDING')+' '+war(e.country)
                for a in e.actions:
                    # Departure ends the enemy war; only the departure itself
                    # must recheck war, subsequent identity work uses its receipt.
                    a.gate=(live+' '+a.gate).strip()
                    replacement=guarded_action(a.name,[flag('R14_'+key+'_WITHDRAWING')]+a.commands,a.gate,a.chance)
                    a.gate=replacement.gate;a.commands=replacement.commands
                e.actions.append(Action('',[],gate=no(live),chance=100))
        # The absent-state colonial branch needs legal ownership of its capital
        # before release. Existing create receivers already check that naturally.

    # Formal entry cannot be selected while limited peace is being implemented.
    block='NOT = { '+f('US_PENDING')+' '+f('SOV_TERMS_PENDING')+' }'
    by['formal_axis'].gate+=' '+block
    for a in by['formal_axis'].actions:
        a.gate+=' '+by['formal_axis'].gate
        a.commands=[protected(c,by['formal_axis'].gate) for c in a.commands]

    current_weak='NOT = { carrier = { country = USA value = 5 when = now } }'
    carrier_leverage='OR = { '+current_weak+' AND = { losses = { country = USA type = carrier value = 4 } NOT = { carrier = { country = USA value = 9 when = now } } lost_national = { country = USA value = 15 } } }'
    hold=objective(1734)+' '+objective(1432)+' '+objective(1565)+' NOT = { lost_national = { country = JAP value = 5 } } carrier = { country = JAP value = 6 when = now } '+carrier_leverage
    harsh=hold+' '+current_weak+' OR = { lost_national = { country = USA value = 25 } carrier = { country = JAP value = 10 when = now } }'
    us_open=active()+' '+pacific()+' '+war('USA')+' '+INDEPENDENT+' year = 1943 event = { id = @pacific_open days = 720 } '+hold+' NOT = { '+f('US_PENDING')+' '+f('US_WAIT')+' '+f('US_PEACE')+' '+f('US_DISMISSED')+' '+f('US_INV_PENDING')+' }'
    pending=f('US_PENDING')+' NOT = { '+f('US_PEACE')+' }'
    live=pending+' '+war('USA')+' '+INDEPENDENT
    accepted=live+' '+f('R14_US_ACCEPTED')
    reset=[clear(x) for x in ('US_HOLD_BROKEN','US_RETURN_HAWAII','US_KEEP_HAWAII','R14_US_ACCEPTED','R14_US_STARTED','R14_US_PEACE_ISSUED','R14_US_TRANSFER_FAILED','R14_US_HAWAII_RETURNED','R14_US_TRY_1','R14_US_TRY_2')]
    abort=[clear('R14_US_ACCEPTED'),clear('US_RETURN_HAWAII'),clear('US_KEEP_HAWAII'),flag('US_WAIT'),later('us_return',90),clear('US_PENDING')]
    by['us_peace'].gate=us_open
    by['us_peace'].desc='After two years of war, hold Hawaii, Singapore and Manila for six months with at least six carriers and less than five percent of Japan lost. America must still lack five carriers; four past carrier losses count only while it has fewer than nine carriers and has lost 15 percent of its territory.\n\nChoose whether to return Hawaii before America answers. Returning it offers better relations and a five-year non-aggression pact. Keeping it needs a stronger victory and leaves a hostile peace. Germany\'s separate war and Japan\'s Soviet war continue.'
    actions(by['us_peace'],[
        guarded_action('Hold our gains for six months',reset+[flag('US_PENDING'),later('us_hold',180)],us_open),
        guarded_action('Wait another six months',[flag('US_WAIT'),later('us_return',180)],us_open,0),
        guarded_action('Continue to fight; dismiss negotiated peace',[flag('US_DISMISSED')],us_open,0)])
    holdlive=live+' '+hold+' NOT = { '+f('US_HOLD_BROKEN')+' }'
    actions(by['us_hold'],[
        guarded_action('Choose the terms we will offer',[later('us_terms',1)],holdlive),
        guarded_action('Our position changed; postpone the offer',abort,pending+' NOT = { '+f('R14_US_ACCEPTED')+' '+f('R14_US_STARTED')+' } '+no(holdlive))])
    by['us_watch'].gate=pending+' NOT = { '+f('R14_US_STARTED')+' '+f('US_HOLD_BROKEN')+' } '+no(hold)
    by['us_watch'].actions=[guarded_action('',[flag('US_HOLD_BROKEN')],by['us_watch'].gate)]
    by['us_terms'].desc='Set out the Hawaiian terms before Washington decides. Returning Hawaii keeps the Asian gains, improves relations by 35 and provides a five-year non-aggression pact. Retaining Hawaii requires America to have fewer than five carriers, plus either 25 percent territorial loss or a Japanese fleet of ten carriers. It worsens relations by 60 and provides no non-aggression pact.\n\nOnly enemy-owned occupied land can change hands. Allied governments keep their own territory.'
    returnterms=holdlive+' NOT = { '+f('R14_US_ACCEPTED')+' }'
    actions(by['us_terms'],[
        guarded_action('Return Hawaii in exchange for a lasting armistice',[flag('US_RETURN_HAWAII'),clear('US_KEEP_HAWAII'),later('us_offer',1,'USA')],returnterms),
        guarded_action('Demand Hawaii; accept a hostile peace',[flag('US_KEEP_HAWAII'),clear('US_RETURN_HAWAII'),later('us_offer',1,'USA')],returnterms+' '+harsh,0),
        guarded_action('Continue the war; cancel the proposal',abort,pending+' NOT = { '+f('R14_US_ACCEPTED')+' '+f('R14_US_STARTED')+' }',0)])
    anyterms='OR = { '+f('US_RETURN_HAWAII')+' AND = { '+f('US_KEEP_HAWAII')+' '+harsh+' } }'
    offerlive=holdlive+' '+anyterms+' NOT = { '+f('R14_US_ACCEPTED')+' }'
    by['us_offer'].desc='Japan has stated its Hawaiian terms. A return of Hawaii offers normalisation and a five-year non-aggression pact. A demand to keep it is a harsher settlement, supported by continuing American naval weakness. We may accept or continue the war.'
    actions(by['us_offer'],[
        guarded_action('Accept the return of Hawaii',[flag('R14_US_ACCEPTED'),later('us_implement',1)],offerlive+' '+f('US_RETURN_HAWAII'),70),
        guarded_action('Accept the loss of Hawaii',[flag('R14_US_ACCEPTED'),later('us_implement',1)],offerlive+' '+f('US_KEEP_HAWAII'),40),
        guarded_action('Continue the war',[later('us_refused',1)],offerlive,30),
        guarded_action('The proposal no longer applies',abort,pending+' NOT = { '+f('R14_US_ACCEPTED')+' } '+no(offerlive))])
    actions(by['us_refused'],[guarded_action('Continue the campaign; reconsider in three months',abort,pending)])

    # Preserve exact builder-generated Asian lists. Record only enemy-owned,
    # authorised occupations present at the beginning; replays cannot add gifts.
    us_claims=[]; owners=[]
    for e in list(EVENTS):
        if not e.key.startswith('us_transfer_'): continue
        owner=e.country; owners.append(owner); entries=[]
        owner_war=war(owner)+(' alliance = { country = USA country = '+owner+' }' if owner!='USA' else '')
        for c in e.actions[0].commands:
            n=parse(resolve(c)); p=get(n,'value')
            if get(n,'type')!='secedeprovince': continue
            p=int(p); expected='R14_US_LAND_'+owner+'_'+str(p)
            extra=' '+f('US_KEEP_HAWAII') if p==1734 else ''
            take=accepted+' '+owner_war+' '+owned(p,owner)+' '+authority(p)+extra
            entries += [protected(flag(expected),take+' NOT = { '+f('R14_US_SNAPSHOT_'+owner)+' }'),
                        protected(cmd('secedeprovince',which='JAP',value=p,when=2),accepted+' '+owner_war+' '+f(expected)+' '+owned(p,owner)+' '+authority(p))]
            us_claims.append((p,owner,expected))
        entries.append(protected(flag('R14_US_SNAPSHOT_'+owner),accepted))
        actions(e,[guarded_action('',entries,accepted)])
    event('r14_us_reset','Prepare a new Pacific proposal','',triggered=True,module='usa',actions=[
        guarded_action('',[clear(x) for _,_,x in us_claims]+[clear('R14_US_SNAPSHOT_'+t) for t in owners],pending+' NOT = { '+f('R14_US_ACCEPTED')+' '+f('R14_US_STARTED')+' }')])
    start_commands=by['us_peace'].actions[0].commands
    pending_pos=next(i for i,c in enumerate(start_commands) if 'type = setflag which = JX_US_PENDING' in c)
    start_commands.insert(pending_pos+1,protected(fire('r14_us_reset'),pending))
    start=accepted+' '+anyterms
    hawaii_return=f('US_RETURN_HAWAII')+' OR = { '+owned(1734)+' '+owned(1734,'USA')+' } '+authority(1734)
    actions(by['us_implement'],[
        guarded_action('',[flag('R14_US_STARTED'),cond(hawaii_return,flag('R14_US_HAWAII_RETURNED')),cond(hawaii_return,cmd('secedeprovince',which='USA',value=1734,when=2))]+[cond('exists = '+t+' '+war(t),later('us_transfer_'+t,0,t)) for t in owners]+[later('r14_us_check',1)],start),
        guarded_action('The proposal changed; preserve existing transfers and stop',abort,pending+' '+no(start))])
    checks=[clear('R14_US_TRANSFER_FAILED'),cond(f('R14_US_HAWAII_RETURNED')+' NOT = { '+owned(1734,'USA')+' }',flag('R14_US_TRANSFER_FAILED'))]
    for p,t,x in us_claims:
        checks.append(protected(flag('R14_US_TRANSFER_FAILED'),f(x)+' NOT = { '+owned(p)+' }'))
    event('r14_us_check','Check the Pacific handover','',triggered=True,module='usa',actions=[
        guarded_action('',checks+[fire('r14_us_result')],accepted),
        guarded_action('',abort,pending+' '+no(accepted)),Action('',[],gate=no(pending),chance=100)])
    resultlive=accepted+' NOT = { '+f('R14_US_TRANSFER_FAILED')+' }'
    event('r14_us_result','Complete the Pacific handover','',triggered=True,module='usa',actions=[
        guarded_action('',[later('us_finish',1,'USA')],resultlive),
        guarded_action('',[flag('R14_US_TRY_1'),later('us_implement',2)],accepted+' '+f('R14_US_TRANSFER_FAILED')+' NOT = { '+f('R14_US_TRY_1')+' }'),
        guarded_action('',[flag('R14_US_TRY_2'),later('us_implement',2)],accepted+' '+f('R14_US_TRANSFER_FAILED')+' '+f('R14_US_TRY_1')+' NOT = { '+f('R14_US_TRY_2')+' }'),
        guarded_action('',abort,accepted+' '+f('R14_US_TRANSFER_FAILED')+' '+f('R14_US_TRY_2'))])
    # Once transfers start, never apply territory-loss entry gates again. Those
    # percentages have changed precisely because the agreed transfer succeeded.
    finishlive=accepted+' '+f('R14_US_STARTED')+' NOT = { '+f('R14_US_TRANSFER_FAILED')+' '+f('R14_US_PEACE_ISSUED')+' }'
    actions(by['us_finish'],[
        guarded_action('Sign the Pacific armistice',[flag('R14_US_PEACE_ISSUED'),cmd('peace',which='JAP',value=0),later('us_signed',2)],finishlive),
        guarded_action('The separate armistice cannot proceed',abort,pending+' '+no(finishlive)+' NOT = { '+f('R14_US_PEACE_ISSUED')+' }')])
    success=pending+' '+f('R14_US_ACCEPTED')+' '+f('R14_US_PEACE_ISSUED')+' NOT = { '+war('USA')+' '+f('R14_US_TRANSFER_FAILED')+' }'
    reward=[cond(f('US_RETURN_HAWAII'),cmd('relation',which='USA',value=35)),cond(f('US_RETURN_HAWAII'),cmd('non_aggression',which='JAP',where='USA',when=1800)),cond(f('US_RETURN_HAWAII'),later('us_treaty_expiry',1800)),cond(f('US_KEEP_HAWAII'),cmd('relation',which='USA',value=-60)),flag('US_PEACE'),cmd('dissent',value=-2),clear('R14_US_ACCEPTED'),clear('US_PENDING')]
    # The closure clears pending last; flag US_PEACE must not invalidate later
    # commands from the already-authorised award batch.
    awardgate=f('US_PENDING')+' '+f('R14_US_PEACE_ISSUED')+' NOT = { '+war('USA')+' }'
    actions(by['us_signed'],[Action('The Pacific armistice is in force',[protected(c,awardgate) for c in reward],gate=success,chance=100),guarded_action('The ceasefire failed; preserve current borders and postpone',abort,pending+' '+no(success))])
    by['us_signed'].desc='The handover and ceasefire have been checked. Japan keeps only the agreed enemy-owned gains. Returning Hawaii improves relations and begins a five-year non-aggression pact. Retaining Hawaii leaves a hostile peace without that pact. Germany\'s separate war and Japan\'s other wars continue. Land already handed over is not awarded again.'

    # Soviet limited peace: explicit selection, checked handover, then peace.
    sovhold=' '.join(objective(p) for p in (1191,1190,1169,1162))+' OR = { '+objective(1142)+' AND = { '+objective(1156)+' lost_national = { country = SOV value = 25 } } }'
    sovopen=active()+' '+pacific()+' '+war('SOV')+' '+INDEPENDENT+' '+sovhold+' NOT = { '+f('SOV_TERMS_PENDING')+' '+f('SOV_TERMS_DONE')+' '+f('SOV_TERMS_WAIT')+' }'
    sp=f('SOV_TERMS_PENDING')+' NOT = { '+f('SOV_TERMS_DONE')+' }'
    sl=sp+' '+INDEPENDENT+' '+war('SOV')
    sa=sl+' '+f('R14_SOV_ACCEPTED')
    sabort=[clear('R14_SOV_ACCEPTED'),clear('SOV_DIRECT'),clear('SOV_CLIENT'),flag('SOV_TERMS_WAIT'),later('soviet_terms_return',180),clear('SOV_TERMS_PENDING')]
    by['soviet_terms'].gate=sovopen
    for i,a in enumerate(by['soviet_terms'].actions):
        a.gate=sovopen
        if i<2:
            a.commands=[clear('SOV_DIRECT'),clear('SOV_CLIENT'),clear('R14_SOV_ACCEPTED'),clear('R14_SOV_SNAPSHOT'),clear('R14_SOV_PEACE_ISSUED'),clear('R14_SOV_TRY_1'),clear('R14_SOV_TRY_2')]+[clear('R14_SOV_LAND_'+str(p)) for p in SOV_PROVINCES]+a.commands
    by['soviet_terms'].actions=[guarded_action(a.name,a.commands,sovopen,a.chance) for a in by['soviet_terms'].actions]
    sv=sl+' '+sovhold+' NOT = { '+f('R14_SOV_ACCEPTED')+' }'
    actions(by['soviet_offer'],[
        guarded_action('Accept the eastern armistice',[flag('R14_SOV_ACCEPTED'),later('soviet_land',1,'SOV')],sv,70),
        guarded_action('Continue the eastern war',[later('soviet_refusal',1)],sv,30),
        guarded_action('The proposed armistice no longer applies',sabort,sp+' NOT = { '+f('R14_SOV_ACCEPTED')+' } '+no(sv))])
    land=[]
    for p in SOV_PROVINCES:
        x=f('R14_SOV_LAND_'+str(p));take=sa+' '+owned(p,'SOV')+' '+authority(p)
        land += [protected(flag('R14_SOV_LAND_'+str(p)),take+' NOT = { '+f('R14_SOV_SNAPSHOT')+' }'),protected(cmd('secedeprovince',which='JAP',value=p,when=2),sa+' '+x+' '+owned(p,'SOV')+' '+authority(p))]
    land += [flag('R14_SOV_SNAPSHOT'),later('r14_sov_check',1)]
    actions(by['soviet_land'],[guarded_action('',land,sa),guarded_action('',sabort,sp+' '+no(sa))])
    schecks=[clear('R14_SOV_FAILED')]+[cond(f('R14_SOV_LAND_'+str(p))+' NOT = { '+owned(p)+' }',flag('R14_SOV_FAILED')) for p in SOV_PROVINCES]
    event('r14_sov_check','Check the eastern border handover','',triggered=True,module='soviet',actions=[guarded_action('',schecks+[fire('r14_sov_result')],sa),guarded_action('',sabort,sp+' '+no(sa)),Action('',[],gate=no(sp),chance=100)])
    event('r14_sov_result','Complete the eastern border agreement','',triggered=True,module='soviet',actions=[
        guarded_action('',[later('r14_sov_peace',1,'SOV')],sa+' NOT = { '+f('R14_SOV_FAILED')+' }'),
        guarded_action('',[flag('R14_SOV_TRY_1'),later('soviet_land',2,'SOV')],sa+' '+f('R14_SOV_FAILED')+' NOT = { '+f('R14_SOV_TRY_1')+' }'),
        guarded_action('',[flag('R14_SOV_TRY_2'),later('soviet_land',2,'SOV')],sa+' '+f('R14_SOV_FAILED')+' '+f('R14_SOV_TRY_1')+' NOT = { '+f('R14_SOV_TRY_2')+' }'),
        guarded_action('',sabort,sa+' '+f('R14_SOV_FAILED')+' '+f('R14_SOV_TRY_2'))])
    spl=sa+' NOT = { '+f('R14_SOV_FAILED')+' '+f('R14_SOV_PEACE_ISSUED')+' }'
    # A foreign-owner receiver issues peace in its own scope.
    event('r14_sov_peace','Sign the eastern armistice','',country='SOV',triggered=True,module='soviet',actions=[guarded_action('',[flag('R14_SOV_PEACE_ISSUED'),cmd('peace',which='JAP',value=0),later('soviet_signed',2)],spl),guarded_action('',sabort,sp+' '+no(spl)+' NOT = { '+f('R14_SOV_PEACE_ISSUED')+' }')])
    ss=sp+' '+f('R14_SOV_ACCEPTED')+' '+f('R14_SOV_PEACE_ISSUED')+' NOT = { '+war('SOV')+' '+f('R14_SOV_FAILED')+' }'
    new_client=f('SOV_CLIENT')+' NOT = { exists = PRI } '+owned(1191)
    sdone=[cond(new_client,flag('R14_PRI_CREATED')),cond(new_client,cmd('independence',which='PRI',value=1)),cond(f('SOV_CLIENT')+' '+f('R14_PRI_CREATED')+' exists = PRI '+owned(1191,'PRI'),cmd('make_puppet',which='PRI')),cond(f('SOV_CLIENT')+' '+puppet('PRI'),later('far_east_local',1,'PRI')),flag('SOV_TERMS_DONE'),clear('R14_SOV_ACCEPTED'),clear('SOV_TERMS_PENDING')]
    award= f('SOV_TERMS_PENDING')+' '+f('R14_SOV_PEACE_ISSUED')+' NOT = { '+war('SOV')+' }'
    actions(by['soviet_signed'],[Action('The eastern armistice is in force',[protected(c,award) for c in sdone],gate=ss,chance=100),guarded_action('The eastern ceasefire failed; postpone these terms',sabort,sp+' '+no(ss))])
    actions(by['soviet_refusal'],[guarded_action('Continue the campaign; reconsider in six months',sabort,sp)])
    fl=puppet('PRI')+' '+f('SOV_TERMS_DONE')+' NOT = { '+f('R14_PRI_AID')+' '+war('PRI')+' }'
    by['far_east_local'].actions=[guarded_action('Begin reconstruction',by['far_east_local'].actions[0].commands+[flag('R14_PRI_AID')],fl),Action('',[],gate=no(fl),chance=100)]
    for key in ('us_hold','us_terms','us_offer'):
        by[key].actions[-1].gate='OR = { NOT = { '+f('US_PENDING')+' } '+f('US_PEACE')+' '+f('R14_US_ACCEPTED')+' '+f('R14_US_STARTED')+' }'
    by['soviet_offer'].actions[-1].gate='OR = { NOT = { '+f('SOV_TERMS_PENDING')+' } '+f('SOV_TERMS_DONE')+' '+f('R14_SOV_ACCEPTED')+' }'

    # Persistent recovery catches interrupted old callbacks, external diplomacy,
    # and closing the war before accepted terms were actually implemented.
    for key,pg,invalid,commands in [('us',pending,no(INDEPENDENT+' '+war('USA')),abort),('sov',sp,no(INDEPENDENT+' '+war('SOV')),sabort)]:
        gate=pg+' '+invalid+' NOT = { '+f('R14_'+('US' if key=='us' else 'SOV')+'_PEACE_ISSUED')+' }'
        event('r14_'+key+'_interrupted','Peace talks are suspended','The war or alliance has changed since these talks began. The separate armistice cannot proceed. Any land already ceded stays with its present owner. No victory or treaty reward is granted. The proposal can return after a waiting period if its military conditions are met again.',gate=gate,persistent=True,offset=1,module='usa' if key=='us' else 'soviet',art='diplomacy',actions=[guarded_action('Continue under the present diplomatic position',commands,gate)])

    # National US surrender: frozen claims may complete after territorial losses
    # change, but ownership, continuing war, and consent must still be rechecked.
    invpending=f('US_INV_PENDING')+' '+f('US_INV_ACCEPTED')
    for key in ('us_inv_snapshot','us_inv_land','us_inv_peace'):
        e=by[key]
        e.actions=[guarded_action(a.name,a.commands,a.gate+' '+war('USA'),a.chance) for a in e.actions]
        e.actions.append(Action('',[later('us_inv_failed',1)],gate=invpending+' NOT = { '+war('USA')+' }',chance=100))
    inv_interrupted=f('US_INV_PENDING')+' NOT = { '+war('USA')+' '+f('US_INV_DONE')+' }'
    event('r14_us_national_interrupted','American surrender talks are suspended',
        'The American war ended before these terms were completed. No further territory or surrender reward is granted. Existing ownership remains in place. Another offer requires a new qualifying war.',
        gate=inv_interrupted,persistent=True,offset=1,module='usa_invasion',art='diplomacy',actions=[
            guarded_action('Continue under the present peace',[clear('US_INV_ACCEPTED'),clear('US_INV_SNAPSHOT_READY'),clear('US_INV_VERIFIED'),flag('US_INV_WAIT'),later('us_inv_return',90),clear('US_INV_PENDING')],inv_interrupted)])
    for key in ('us_inv_snapshot','us_inv_land'):
        for a in by[key].actions:
            a.commands=[widen(c,True) for c in a.commands]
    # National terms accept actual allied objectives. Allocation itself remains
    # explicitly USA-owned; independent allied land can never enter its claims.
    for key in ('us_mainland','us_national_terms','us_inv_offer'):
        e=by[key]; e.gate=widen(e.gate)
        for a in e.actions:a.gate=widen(a.gate)

    # Compact public gates. Hidden one-day watchers maintain advisory flags;
    # every action using them hands execution to a same-country receiver which
    # rechecks actual contemporary control/alliance before any command runs.
    # Stale flags can show an offer briefly, but can never authorise a transfer.
    wrapped=[]
    for e in list(EVENTS):
        for i,a in enumerate(e.actions):
            if 'JX_R14_CAPTURE_' not in a.gate or not a.commands:continue
            key='r14_commit_'+e.key+'_'+str(i)
            full=expanded(a.gate)
            fallback=[]
            if e.key in ('us_hold','us_terms','us_offer','us_implement'):
                fallback=[protected(c,pending+' NOT = { '+f('R14_US_PEACE_ISSUED')+' }') for c in abort]
            elif e.key=='soviet_offer':
                fallback=[protected(c,sp+' NOT = { '+f('R14_SOV_PEACE_ISSUED')+' }') for c in sabort]
            event(key,'Carry out the agreed terms','',country=e.country,triggered=True,module=e.module,actions=[guarded_action('',a.commands,full),guarded_action('',fallback,no(full))])
            a.commands=[fire(key)]
            wrapped.append(key)
    for p in sorted(OBJECTIVES):
        actual=coalition(p);marker=f('R14_CAPTURE_'+str(p))
        gate='flag = JX_ACTIVE OR = { AND = { '+marker+' '+no(actual)+' } AND = { NOT = { '+marker+' } '+actual+' } }'
        event('r14_capture_'+str(p),'Allied occupation changes','',gate=gate,persistent=True,offset=1,module='diplomacy',actions=[
            guarded_action('',[flag('R14_CAPTURE_'+str(p))],actual+' NOT = { '+marker+' }'),
            guarded_action('',[clear('R14_CAPTURE_'+str(p))],marker+' '+no(actual))])

    treaty=f('US_PEACE')+' '+f('US_RETURN_HAWAII')+' NOT = { '+war('USA')+' '+f('R14_ARMISTICE_BROKEN')+' '+f('R14_US_RENEWED')+' } event = { id = @us_signed days = 1800 }'
    actions(by['us_treaty_expiry'],[
        guarded_action('Renew the non-aggression agreement',[cmd('non_aggression',which='JAP',where='USA',when=1800),flag('R14_US_RENEWED')],treaty),
        guarded_action('Let ordinary diplomacy resume',[flag('US_TREATY_EXPIRED'),flag('R14_US_RENEWED')],treaty,0)])

    # Store a full occupation/consent predicate once per province, not once per
    # snapshot clause and owner. Refresh it synchronously before every batch
    # that uses it, including cached actions and delayed retries. Ownership and
    # opponent-war checks remain on each individual transfer command.
    authority_receivers=[]
    for e in list(EVENTS):
        for a in e.actions:
            required=sorted({int(p) for c in a.commands for p in re.findall(r'JX_R14_AUTH_(\d+)\b',c)})
            if required:
                a.commands=[fire('r14_authorise_'+str(p)) for p in required]+a.commands
                authority_receivers.append(e.key)
    for p in sorted(AUTHORITIES):
        actual=coalition(p,True)
        event('r14_authorise_'+str(p),'Check the present occupation agreement','',triggered=True,module='diplomacy',actions=[
            Action('',[clear('R14_AUTH_'+str(p)),cond(actual,flag('R14_AUTH_'+str(p)))],chance=100)])

    assert all(next(e for e in EVENTS if e.key==k).id==v for k,v in original_ids.items())
    REPORT.update(original_count=len(original_ids),added=len(EVENTS)-len(original_ids),partners=list(PARTNERS),country_roots=[e.key for e in roots],limited_claims=len(us_claims),current_carrier_gate=carrier_leverage,harsh_gate=harsh,objectives=sorted(OBJECTIVES),authorities=sorted(AUTHORITIES),authority_receivers=sorted(set(authority_receivers)),guarded_commits=wrapped,flags=['JX_US_PEACE','JX_US_RETURN_HAWAII','JX_US_KEEP_HAWAII','JX_SOV_TERMS_DONE'])
    return REPORT

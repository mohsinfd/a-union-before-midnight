"""R14 Chinese surrender and non-destructive postwar army handling.

No IDs are allocated, files installed or game processes started on import.
"""
from catalog import EVENTS, Action, event, cmd, cond, flag, clear, later, puppet, control
from copy import deepcopy

MAX_SURVIVORS = 60
NATIVE_CHAIN = (2011012, 2012017, 2011013, 2011014,
                2011015, 2012018, 2011016, 2011017)
REPORT = {}
ORIGINAL_REORGANISE = None
INTERRUPTION_REPORT = {}


def append_interruption():
    """Append AFTER all R14 events: retain every already-released R14 ID.

    A receiver belonging to annexed China never executes. Japan must close its
    own pending negotiation rather than wait forever for the missing country.
    """
    if INTERRUPTION_REPORT:return INTERRUPTION_REPORT
    from r14_peace import guarded_action
    live=('flag = JX_ACTIVE flag = JX_CHINA_LIMITED_PENDING '
          'NOT = { flag = JX_CHINA_LIMITED_DONE exists = CHI }')
    e=event('r14_china_limited_interrupted','Chinese peace talks end','',
            gate=live,persistent=True,offset=1,year=1937,module='diplomacy',
            actions=[guarded_action('',[
                clear('CHINA_LIMITED_ACCEPTED_R14'),clear('CHINA_LIMITED_PENDING'),
                flag('CHINA_LIMITED_WAIT'),later('china_limited_return',90),
            ],live)])
    INTERRUPTION_REPORT.update(applied=True,event=e.key,id=e.id)
    return INTERRUPTION_REPORT


def army_limit(tag):
    # Documented daily own-force statistics include own expeditionary troops.
    # Ready divisions only: no construction orders or dormant scenario units.
    return ('NOT = { army = { country = '+tag+
            f' size = {MAX_SURVIVORS+1} type = 0 when = 0 where = 1 which = 1 }} }}')


def decisive():
    return ('OR = { NOT = { exists = CHI } AND = { '+army_limit('CHI')+
            ' lost_VP = { country = CHI value = 65 } } } '
            'OR = { exists = CHI NOT = { exists = U87 } AND = { '+army_limit('U87')+
            ' lost_VP = { country = U87 value = 65 } } }')


def _guard(e, extra):
    fallback = False
    for a in e.actions:
        if a.commands:
            a.gate = (a.gate+' '+extra).strip()
        else:
            fallback = True
            a.gate = 'OR = { AND = { '+(a.gate or 'ai = yes ai = no')+' } NOT = { AND = { '+extra+' } } }'
    if not fallback:e.actions.append(Action('',[],gate='NOT = { AND = { '+extra+' } }'))


def apply():
    global ORIGINAL_REORGANISE
    if REPORT:return REPORT
    by = {e.key:e for e in EVENTS}
    before = {e.key:e.id for e in EVENTS}
    root = by['china']
    extra = decisive()
    root.gate += ' '+extra
    # The decision's material actions also defend against a forced invocation.
    for a in root.actions:
        if any('JX_china_PENDING' in c for c in a.commands):
            a.gate = (a.gate+' '+extra).strip()
    root.desc = ('A decisive Chinese defeat requires Nanjing, Shanghai and Chongqing under Japanese control, '
                 '55% of Chinese national territory lost, 65% of victory points lost, and no more than '
                 '60 surviving deployed Chinese land formations. Troops serving abroad still count; '
                 'unbuilt orders and dormant formations do not.\n\n'
                 'Choose a Chinese puppet or an independent settlement, with the stated Shanghai base terms. '
                 'Surviving Chinese troops remain with their government. No replacement army is created. '
                 'A separate limited peace can end the war earlier without making China a puppet.')
    # Check once more before the receiver ends the war or changes CHI's tag.
    for key in ('china_withdraw', 'china_withdraw_existing'):
        tag='CHI' if key=='china_withdraw' else 'U87'
        battlefield=('war = { country = JAP country = '+tag+' } '+
                     ' '.join(control(p) for p in (1337,1338,1299))+
                     ' lost_national = { country = '+tag+' value = 55 }')
        _guard(by[key],extra+' '+battlefield)

    # Limited peace deliberately keeps the larger Chinese army and government.
    # Pending + recorded Chinese acceptance protect every delayed receiver.
    limited = by['china_limited']
    for a in limited.actions:a.gate=(a.gate+' '+limited.gate+' year = 1937').strip()
    pending=('flag = JX_ACTIVE exists = JAP exists = CHI flag = JX_CHINA_LIMITED_PENDING '
             'NOT = { ispuppet = JAP flag = JX_china_PENDING flag = JX_china_SETTLED '
             'flag = JX_CHINA_LIMITED_DONE }')
    battlefield=('war = { country = JAP country = CHI } '+
                 ' '.join(control(p) for p in (1337,1338,1317))+
                 ' lost_national = { country = CHI value = 35 }')
    offer=by['china_limited_offer']
    offer.actions[0].commands.insert(0,flag('CHINA_LIMITED_ACCEPTED_R14'))
    _guard(offer,pending+' '+battlefield)
    offer.actions[-1].commands=[clear('CHINA_LIMITED_PENDING'),flag('CHINA_LIMITED_WAIT'),later('china_limited_return',90)]
    offer.actions[-1].gate=pending+' NOT = { AND = { '+battlefield+' } }'
    offer.actions.append(Action('',[],gate='NOT = { AND = { '+pending+' } }'))
    accept=by['china_limited_accept']
    accepted=pending+' flag = JX_CHINA_LIMITED_ACCEPTED_R14'
    _guard(accept,accepted+' '+battlefield)
    # If the front changes during negotiations, close cleanly without a peace.
    accept.actions[-1].commands=[clear('CHINA_LIMITED_PENDING'),clear('CHINA_LIMITED_ACCEPTED_R14'),
                                flag('CHINA_LIMITED_WAIT'),later('china_limited_return',90)]
    accept.actions[-1].gate=pending+' NOT = { AND = { flag = JX_CHINA_LIMITED_ACCEPTED_R14 '+battlefield+' } }'
    accept.actions.append(Action('',[],gate='NOT = { AND = { '+pending+' } }'))
    _guard(by['china_limited_signed'],accepted)
    _guard(by['china_limited_refused'],pending)
    for key in ('china_limited_signed','china_limited_refused'):
        for a in by[key].actions:
            if a.commands:a.commands.insert(0,clear('CHINA_LIMITED_ACCEPTED_R14'))

    # Replace the destructive delayed size test at its EXISTING event ID.
    # This closes for small armies and while at war too. Later construction can
    # never reopen it, and neither an absent capital nor independence delays it.
    assess = by['cn_reorganise']
    ORIGINAL_REORGANISE=deepcopy(assess)
    assess.title = 'China retains its surviving army'
    assess.desc = ''
    assess.gate = ('flag = JX_china_SETTLED exists = U87 '
                   'NOT = { flag = JX_CN_ASSESSED_R14 }')
    assess.offset = 1
    assess.actions = [Action('',[
        flag('CN_ASSESSED_R14'),
        cond(puppet('U87'),cmd('ai',which='"jx/china_home_b1.ai"')),
    ],gate=assess.gate,chance=100),
        Action('',[],gate='NOT = { AND = { '+assess.gate+' } }')]
    # Compatibility only: pre-R14 saves may already contain identifiable locked
    # template units or the explicitly recorded B1 legacy IDs. Their existing
    # release waves unlock those identities, never remove or add formations.
    independent = by['cn_independent_b1']
    independent.gate = ('OR = { flag = JX_CN_REORG flag = JX_CN_LEGACY } '
                        'NOT = { '+puppet('U87')+' flag = JX_CN_INDEPENDENT }')
    for a in independent.actions:
        if a.commands:a.gate = independent.gate
    by['cn_notice'].title = 'Chinese army integration'
    by['cn_notice'].desc = ('Surviving formations from the earlier army agreement remain in service. '
                            'The agreed movement restrictions end in stages. No replacement divisions are created.')
    # Actions can remain open while their battlefield or diplomatic state
    # changes. Acquire a private receipt before the batch changes its own gate.
    from r14_peace import guarded_action
    protected_keys=('china','china_withdraw','china_withdraw_existing','china_limited',
                    'china_limited_offer','china_limited_accept','china_limited_signed',
                    'china_limited_refused','cn_reorganise','cn_independent_b1')
    for key in protected_keys:
        e=by[key]
        e.actions=[guarded_action(a.name,a.commands,a.gate,a.chance) if a.commands else a for a in e.actions]
    assert before == {e.key:e.id for e in EVENTS}, 'R14 China must preserve event IDs'
    REPORT.update(max_surviving_deployed=MAX_SURVIVORS,retained_ids=len(before),
                  native_chain=list(NATIVE_CHAIN),army_replacement_removed=True)
    return REPORT


def install(source,target,read,write,parse,serialise):
    """Call AFTER patch_baseline; retain other native patches in target file.

    Source is accepted for the common installer contract. The target is already
    restored from clean B&I by the builder. Repeating this hook is idempotent.
    """
    path=target/'db/events/japan.txt'
    tree=parse(read(path));seen=[]
    def get(n,k,default=None):return next((v for key,v in n if key==k),default)
    def guard(n,k):
        node=get(n,k)
        if node is None:n.append((k,[('NOT',[('flag','JX_ACTIVE')])]))
        elif ('NOT',[('flag','JX_ACTIVE')]) not in node:node.append(('NOT',[('flag','JX_ACTIVE')]))
    def inert(a):
        return (get(a,'name')=='ACTION_NAME_OK' and get(a,'trigger')==[('flag','JX_ACTIVE')]
                and get(a,'command')==[])
    for k,e in tree:
        if k!='event' or int(get(e,'id',0)) not in NATIVE_CHAIN:continue
        seen.append(int(get(e,'id')));guard(e,'trigger')
        for key,a in e:
            if key=='action' or key.startswith('action_'):
                if inert(a):continue
                guard(a,'trigger')
        # A stale directly triggered stock receiver must have an inert option.
        if not any(key=='action' and inert(a) for key,a in e):
            e.append(('action',[('name','ACTION_NAME_OK'),('ai_chance','100'),
                                ('trigger',[('flag','JX_ACTIVE')]),('command',[])]))
    assert sorted(seen)==sorted(NATIVE_CHAIN),('Missing B&I China chain',seen)
    write(path,serialise(tree)+'\n')
    return {'file':'db/events/japan.txt','guarded_native_china_events':sorted(seen)}

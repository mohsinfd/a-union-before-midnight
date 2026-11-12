"""Append-only compatibility and eligibility checks for Japan Rising construction.

Call apply() once at the END of prepare_catalog(), then refresh the builder's
IDS from catalog.EVENTS. No build import, installation or game execution here.

The installed engine contract requires ownership/control, construction research
and supply. There is no documented province-supply event predicate. The original
snapshot helpers remain registered for older saves, but L2 awards use native
construction in the due-date event after eligibility checks. Engine rejection
after those checks is not claimed to be an observed atomic transaction.
"""
from pathlib import Path
from collections import defaultdict
import csv
import re
from catalog import EVENTS,Action,event,cmd,cond,flag,clear,fire,later,money,supplies,owned,control
from audit_japan_baseline import parse,get,getall,num

from runtime_paths import SOURCE
from runtime_paths import GAME
IC_BOUND=200
APPLIED=False
REPORT=[]


def effective_award(definition,action_index=0):
    """Expose promised awards to offline bounds after moving them to receipts."""
    e=next(x for x in EVENTS if x.key==definition) if isinstance(definition,str) else definition
    row=next((r for r in REPORT if r['event']==e.key and r['action']==action_index),None)
    if row:
        receipt=next(x for x in EVENTS if x.key==row['receipt_event'])
        return [cmd('construct',which=k,where=p,value=d) for p,k,d in row['buildings']]+receipt.actions[0].commands
    return e.actions[action_index].commands


def read(p):return p.read_text(encoding='latin1')


def building(p,kind,n):
    return f'building = {{ province = {p} type = {kind} value = {n:g} }}'


def _allow_techs():
    result=defaultdict(set)
    for p in (SOURCE/'db/tech').glob('*.txt'):
        for tree in getall(parse(read(p)),'technology'):
            for app in getall(tree,'application'):
                for c in getall(get(app,'effects',[]),'command'):
                    if get(c,'type')=='allow_building' and not get(c,'trigger'):
                        result[get(c,'which')].add(get(app,'id'))
    return result


def _constructs(action):
    grouped=defaultdict(int)
    for text in action.commands:
        n=parse(text)
        if get(n,'type')!='construct' or num(n,'value')<=0:continue
        if get(n,'trigger'):raise ValueError('Conditional construction requires an explicit transaction policy: '+text)
        grouped[(int(get(n,'where')),get(n,'which'))]+=int(num(n,'value'))
    return [(p,kind,delta) for (p,kind),delta in grouped.items()]


def _eligibility(actor,builds,rows,allow):
    terms=[]
    for p,kind,delta in builds:
        terms += [owned(p,actor),control(p,actor)]
        if kind in allow:
            terms.append('OR = { '+' '.join(f'technology = {{ country = {actor} value = {t} }}' for t in sorted(allow[kind]))+' }')
        cap=IC_BOUND if kind=='ic' else 100 if kind=='infrastructure' else 10
        # Infrastructure maximum sizes can be fractional. Keep strictly below
        # cap-delta so clamping cannot be mistaken for a full ten-point award.
        threshold=cap-delta+1
        if kind=='infrastructure':
            # Saved infrastructure uses a fraction while commands use percentage
            # points. The manual does not explicitly state building-trigger
            # scaling. Recognise both conventions instead of assuming one.
            terms.append('OR = { AND = { NOT = { '+building(p,kind,2)+' '+building(p,kind,(100-delta)/100)+' } } AND = { '+building(p,kind,2)+' NOT = { '+building(p,kind,100-delta)+' } } }')
        else:terms.append('NOT = { '+building(p,kind,threshold)+' }')
        if kind=='ic':
            terms.append('OR = { AND = { NOT = { '+building(p,'infrastructure',2)+' } '+building(p,'infrastructure',.31)+' } AND = { '+building(p,'infrastructure',2)+' '+building(p,'infrastructure',31)+' } }')
        if kind=='naval_base' and rows[p].get('Port Allowed')!='1':terms.append('NOT = { exists = '+actor+' }')
        if kind=='coastal_fort' and float(rows[p].get('Beaches') or 0)<=0:terms.append('NOT = { exists = '+actor+' }')
        if kind in {'rocket_test','nuclear_reactor'}:
            raise ValueError('Special building needs a specific geometry policy: '+kind)
    return ' '.join(dict.fromkeys(terms))


def _refund_commands(parent):
    result=[]
    for text in parent.actions[0].commands:
        n=parse(text)
        if get(n,'type') in {'money','supplies'} and num(n,'value')<0:
            result.append(cmd(get(n,'type'),value=-num(n,'value')))
    result += [clear(parent.key+'_PENDING'),flag(parent.key+'_WAIT'),later(parent.key+'_return',90)]
    return result


def _replace_capped_milestones(by_key):
    # These inherited locations start with level-ten ports (Hawaii also has a
    # level-ten airfield). Field packages support occupation without claiming
    # event construction in enemy-owned land or adding capacity above the cap.
    choices={
        'hawaii':('Support the Hawaiian bridgehead',
                  'Hawaii already starts with level-ten port and airfield facilities. Choose 100 convoy transports and 30 escorts, or a 1,600-supply operating reserve. These finite support packages work while the islands are occupied; they do not expand capped bases.',
                  [cmd('transport_pool',which=-1,value=100),cmd('escort_pool',which=-1,value=30)],
                  'Prepare the supply reserve',[supplies(1600)]),
        'singapore':('Keep the Singapore routes working',
                     'Singapore starts with a level-ten port. Choose 80 convoy transports and 40 escorts, or a 1,600-supply reserve for operations from the captured base. Existing facilities still need ships and supplies; this does not add port levels.',
                     [cmd('transport_pool',which=-1,value=80),cmd('escort_pool',which=-1,value=40)],
                     'Prepare the operating supply reserve',[supplies(1600)]),
        'hongkong':('Support the Hong Kong station',
                    'Hong Kong starts with a level-ten port. Choose a 1,600-supply reserve, or 60 convoy escorts for the shipping network. These finite support choices do not pretend to expand the occupied port.',
                    [supplies(1600)],'Fit the convoy escorts',[cmd('escort_pool',which=-1,value=60)]),
    }
    for key,(title,desc,reward,label,alt) in choices.items():
        parent=by_key[key];parent.title=title
        parent.desc=desc+' Funding costs 140 money and 800 supplies; work takes 150 days. You may delay or dismiss it.'
        parent.actions[0].name='Fund the first support package';parent.actions[1].name=label
        for idx,commands in enumerate((reward,alt)):
            finish=by_key[f'{key}_finish_{idx}'];finish.title=title+' - support ready';finish.desc=desc
            markers=[c for c in finish.actions[0].commands if get(parse(c),'type') in {'setflag','clrflag'}]
            finish.actions[0].commands=commands+markers


def _synthetic(by_key):
    parent=by_key['synthetic'];finish=by_key['synthetic_finish_0']
    changed=[]
    for text in finish.actions[0].commands:
        n=parse(text)
        if get(n,'type')=='add_prov_resource' and get(n,'where')=='energy':
            text=cmd('add_prov_resource',which=1550,where='energy',value=-20)
        changed.append(text)
    finish.actions[0].commands=changed
    extra=owned(1552)+' '+control(1552)+' '+owned(1550)+' '+control(1550)
    parent.actions[0].gate+=' '+extra;finish.actions[0].gate+=' '+extra
    if len(finish.actions)>1:
        finish.actions[1].gate='flag = JX_synthetic_PENDING NOT = { AND = { '+finish.actions[0].gate+' } }'
    parent.desc=parent.desc.replace('consuming twenty daily provincial energy output','consuming twenty daily provincial energy output at Yokohama (1550), which starts with 47 energy')
    finish.desc+=' The coal input is deducted at Japanese-owned and controlled Yokohama (1550), not zero-energy Tokyo.'


def _occupied_field_awards(by_key):
    """Keep a useful funded choice while the site is still enemy-owned."""
    replacements={
        'suez':(0,'Supply the fleet through Suez',
                'Commission 60 convoy transports and 25 escorts for the western route. Alternatively expand local airfield and AA facilities when Japan owns and controls the site. Shipping can be funded during occupation; this does not add buildings or bypass canal control.',
                [cmd('transport_pool',which=-1,value=60),cmd('escort_pool',which=-1,value=25)]),
        'forward_air':(1,'Fund the forward supply route instead',
                       'Build two airfield levels at Japanese-owned and controlled Soerabaja, or commission 40 convoy transports and a 1,000-supply reserve. The shipping choice is available during occupation. It supplies operations; it does not claim to create an airfield.',
                       [cmd('transport_pool',which=-1,value=40),supplies(1000)]),
        'siberian_rail':(0,'Fund the railway crews and operating reserve',
                         'Organise field railway crews and depots for 5 percent more transport capacity and a 1,500-supply operating reserve. Or order four mountain divisions through normal IC and manpower. This field programme works on occupied land; it does not claim provincial infrastructure construction.',
                         [cmd('tc_mod',value=5),supplies(1500)]),
        'thai_connection':(0,'Fund the railway crews and operating reserve',
                           'With Thailand allied and Rangoon held, hire railway crews and loading teams for 2 percent more transport capacity and a 1,200-supply reserve. Or add two airfield and two AA levels at Rangoon when Japan owns and controls it. The first choice works during occupation and does not add provincial infrastructure.',
                           [cmd('tc_mod',value=2),supplies(1200)]),
        'outer_oil':(0,'Restore the oil output and field stores',
                     'Restore five daily provincial oil output at Ahvaz and provide 500 supplies. This can operate while Japan controls the occupied field. Or expand its airfield and AA after Japan legally owns it. Oil still needs a working shipping route.',
                     [cmd('add_prov_resource',which=1089,where='oil',value=5),supplies(500)]),
    }
    for key,province in [('sumatra_oil',1636),('borneo_oil',1632),('java_oil',1653)]:
        replacements[key]=(0,'Restore the oil and commission tankers',
                           'Restore five daily provincial oil output and commission 40 convoy transports. Or restore three oil output and build two airfield levels when Japan owns and controls the site. The tanker choice works during occupation; resources still need protected shipping.',
                           [cmd('add_prov_resource',which=province,where='oil',value=5),cmd('transport_pool',which=-1,value=40)])
    for key,(choice,label,desc,rewards) in replacements.items():
        parent=by_key[key];pricing=parent.desc.split('Funding costs',1)[-1]
        parent.desc=desc+' Funding costs'+pricing;parent.actions[choice].name=label
        for i in (0,1):by_key[f'{key}_finish_{i}'].desc=desc+' The setup payment was made when work began. Normal military production, where selected, still takes IC, manpower and time.'
        finish=by_key[f'{key}_finish_{choice}']
        markers=[c for c in finish.actions[0].commands if get(parse(c),'type') in {'setflag','clrflag'}]
        finish.actions[0].commands=rewards+markers


def apply():
    global APPLIED
    if APPLIED:return REPORT
    APPLIED=True
    by_key={e.key:e for e in EVENTS}
    _replace_capped_milestones(by_key)
    _occupied_field_awards(by_key)
    _synthetic(by_key)
    rows={int(r['Id']):r for r in csv.DictReader(read(GAME/'map/Map_1/Province.csv').splitlines(),delimiter=';') if r.get('Id','').isdigit()}
    names={}
    for line in read(GAME/'map/Map_1/province_names.csv').splitlines():
        cells=line.split(';')
        if len(cells)>1 and re.fullmatch(r'PROV\d+',cells[0]):names[int(cells[0][4:])]=cells[1]
    allow=_allow_techs()
    # Move parent DONE/PENDING markers to the recipient's observed delivery.
    # The parent now fires the receiver immediately, eliminating the day-long
    # gap during which a recipient could disappear after successful payment.
    recipients={}
    for finish in list(EVENTS):
        match=re.fullmatch(r'(.+)_finish_(\d+)',finish.key)
        if not match:continue
        parent=by_key[match[1]]
        for i,text in enumerate(list(finish.actions[0].commands)):
            n=parse(text);target=str(get(n,'which','')).removeprefix('@')
            child=by_key.get(target)
            if get(n,'type') not in {'event','trigger'} or not child or not any(_constructs(a) for a in child.actions):continue
            markers=[c for c in finish.actions[0].commands if get(parse(c),'which') in {'JX_'+parent.key+'_DONE','JX_'+parent.key+'_PENDING'}]
            finish.actions[0].commands=[c for c in finish.actions[0].commands if c not in markers]
            finish.actions[0].commands=[fire(target) if c==text else c for c in finish.actions[0].commands]
            child.actions[0].commands+=markers
            child.actions[0].gate+=' flag = JX_'+parent.key+'_PENDING '+finish.actions[0].gate
            recipients[child.key]=(parent,int(match[2]))
    original=list(EVENTS)
    for e in original:
        for ai,a in enumerate(list(e.actions)):
            builds=_constructs(a)
            if not builds:continue
            match=re.fullmatch(r'(.+)_finish_(\d+)',e.key)
            paid=(by_key[match[1]],int(match[2])) if match else recipients.get(e.key)
            eligibility=_eligibility(e.country,builds,rows,allow)
            original_gate=a.gate
            valid=(original_gate+' '+eligibility).strip()
            if paid:
                parent,choice=paid
                parent.actions[choice].gate+=' '+eligibility
                note=' Building work requires ownership and control of every site, construction research and room for the full increase. If the work cannot finish, it is cancelled and the setup payment is returned.'
                if note not in parent.desc:parent.desc+=note
            number=len(REPORT);stem=f'cs_{number}';active='CS_'+str(number)+'_ACTIVE';complete='CS_'+str(number)+'_DONE'
            valid+=' NOT = { flag = JX_'+active+' flag = JX_'+complete+' }'
            nonbuilding=[text for text in a.commands if get(parse(text),'type')!='construct']
            snapshot=[];observed=[];rollback=[];cleanup=[]
            for bi,(p,kind,delta) in enumerate(builds):
                cap=IC_BOUND if kind=='ic' else 100 if kind=='infrastructure' else 10
                step=10 if kind=='infrastructure' and delta%10==0 else 1
                alternatives=[]
                modes=[('',1,'')]
                if kind=='infrastructure':
                    modes=[('R',.01,'NOT = { '+building(p,kind,2)+' }'),('P',1,building(p,kind,2))]
                for mode,scale,mode_gate in modes:
                    marker=f'CS_{number}_{bi}_{mode}BEFORE'
                    cleanup.append(clear(marker))
                    for before in range(0,cap-delta+1,step):
                        prior=mode_gate+' '+building(p,kind,before*scale)+' NOT = { '+building(p,kind,(before+step)*scale)+' }'
                        after=f'flag = {{ which = JX_{marker} when = 0 value = {before+1} }} '+building(p,kind,(before+delta)*scale)
                        snapshot.append(cond(prior,cmd('setflag',which='JX_'+marker,value=before+1)))
                        alternatives.append('AND = { '+after+' }')
                        rollback.append(cond(after,cmd('construct',which=kind,where=p,value=-delta)))
                observed.append('OR = { '+' '.join(alternatives)+' }')
            success='flag = JX_'+active+' '+' '.join(observed)
            failed='flag = JX_'+active+' NOT = { AND = { '+' '.join(observed)+' } }'
            refunds=_refund_commands(paid[0]) if paid else []
            refund_key=stem+'_refund'
            refund_gate=('flag = JX_'+paid[0].key+'_PENDING NOT = { flag = JX_'+paid[0].key+'_DONE }') if paid else ('NOT = { flag = JX_'+complete+' }')
            event(refund_key,'Building work cancelled',
                  'The promised facilities could not be completed. This attempt adds no buildings or other benefits. The setup payment is returned. Reconsider after 90 days, when ownership, research, supply and room permit the work.' if paid else '',
                  country=paid[0].country if paid else e.country,triggered=True,
                  actions=[Action('Recover the setup funds' if paid else '',refunds if paid else nonbuilding+[flag(complete)],gate=refund_gate,chance=100),
                           Action('The payment has already been processed' if paid else '',[],gate='NOT = { AND = { '+refund_gate+' } }')],module='construction_safety',art=e.art)
            event(stem+'_verify','Check the building delivery','',country=e.country,triggered=True,
                  actions=[Action('',nonbuilding+cleanup+[clear(active),flag(complete)],gate=success,chance=100),
                           Action('',rollback+cleanup+[clear(active),fire(refund_key)],gate=failed),
                           Action('',[],gate='NOT = { flag = JX_'+active+' }')],module='construction_safety',
                  purpose='Synchronous observed-growth receipt; all other rewards and DONE wait for delivery. Roll back only observed increments from this uninterrupted attempt.')
            event(stem+'_start','Build and verify the funded facilities','',country=e.country,triggered=True,
                  actions=[Action('',[flag(active)]+snapshot+[cmd('construct',which=k,where=p,value=d) for p,k,d in builds]+[fire(stem+'_verify')],gate=valid,chance=100),
                           Action('',[fire(refund_key)] if paid else [],gate='NOT = { AND = { '+valid+' } }')],module='construction_safety')
            a.gate=valid;a.commands=[fire(stem+'_start')]
            if paid:
                # At a recipient receiver, failure refunds the Japanese payer
                # rather than silently replacing the factory with local supplies.
                pending='flag = JX_'+paid[0].key+'_PENDING'
                failure=Action('The work is unavailable; return the setup funds',[fire(refund_key)],gate=pending+' NOT = { AND = { '+valid+' } }')
                if len(e.actions)>1:e.actions[1]=failure
                else:e.actions.append(failure)
                e.actions.append(Action('No further work is due',[],gate='NOT = { '+pending+' }'))
            else:
                e.actions.append(Action('Deliver the supply grant; factory work is unavailable',[fire(refund_key)],gate='NOT = { flag = JX_'+complete+' } NOT = { AND = { '+valid+' } }'))
                e.actions.append(Action('The grant has already been delivered',[],gate='flag = JX_'+complete))
            e.title=e.title.replace(' - completed',' - work is due')
            sites=', '.join(f'{d} '+('IC' if k=='ic' else k.replace('_',' '))+f' at {names.get(p,str(p))} ({p})' for p,k,d in builds)
            e.desc=('The funded work is due: '+sites+'. The country doing the work must own and control the sites, have the construction research and enough supply and room. If the whole job cannot finish, it is cancelled and the setup payment is returned. Other funded benefits follow only after all building work is completed.') if paid else ('The development grant can add '+sites+'. The receiving country must own and control the site and have the research, supply and room to build. If factory work is unavailable, the supply grant still arrives once.')
            REPORT.append({'event':e.key,'country':e.country,'action':ai,'payer':paid[0].key if paid else None,
                           'buildings':builds,'eligibility':eligibility,'snapshot_event':stem+'_start','receipt_event':stem+'_verify'})
    # Use native event construction at the due-date window. The former
    # synchronous snapshot/rollback chain cancelled a valid home award in the
    # user's engine and exposed its technical receivers. Keep all eligibility
    # checks and once-only markers, without claiming an atomic delivery receipt.
    # Leave old helper IDs registered for save compatibility; new awards never
    # enter their snapshot/rollback path.
    latest={x.key:x for x in EVENTS}
    for r in REPORT:
        original=latest[r['event']];action=original.actions[r['action']]
        receipt=latest[r['receipt_event']]
        extras=[c for c in receipt.actions[0].commands
                if not (get(parse(c),'type') in {'setflag','clrflag'} and
                        str(get(parse(c),'which','')).startswith('JX_CS_'))]
        number=r['snapshot_event'].split('_')[1]
        done='CS_'+number+'_DONE'
        action.commands=[cmd('construct',which=k,where=p,value=d) for p,k,d in r['buildings']]+extras+[flag(done)]
        if r['payer'] and original.country==latest[r['payer']].country:
            refund=latest[r['receipt_event'].replace('_verify','_refund')]
            if len(original.actions)>1:original.actions[1].commands=refund.actions[0].commands
        original.title=original.title.replace(' - work is due',' - ready to open')
        sites=', '.join(str(d)+' '+('IC' if k=='ic' else k.replace('_',' '))+' at '+names.get(p,str(p)) for p,k,d in r['buildings'])
        original.desc='The funded work is ready: '+sites+'. Open the facilities now. The setup bill was paid when the programme began. The sites must still be owned, controlled and able to support construction. If those requirements fail, the setup funds are returned and the offer can return in 90 days.' if r['payer'] else 'The agreed development grant adds '+sites+'. Ownership, control, research and construction capacity are checked before the award.'
        r['delivery_policy']='native construction once after eligibility checks; no snapshot rollback'
    return REPORT

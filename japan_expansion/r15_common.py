"""Finite Japanese commitments with one shared, owner-checked investment slot.

No game, filesystem or catalogue mutation on import. Modules declare proposals
after the released R14.1 catalogue, then use the existing final render passes.
"""
from catalog import EVENTS, Action, event, cmd, flag, clear, fire, later, cond, active
from r14_peace import guarded_action

REPORT = {}
ALIASES = {'manpower':'manpowerpool','oil':'oilpool','energy':'energypool',
           'metal':'metalpool','rare_materials':'rarematerialspool'}


def f(name):return 'flag = JX_'+name
def no(gate):return 'NOT = { AND = { '+gate+' } }'
def resources(cost,sign=1):
    assert set(cost)<=set(ALIASES)|{'money','supplies'}
    return [cmd(ALIASES.get(kind,kind),value=amount*sign) for kind,amount in cost.items() if amount]
def funds(cost):return ' '.join(f'{kind} = {amount:g}' for kind,amount in cost.items() if amount)


def proposal(key,title,desc,context,choices,*,year=1941,art='army',module='r15_strategy',retry_on_failure=False):
    """Each choice: label/cost/days/valid/rewards, optional focus.

    Context controls initial availability; valid controls funding and delivery.
    Losing the original crisis need not cancel rebuilding already commissioned.
    A private funding clock sets the timetable. Reopening the public proposal
    while work is pending cannot move its delivery date.
    """
    assert key.startswith('r15_') and key not in REPORT and len(choices)==2
    assert all(c['days']>0 and c['cost'] for c in choices)
    stem=key.upper();owner=stem+'_OWNS_COMMITMENT';pending=stem+'_PENDING'
    closed=stem+'_CLOSED';declined=stem+'_DECLINED';waiting=stem+'_WAIT'
    rootgate=active()+f' year = {year} '+context+' NOT = { '+f(closed)+' '+f(declined)+' '+f(pending)+' '+f(waiting)+' }'
    free='NOT = { '+f('R15_MAJOR_PENDING')+' }'
    bills=[]
    for c in choices:
        bill=', '.join(f'{v:,g} {k.replace("_"," ")}' for k,v in c['cost'].items() if v)
        bills.append(c['label']+f': {bill}; {c["days"]} days.')
    failure=(' Failed work can be reconsidered after 90 days.' if retry_on_failure else ' One funded attempt; a refund also ends this plan.')
    text=desc+'\n\n'+'\n'.join(bills)+'\n\nTraining and transport staff can handle one major programme at a time. Completing one choice closes the other. If delivery cannot proceed, all paid inputs return.'+failure+' Stopping work ends this plan: recover all manpower, oil and metal and 75% of supplies; money is spent.'
    assert len(text)<=1100,(key,len(text))
    root=event(key,title,text,decision=True,persistent=True,gate=rootgate,year=year,
               art=art,module=module,ready=f'year = {year}',actions=[])
    rows=[]
    for index,c in enumerate(choices):
        selected=stem+'_CHOICE_'+str(index);finish=key+'_finish_'+str(index);clock=key+'_clock_'+str(index)
        valid=active()+' '+c.get('valid','')
        gate=rootgate+' '+free+' '+funds(c['cost'])+' '+valid
        focus=c.get('focus');focusname='R15_FOCUS_'+focus if focus else None
        start=[flag(owner),flag('R15_MAJOR_PENDING'),flag(pending),flag(selected)]
        if focusname:start.append(flag(focusname))
        start+=resources(c['cost'],-1)+[fire(clock),later(finish,c['days'])]
        root.actions.append(guarded_action(c['label'],start,gate,100 if index==0 else 0))
        clockgate=f(pending)+' '+f(selected)+' '+f(owner)
        event(clock,'The preparations begin','',triggered=True,year=year,module=module,art=art,
              actions=[Action('',[],gate=clockgate,chance=100),Action('',[],gate=no(clockgate),chance=100)])
        due=f(pending)+' '+f(selected)+' NOT = { '+f(closed)+' } '+f'event = {{ id = @{clock} days = {c["days"]} }}'
        cleanup=[clear(selected),clear(pending),
                 cond(f(owner),clear('R15_MAJOR_PENDING')),clear(owner)]
        if focusname:cleanup.append(clear(focusname))
        success=list(c['rewards'])
        if focusname:success.append(flag(focusname+'_DONE'))
        success+=cleanup+[flag(closed)]
        refund=resources(c['cost'])+cleanup
        if retry_on_failure:
            waitbranch=stem+'_WAIT_'+str(index);back=key+'_return_'+str(index)
            refund += [flag(waitbranch),flag(waiting),later(back,90)]
            returns=f(waitbranch)+' '+f(waiting)+' NOT = { '+f(pending)+' '+f(closed)+' } '+f'event = {{ id = @{finish} days = 90 }}'
            event(back,title+' - the plan can be reconsidered','',triggered=True,year=year,module=module,art=art,
                  actions=[guarded_action('',[clear(waitbranch),clear(waiting)],returns),Action('',[],gate=no(returns),chance=100)])
        else:refund.append(flag(closed))
        completion=event(finish,title+' - preparations complete',
            c.get('result',c['label']+'. The promised forces and stocks are ready. Units need normal organisation, fuel and supplies.'),
            triggered=True,year=year,module=module,art=art,actions=[
                guarded_action('Put the preparations into service',success,due+' '+valid),
                guarded_action('Return the investment; delivery cannot proceed',refund,due+' '+no(valid)),
                Action('',[],gate=no(due),chance=100)])
        assert len(completion.desc)<=1100
        rows.append(dict(choice=index,finish=finish,clock=clock,cost=c['cost'],days=c['days'],
                         valid=c.get('valid',''),focus=focus,owner=owner,rewards=list(c['rewards'])))
    root.actions += [Action('Close this window without changing plans',[],gate=rootgate),
                     guarded_action('Set this plan aside for the rest of the campaign',[flag(declined)],rootgate,0)]
    pending_view=active()+' '+f(pending)+' NOT = { '+f(closed)+' }'
    root.gate='OR = { AND = { '+rootgate+' } AND = { '+pending_view+' } }'
    root.actions[2].gate='OR = { AND = { '+rootgate+' } AND = { '+pending_view+' } }'
    for index,c in enumerate(choices):
        selected=stem+'_CHOICE_'+str(index)
        stop=pending_view+' '+f(selected)+' '+f(owner)
        returned={k:(v*.75 if k=='supplies' else v) for k,v in c['cost'].items() if k!='money'}
        cleanup=[clear(selected),clear(pending),flag(closed),cond(f(owner),clear('R15_MAJOR_PENDING')),clear(owner)]
        if c.get('focus'):cleanup.append(clear('R15_FOCUS_'+c['focus']))
        root.actions.append(guarded_action('Cancel permanently; lose money and 25% of supplies',resources(returned)+cleanup,stop,0))
    REPORT[key]=dict(key=key,owner=owner,pending=pending,closed=closed,choices=rows,retry_on_failure=retry_on_failure,
                    cancellation='Ends the plan; all manpower/oil/metal and75% supplies return, money spent.')
    return root

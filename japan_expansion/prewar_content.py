"""Six substantial optional human-Japan preparations, appended after R10.

Importing is inert. Call append_events() after all existing catalogue passes,
then refresh the builder's IDS. Funding is manual; exactly one guarded notice
arrives when the selected work is due. No reminder, claim-card or war cascade.
"""
from dataclasses import dataclass
from catalog import EVENTS, Action, event, cmd, active, human, flag, clear, later, owned, control, war

REPORT = {}
MODULE = 'prewar_content'
POOL_COMMANDS = {'money':'money', 'supplies':'supplies', 'oil':'oilpool',
                 'energy':'energypool', 'metal':'metalpool', 'manpower':'manpowerpool'}
DOCUMENTED_NEW_COMMANDS = {'morale', 'max_organization', 'naval_defense', 'speed',
                           'surface_detection', 'shore_attack', 'max_amphib_mod', 'trickleback_mod'}


@dataclass
class Choice:
    label: str
    result: str
    costs: dict
    rewards: list[str]
    context: str = ''
    buildings: tuple = ()  # (province, kind, positive increment)


@dataclass
class Programme:
    key: str
    title: str
    story: str
    year: int
    month: str
    days: int
    choices: tuple[Choice, Choice]
    art: str = 'industry'


def _build(province, kind, delta):
    return cmd('construct', which=kind, where=province, value=delta)


def _vital(province):
    return owned(province)+' '+control(province)


def _building(province, kind, level):
    return f'building = {{ province = {province} type = {kind} value = {level:g} }}'


def _not(gate):
    return 'NOT = { AND = { '+gate+' } }'


def _eligibility(choice):
    """Native ownership, construction research, capacity and IC-infra contract.

    Province supply has no documented trigger. These are owned home-city sites;
    supply rejection is still an engine qualification, documented in the text.
    """
    gates = [human(), choice.context]
    for province, kind, delta in choice.buildings:
        gates += [_vital(province), f'technology = {5800 if kind == "ic" else 2800}']
        cap = 200 if kind == 'ic' else 10
        gates.append('NOT = { '+_building(province, kind, cap-delta+1)+' }')
        if kind == 'ic':
            # DH saves infrastructure as a fraction; older event conventions
            # may use percentage points. Require >30 in either representation.
            gates.append('OR = { AND = { NOT = { '+_building(province,'infrastructure',2)+' } '+
                         _building(province,'infrastructure',.31)+' } AND = { '+
                         _building(province,'infrastructure',2)+' '+_building(province,'infrastructure',31)+' } }')
    return ' '.join(dict.fromkeys(gates))


def programmes():
    labour = dict(money=45, supplies=400, metal=300)
    flight = dict(money=60, supplies=450, oil=250)
    radio = dict(money=75, supplies=600, metal=500, energy=1000)
    landing = dict(money=80, supplies=800, oil=300)
    medicine = dict(money=60, supplies=700)
    industry = dict(money=90, supplies=900, metal=1000)
    return (
        Programme('prewar_rural_works', 'Rural recovery: workshops or reserve rolls?',
            'Officials seek work for rural households while the Army wants a broader register of fit recruits. '
            'Industrial employment commits men who could otherwise enter the replacement pool. Reserve registration '
            'preserves that military option, but another levy is unpopular. This is an economic choice, not a change of government.',
            1933, 'april', 270, (
                Choice('Employ the workforce in Nagoya workshops',
                       'Add 3 physical IC at Nagoya (1557). Earmark 25 manpower for permanent civilian employment now; it is not returned after successful completion.',
                       {**labour, 'manpower':25}, [_build(1557,'ic',3)], buildings=((1557,'ic',3),)),
                Choice('Register and train a larger national reserve',
                       'Add 40 manpower to the pool after training, with 1 dissent from the unpopular reserve levy. There are no completed divisions or new daily recruits.',
                       labour, [cmd('manpowerpool',value=40),cmd('dissent',value=1)]),
            )),
        Programme('prewar_deck_commission', 'The carrier safety commission',
            'Crowded flight decks expose a choice between trained crews and heavier protection. Instructors can improve '
            'recovery between missions, while protected decks reduce vulnerability at the cost of speed. Both require '
            'fuel-consuming trials rather than a new production discount.',
            1934, 'june', 240, (
                Choice('Build an experienced deck and aircrew school',
                       'Fleet and light carrier air groups gain 8 morale and 5 maximum organisation. They still need researched aircraft, fuel and normal replacements.',
                       flight, [cmd(kind,which=u,value=value) for u in ('cag','light_cag')
                                for kind,value in (('morale',8),('max_organization',5))], context=_vital(1554)),
                Choice('Adopt protected flight decks and stricter damage control',
                       'Fleet and light carriers reduce sea-defence vulnerability by 4 (lower is better), but lose 1 speed. The slower fleet must be planned around its slowest ship.',
                       flight, [cmd(kind,which=u,value=value) for u in ('carrier','light_carrier')
                                for kind,value in (('naval_defense',-4),('speed',-1))], context=_vital(1554)),
            ), art='naval'),
        Programme('prewar_navigation_trials', 'Navigation trials or a coastal warning belt?',
            'The same communications and precision-instrument budget can support long ocean searches or fixed defence '
            'of the industrial coast. One reaches beyond the home islands; the other stays with the cities it protects.',
            1935, 'february', 180, (
                Choice('Train maritime navigation and search crews',
                       'Naval bombers gain 300 km range and 2 surface detection. No aircraft, naval attack or instant research is awarded.',
                       radio, [cmd('range',which='naval_bomber',value=300),cmd('surface_detection',which='naval_bomber',value=2)], context=_vital(1552)),
                Choice('Build the Tokyo and Hiroshima AA warning belt',
                       'Add 2 AA levels at Tokyo (1552) and 2 at Hiroshima (1554). These fixed facilities cannot accompany the fleet.',
                       radio, [_build(p,'flak',2) for p in (1552,1554)], buildings=((1552,'flak',2),(1554,'flak',2))),
            ), art='air'),
        Programme('prewar_landing_trials', 'The joint landing experiment',
            'A landing can fail because too many divisions crowd its control net, or because the troops cannot break '
            'out of the beachhead. Trial landings and Army-Navy signals exercises must settle one priority. This is '
            'preparation with ordinary Marine divisions; it opens no experimental unit class.',
            1936, 'may', 180, (
                Choice('Coordinate a larger first assault wave',
                       'Raise the maximum amphibious assault size before the severe stacking penalty by 1 formation; standard Marines also gain 5 maximum organisation. Ordinary doctrine and landing rules remain.',
                       landing, [cmd('max_amphib_mod',value=1,when=1),cmd('max_organization',which='marine',value=5)], context=_vital(1554)),
                Choice('Train the Marines to break out under fire',
                       'Standard Marines gain 12 percentage points of shore attack and 8 of river attack. The assault-size limit stays unchanged; this does not cancel every landing penalty.',
                       landing, [cmd('shore_attack',which='marine',value=12),cmd('river_attack',which='marine',value=8)], context=_vital(1554)),
            ), art='army'),
        Programme('prewar_medical_service', 'Build a medical service or certify the next reserve?',
            'The Army can spend this medical budget on the treatment chain that returns wounded men to service, or '
            'on examinations and training that certify a finite pool of additional recruits. In peace these are '
            'fitness and reserve preparations; an existing China war does not dictate the choice.',
            1938, 'march', 180, (
                Choice('Create the evacuation and rehabilitation service',
                       'Add 25 percentage points to the national trickle-back efficiency modifier. At the unmodified 0.15 casualty-return factor this adds 3.75 percentage points to casualty recovery; it is not 25 percent of every loss and creates no instant manpower.',
                       medicine, [cmd('trickleback_mod',value=25)], context=_vital(1552)),
                Choice('Certify and train the next reserve intake',
                       'Release 50 manpower once after medical examinations and reserve training. The levy adds 1 dissent. No permanent recruitment rate or formation is granted.',
                       medicine, [cmd('manpowerpool',value=50),cmd('dissent',value=1)], context=_vital(1552)),
            ), art='army'),
        Programme('prewar_factory_dispersion', 'Disperse the next factory investment?',
            'Managers want maximum output from the capital, while civil-defence planners want a smaller protected '
            'complex farther north. This allocates new factory investment: existing factories are not moved or removed. '
            'More factories still require energy, metal, rares and workers in the ordinary economy.',
            1940, 'january', 270, (
                Choice('Build a smaller protected complex at Sendai',
                       'Add 2 physical IC and 4 AA levels at Sendai (1549). It has fewer new factories than the concentrated alternative, with an immediate fixed air-defence investment.',
                       industry, [_build(1549,'ic',2),_build(1549,'flak',4)], buildings=((1549,'ic',2),(1549,'flak',4))),
                Choice('Concentrate the new workshops in Tokyo',
                       'Add 4 physical IC at Tokyo (1552), with no additional AA. This produces more capacity and consumes more industrial feedstock; normal air defence remains your responsibility.',
                       industry, [_build(1552,'ic',4)], buildings=((1552,'ic',4),)),
            )),
    )


def append_events():
    if REPORT:
        return REPORT
    prior = {e.key:e.id for e in EVENTS}
    if 'prewar_rural_works' in prior:
        raise RuntimeError('Prewar content already exists without its application receipt')
    rows = []
    for spec in programmes():
        prewar = ('NOT = { flag = JX_PACIFIC '+war('USA')+' '+war('ENG')+' }')
        # Dates are repeated in action eligibility so a stale/direct action
        # cannot fund a later programme ahead of its advertised opening.
        date = f'year = {spec.year} OR = {{ year = {spec.year+1} month = {spec.month} }}'
        unopened = (f'NOT = {{ flag = JX_{spec.key}_DONE flag = JX_{spec.key}_PENDING '
                    f'flag = JX_{spec.key}_DISMISSED flag = JX_{spec.key}_CANCELLED }}')
        available = active()+' '+date+' '+prewar+' '+unopened
        labels = []
        for i, choice in enumerate(spec.choices):
            costs = ', '.join(f'{v:,} {k}' for k,v in choice.costs.items())
            labels.append(f'{choice.label}: pay {costs} now. After {spec.days} days: {choice.result}')
        desc = spec.story+'\n\n'+'\n\n'.join(labels)
        desc += ('\n\nChoose and pay once in this manual decision. One completion notice arrives when the work is due; '
                 'there are no quarterly reminders or recurring payments. Leave the proposal available or dismiss it '
                 'permanently. New funding closes when the Pacific war starts or Japan fights America or Britain; '
                 'work already funded may finish during war. If the selected site, technology or capacity check '
                 'fails at completion, recover the exact paid inputs once and close the programme. No alternative '
                 'reward is substituted. Construction still requires the normal engine supply conditions at the named home city.')
        source = event(spec.key,spec.title,desc,decision=True,persistent=True,year=spec.year,
                       gate=available,actions=[],module=MODULE,art=spec.art,
                       purpose='One optional pre-Pacific programme; two exclusive funded outcomes, no automatic war or reminder.')
        source.start_month = spec.month
        source.manual_only = True
        for i, choice in enumerate(spec.choices):
            selected = spec.key+f'_SELECTED_{i}'
            inputs = ' '.join(f'{k} = {v}' for k,v in choice.costs.items())
            validity = _eligibility(choice)
            payment = [cmd(POOL_COMMANDS[k],value=-v) for k,v in choice.costs.items()]
            refund = [cmd(POOL_COMMANDS[k],value=v) for k,v in choice.costs.items()]
            target = spec.key+f'_finish_{i}'
            source.actions.append(Action(choice.label,payment+[flag(spec.key+'_PENDING'),flag(selected),later(target,spec.days)],
                                         gate=available+' '+inputs+' '+validity,chance=100 if i == 0 else 0))
            live = (f'flag = JX_{spec.key}_PENDING flag = JX_{selected} '
                    f'NOT = {{ flag = JX_{spec.key}_DONE flag = JX_{spec.key}_CANCELLED }} '
                    f'event = {{ id = @{spec.key} days = {spec.days} }}')
            close = [clear(spec.key+'_PENDING'),clear(selected)]
            finish = event(target,spec.title+' - work completed',
                'The funded work is due. '+choice.result+' The payment was made at the start. '
                'If the selected outcome is no longer eligible, the exact original payment is returned instead. '
                'This programme then closes; it cannot repeatedly supply refunds or rewards.',
                triggered=True,actions=[
                    Action('Put the selected work into service',choice.rewards+[flag(spec.key+'_DONE')]+close,
                           gate=live+' '+validity,chance=100),
                    Action('The work cannot finish; recover the original investment',refund+[flag(spec.key+'_CANCELLED')]+close,
                           gate=live+' '+_not(validity)),
                    Action('',[],gate=_not(live)),
                ],module=MODULE,art=spec.art,
                purpose='Selected-branch receipt, elapsed-time gate and exact refund; stale or early dispatch is inert.')
            rows.append({'programme':spec.key,'choice':i,'source_id':source.id,'finish_id':finish.id,
                         'year':spec.year,'month':spec.month,'days':spec.days,'costs':dict(choice.costs),
                         'buildings':choice.buildings,'eligibility':validity,'rewards':list(choice.rewards)})
        source.actions += [Action('Leave this proposal available',[],gate=available),
                           Action('Dismiss this proposal permanently',[flag(spec.key+'_DISMISSED')],gate=available)]
    assert prior == {e.key:e.id for e in EVENTS if e.key in prior}
    REPORT.update(programmes=6, decisions=6, receivers=12, rows=rows,
                  documented_command_types=sorted(DOCUMENTED_NEW_COMMANDS), preserved_ids=len(prior))
    return REPORT

"""Finite 1945-50 political settlements. Applied before final integrity passes.

Existing recovery and Chinese/Indian autonomy IDs are retained. No save migration,
automatic alliance changes, percentage bonuses, or repeating grants are added.
"""
from catalog import EVENTS, Action, event, cmd, flag, clear, later, fire, active, owned, control, puppet
from unique_unit_events import transaction_commands

REPORT = {}


def not_(gate):
    return 'NOT = { AND = { ' + gate + ' } }'


def timed(key, days):
    return f'event = {{ id = @{key} days = {days} }}'


def funds(cost):
    return ' '.join(f'{kind} = {value}' for kind, value in cost.items())


def resources(cost, sign):
    aliases = {'manpower': 'manpowerpool', 'oil': 'oilpool', 'metal': 'metalpool',
               'rare_materials': 'rarematerialspool'}
    return [cmd(aliases.get(kind, kind), value=value * sign) for kind, value in cost.items()]


def guarded(commands, gate):
    return transaction_commands(commands, gate)


def infrastructure(province):
    def level(value):
        return f'building = {{ province = {province} type = infrastructure value = {value} when = now }}'
    return ('OR = { AND = { NOT = { '+level(2)+' } '+level(.31)+
            ' } AND = { '+level(2)+' '+level(31)+' } }')


def site(province, amount=4):
    return (owned(province) + ' ' + control(province) +
            ' technology = 5800 '+infrastructure(province)+
            f' NOT = {{ building = {{ province = {province} type = ic value = {201-amount} when = now }} }}')


def _choice(name, root_gate, mode, commands, extra='', chance=0):
    """Commit once before spending; cached action replay cannot pay or reward twice."""
    gate = (root_gate + ' ' + extra).strip()
    execution = mode + '_EXECUTING'
    pending = 'flag = JX_' + execution
    return Action(name, guarded([flag(execution)], gate) +
                  guarded(commands + [flag(mode), clear(execution)], pending),
                  gate=gate, chance=chance)


def paid_branch(root, suffix, title, text, cost, days, live, rewards, *, year=1945, art='industry'):
    """One paid choice -> dated completion/refund, each command protected.

    Resource requirements apply to the commit, not to later individual debits.
    The receipt flag is set last, so every command sees the same transaction.
    """
    key = 'r14_' + root.key + '_' + suffix
    mode = key.upper() + '_PENDING'
    end = key.upper() + '_CLOSED'
    root_gate = root.gate + ' ' + root.ready
    start = _choice(title, root_gate, mode,
                    resources(cost, -1) + [flag('R14_' + root.key.removeprefix('r14_').upper() + '_CHOSEN'), later(key, days)],
                    funds(cost)+' '+live)
    pending = f'flag = JX_{mode} NOT = {{ flag = JX_{end} }}'
    elapsed = timed(root.key, days)
    valid = pending + ' ' + elapsed + ' ' + live
    invalid = pending + ' ' + elapsed + ' ' + not_(live)
    event(key, title, text, triggered=True, year=year, art=art, module='postwar', actions=[
        Action('Put the agreement into effect', guarded(rewards + [flag(end)], valid), gate=valid, chance=100),
        Action('Cancel the work and return the full investment',
               guarded(resources(cost, 1) + [flag(end)], invalid), gate=invalid, chance=100),
        Action('', [], gate=not_(pending + ' ' + elapsed), chance=100)])
    return start


def home(by):
    root = by['civil_recovery']
    root.title = 'Japan after the long war'
    root.desc = ('Peace leaves a choice between civilian reconstruction and another generation of soldiers. '
                 'Civilian work ties up 60 manpower for a year, costs 400 money and 2,500 supplies, '
                 'then returns the workers and adds six factories in Tokyo. War cancels the work and returns the investment.\n\n'
                 'Keeping the training camps open costs 400 money, 5,000 supplies and 2,000 oil. '
                 'After six months it adds 80 trained manpower, 3,000 supplies and 1,000 oil. '
                 'Training can finish during a new war if Tokyo remains Japanese. Choose once.')
    root.gate = active() + ' atwar = no NOT = { flag = JX_R14_CIVIL_RECOVERY_CHOSEN flag = JX_R14_CIVIL_RECOVERY_DECLINED }'
    root.ready = 'year = 1945'
    root.year = 1945
    root.actions = [
        paid_branch(root, 'civilian', 'Rebuild civilian Japan',
                    'Tokyo receives six factories and the 60 workers return to the manpower pool. '
                    'Renewed war, occupation or unsuitable factory land cancels the project with a full refund.',
                    {'money':400, 'supplies':2500, 'manpower':60}, 360,
                    active() + ' atwar = no NOT = { flag = JX_R14_HOME_WORK_BROKEN } ' + site(1552,6),
                    [cmd('construct', which='ic', where=1552, value=6), cmd('manpowerpool', value=60), cmd('dissent', value=-3)]),
        paid_branch(root, 'reserves', 'Keep the training camps open',
                    'The final wartime classes enter the trained reserve: 80 manpower, 3,000 supplies and 1,000 oil. '
                    'No divisions are created. Occupation of Tokyo cancels the work with a full refund.',
                    {'money':400, 'supplies':5000, 'oil':2000}, 180,
                    active() + ' ' + owned(1552) + ' ' + control(1552),
                    [cmd('manpowerpool', value=80), cmd('supplies', value=3000), cmd('oilpool', value=1000)])]
    root.actions += [_choice('End these plans; retain the present economy', root.gate, 'R14_CIVIL_RECOVERY_DECLINED', [], chance=100)]
    broken = ('flag = JX_R14_CIVIL_RECOVERY_CIVILIAN_PENDING '
              'NOT = { flag = JX_R14_CIVIL_RECOVERY_CIVILIAN_CLOSED flag = JX_R14_HOME_WORK_BROKEN } atwar = yes')
    event('r14_home_work_interrupted','Civilian reconstruction is interrupted','',gate=broken,
          persistent=True,offset=1,year=1945,module='postwar',actions=[Action('',guarded([flag('R14_HOME_WORK_BROKEN')],broken),chance=100)])


def partners(by):
    for key, tag, name, capital in [('china_autonomy','U87','China',1337), ('india_autonomy','IND','India',1459)]:
        root = by[key]
        chosen = 'R14_' + key.upper() + '_CHOSEN'
        root.title = name + ': the postwar agreement'
        root.desc = (f'{name} asks what follows the war. Sovereignty ends Japanese puppet status while retaining the existing alliance. '
                     'Civilian aid costs 250 money and 3,000 supplies; after a year it builds four local factories. '
                     'The same aid can be given while keeping the present puppet agreement.\n\n'
                     'A standing-army agreement instead costs 250 money and 5,000 supplies. After six months the partner '
                     'receives 80 manpower and 5,000 supplies for its own forces. All three agreements retain Japanese '
                     'military access; they transfer no land and create no new wars. Civilian aid requires both countries at peace.')
        root.gate = (active() + ' year = 1947 exists = ' + tag + ' ' + puppet(tag) +
                     f' NOT = {{ flag = JX_{chosen} flag = JX_{key}_DONE }}')
        root.ready = ''
        root.year = 1947
        root.actions = []
        for mode, label, sovereign, military in [
            ('sovereign','Grant sovereignty and civilian aid',True,False),
            ('civilian','Keep the present treaty; fund civilian recovery',False,False),
            ('military','Keep the present treaty; support its standing army',False,True)]:
            cost = {'money':250,'supplies':5000 if military else 3000}
            receipt = 'R14_' + key.upper() + '_' + mode.upper()
            confirm = 'r14_' + key + '_' + mode
            gate = root.gate + ' ' + funds(cost)
            if not military:
                gate += (f' atwar = no NOT = {{ atwar = {tag} war = {{ country = {tag} country = JAP }} }}'
                         f' owned = {{ province = {capital} data = {tag} }} control = {{ province = {capital} data = {tag} }}'
                         f' technology = {{ country = {tag} value = 5800 }} '+infrastructure(capital)+
                         f' NOT = {{ building = {{ province = {capital} type = ic value = 197 when = now }} }}')
            commands = resources(cost,-1) + [flag(chosen), flag(key+'_DONE'), flag(receipt)]
            if sovereign:
                commands += [cmd('end_mastery',which=tag)]
            commands += [later(confirm,1,tag), later(confirm+'_check',2)]
            root.actions.append(_choice(label,gate,receipt+'_PENDING',commands,chance=100 if mode=='civilian' else 0))
            relation = (f'NOT = {{ ispuppet = {tag} }}' if sovereign else puppet(tag))
            pending = f'flag = JX_{receipt} NOT = {{ flag = JX_{receipt}_DELIVERED }}'
            safe = f'exists = JAP NOT = {{ war = {{ country = {tag} country = JAP }} }} ' + relation
            # Confirmation is the partner's explicit consent to access. No ownership changes.
            confirmation_safe = safe+(f' atwar = no NOT = {{ atwar = JAP }}' if not military else '')
            valid = pending+' '+confirmation_safe+' '+timed(key,1)
            finish = confirm+'_finish'
            refund = confirm+'_refund'
            invalid_confirm = pending+' '+timed(key,1)+' '+not_(confirmation_safe)
            event(confirm, name + ' signs its new agreement',
                  ('The government renews Japanese military access and begins a six-month reserve-training programme. '
                   'Japan has paid 250 money and 5,000 supplies. Trained reserves and their equipment go to this country, not Japan.' if military else
                   'The government renews Japanese military access and begins a year of civilian factory construction. '
                   'Japan has paid 250 money and 3,000 supplies. Four factories are planned in the capital.'),
                  country=tag,triggered=True,year=1947,art='diplomacy',module='postwar',actions=[
                      Action('Sign the access and reconstruction agreement',
                             guarded([cmd('access',which='JAP'),flag(receipt+'_ACCEPTED'),later(finish,180 if military else 360,tag),flag(receipt+'_DELIVERED')],valid),
                             gate=valid,chance=100),
                      Action('Return the unused investment',guarded([flag(receipt+'_REFUND_DUE'),fire(refund),flag(receipt+'_DELIVERED')],invalid_confirm),gate=invalid_confirm,chance=100),
                      Action('',[],gate=not_(pending+' '+timed(key,1)),chance=100)])
            done = f'flag = JX_{receipt}_ACCEPTED NOT = {{ flag = JX_{receipt}_FINISHED }}'
            live = safe
            if not military:
                live += (f' atwar = no NOT = {{ atwar = JAP flag = JX_{receipt}_WAR_BROKEN }} owned = {{ province = {capital} data = {tag} }} control = {{ province = {capital} data = {tag} }} technology = 5800 '+infrastructure(capital)+
                         f' NOT = {{ building = {{ province = {capital} type = ic value = 197 when = now }} }}')
            due = done+' '+timed(confirm,180 if military else 360)
            benefit = ([cmd('manpowerpool',value=80),cmd('supplies',value=5000)] if military else
                       [cmd('construct',which='ic',where=capital,value=4),cmd('supplies',value=3000)])
            event(finish,name + (': trained reserves enter service' if military else ': civilian factories reopen'),
                  ('The paid programme adds 80 manpower and 5,000 supplies to this country.' if military else
                   'The paid programme adds four factories and 3,000 supplies to this country. War or loss of the capital cancels factory work; Japan receives its full original investment back.'),
                  country=tag,triggered=True,year=1947,art='army' if military else 'industry',module='postwar',actions=[
                      Action('Complete the agreement',guarded(benefit+[flag(receipt+'_FINISHED')],due+' '+live),gate=due+' '+live,chance=100),
                      Action('Return the unused Japanese investment',guarded([flag(receipt+'_REFUND_DUE'),fire(refund),flag(receipt+'_FINISHED')],due+' '+not_(live)),gate=due+' '+not_(live),chance=100),
                      Action('',[],gate=not_(due),chance=100)])
            refund_gate = f'flag = JX_{receipt}_REFUND_DUE NOT = {{ flag = JX_{receipt}_REFUNDED }}'
            event(refund,'Unused reconstruction funds return',
                  name+' could not complete the agreed programme. The original money and supplies return to Japan. Its political status is unchanged.',
                  triggered=True,year=1947,art='diplomacy',module='postwar',actions=[
                      Action('Recover the investment',guarded(resources(cost,1)+[flag(receipt+'_REFUNDED')],refund_gate),gate=refund_gate,chance=100),
                      Action('',[],gate=not_(refund_gate),chance=100)])
            unreceived = pending+' '+timed(key,2)
            event(confirm+'_check','The reconstruction agreement is confirmed','',
                  triggered=True,year=1947,art='diplomacy',module='postwar',actions=[
                      Action('',guarded([flag(receipt+'_REFUND_DUE'),fire(refund),flag(receipt+'_DELIVERED')],unreceived),gate=unreceived,chance=100),
                      Action('',[],gate=not_(unreceived),chance=100)])
            # A receiver queued in a country that has been annexed cannot run.
            # Japan owns this last-resort receipt, so its investment is not lost
            # with the recipient's government. It closes the foreign completion
            # too, preventing a later re-created country from collecting twice.
            missing = (done+' '+timed(confirm,180 if military else 360)+
                       f' NOT = {{ exists = {tag} }}')
            event(confirm+'_government_lost',name+' cannot complete its agreement',
                  name+' no longer exists. Its paid programme is cancelled and the full original Japanese investment is returned.',
                  gate=missing,persistent=True,offset=1,year=1947,art='diplomacy',module='postwar',actions=[
                      Action('Recover the unused investment',guarded([flag(receipt+'_REFUND_DUE'),fire(refund),flag(receipt+'_FINISHED')],missing),gate=missing,chance=100)])
            if not military:
                interrupted = (f'flag = JX_{receipt}_ACCEPTED OR = {{ atwar = yes atwar = JAP }} '
                               f'NOT = {{ flag = JX_{receipt}_FINISHED flag = JX_{receipt}_WAR_BROKEN }}')
                event(confirm+'_interrupted','Civilian reconstruction is interrupted','',country=tag,
                      gate=interrupted,persistent=True,offset=1,year=1947,module='postwar',actions=[
                          Action('',guarded([flag(receipt+'_WAR_BROKEN')],interrupted),chance=100)])
        root.actions.append(_choice('Keep the present relationship without a new grant',root.gate,chosen,[flag(key+'_DONE')],chance=0))
        # Old direct receivers are no longer scheduled by these replaced windows.
        # They remain at their original IDs for compatibility; deny unfunded replay.
        for suffix in ('access','grant'):
            old = by[key+'_'+suffix]
            old.actions = [Action('',[],chance=100)]
            old.desc = 'The earlier agreement has been replaced by a paid postwar settlement.'


def america(by):
    base = (active() + ' year = 1945 flag = JX_US_PEACE exists = USA '+
            'NOT = { war = { country = JAP country = USA } } '+timed('us_signed',360)+
            ' NOT = { flag = JX_R14_AMERICAN_FUTURE_CHOSEN flag = JX_R14_AMERICAN_FUTURE_DECLINED }')
    root = event('r14_american_future','America across the Pacific',
                 'A year after the armistice, its terms still shape the peace. Returning Hawaii opens a commercial settlement: '
                 '600 money and 3,000 supplies buy a single delivery of 12,000 oil, 12,000 metal and 6,000 rares after six months. '
                 'These are finite purchases, not daily income.\n\n'
                 'Keeping Hawaii closes that offer. Instead, 400 money, 5,000 supplies and 3,000 oil can strengthen Pearl Harbor: '
                 'three coastal fort levels, three anti-aircraft levels and 3,000 supplies after six months. '
                 'America answers by funding its own Pacific escort force. Neither choice creates a war.',
                 decision=True,gate=base,year=1945,art='diplomacy',module='postwar')
    root.ready=''
    live = active()+' flag = JX_US_PEACE exists = USA NOT = { war = { country = JAP country = USA } flag = JX_R14_ARMISTICE_BROKEN }'
    commerce = paid_branch(root,'commerce','Reopen American commerce',
                          'The six-month purchase delivers 12,000 oil, 12,000 metal and 6,000 rares. Renewed war cancels it with a full refund.',
                          {'money':600,'supplies':3000},180,live+' flag = JX_US_RETURN_HAWAII',
                          resources({'oil':12000,'metal':12000,'rare_materials':6000},1)+[later('r14_us_export_receipt',1,'USA')],art='diplomacy')
    commerce.gate += ' flag = JX_US_RETURN_HAWAII'
    # Both the action and every commit command must enforce the selected treaty.
    commerce.commands = guarded(commerce.commands,'flag = JX_US_RETURN_HAWAII')
    hawaii = (live+' flag = JX_US_KEEP_HAWAII technology = 2800 '+owned(1734)+' '+control(1734)+
              ' NOT = { building = { province = 1734 type = coastal_fort value = 8 when = now } building = { province = 1734 type = flak value = 8 when = now } }')
    retention = paid_branch(root,'hawaii','Strengthen Pearl Harbor',
                           'Hawaii receives three coastal fort levels, three anti-aircraft levels and 3,000 supplies. '
                           'A new American war or loss of the island cancels the work with a full refund.',
                           {'money':400,'supplies':5000,'oil':3000},180,hawaii,
                           [cmd('construct',which='coastal_fort',where=1734,value=3),cmd('construct',which='flak',where=1734,value=3),cmd('supplies',value=3000),later('r14_us_pacific_rebuild',1,'USA')],art='naval')
    retention.gate += ' flag = JX_US_KEEP_HAWAII'
    retention.commands = guarded(retention.commands,'flag = JX_US_KEEP_HAWAII')
    root.actions = [commerce,retention,_choice('Let the armistice stand without a new agreement',base,'R14_AMERICAN_FUTURE_DECLINED',[],chance=100)]
    broken = ('flag = JX_US_PEACE war = { country = JAP country = USA } '
              'NOT = { flag = JX_R14_ARMISTICE_BROKEN }')
    event('r14_armistice_broken','The Pacific armistice is broken','',gate=broken,
          persistent=True,offset=1,year=1943,module='postwar',actions=[
              Action('',guarded([flag('R14_ARMISTICE_BROKEN')],broken),chance=100)])
    root.gate += ' NOT = { flag = JX_R14_ARMISTICE_BROKEN }'
    for action in root.actions:
        action.gate += ' NOT = { flag = JX_R14_ARMISTICE_BROKEN }'
        action.commands = guarded(action.commands,'NOT = { flag = JX_R14_ARMISTICE_BROKEN }')
    # Receipts are one-time, do not change diplomacy or take any foreign land.
    for key,title,gate,commands,desc in [
        ('r14_us_export_receipt','Japanese commerce resumes',
         'flag = JX_R14_R14_AMERICAN_FUTURE_COMMERCE_CLOSED flag = JX_US_RETURN_HAWAII',
         [cmd('money',value=600),cmd('supplies',value=3000)],
         'Japan has received a finite paid shipment of oil, metal and rares. American exporters receive the 600 money and 3,000 supplies paid under the agreement.'),
        ('r14_us_pacific_rebuild','The Pacific Fleet returns to its bases',
         'flag = JX_R14_R14_AMERICAN_FUTURE_HAWAII_CLOSED flag = JX_US_KEEP_HAWAII money = 400 supplies = 5000',
         [cmd('money',value=-400),cmd('supplies',value=-5000),cmd('transport_pool',value=120),cmd('escort_pool',value=80)],
         'Japanese fortification of Hawaii prompts a funded American response. Spend 400 money and 5,000 supplies to add 120 convoy transports and 80 convoy escorts. These are convoy pools, not warship flotillas.')]:
        receipt = 'R14_'+key.upper()+'_DONE'
        valid = gate+' NOT = { war = { country = JAP country = USA } flag = JX_'+receipt+' }'
        # The budget check protects only initial commitment; costs cannot
        # invalidate the rest of an already accepted transaction.
        mode = receipt+'_PENDING'
        event(key,title,desc,country='USA',triggered=True,year=1945,art='naval',module='postwar',actions=[
            _choice('Approve the agreement',valid,mode,commands+[flag(receipt)],chance=100),
            Action('Make no further commitment',[],gate=not_(valid),chance=100)])


def apply():
    if REPORT:
        return REPORT
    before = {e.key:e.id for e in EVENTS}
    by = {e.key:e for e in EVENTS}
    home(by)
    partners(by)
    america(by)
    # The old construction pass recorded awards before these offers/receivers
    # were replaced. Its metadata must describe the live catalogue, not expose
    # an obsolete receipt through effective_award(). Keep orphan IDs registered.
    import construction_safety
    replaced = ('civil_recovery','china_autonomy','india_autonomy')
    stale = [row for row in construction_safety.REPORT if row['event'].startswith(replaced)]
    construction_safety.REPORT[:] = [row for row in construction_safety.REPORT if row not in stale]
    assert all(next(e.id for e in EVENTS if e.key==key)==eid for key,eid in before.items())
    REPORT.update(applied=True,modified=['civil_recovery','china_autonomy','india_autonomy'],
                  added=[e.key for e in EVENTS if e.key not in before],original_ids_preserved=True,
                  obsolete_construction_metadata_removed=[row['event'] for row in stale])
    return REPORT

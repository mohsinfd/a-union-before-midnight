"""B1: finite island detachments, Chinese integration, Italian recovery.

Append after all existing catalog extensions. Never renumber saved event IDs.
"""
import json
from pathlib import Path
from catalog import EVENTS, Action, event, cmd, cond, flag, later, active, puppet, control, owned

HERE = Path(__file__).resolve().parent
ISLANDS = [(1362,'Taipei'),(1562,'Amami'),(1564,'Northern Okinawa'),
 (1661,'Iwo Jima'),(1662,'Chichi Jima'),(1663,'Motoyama'),(1665,'Ponape'),
 (1666,'Kusaie'),(1667,'Truk'),(1668,'Woleai'),(1669,'Yap'),(1670,'Peleliu'),
 (1672,'Minami Torishima'),(1674,'Bikini'),(1675,'Eniwetok'),(1676,'Kwajalein'),
 (1677,'Majuro'),(1681,'Wotje'),(1684,'Rota'),(1685,'Saipan'),(1686,'Pagan')]
BASE_GAPS = [(1338,'Shanghai'),(1361,'Gaoxiong'),(1563,'Southern Okinawa'),
 (1554,'Hiroshima'),(1559,'Matsuyama'),(1542,'Toyohara'),(1543,'Shana'),
 (1219,'Port Arthur'),(1232,'Busan'),(1365,'Haikou')]
ISLAND_TYPE = 28632
CHINA_TYPE = 28631
CHINA_ROSTER = [('infantry',9)]*26+[('hq',2)]*4+[('cavalry',2)]*2
CHINA_ROSTER += ([('infantry',9)]*23+[('militia',4)]*9)*2
APPLIED = False

def apply():
    global APPLIED
    if APPLIED:return
    APPLIED=True
    by={e.key:e for e in EVENTS}
    by['china'].gate += ' OR = { NOT = { exists = CHI } lost_VP = { country = CHI value = 65 } }'
    by['china'].desc += '\n\nPuppet terms also require 65 percent of Chinese victory points lost. An inherited army of 96 or more formations is reorganised into 96: 32 mobile now, 32 after one year and 32 after two years. A smaller army receives no free expansion. Locked formations remain local defenders.'
    by['base_guard'].year=1939
    by['base_guard'].gate=by['base_guard'].gate.replace('flag = JX_PACIFIC','')
    # A supply purchase is not construction at Nanjing. The railroad alternative
    # still requires a friendly settled successor, rather than arbitrary control.
    for i in (0,1):
        e=by['procurement1937_finish_'+str(i)]
        friendly='OR = { '+control(1337)+' AND = { '+puppet('U87')+' '+control(1337,'U87')+' } }'
        for a in e.actions:
            a.gate=a.gate.replace(control(1337),friendly)

    # Defined identities make documented lock/unlock commands deterministic.
    # Scenario templates are dormant CHI units, transferred by the CHI->U87
    # settlement; they have no location and are not deployed units to remove.
    templates=' '.join(f'division_exists = {{ type = {CHINA_TYPE} id = {i} }}' for i in range(1,97))
    cn_gate='flag = JX_china_SETTLED '+puppet('U87')+' atwar = no army = { country = U87 size = 96 when = 0 where = 1 } NOT = { flag = JX_CN_REORG flag = JX_CN_LEGACY } '+templates
    commands=[cmd('remove_units',which='land',where=-1,when=3,value='"'+c+'"') for c in ('Asia','Europe','Africa','Oceania','North America','South America')]
    # Templates stay in the force pool until their explicitly controlled city
    # is available; the actor's capital fallback is not guessed.
    for start in range(1,97,8):
        commands.append(cmd('add_corps',which='"Chinese Home Army '+str((start-1)//8+1)+'"',value='land',where=1337))
        commands += [cmd('activate_division',which=CHINA_TYPE,value=i,where=1337,when=0) for i in range(start,start+8)]
    commands += [cmd('unlock_division',which=CHINA_TYPE,value=i) for i in range(1,33)]
    commands += [flag('CN_REORG'),cmd('ai',which='"jx/china_home_b1.ai"')]
    commands += [later('cn_release_1',360,'U87'),later('cn_release_2',720,'U87'),later('cn_notice',1)]
    event('cn_reorganise','China rebuilds its national army','',country='U87',year=1937,
          gate=cn_gate+' '+control(1337,'U87'),actions=[Action('',commands,chance=100)],offset=3,module='campaign_balance',art='army')
    for stage,lo,hi in ((1,33,65),(2,65,97)):
        gate=puppet('U87')+f' flag = JX_CN_REORG NOT = {{ flag = JX_CN_RELEASE_{stage} flag = JX_CN_LEGACY }}'
        event('cn_release_'+str(stage),'Chinese formations finish integration','',country='U87',triggered=True,
          actions=[Action('',[cmd('unlock_division',which=CHINA_TYPE,value=i) for i in range(lo,hi)]+[flag('CN_RELEASE_'+str(stage)),later('cn_notice_'+str(stage),1)],gate=gate,chance=100),
                   Action('',[],gate='NOT = { AND = { '+gate+' } }')],module='campaign_balance',art='army')
    for key,title,desc in [('cn_notice','China: 32 formations ready for field service','China has 96 formations. Thirty-two may move now. The other 64 defend their current positions: 32 unlock after one year and the final 32 after two years. Mobilisation can reinforce them, but does not remove the movement locks.'),
       ('cn_notice_1','China: 32 more formations ready','The second group has completed integration. Sixty-four of the original 96 formations may now move. The final group unlocks after the second year.'),
       ('cn_notice_2','China: army integration complete','All surviving formations in the original 96-formation settlement army may now move. No replacement divisions are created.')]:
        event(key,title,desc,triggered=True,actions=[Action('Understood',[],chance=100)],module='campaign_balance',art='army')

    legacy=json.loads((HERE/'china_legacy_b1.json').read_text()) if (HERE/'china_legacy_b1.json').exists() else {'stages':[[],[]]}
    for stage,ids in enumerate(legacy['stages'],1):
        gate=puppet('U87')+f' flag = JX_CN_LEGACY NOT = {{ flag = JX_CN_RELEASE_{stage} }}'
        event('cn_legacy_release_'+str(stage),'Chinese formations finish integration','',country='U87',triggered=True,
          actions=[Action('',[cmd('unlock_division',which=t,value=i) for t,i in ids]+[flag('CN_RELEASE_'+str(stage)),later('cn_notice_'+str(stage),1)],
                    gate=gate,chance=100),Action('',[],gate='NOT = { AND = { '+gate+' } }')],module='campaign_balance',art='army')
    # An independent China must not inherit permanent Japanese movement locks.
    unlock=[cmd('unlock_division',which=CHINA_TYPE,value=i) for i in range(1,97)]
    unlock += [cond('flag = JX_CN_LEGACY',cmd('unlock_division',which=t,value=i)) for ids in legacy['stages'] for t,i in ids]
    event('cn_independent_b1','China resumes full control of its army','',country='U87',year=1937,
      gate='flag = JX_CN_REORG NOT = { '+puppet('U87')+' flag = JX_CN_INDEPENDENT }',
      actions=[Action('',unlock+[flag('CN_INDEPENDENT'),flag('CN_RELEASE_1'),flag('CN_RELEASE_2')],chance=100)],module='campaign_balance',art='army')

    def named_garrison_commands(entries, first_id):
        out=[]
        for i,(p,name) in enumerate(entries,first_id):
            division_name=name+' Defence Detachment'
            # Give the one-division corps the same clear label as its division.
            # Leader ID 0 is the intended no-commander value; verify in-game.
            out.append(cmd('add_corps',which='"'+division_name+'"',value='land',where=p,when=0))
            out.append(cmd('activate_division',which=ISLAND_TYPE,value=i,where=p,when=0))
        return out
    guards=named_garrison_commands(ISLANDS,1)
    # Only available when all deployment sites are Japanese-controlled. No
    # payment for enemy-held islands and no spawn behind enemy lines.
    island_gate=active()+' NOT = { flag = JX_ISLAND_CALLUP } '+' '.join(control(p) for p,n in ISLANDS)
    island_gate += ' '+' '.join(f'division_exists = {{ type = {ISLAND_TYPE} id = {i} }}' for i in range(1,len(ISLANDS)+1))
    event('island_callup','Call up the island defence detachments',
      'Put 21 small, static detachments on Taiwan, Okinawa, Amami and the Japanese Pacific islands. Each is capped at 25 percent of a full garrison division and has no artillery brigade. Mobilisation cannot expand it beyond that cap.\n\nThe call-up costs 53 manpower, 900 supplies and 60 money, once. These local defenders can resist an empty-base raid; they cannot replace a fleet or stop a supported invasion.',
      decision=True,year=1939,gate=island_gate,ready='manpower = 53 supplies = 900 money = 60',
      actions=[Action('Call up the local defenders',[cmd('trigger',which='@island_muster_b1')],chance=100)],module='campaign_balance',art='pacific')
    event('island_muster_b1','Island defence detachments take their posts','',triggered=True,
      actions=[Action('',[cmd('manpowerpool',value=-53),cmd('supplies',value=-900),cmd('money',value=-60)]+guards+[flag('ISLAND_CALLUP')],
      gate=island_gate+' manpower = 53 supplies = 900 money = 60',chance=100)],module='campaign_balance',art='pacific')

    # Finite national contingency reserves; no German or Japanese payment.
    ita_gate='ai = yes flag = JX_ACTIVE war = { country = ITA country = ENG } NOT = { flag = JX_ITA_RECOVERY_B1 } OR = { NOT = { oil = 500 } NOT = { army = { country = ITA size = 30 } } AND = { NOT = { '+control(750,'ITA')+' '+control(761,'ITA')+' '+control(765,'ITA')+' } } }'
    event('ita_recover_b1','Italy calls up its home reserves','',country='ITA',year=1940,offset=7,
      gate=ita_gate,actions=[Action('',[cmd('trigger',which='@ita_apply_b1')],chance=100)],module='campaign_balance',art='army')
    event('ita_apply_b1','Italy calls up its home reserves','',country='ITA',triggered=True,
      actions=[Action('',[flag('ITA_RECOVERY_B1'),cmd('oilpool',value=4000),cmd('supplies',value=4000),
       cmd('ai',which='"jx/ita_recovery_b1.ai"'),later('ita_oil_end_b1',360,'ITA'),cmd('free_oil',value=8),
       cond('NOT = { army = { country = ITA size = 30 } } '+control(419,'ITA'),cmd('add_corps',which='"Italian Home Reserve"',value='land',where=419))]+
       [cond('NOT = { army = { country = ITA size = 30 } } '+control(419,'ITA'),cmd('add_division',which='"Home Reserve '+str(i)+'"',value='infantry',when=9)) for i in range(1,13)],gate=ita_gate,chance=100)],module='campaign_balance',art='army')
    event('ita_oil_end_b1','The Italian emergency fuel reserve ends','',country='ITA',triggered=True,
      actions=[Action('',[cmd('free_oil',value=-8),flag('ITA_FUEL_END_B1')],gate='flag = JX_ITA_RECOVERY_B1 NOT = { flag = JX_ITA_FUEL_END_B1 }',chance=100)],module='campaign_balance')

    # B2 is append-only: the original 21 and every B1 event ID stay unchanged.
    # Hainan is separate so a hostile Haikou cannot block Japanese home defence.
    for key,entries,mp,supply,budget in [('base_gaps_b2',list(enumerate(BASE_GAPS[:9],22)),22.5,360,27),
                                       ('haikou_b2',[(31,BASE_GAPS[9])],2.5,40,3)]:
        site_gate=[]
        for i,(p,name) in entries:
            friendly=control(p)
            if p==1365:
                friendly='OR = { '+friendly+' AND = { '+control(p,'CGX')+' '+puppet('CGX')+' } AND = { '+control(p,'U87')+' '+puppet('U87')+' } }'
            site_gate += [friendly,f'division_exists = {{ type = {ISLAND_TYPE} id = {i} }}']
        gate=active()+f' NOT = {{ flag = JX_{key}_DONE }} manpower = {mp} supplies = {supply} money = {budget} '+' '.join(site_gate)
        commands=[cmd('manpowerpool',value=-mp),cmd('supplies',value=-supply),cmd('money',value=-budget)]
        first_id=entries[0][0]
        commands += named_garrison_commands([(p,name) for i,(p,name) in entries],first_id)
        commands.append(flag(key+'_DONE'))
        title='Local defenders for Haikou' if key=='haikou_b2' else 'Local defenders for the remaining bases'
        desc=('Small, static garrisons take their posts at '+', '.join(name for i,(p,name) in entries)+'. Each has 25 strength and a permanent maximum of 25, with no artillery brigade. '
              f'The one-time call-up costs {mp:g} manpower, {supply} supplies and {budget} money in total. It does not move any existing formation.')
        event(key,title,'',year=1939,offset=3,persistent=True,gate=gate,
          actions=[Action('',[cmd('trigger',which='@'+key+'_apply')],chance=100)],module='campaign_balance',art='pacific')
        event(key+'_apply',title,desc,triggered=True,
          actions=[Action('Put the defenders in place',commands,gate=gate,chance=100),
                   Action('No deployment or payment',[],gate='NOT = { AND = { '+gate+' } }')],module='campaign_balance',art='pacific')


def scenario_templates(serialize):
    china=[]
    for i,(typ,model) in enumerate(CHINA_ROSTER,1):
        china.append(('landdivision',[('dormant','yes'),('id',[('type',str(CHINA_TYPE)),('id',str(i))]),
          ('name',f'Chinese Home Army {i:02d}'),('type',typ),('model',str(model)),('strength','100'),('locked','yes')]))
    japan=[]
    for i,(p,name) in enumerate(ISLANDS+BASE_GAPS,1):
        japan.append(('landdivision',[('dormant','yes'),('id',[('type',str(ISLAND_TYPE)),('id',str(i))]),
          ('name',name+' Defence Detachment'),('type','garrison'),('model','4'),('strength','25'),('max_strength','25'),('locked','yes')]))
    return china,japan


def italy_ai(text,parse,get,serialise):
    n=parse(text)
    def put(node,key,value):
        node[:]=[(k,v) for k,v in node if k!=key];node.append((key,str(value)))
    # These partial switch files must not reset the recovered priorities.
    g=get(n,'garrison')
    if get(n,'exp_force_ratio') is not None:put(n,'exp_force_ratio','0.05')
    if g is not None:
        put(g,'defend_overseas_beaches','yes');put(g,'overseas_multiplier','1.2')
        priorities=get(g,'province_priorities')
        if priorities is None:priorities=[];g.append(('province_priorities',priorities))
        for p,w in ((419,150),(422,140),(430,150),(433,150),(377,100),(750,150),(761,130),(765,130)):
            put(priorities,str(p),max(float(get(priorities,str(p),0)),w))
    return serialise(n)+'\n'


def extra_ai(partner,parse,get,serialise):
    china=partner.replace('max_garrison_prop = 0.35','max_garrison_prop = 0.65').replace('min_garrison_prop = 0.20','min_garrison_prop = 0.45')
    italy='''switch = no
reinforcement = 1.0
upgrading = 0.15
exp_force_ratio = 0.0
max_garrison_prop = 0.45
min_garrison_prop = 0.25
max_redeploying = 0.10
military = {
 relative_build_scheme = no
 infantry = 60 motorized = 4 bergsjaeger = 8 hq = 2 garrison = 8
 interceptor = 8 naval_bomber = 4 destroyer = 4 transports = 2
}
garrison = {
 defend_overseas_beaches = yes
 home_multiplier = 1.5
 overseas_multiplier = 1.2
 beach = 80
 capital = 100
 province_priorities = { 419 = 150 422 = 140 430 = 150 433 = 150 377 = 100 750 = 150 761 = 130 765 = 130 }
}
'''
    # Partial AI files merge individual military weights. Explicitly zero all
    # other ordinary branches so old armour/cavalry weights cannot survive and
    # turn the new 100-point allocation into an invalid total.
    tree=parse(italy);mil=get(tree,'military');keys={k for k,v in mil}
    for k,v in get(parse(partner),'military',[]):
        if k not in keys:mil.append((k,'0'))
    italy=serialise(tree)+'\n'
    return {'ai/jx/china_home_b1.ai':china,'ai/jx/ita_recovery_b1.ai':italy}


def install_assets(source,target,read,write,parse,get,serialise):
    cn,jp=scenario_templates(serialise)
    for rel,add in [('scenarios/1933/china nationalist.inc',cn),('scenarios/1933/japan.inc',jp)]:
        root=parse(read(source/rel));get(root,'country').extend(add);write(target/rel,serialise(root)+'\n')
    partner=read(target/'ai/jx/partner_land.ai')
    for rel,text in extra_ai(partner,parse,get,serialise).items():write(target/rel,text)
    for path in (source/'ai').rglob('*.ai'):
        if path.name.lower().startswith('ita_'):
            rel=path.relative_to(source)
            base=read(target/rel) if (target/rel).exists() else read(path)
            write(target/rel,italy_ai(base,parse,get,serialise))

"""Focused research/personnel pass; retain historical IDs and cabinet events."""
from pathlib import Path
from collections import Counter
import json
import cabinet_expansion

TEAM_PATCHES={
    50013:(5,['munitions','training','general_equipment','artillery','electronics']),
    50063:(7,['general_equipment','management','training','artillery','munitions']),
    50042:(6,['centralized_execution','large_unit_tactics','management','training','infantry_focus']),
    50015:(5,['large_unit_tactics','individual_courage','centralized_execution','training','infantry_focus']),
    50020:(7,['small_unit_tactics','centralized_execution','combined_arms_focus','training','large_unit_tactics','infantry_focus']),
    50003:(8,['naval_engineering','technical_efficiency','carrier_design','management','naval_artillery']),
    50037:(7,['naval_engineering','naval_artillery','technical_efficiency','electronics','carrier_design']),
    50009:(7,['technical_efficiency','fighter_design','mechanics','bomber_design','aircraft_testing','aeronautics']),
    50005:(7,['fighter_design','naval_artillery','avionics','bomber_design','aircraft_testing','aeronautics']),
    50028:(7,['bomber_design','munitions','aeronautics','aircraft_testing','fighter_design','mechanics']),
    50001:(6,['aeronautics','fighter_design','aircraft_testing','bomber_design','naval_artillery']),
    50064:(5,['aeronautics','avionics','aircraft_testing','rocketry','fighter_design']),
    50065:(6,['decentralized_execution','submarine_tactics','small_taskforce_tactics','centralized_execution','seamanship','naval_training']),
    286010:(7,['carrier_tactics','large_taskforce_tactics','naval_training','centralized_execution','seamanship']),
    286011:(6,['naval_training','naval_engineering','small_taskforce_tactics','centralized_execution','seamanship']),
    286016:(6,['small_unit_tactics','combined_arms_focus','training','decentralized_execution','blitzkrieg_tactics','maneuver_tactics']),
}
EXTRA_TEAMS=[
    (286018,'Army Mountain Warfare School',6,1933,['mountain_training','small_unit_tactics','artillery','vehicle_engineering','training'],'mountain_school'),
    (286019,'Army Field Trials Centre',6,1943,['infantry_focus','small_unit_tactics','training','electronics','industrial_engineering'],'field_trials'),
]
PERSONALITIES=[
    ('jx escort priorities',1201,'ChiefOfNavy','Escort and merchant shipping',
     'Destroyer and transport construction time and cost -4 percent, including convoy escorts/transports. Fleet carriers take 3 percent longer. This favours sea-route protection over carrier expansion.',
     [('unit','destroyer','all',-.04),('unit','transport','all',-.04),('unit','carrier','time',.03)]),
    ('jx pilot continuity',1202,'ChiefOfAir','Pilot training and replacements',
     'Air organisation and morale +5 percent; aircraft construction takes 3 percent longer. CAG and light-CAG organisation/morale receive the same training bonus and their construction takes 3 percent longer.',
     [('unit','air','organisation',.05),('unit','air','morale',.05),('unit','air','time',.03),
      ('extra','cag','organisation',.05),('extra','cag','morale',.05),('extra','cag','time',.03),
      ('extra','light_cag','organisation',.05),('extra','light_cag','morale',.05),('extra','light_cag','time',.03)]),
    ('jx joint logistics',1203,'ChiefOfStaff','Joint logistics',
     'Transport capacity +8 percent and national unit supply use -6 percent. Land attack -3 percent. This supports a dispersed war but gives up some immediate combat strength.',
     [('tc_mod',None,None,.08),('supply_consumption',None,None,-.06),('unit','land','attack',-.03)]),
]
from runtime_paths import SOURCE as _SOURCE
PERSONALITIES+=cabinet_expansion.personalities(_SOURCE,lambda p:p.read_text(encoding='latin1'))
FULL_NAMES={50040:'Kiichiro Higuchi',50049:'Tomitaro Horii',50056:'Shojiro Iida',50060:'Hitoshi Imamura',
            50106:'Tadamichi Kuribayashi',50158:'Sadamu Shimomura',50255:'Chuichi Nagumo',50269:'Jisaburo Ozawa',
            50283:'Raizo Tanaka',50292:'Isoroku Yamamoto',50300:'Mitsuo Fuchida',50303:'Minoru Genda',50320:'Jisaburo Ozawa',
            50324:'Saburo Sakai',50327:'Michio Sugawara',50332:'Joichi Tomonaga',50524:'Yoshitoshi Tokugawa'}
REPORT={}


def apply_teams(target,read,write):
    path=target/'db/tech/teams/teams_jap.csv';lines=[];changed=[]
    for line in read(path).splitlines():
        r=line.split(';')
        if r[0].isdigit() and int(r[0]) in TEAM_PATCHES:
            skill,skills=TEAM_PATCHES[int(r[0])];old={'skill':r[3],'skills':[x for x in r[6:] if x and x.lower()!='x']}
            r[3]=str(skill);r=r[:6]+skills+['']*(32-len(skills))+['x'];changed.append({'id':int(r[0]),'name':r[1],'before':old,'skill':skill,'skills':skills})
        if r[0]=='50028':r[2]='jx_aircraft_works_team'
        lines.append(';'.join(r))
    for tid,name,skill,start,skills,art in EXTRA_TEAMS:
        lines.append(';'.join([str(tid),name,'jx_team_'+str(tid),str(skill),str(start),'1970']+skills+['']*(32-len(skills))+['x']))
    write(path,'\n'.join(lines)+'\n');REPORT['research_changes']=changed
    return EXTRA_TEAMS


def apply_roster(source,target,read,write,parse,serialise):
    out=[];changes=[];promotions=[]
    for line in read(source/'db/leaders/japan.csv').splitlines():
        r=line.split(';')
        if len(r)<18 or not r[1].isdigit():out.append(line);continue
        old=r.copy();lid=int(r[1]);start=int(r[15]);branch=int(r[13])
        if lid in FULL_NAMES:r[0]=FULL_NAMES[lid]
        if lid in {50300,50303}:
            r[3]=r[15]='1941';start=1941
        if lid==50524:
            r[16]='1937';r[6]='1990' # active school command, not an instant air marshal
        if lid==50292:r[16]='1951' # conditional combat-death event remains authoritative
        if lid==50040:r[9]=str(int(r[9])|2|8)
        if lid==50056:r[9]=str(int(r[9])|524288)
        if lid==50324:r[9]=str((int(r[9])&~16384)|4096)
        if lid==50332:r[9]=str(int(r[9])|131072)
        # Career progression is a game calibration, not a claim that every
        # historical rank maps literally to a DH formation-command rank.
        if 1930<=start<=1945 and int(r[10])>=2 and int(r[8])>=5 and not int(r[9])&512:
            target_year=max(1936,start+3) if branch==2 else max(1938,start+5)
            if int(r[4])>target_year:
                promotions.append({'id':lid,'name':r[0],'rank':2,'before':r[4],'after':target_year});r[4]=str(target_year)
            if int(r[10])>=3 and int(r[8])>=7:
                target_year=max(1943,start+7) if branch==2 else max(1944,start+9)
                if int(r[5])>target_year:
                    promotions.append({'id':lid,'name':r[0],'rank':1,'before':r[5],'after':target_year});r[5]=str(target_year)
        if old!=r:changes.append({'id':lid,'before':old,'after':r})
        out.append(';'.join(r))
    write(target/'db/leaders/japan.csv','\n'.join(out)+'\n')
    REPORT['leader_changes']=changes;REPORT['promotion_changes']=promotions
    # Preserve cabinet IDs and political events. Extend only office availability
    # where the native retirement year already permits service past 1950.
    out=[];minister_changes=[]
    for line in read(source/'db/ministers/ministers_jap.csv').splitlines():
        r=line.split(';')
        if not r[0].isdigit():out.append(line);continue
        old=r.copy();mid=int(r[0])
        if mid==50131:r[7]='jx joint logistics'
        if mid==50164:r[7]='jx pilot continuity'
        if mid in {50369,50370} and int(r[5])>=1951:r[4]='1951'
        if mid in {50010,50167}:r[4]=r[5]='1951'
        if old!=r:minister_changes.append({'id':mid,'before':old,'after':r})
        out.append(';'.join(r))
    # A new appointment for an already documented person; use his existing
    # identity-specific historical portrait, not a fabricated new face.
    out.append('286120;Chief of Navy;Nomura Naokuni;1944;1951;1974;PA;jx escort priorities;Medium;M5135;X')
    out += [';'.join(r) for r in cabinet_expansion.rows(source,read)]
    write(target/'db/ministers/ministers_jap.csv','\n'.join(out)+'\n')
    root=parse(read(source/'db/ministers/minister_personalities.txt'))
    ids={int(dict(n).get('id',-1)) for k,n in root if k=='minister'}
    for trait,pid,position,name,desc,commands in PERSONALITIES:
        assert pid not in ids
        n=[('trait',trait),('id',str(pid)),('name','JX_PERSONALITY_'+str(pid)+'_NAME'),('desc','JX_PERSONALITY_'+str(pid)+'_DESC'),('position',position)]
        for typ,which,when,value in commands:
            c=[('type',typ),('value',str(value))]
            if which:c.append(('which',which))
            if when:c.append(('when',when))
            n.append(('command',c))
        root.append(('minister',n))
    write(target/'db/ministers/minister_personalities.txt',serialise(root)+'\n')
    REPORT['minister_changes']=minister_changes;REPORT['new_minister_id']=286120


def graphics(target,art_dir):
    from PIL import Image,ImageOps
    im=Image.open(art_dir/'aircraft_works.png').convert('RGB')
    ImageOps.fit(im,(96,96),method=Image.Resampling.LANCZOS).save(target/'gfx/interface/pics/jx_aircraft_works_team.bmp')

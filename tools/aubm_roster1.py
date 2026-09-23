"""ROSTER1: distinct cabinet candidates, command roles and research coverage.

Pure transformations on the installed BALANCE1 baseline. New campaigns only.
No new event, alliance flag, global research bonus or commander count increase.
"""
from collections import Counter
import json
from dh_save_spans import Node, parse, replace, walk

MINISTERS='db/ministers/ministers_ind.csv'
PERSONALITIES='db/ministers/minister_personalities.txt'
LEADERS='db/leaders/india.csv'
TEAMS='db/tech/teams/teams_ind.csv'
MARKER='# AUBM_ROSTER1'

# Same person AND same office only. Keep the modern named portrait/version.
# Different offices occupied by one person are intentionally not duplicates.
ALIASES={
 **{i:251001 for i in (250001,250056,251011,251040)},
 250013:251002,250018:251003,250004:251004,251033:251004,
 **{i:251005 for i in (250031,251015,251025,251034)},
 250034:251006,
 **{i:251007 for i in (250043,251017,251036)},
 **{i:251008 for i in (250048,251018,251028,251037)},
 **{i:251009 for i in (250050,251019,251029,251038)},
 **{i:251010 for i in (250052,251020,251030,251039)},
 250070:251022,251031:251022,251032:251023,251035:251026,
 250040:251027,250066:250007,
}
OFFICES={
 'headofstate':'Head of State','headofgovernment':'Head of Government',
 'foreignminister':'Foreign Minister','armamentminister':'Minister of Armament',
 'ministerofsecurity':'Minister of Security','ministerofintelligence':'Head of Military Intelligence',
 'chiefofstaff':'Chief of Staff','chiefofarmy':'Chief of Army',
 'chiefofnavy':'Chief of Navy','chiefofair':'Chief of Air Force',
}

def rows(text):
    return [line.split(';') for line in text.splitlines() if line and line.split(';')[0].isdigit()]

def rewrite_rows(text,updates,drop=(),extra=()):
    out=[];seen=set()
    for line in text.splitlines(keepends=True):
        cells=line.rstrip('\r\n').split(';')
        if cells[0].isdigit():
            eid=int(cells[0]);seen.add(eid)
            if eid in drop:continue
            if eid in updates:
                for col,value in updates[eid].items():cells[col]=str(value)
                ending='\r\n' if line.endswith('\r\n') else '\n'
                line=';'.join(cells)+ending
        out.append(line)
    if set(updates)-seen:raise ValueError('Missing roster IDs '+str(set(updates)-seen))
    for row in extra:
        if int(row[0]) in seen:raise ValueError('New roster ID collision '+row[0])
        out.append(';'.join(map(str,row))+'\r\n')
    return ''.join(out)

def command(kind,which=None,when=None,value=0):
    return '{ type = '+kind+(' which = '+which if which else '')+(' when = '+when if when else '')+' value = '+str(value)+' }'

def unit(kind,when,value):return command('unit',kind,when,value)

# Existing tailored personalities are narrowed where they otherwise beat all
# alternatives. No new universal IC/research/shipbuilding discount is introduced.
TRAITS={
 320:('Indian Ocean Fleet Architect','ChiefOfNavy','Carrier groups and scouting first. Better carrier organisation, naval-air morale and fleet research; slower battleship procurement.',[
  command('research','naval_doctrines','time',-.03),unit('carrier','organisation',.05),unit('light_carrier','organisation',.05),unit('naval_bomber','morale',.04),command('detection','navy',value=.05),unit('battleship','time',.03)]),
 321:('Indian Air Institution Builder','ChiefOfAir','Air doctrine and fighter readiness first. Stronger interceptors and a better-trained air staff; strategic bomber procurement receives less priority.',[
  command('research','air_doctrines','time',-.04),unit('interceptor','organisation',.05),unit('multi_role','organisation',.05),unit('strategic_bomber','time',.03)]),
 9318300:('Battle Fleet Gunnery','ChiefOfNavy','Heavy guns and surface squadrons. Battleships, battlecruisers and heavy cruisers hit harder; carrier construction takes longer.',[
  unit('battleship','attack',.05),unit('battlecruiser','attack',.05),unit('heavy_cruiser','attack',.05),unit('carrier','time',.04)]),
 9318301:('Sea Lane Commander','ChiefOfNavy','Keep the sea lanes open. Better escort organisation and detection, cheaper convoy transports; battleship construction receives less priority.',[
  unit('destroyer','organisation',.05),command('detection','navy',value=.06),unit('transport','cost',-.05),unit('battleship','time',.04)]),
 9318302:('Undersea Warfare Chief','ChiefOfNavy','A raiding fleet, not a battle line. Better submarine attack and organisation, with slower carrier construction.',[
  unit('submarine','attack',.06),unit('submarine','organisation',.04),unit('carrier','time',.04)]),
 9318303:('Mobile Columns Chief','ChiefOfArmy','Armour and motorised formations receive the best staff work. Infantry production is slightly slower; no bonus is given to every land division.',[
  unit('armor','organisation',.05),unit('light_armor','organisation',.05),unit('motorized','morale',.05),unit('mechanized','morale',.05),unit('infantry','time',.03)]),
 9318304:('Frontier Service Chief','ChiefOfArmy','Mountain troops, engineers and difficult frontiers come first. Stronger specialist organisation and cheaper engineer brigades; slower tank procurement.',[
  unit('bergsjaeger','organisation',.06),unit('marine','organisation',.04),command('extra','engineer','cost',-.05),unit('armor','time',.03)]),
 9318305:('Army Air Support Chief','ChiefOfAir','Put aircraft over the battlefield. Better close-support and tactical bomber performance; interceptor production receives less priority.',[
  unit('cas','attack',.05),unit('tactical_bomber','morale',.05),unit('transport_plane','organisation',.04),unit('interceptor','time',.03)]),
 9318306:('Maritime Air Chief','ChiefOfAir','Train the fleet air arm. Naval bombers gain attack and organisation and carriers gain organisation; strategic bombers take longer to build.',[
  unit('naval_bomber','attack',.05),unit('naval_bomber','organisation',.04),unit('carrier','organisation',.03),unit('strategic_bomber','time',.04)]),
 9318307:('Long Range Air Chief','ChiefOfAir','Range, navigation and sustained bombing. Better strategic bomber organisation and morale, and improved bomber research; fighters take longer to build.',[
  unit('strategic_bomber','organisation',.05),unit('strategic_bomber','morale',.05),command('research','aircraft','time',-.02),unit('interceptor','time',.04)]),
 9318308:('Resource First Planner','ArmamentMinister','Expand the mines and oil industry before adding more factory demand. Energy, metals, alloys and oil output rise; factory output falls slightly.',[
  command('resource','energy',value=.10),command('resource','metal',value=.08),command('resource','rare_materials',value=.08),command('resource','oil',value=.05),command('production','production','national',-.02)]),
 9318309:('Civil Liberties Counsel','MinisterOfSecurity','Public trust reduces civilian demand and unrest. Tax receipts improve, but the state maintains a smaller domestic intelligence network.',[
  command('production','consumer',value=-.04),command('dissent',value=-.02),command('resource','money',value=.03),command('intelligence_network',when='national',value=-1)]),
 9318310:('District Organiser','MinisterOfSecurity','Local recruitment and distribution get practical support. More national manpower growth and supplies, at a modest treasury cost.',[
  command('populationgrowth',when='national',value=.06),command('production','supplies',value=.04),command('resource','money',value=-.03)]),
 9318311:('Frugal Procurement Chief','ArmamentMinister','Spend carefully before ordering more factories. Less civilian demand, cheaper upgrades and better revenues, but slower new factory construction.',[
  command('production','consumer',value=-.04),command('production','upgrading',value=-.04),command('resource','money',value=.05),command('province','ic','time',.03)]),
}

MIN_UPDATES={
 250005:{7:'District Organiser',9:'INDM_KIDWAI'},250009:{7:'Battle Fleet Gunnery',9:'INDL251101'},
 250032:{7:'Civil Liberties Counsel'},
 250046:{2:'S. M. Shrinagesh',6:'SD',9:'L505075'},
 250053:{3:1933,7:'Maritime Air Chief',9:'INDL251202'},
 250054:{7:'Long Range Air Chief'},250055:{7:'Army Air Support Chief',9:'INDL251203'},
 250025:{3:1935},250036:{2:'Homi J. Bhabha',3:1936},
}

def minister_row(eid,office,name,year,ideology,trait,picture):
    return [str(eid),office,name,str(year),'1964','1999',ideology,trait,'High',picture,'X']

NEW_MINISTERS=[
 minister_row(251101,'Chief of Navy','H. M. S. Choudri',1933,'SL','Sea Lane Commander','L505091'),
 minister_row(251102,'Chief of Navy','S. M. Ahsan',1936,'LWR','Undersea Warfare Chief','L505000'),
 minister_row(251103,'Chief of Army','K. S. Thimayya',1933,'SL','Mobile Columns Chief','L505079'),
 minister_row(251104,'Chief of Army','S. M. Shrinagesh',1933,'SD','Frontier Service Chief','L505075'),
 minister_row(251105,'Minister of Armament','Sir Chhotu Ram',1933,'SL','Resource First Planner','M59026'),
 minister_row(251106,'Minister of Armament','C. Rajagopalachari',1933,'SL','Frugal Procurement Chief','INDM_RAJAGOPALACHARI'),
 minister_row(251107,'Chief of Air Force','Karun Krishna Majumdar',1936,'LWR','Army Air Support Chief','INDL251201'),
]

# Six or seven real component types per specialist; no globally fast mega-team.
TEAM_PLAN={
 250003:(7,'IACS Fuel and Chemical Laboratory','chemistry industrial_engineering mathematics management mechanics nuclear_physics',1930),
 250004:(7,'Military Engineer Services','general_equipment mechanics technical_efficiency vehicle_engineering artillery training',1930),
 250005:(7,'Indian Ordnance Factories','mechanics munitions artillery general_equipment electronics technical_efficiency training',1930),
 250006:(7,'Garden Reach Escort and Submarine Works','naval_engineering technical_efficiency electronics submarine_design mechanics chemistry',1930),
 250007:(7,'Mazagon Surface Ship Bureau','naval_engineering naval_artillery technical_efficiency electronics mechanics',1930),
 250008:(7,'Tata Transport and Bomber Works','bomber_design aeronautics aircraft_testing avionics mechanics general_equipment',1930),
 250010:(8,'Cariappa General Staff','centralized_execution large_unit_tactics training combined_arms_focus infantry_focus individual_courage',1930),
 250011:(7,"Messervy's Field Exercises Board",'decentralized_execution small_unit_tactics combined_arms_focus infantry_focus general_equipment training medicine',1933),
 250012:(7,'No. 1 Squadron Fighter School','fighter_tactics training piloting aeronautics electronics decentralized_execution',1930),
 250013:(7,"Walchand's Fighter Design Bureau",'fighter_design aeronautics aircraft_testing avionics mechanics technical_efficiency',1930),
 250015:(8,'Bhatnagar Applied Science Group','munitions mechanics artillery general_equipment electronics chemistry',1930),
 250018:(7,"Katari's Ocean Operations Staff",'large_taskforce_tactics centralized_execution naval_engineering technical_efficiency management seamanship',1930),
 250019:(7,'Armoured Vehicle Development School','vehicle_engineering mechanics electronics artillery technical_efficiency munitions',1930),
 250021:(8,'Indian Carrier Design Board','carrier_design naval_engineering technical_efficiency electronics aircraft_testing',1930),
 250022:(7,"Aspy Engineer's Carrier Warfare School",'carrier_tactics large_taskforce_tactics naval_training aircraft_testing piloting naval_engineering seamanship',1930),
 250023:(7,'Monsoon Surface Fleet Staff','large_taskforce_tactics small_taskforce_tactics naval_training naval_artillery centralized_execution naval_engineering',1930),
 250024:(7,'Visakhapatnam Undersea Warfare School','submarine_tactics small_taskforce_tactics seamanship naval_training naval_engineering submarine_design',1933),
 250025:(8,'Mukerjee Air Defence Staff','centralized_execution large_unit_tactics fighter_tactics training electronics piloting',1933),
 250026:(8,'Thimayya Mobile Warfare School','combined_arms_focus centralized_execution large_unit_tactics training technical_efficiency maneuver_tactics blitzkrieg_tactics',1933),
 250027:(8,'Quetta-Delhi Frontier Staff College','small_unit_tactics decentralized_execution infantry_focus individual_courage training mountain_training',1933),
 250030:(7,'Bose Maritime Signals Centre','electronics mathematics naval_training technical_efficiency mechanics naval_artillery',1935),
 250031:(6,'Bengal Chemical and Army Medical Service','medicine chemistry industrial_engineering management training general_equipment',1930),
}
NEW_TEAMS={
 250032:(7,'Cochin Landing Warfare School','naval_engineering naval_artillery small_unit_tactics infantry_focus naval_training general_equipment marine_training',1934,'TT250004'),
 250033:(7,'Aircraft Armament Trials Unit','bomber_design fighter_design aeronautics munitions avionics aircraft_testing naval_artillery',1934,'TT250013'),
 250034:(7,'Army-Air Cooperation School','combined_arms_focus bomber_tactics piloting training general_equipment airborne_training aeronautics',1933,'TT250012'),
 250035:(7,'Long-Range Air Navigation School','bomber_tactics training mechanics aeronautics centralized_execution electronics chemistry',1936,'TT250020'),
}

# Reassign roles, not stronger ranks or skill. Trait bitmasks come from the
# installed engine's Leader Traits.txt. These are alternate-campaign game roles.
LEADER_ROLES={
 250021:1|2|268435456,250070:2|32,250074:256|4194304|4,
 251011:1|16|536870912,251012:128|4|67108864,
 251024:32|4|1,251026:2|16777216,251027:256|64,
 251028:4|2097152,251030:128|1,251031:32|2|8388608,
 251033:2|4194304,251035:32|524288|1,251036:64|16|1048576,
 251038:256|524288|1073741824,251039:256|32,
 251040:256|16|134217728,251043:2|262144,251044:16|262144,
 251050:256|4194304,251052:128|1073741824,
 250084:2048|8192,250085:2048|4096,250089:4096|8192,
 250100:4096|2048,250113:1024|8192,251101:4096,
 251102:4096|8192,251103:1024|2048,251104:2048|8192,
 251105:4096|2048,
 250117:4096|8192,250125:32768|65536,250137:4096|65536,
 250138:4096,251201:16384|65536,251202:131072|8192,
 251203:16384|8192,251204:131072|4096,251205:32768|8192,
 251206:8192|65536,251207:4096|65536,251208:16384|65536,
}
GIVEN='Arvind Raghavan Harish Devendra Yusuf Farid Narayan Krishan Prakash Harjit Amar Balwant Jal Keshav Hamid Nalin Shankar Salim Dinesh Manohar Rashid Ashok Suresh Jagat Arun Dilip Nasir Govind Vinod Ramesh'.split()

def minister_references(files):
    """Remap only minister contexts; leader and team IDs share these numbers."""
    out=dict(files);changed=[]
    for p,t in files.items():
        if not (p.startswith('db/events/') and p.endswith('.txt')):continue
        edits=[]
        for n in walk(parse(t)):
            typ=n.get('type')
            if typ in set(OFFICES)|{'sleepminister','wakeminister'}:
                val=n.get('which')
                if val and val.isdigit() and int(val) in ALIASES:
                    if typ=='sleepminister':raise ValueError('Alias retirement needs explicit review: '+p)
                    f=n.field('which');edits.append((f.value_start,f.end,str(ALIASES[int(val)])))
            for f in n.fields:
                if f.key in set(OFFICES)|{'minister','incabinet'} and isinstance(f.value,str) and f.value.isdigit() and int(f.value) in ALIASES:
                    edits.append((f.value_start,f.end,str(ALIASES[int(f.value)])))
        if edits:out[p]=replace(t,edits);changed.append(dict(path=p,references=len(edits)))
    return out,changed

def transform(files):
    if MARKER in files[PERSONALITIES]:
        ministers={int(row[0]) for row in rows(files[MINISTERS])}
        teams={int(row[0]):row for row in rows(files[TEAMS])}
        if ministers&set(ALIASES) or not {int(row[0]) for row in NEW_MINISTERS}<=ministers or not set(NEW_TEAMS)<=teams.keys():
            raise ValueError('Partial ROSTER1 installation')
        for eid,(skill,name,specs,year) in TEAM_PLAN.items():
            if teams[eid][1]!=name or teams[eid][3]!=str(skill) or [s for s in teams[eid][6:-1] if s]!=specs.split():raise ValueError('Partial ROSTER1 team '+str(eid))
        remapped,refs=minister_references(files)
        if refs:raise ValueError('Partial ROSTER1 minister reference repair')
        return dict(files),{}
    out=dict(files);report={}
    out[MINISTERS]=rewrite_rows(files[MINISTERS],MIN_UPDATES,ALIASES,NEW_MINISTERS)
    report['ministers']=dict(before=len(rows(files[MINISTERS])),after=len(rows(out[MINISTERS])),removed_aliases=ALIASES,new_candidates=len(NEW_MINISTERS))
    text=files[PERSONALITIES];edits=[];present=set()
    for n in parse(text).all('minister'):
        eid=int(n.get('id'))
        if eid not in TRAITS:continue
        if eid>=9318300:raise ValueError('New personality ID collision '+str(eid))
        present.add(eid);trait,position,desc,commands=TRAITS[eid]
        block='\n trait = '+json.dumps(trait)+'\n id = '+str(eid)+'\n name = '+json.dumps(trait)+'\n desc = '+json.dumps(desc)+'\n position = '+position+'\n value = 0\n'+'\n'.join(' command = '+c for c in commands)+'\n'
        edits.append((n.start+1,n.end-1,block))
    if present!={320,321}:raise ValueError('Missing existing military personalities')
    out[PERSONALITIES]=replace(text,edits)+'\n'+MARKER+'\n'
    for eid,(trait,position,desc,commands) in TRAITS.items():
        if eid in present:continue
        out[PERSONALITIES]+='minister = { trait = '+json.dumps(trait)+' id = '+str(eid)+' name = '+json.dumps(trait)+' desc = '+json.dumps(desc)+' position = '+position+' value = 0\n'+'\n'.join('command = '+c for c in commands)+'\n}\n'
    updates={eid:{1:name,3:skill,4:year,**{6+i:s for i,s in enumerate(specs.split()+['']*(32-len(specs.split())))}} for eid,(skill,name,specs,year) in TEAM_PLAN.items()}
    extra=[]
    for eid,(skill,name,specs,year,pic) in NEW_TEAMS.items():
        extra.append([str(eid),name,pic,str(skill),str(year),'1970']+specs.split()+['']*(32-len(specs.split()))+['x'])
    out[TEAMS]=rewrite_rows(files[TEAMS],updates,extra=extra)
    leaders=[r.split(';') for r in files[LEADERS].splitlines()[1:] if r and not r.startswith('#')]
    updates={eid:{9:traits} for eid,traits in LEADER_ROLES.items()}
    reserve_count=Counter();used=set();renamed=0
    for r in leaders:
        eid=int(r[1]);oldname=r[0]
        if eid<252000:continue
        surname=oldname.split()[-2] # Preserve its existing region/family distribution.
        j=reserve_count[surname];reserve_count[surname]+=1
        name=GIVEN[j%len(GIVEN)]+' '+surname+' (R)'
        if name in used:raise ValueError('Fictional reserve name pool exhausted: '+name)
        used.add(name);updates[eid]={0:name};renamed+=1
    # Leader CSV uses column1 as ID, unlike the other two rosters.
    lines=[]
    for line in files[LEADERS].splitlines(keepends=True):
        r=line.rstrip('\r\n').split(';')
        if len(r)>1 and r[1].isdigit() and int(r[1]) in updates:
            for col,v in updates[int(r[1])].items():r[col]=str(v)
            line=';'.join(r)+('\r\n' if line.endswith('\r\n') else '\n')
        lines.append(line)
    out[LEADERS]=''.join(lines)
    out,refs=minister_references(out)
    report.update(minister_reference_changes=refs,leader_profiles=len(LEADER_ROLES),fictional_reserves_renamed=renamed,team_profiles=len(TEAM_PLAN),new_teams=len(NEW_TEAMS))
    return out,report

def research_audit(files,teamtext):
    """Weighted component matching, NOT a prediction of exact research days.

    All unlocked teams whose start year permits the application are compared.
    Actual event locks, active projects, blueprint/sliders/minister effects and
    exclusive doctrine prerequisites still govern a real campaign.
    """
    teams=rows(teamtext);loc={r.split(';')[0]:r.split(';')[1] for r in files['config/tech_names.csv'].splitlines() if ';' in r}
    result=[]
    for p,t in files.items():
        if not p.startswith('db/tech/') or not p.endswith('_tech.txt'):continue
        tech=parse(t).get('technology')
        if not tech:continue
        for a in tech.all('application'):
            year=int(a.get('year',0))
            if not 1933<=year<=1947:continue
            components=[(c.get('type').lower(),float(c.get('difficulty'))*(2 if c.get('double_time')=='yes' else 1)) for c in a.all('component')]
            if not components:continue
            ranking=[]
            for r in teams:
                if int(r[4])>year or int(r[5])<year:continue
                specs={s.lower() for s in r[6:-1] if s}
                coverage=sum(w for s,w in components if s in specs)/sum(w for _,w in components)
                ranking.append(dict(id=int(r[0]),name=r[1],skill=int(r[3]),coverage=round(coverage,5)))
            ranking.sort(key=lambda x:(-x['coverage'],-x['skill'],x['id']))
            best=ranking[0]
            winners=[r['id'] for r in ranking if (r['coverage'],r['skill'])==(best['coverage'],best['skill'])]
            result.append(dict(id=int(a.get('id')),name=loc.get(a.get('name'),a.get('name')),year=year,category=tech.get('category'),components=components,best=winners,top=ranking[:4]))
    return result

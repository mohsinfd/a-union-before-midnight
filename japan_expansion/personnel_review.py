"""Installed personnel/research regression audit. Does not execute Darkest Hour."""
from collections import Counter
import hashlib
import json
from PIL import Image
from build import HERE,SOURCE,TARGET,GAME,VERSION,read,parse,get,getall
from offline_review import teams
from japan_personnel import TEAM_PATCHES,EXTRA_TEAMS,FULL_NAMES,PERSONALITIES
from cabinet_expansion import APPOINTMENTS,POSITIONS,rows as cabinet_rows
import unique_divisions
import unique_attachments
import force_delivery_audit
import japanese_research_names


def csv_rows(folder,relative,id_column):
    rows={}
    for line in read(folder/relative).splitlines():
        r=line.split(';')
        if len(r)>id_column and r[id_column].isdigit():
            key=int(r[id_column]);assert key not in rows,(relative,key)
            rows[key]=r
    return rows


def active_counts(rows,year):
    return {name:sum(int(r[13])==branch and int(r[15])<=year<=min(int(r[16]),int(r[17]))
                     for r in rows.values()) for branch,name in enumerate(('army','navy','air'))}


def portrait_exists(name):
    # DH uses the root installation for assets absent from the selected mod.
    return any((root/'gfx/interface/pics'/(name+'.bmp')).exists() for root in (TARGET,GAME))


def run():
    force_delivery_audit.configure_personality()
    old=csv_rows(SOURCE,'db/leaders/japan.csv',1);new=csv_rows(TARGET,'db/leaders/japan.csv',1)
    assert old.keys()==new.keys() and len(new)==532
    changes=[];promotions=[]
    for lid,r in new.items():
        b=old[lid]
        # No duplicate officers, branch swaps, free skill/XP, or substituted faces.
        assert all(r[i]==b[i] for i in (1,2,7,8,10,11,12,13,14,17)),lid
        if b!=r:changes.append({'id':lid,'before':b,'after':r})
        if any(b[i]!=r[i] for i in (4,5)):
            promotions.append({'id':lid,'name':r[0],'before':b[3:7],'after':r[3:7]})
            assert int(r[3])<=int(r[4])<=int(r[5]),(lid,'promotion chronology')
        if b!=r and r[14].lower()!='unknown':
            assert portrait_exists(r[14]),(lid,r[14])
    assert all(new[lid][0]==name for lid,name in FULL_NAMES.items())
    assert all(int(new[lid][15])==1941 for lid in (50300,50303))
    assert int(new[50524][16])==1937 and int(new[50524][6])==1990
    assert int(new[50292][16])>=1950
    assert int(new[50040][9])&10==10 and int(new[50056][9])&524288
    assert int(new[50324][9])&4096 and not int(new[50324][9])&16384
    assert int(new[50332][9])&131072
    availability=[{'year':y,'baseline':active_counts(old,y),'installed':active_counts(new,y)}
                  for y in (1933,1937,1941,1945,1950)]
    for row in availability:
        assert all(row['installed'][b]>=row['baseline'][b] for b in ('army','navy','air'))

    oldmin=csv_rows(SOURCE,'db/ministers/ministers_jap.csv',0)
    newmin=csv_rows(TARGET,'db/ministers/ministers_jap.csv',0)
    new_ids={286120}|{r[0] for r in APPOINTMENTS}
    assert newmin.keys()-oldmin.keys()==new_ids and not oldmin.keys()-newmin.keys()
    assert newmin[286120][2]=='Nomura Naokuni' and newmin[286120][9]=='M5135'
    assert portrait_exists('M5135')
    # Catch ID collisions with another country's appointments, not only Japan.
    new_id_occurrences=[]
    for p in (TARGET/'db/ministers').glob('ministers_*.csv'):
        for line in read(p).splitlines():
            if line.split(';')[0].isdigit() and int(line.split(';')[0]) in new_ids:new_id_occurrences.append((int(line.split(';')[0]),p.name))
    assert Counter(mid for mid,p in new_id_occurrences)==Counter(new_ids),new_id_occurrences
    assert all(p=='ministers_jap.csv' for mid,p in new_id_occurrences)
    for r in cabinet_rows(SOURCE,read):
        if r[0]=='286122':r[2]='Fujiwara Ginjiro (Civil Works)'
        assert newmin[int(r[0])]==r and portrait_exists(r[9])
    assert len({newmin[r[0]][9] for r in APPOINTMENTS})==10
    face_hashes=[]
    for mid,*_ in APPOINTMENTS:
        p=next(root/'gfx/interface/pics'/(newmin[mid][9]+'.bmp') for root in (TARGET,GAME)
               if (root/'gfx/interface/pics'/(newmin[mid][9]+'.bmp')).exists())
        with Image.open(p) as im:face_hashes.append(hashlib.sha256(im.convert('RGB').tobytes()).hexdigest())
    assert len(set(face_hashes))==10,'New appointment portraits reuse image content'
    nodes=getall(parse(read(TARGET/'db/ministers/minister_personalities.txt')),'minister')
    ids=[get(n,'id') for n in nodes];assert len(ids)==len(set(ids))
    traits=[get(n,'trait').lower() for n in nodes];assert len(traits)==len(set(traits))
    positions=POSITIONS
    loc=read(TARGET/'config/japan_rising.csv')
    for trait,pid,position,name,desc,commands in PERSONALITIES:
        node=next(n for n in nodes if get(n,'id')==str(pid))
        assert get(node,'trait')==trait and get(node,'position')==position
        for key in ('NAME','DESC'):assert 'JX_PERSONALITY_'+str(pid)+'_'+key+';' in loc
        users=[r for r in newmin.values() if r[7]==trait];assert len(users)==1
        assert positions[users[0][1]]==position
        cs=getall(node,'command')
        assert all(get(c,'type') in {'unit','extra','tc_mod','supply_consumption','resource','production','province','diplomacy_cost','diplomacy_chances','research'} for c in cs)
        expected=list(commands)
        for typ,which,when,value in list(expected):
            if typ=='unit':
                for unit,info in unique_divisions.CLASSES.items():
                    candidate=(typ,unit,when,value)
                    if which==info['base'] and candidate not in expected:expected.append(candidate)
        for typ,which,when,value in list(expected):
            if typ=='extra':
                for unit,info in unique_attachments.ATTACHMENTS.items():
                    candidate=(typ,unit,when,value)
                    if which==info['base'] and candidate not in expected:expected.append(candidate)
        assert len(cs)==len(expected)
        for c,(typ,which,when,value) in zip(cs,expected):
            assert (get(c,'type'),get(c,'which'),get(c,'when'),float(get(c,'value')))==(typ,which,when,value)
            assert abs(float(get(c,'value'))) <= (5 if typ=='diplomacy_chances' else .15)
    late_army=[r for r in newmin.values() if r[1]=='Chief of Army' and r[6] in {'PA','FA','NS'}
               and int(r[3])<=1950<=min(int(r[4]),int(r[5]))]
    assert {50369,50370}<=set(int(r[0]) for r in late_army)
    assert len({r[7].lower() for r in late_army})>=3
    for mid in (50010,50167):assert min(int(newmin[mid][4]),int(newmin[mid][5]))>=1950
    ambush=next(e for e in getall(parse(read(TARGET/'db/events/Add_on.txt')),'event') if get(e,'id')=='1000212')
    actions=sum((getall(ambush,k) for k in ('action','action_a','action_b','action_c')),[])
    sleeps=[get(c,'which') for a in actions for c in getall(a,'command') if get(c,'type')=='sleepleader']
    assert '50292' in sleeps and '50200' not in sleeps
    assert 'JAP' in str(get(ambush,'trigger')) and 'USA' in str(get(ambush,'trigger'))

    base=teams(SOURCE,'jap');pool=teams(TARGET,'jap');byid={t['id']:t for t in pool}
    assert len(base)==54 and len(pool)==64 and len(byid)==len(pool)
    for tid,(name,start) in japanese_research_names.NAMES.items():
        assert byid[tid]['name']==name and byid[tid]['start']==start
    components=set()
    for p in (TARGET/'db/tech').glob('*.txt'):
        for tree in getall(parse(read(p)),'technology'):
            for a in getall(tree,'application'):
                components.update(get(c,'type').lower() for c in getall(a,'component'))
    for tid in set(TEAM_PATCHES)|{t[0] for t in EXTRA_TEAMS}:
        assert byid[tid]['skills']<=components,(tid,byid[tid]['skills']-components)
    assert 'large_unit_tactics' in byid[50015]['skills'] and 'large_taskforce_tactics' not in byid[50015]['skills']
    # A real missing speciality, unlike the earlier case-sensitive aircraft comparison.
    assert not any('mountain_training' in t['skills'] and t['start']<=1933 for t in base)
    assert 'mountain_training' in byid[286018]['skills'] and byid[286018]['start']==1933
    research=json.loads((HERE/'OFFLINE_REVIEW.json').read_text())
    assert any(r['unit']=='interceptor' and r['matched']>=4 for r in research['research'])
    assert all(r['matched']==r['components'] for r in research['research'] if r['unit']=='bergsjaeger')
    portraits=[]
    for tid in (286018,286019,50028):
        p=TARGET/'gfx/interface/pics'/(byid[tid]['image']+'.bmp')
        with Image.open(p) as im:
            assert im.size==(96,96) and im.mode=='RGB'
            portraits.append(hashlib.sha256(im.tobytes()).hexdigest())
    assert len(set(portraits))==3
    report={'result':'PASS','version':VERSION,'game_executed':False,'leaders':len(new),
            'leader_records_changed':len(changes),'leader_promotion_records_changed':len(promotions),
            'leader_availability':availability,'leader_changes':changes,'promotions':promotions,
            'baseline_teams':len(base),'installed_teams':len(pool),'team_profiles_reworked':len(TEAM_PATCHES),
            'new_teams_this_pass':len(EXTRA_TEAMS),'new_institution_pictures_this_pass':3,
            'minister_appointments_before':len(oldmin),'minister_appointments_after':len(newmin),
            'new_minister_personalities':len(PERSONALITIES),'late_army_personalities':[r[7] for r in late_army],
            'new_1937_appointments':len(APPOINTMENTS),'new_1937_distinct_historical_portraits':10,
            'yamamoto_ambush_leader_id':50292,'no_base_skill_or_experience_increase':True}
    (HERE/'PERSONNEL_REVIEW.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    lines=['# Japan R4: research and personnel review','',
           'PASS: installed-file checks. No game launch, effective research-day calculation, or campaign balance claim.','',
           f'Japan retains all {len(new)} leader records, their branches, portraits, base skill, experience and maximum skill. '
           f'{len(changes)} records change; {len(promotions)} have revised promotion dates. The progression changes are game calibration, not historical rank claims.','',
           '| Year | Army before / after | Navy before / after | Air before / after |','| --- | --- | --- | --- |']
    for r in availability:
        lines.append('| '+str(r['year'])+' | '+' | '.join(str(r['baseline'][b])+' / '+str(r['installed'][b]) for b in ('army','navy','air'))+' |')
    lines+=['','Availability is a date-based roster count; scripted deaths, historical purges, country status and the engine can reduce the live pool. Promotion dates do not guarantee an immediate automatic promotion.','',
            'There are 64 research teams: 54 inherited, eight from earlier Japan Rising work and two from R4. Sixteen profiles were reworked. See OFFLINE_REVIEW.md for 35 unit/year comparisons, with case-normalised component types. Matching components is a proxy, not a research-time or doctrine-prerequisite simulation.','',
            'L4 adds ten optional 1937 appointment agendas, each with a benefit and a cost. They use ten distinct identity-specific historical portraits from the source roster. These are alternate policies for existing people, not ten invented politicians. The earlier Nomura appointment remains dated 1944. Three distinct institute scenes were generated.','',
            'Two existing army chiefs remain available in 1950, giving three different PA/FA/NS army-chief personalities at that date. Actual selectability depends on government and scripted removals.','',
            'The inherited Yamamoto ambush now removes admiral 50292, rather than unrelated army record 50200. His normal roster end dates no longer force removal in 1944 if that conditional event did not happen. The event retains its original USA-war and island-control conditions; it is not an interception simulation.','',
            'Unchanged stock records with unknown portraits remain; this pass does not claim every historical photograph or death date was repaired. In-game promotion, minister stacking, selection and research display remain for the user playtest.']
    (HERE/'PERSONNEL_REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'leader_changes','promotions'}}))


if __name__=='__main__':run()

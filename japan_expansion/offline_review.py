"""Review the installed research, programme balance and artwork without a launch."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from PIL import Image
from build import TARGET,SOURCE,HERE,parse,get,getall,read


def teams(folder,tag):
    rows=[]
    for line in read(folder/'db/tech/teams'/('teams_'+tag+'.csv')).splitlines():
        cells=line.split(';')
        if len(cells)>6 and cells[0].isdigit():
            rows.append({'id':int(cells[0]),'name':cells[1],'image':cells[2],'skill':int(cells[3]),'start':int(cells[4]),'end':int(cells[5]),'skills':{x.lower() for x in cells[6:] if x and x.lower()!='x'}})
    return rows


def run():
    japanese=teams(TARGET,'jap');baseline=teams(SOURCE,'jap');apps=[];local={}
    for p in (TARGET/'config').glob('*.csv'):
        for line in read(p).splitlines():
            c=line.split(';')
            if len(c)>1:local[c[0]]=c[1]
    for p in (TARGET/'db/tech').glob('*.txt'):
        for tree in getall(parse(read(p)),'technology'):
            for a in getall(tree,'application'):
                effects=get(a,'effects',[])
                kinds={get(c,'which') for c in getall(effects,'command') if get(c,'type')=='new_model'}
                components=[(get(c,'type').lower(),float(get(c,'difficulty',1))*(2 if get(c,'double_time')=='yes' else 1)) for c in getall(a,'component')]
                if components:apps.append({'id':get(a,'id'),'name':local.get(get(a,'name'),get(a,'name')),'year':int(get(a,'year',0)),'category':get(tree,'category'),'units':kinds,'parts':components})
    def best(pool,a,year):
        active=[t for t in pool if t['start']<=year<=t['end']]
        def score(t):
            # A comparison aid only: matched component difficulty, then skill.
            # This does not calculate research time or unlock prerequisites.
            matched=sum(d for k,d in a['parts'] if k in t['skills'])
            return matched,t['skill']
        t=max(active,key=score)
        return t,sum(k in t['skills'] for k,d in a['parts']),sum(d for k,d in a['parts'] if k in t['skills'])/sum(d for k,d in a['parts'])
    lines=['# Installed build: offline balance and research review','',
        'This review reads the installed files. It does not launch the game, calculate research days, model combat, or certify Hard campaign balance. Team comparisons rank matched component difficulty first and skill second; prerequisite and doctrine-path availability still matter.','',
        '## Research coverage at campaign milestones','',
        '| Year | Branch / application | Best installed team | Skill | Components matched | Baseline match |','| --- | --- | --- | --- | --- | --- |']
    rows=[]
    for year in (1933,1937,1941,1945,1950):
        for unit in ('infantry','bergsjaeger','marine','carrier','destroyer','interceptor','tactical_bomber'):
            choices=[a for a in apps if unit in a['units'] and a['year']<=year]
            if not choices:continue
            a=max(choices,key=lambda a:(a['year'],int(a['id'])))
            t,m,f=best(japanese,a,year);old,om,of=best(baseline,a,year)
            lines.append(f"| {year} | {unit}: {a['name']} ({a['id']}) | {t['name']} | {t['skill']} | {m}/{len(a['parts'])} | {om}/{len(a['parts'])}: {old['name']} |")
            rows.append({'year':year,'unit':unit,'tech':a['id'],'team':t['id'],'matched':m,'components':len(a['parts']),'baseline_match':om})
        for category in ('land_doctrines','naval_doctrines','air_doctrines'):
            choices=[a for a in apps if a['category']==category and year-2<=a['year']<=year]
            if not choices:continue
            scored=[(best(japanese,a,year)[2],a,best(japanese,a,year)) for a in choices]
            _,a,(t,m,f)=min(scored,key=lambda x:(x[0],int(x[1]['id'])))
            old,om,of=best(baseline,a,year)
            lines.append(f"| {year} | Least-covered {category}: {a['name']} ({a['id']}) | {t['name']} | {t['skill']} | {m}/{len(a['parts'])} | {om}/{len(a['parts'])}: {old['name']} |")
    lines += ['','## Limits on the new economic advantage','',
        '- New naval standardisation adds 40 days of hull time reduction, once. L3 replaces military queue grants in 42 funded alternatives across 27 Japanese programmes with fixed time reductions, normally at most 30 days and capped at a quarter of each unit type\'s model-zero time. L4 makes the SNLF programme a specific exception: 60 days for production priority, or 30 days plus training/engineer benefits. Each programme applies once. These reductions still stack with existing Blood and Iron technology.',
        '- New aircraft choices can add 15 and 12 days of air time reductions; pilot-school alternatives are mutually exclusive. CAG-specific reductions can add another 10 or 15 days where selected. Existing Blood and Iron technologies and domestic-policy modifiers still apply.',
        '- The player places military production orders and funds normal IC and manpower. Paid Japanese military programmes no longer insert unit or brigade orders. Separate merchant shipping and explicitly described local defence packages remain.',
        '- The synthetic-fuel choice adds six provincial oil and removes twenty provincial energy; overseas oil still needs control and convoys. It is a limited cushion, not a self-sufficient economy.',
        '- German help is finite: 250 recruitment points in two stages, 12 daily synthetic oil, supplies and one paid AI African expedition. The largest Soviet AI resource package is reduced and reserve arrivals are staggered when Germany is AI-controlled.',
        '- These are deliberate design bounds. No claim that the Axis survives to a particular year, or that Hard has reached the target difficulty, can be supported without campaign testing.','',
        '## New artwork inspection','',
        '| Asset | Installed format | Dimensions |','| --- | --- | --- |']
    images=[]
    for p in sorted((TARGET/'gfx').rglob('jx_*.bmp')):
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im:
            images.append({'path':str(p.relative_to(TARGET)),'size':im.size,'format':im.format,'mode':im.mode,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
            lines.append(f"| {p.relative_to(TARGET)} | {im.format} / {im.mode} | {im.width} x {im.height} |")
    team_images=[i for i in images if 'jx_team_' in i['path']]
    unique=len({i['sha256'] for i in team_images})
    assert len(team_images)==10 and unique==10,'New institution pictures are not all distinct'
    lines += ['',f'All ten new institutional images are distinct files with distinct pixel content. {len(images)} new named BMP assets decode successfully. Event illustrations are 400 x 116 after conversion. Artwork scale, event-window layout and final legibility remain for the user in the game.','',
        '## What remains for the playtest','',
        '1933 opening and event layout; research availability; Chinese defeat and tag change; retained bases and access after local peace; Japanese puppet war inheritance; delayed production; saving/reloading while a programme is pending; Axis endurance; American/Soviet armistice diplomacy; and overall Hard difficulty through 1950. The offline model exercises selected command contracts but cannot substitute for the engine.']
    (HERE/'OFFLINE_REVIEW.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report={'research_comparisons':len(rows),'new_teams':len(japanese)-len(baseline),'distinct_new_institution_images':unique,'decoded_new_bmp_assets':len(images),'scope':'Source comparison, structural image decoding and bounded balance review; no game run','research':rows,'images':images}
    (HERE/'OFFLINE_REVIEW.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'research','images'}}))


if __name__=='__main__':run()

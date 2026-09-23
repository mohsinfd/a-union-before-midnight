"""Build/install the new-game roster delta on top of installed BALANCE1."""
from collections import Counter
from pathlib import Path
import argparse
import json
import re
import build_balance1 as b
import aubm_roster1 as r
from dh_save_spans import parse, replace, walk, Node

ROOT=b.ROOT;BUILD=ROOT/'build/roster1';VERSION='27-ROSTER1'

def portrait_exists(mod,name):
    # DH falls back to the base game's gfx tree for inherited portraits.
    return any((root/'gfx/interface/pics'/(name+'.bmp')).exists() for root in (mod,mod.parents[1]))

def snapshot(mod):
    manifest=BUILD/'baseline.json'
    if manifest.exists():
        info=json.loads(manifest.read_text())
        if str(mod.resolve()).lower()!=info['installation'].lower():raise ValueError('Wrong roster installation')
        out={}
        for p,h in info['hashes'].items():
            data=b.safe(BUILD/'baseline',p).read_bytes()
            if b.sha(data)!=h:raise ValueError('Roster snapshot changed '+p)
            out[p]=data.decode('latin1')
        return out
    receipt=mod/'AUBM_BALANCE1_INSTALL_RECEIPT.json'
    if not receipt.exists():raise ValueError('Install BALANCE1 first')
    previous=json.loads(receipt.read_text())
    for p,h in previous['files'].items():
        if b.sha((mod/p).read_bytes())!=h:raise ValueError('BALANCE1 live file changed: '+p)
    out=b.collect(mod)
    for p in (r.MINISTERS,r.PERSONALITIES,r.LEADERS,'config/tech_names.csv'):
        out[p]=(mod/p).read_bytes().decode('latin1')
    for p in (mod/'db/tech').glob('*_tech.txt'):out[p.relative_to(mod).as_posix()]=p.read_bytes().decode('latin1')
    for p,t in out.items():
        dst=b.safe(BUILD/'baseline',p);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(t.encode('latin1'))
    b.dump(manifest,dict(installation=str(mod.resolve()),requires='27-BALANCE1',hashes={p:b.sha(t.encode('latin1')) for p,t in out.items()}))
    return out

def identify(files):
    out=dict(files);p='scenarios/1933.eug';text=out[p]
    f=parse(text).get('header').field('name')
    out[p]=replace(text,[(f.value_start,f.end,'"India 1933 - 27-ROSTER1 [NEW GAME PLAYTEST]"')])
    p='config/text.csv'
    out[p],count=re.subn(r'(?m)^(FEMAINBTN_SINGLE;)[^;]*;',lambda m:m[1]+'\xa7777 PLAY '+VERSION+';',out[p])
    if count!=1:raise ValueError('Menu version line missing')
    p='db/events/india_v3/00_bootstrap.txt';text=out[p];edits=[]
    for e in parse(text).all('event'):
        if e.get('id')!='9270000':continue
        for key,val in [('name','AUBM 27-ROSTER1 - New Campaign'),('desc','ROSTER1 includes BALANCE1. Cabinet duplicates are consolidated; new rivals offer different policies. Commanders have distinct battlefield roles. Research teams specialise in different weapons and doctrines. Start a new campaign: existing saves are not migrated. Automated checks pass; native campaign testing is still needed.')]:
            f=e.field(key);edits.append((f.value_start,f.end,json.dumps(val)))
    if len(edits)!=2:raise ValueError('Opening identification missing')
    out[p]=replace(text,edits)
    return out

def index_events(files):
    lookup={p.lower():p for p in files};result={}
    for rel in b.registered(files):
        for e in parse(files[lookup[rel]]).all('event'):
            eid=int(e.get('id'))
            if eid in result:raise ValueError('Duplicate event '+str(eid))
            result[eid]=e
    return result

def validate(base,out,mod):
    errors=[];warnings=[]
    ms=r.rows(out[r.MINISTERS]);mi={int(row[0]):row for row in ms}
    if len(mi)!=len(ms):errors.append('Duplicate minister IDs')
    if set(mi)&set(r.ALIASES):errors.append('Removed cabinet aliases survive')
    names=Counter((row[1],row[2].lower()) for row in ms)
    if any(v>1 for v in names.values()):errors.append('Repeated person in same cabinet post')
    ps=parse(out[r.PERSONALITIES]).all('minister')
    personalities={n.get('trait').lower():n for n in ps}
    if len(personalities)!=len(ps):errors.append('Duplicate personality names')
    if len({n.get('id') for n in ps})!=len(ps):errors.append('Duplicate personality IDs')
    office_positions={'Head of State':'headofstate','Head of Government':'headofgovernment','Foreign Minister':'foreignminister','Minister of Armament':'armamentminister','Minister of Security':'ministerofsecurity','Head of Military Intelligence':'ministerofintelligence','Chief of Staff':'chiefofstaff','Chief of Army':'chiefofarmy','Chief of Navy':'chiefofnavy','Chief of Air Force':'chiefofair'}
    for row in ms:
        trait=personalities.get(row[7].lower())
        if trait is None:errors.append('Unknown minister personality '+row[7]);continue
        if trait.get('position','all').lower() not in ('all',office_positions[row[1]]):errors.append('Personality wrong office '+str(row[:3]))
    changed={p:t for p,t in out.items() if base.get(p)!=t}
    for p,t in changed.items():
        if p not in (r.MINISTERS,r.PERSONALITIES,r.LEADERS,r.TEAMS,'config/text.csv','scenarios/1933.eug') and not p.startswith('db/events/'):
            errors.append('Out-of-scope roster write '+p)
        if p.endswith(('.eug','.txt')):parse(t)
    events=index_events(out);original=index_events(base)
    if events.keys()!=original.keys():errors.append('Roster patch unexpectedly adds/removes events')
    for eid,e in events.items():
        for n in walk(e):
            typ=n.get('type')
            if typ in set(r.OFFICES)|{'sleepminister','wakeminister'}:
                value=n.get('which')
                if value and value.isdigit():
                    i=int(value)
                    if i in r.ALIASES:errors.append(f'Event{eid} retains minister alias{i}')
                    if 250000<=i<252000:
                        if i not in mi:errors.append(f'Event{eid} missing Indian minister{i}')
                        elif typ in r.OFFICES and r.OFFICES[typ]!=mi[i][1]:errors.append(f'Event{eid} wrong minister post{i}')
    # Candidate/portrait and component validity, without inventing new assets.
    new_min_ids={int(row[0]) for row in r.NEW_MINISTERS}
    for row in ms:
        if int(row[0]) in new_min_ids|set(r.MIN_UPDATES):
            if not portrait_exists(mod,row[9]):errors.append('Missing minister portrait '+row[9])
    ts=r.rows(out[r.TEAMS]);ti={int(row[0]):row for row in ts}
    if len(ti)!=len(ts):errors.append('Duplicate team IDs')
    valid_specs={c.get('type').lower() for p,t in out.items() if p.endswith('_tech.txt') for n in walk(parse(t)) for c in n.all('component')}
    for row in ts:
        if len(row)!=39:errors.append('Malformed team row '+row[0])
        spec=[x for x in row[6:-1] if x]
        if len(spec)!=len(set(spec)):errors.append('Duplicate team specialty '+row[0])
        if set(spec)-valid_specs:errors.append('Unknown research component '+str(set(spec)-valid_specs))
        if not portrait_exists(mod,row[2]):errors.append('Missing research portrait '+row[2])
    old_leaders={row.split(';')[1]:row.split(';') for row in base[r.LEADERS].splitlines()[1:] if row and not row.startswith('#')}
    new_leaders={row.split(';')[1]:row.split(';') for row in out[r.LEADERS].splitlines()[1:] if row and not row.startswith('#')}
    if old_leaders.keys()!=new_leaders.keys():errors.append('Commander ID set changed')
    for eid,row in new_leaders.items():
        for col in (3,4,5,6,7,8,10,11,12,13,14,15,16,17):
            if row[col]!=old_leaders[eid][col]:errors.append('Unexpected rank/skill/date/portrait change '+eid)
        if int(eid) in r.LEADER_ROLES:
            typ=int(row[13]);mask=int(row[9])
            allowed=(1|2|4|8|16|32|64|128|256|512|sum(1<<i for i in range(18,31))) if typ==0 else (512|1024|2048|4096|8192 if typ==1 else 512|4096|8192|16384|32768|65536|131072)
            if mask&~allowed:errors.append('Invalid branch trait '+eid)
            if mask.bit_count()>3:errors.append('Excessive spotlight trait stack '+eid)
    # New IDs must not clash with other countries within their own namespaces.
    for folder,ids,own in [('db/ministers',new_min_ids,'ministers_ind.csv'),('db/tech/teams',set(r.NEW_TEAMS),'teams_ind.csv')]:
        for f in (mod/folder).glob('*.csv'):
            if f.name.lower()==own:continue
            present={int(row[0]) for row in r.rows(f.read_bytes().decode('latin1'))}
            if ids&present:errors.append('Roster ID collision with '+str(f))
    return dict(passed=not errors,errors=errors,warnings=warnings,version=VERSION,requires='27-BALANCE1',registered_events=len(events),delta_files=len(changed),ministers=len(ms),teams=len(ts),leaders=len(new_leaders),native_playtested=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--install',action='store_true');ap.add_argument('--mod',type=Path,default=b.DEFAULT);args=ap.parse_args()
    base=snapshot(args.mod);out,changes=r.transform(base);out=identify(out)
    again,_=r.transform(out)
    if identify(again)!=out:raise ValueError('Roster composition is not idempotent')
    report=validate(base,out,args.mod)
    b.dump(BUILD/'validation.json',report);b.dump(BUILD/'changes.json',changes)
    before=r.research_audit(base,base[r.TEAMS]);after=r.research_audit(out,out[r.TEAMS])
    b.dump(BUILD/'research-before.json',before);b.dump(BUILD/'research-after.json',after)
    for p,t in out.items():
        if base.get(p)==t:continue
        dest=b.safe(BUILD/'delta',p);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(t.encode('latin1'))
    b.dump(BUILD/'manifest.json',dict(version=VERSION,files={p:b.sha(t.encode('latin1')) for p,t in out.items() if base.get(p)!=t}))
    print(json.dumps(report,indent=2))
    if not report['passed']:raise SystemExit(1)
    if args.install:
        # Reuse the tested hash-guarded, save-preserving transaction, but give
        # this independent delta its own receipt and backup namespace.
        old_build,old_version=b.BUILD,b.VERSION
        b.BUILD,b.VERSION=BUILD,VERSION
        try:receipt=b.install(args.mod,base,out,report,receipt_name='AUBM_ROSTER1_INSTALL_RECEIPT.json')
        finally:b.BUILD,b.VERSION=old_build,old_version
        print('Installed '+VERSION+'; '+str(len(receipt['files']))+' files; saves unchanged; backup '+receipt['backup'])
    else:print('Staged only; no live files changed.')

if __name__=='__main__':main()

"""Snapshot, compose, validate and optionally install the BALANCE1 delta.

Never builds from the stale authored overlay. Only registered installed events,
AI files and explicit version strings may be installed. No save/art modifications.
Baseline is immutable; installation is hash-guarded and backed up transactionally.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from dh_save_spans import parse, replace, walk, Node
import aubm_balance1_economy as economy
import aubm_balance1_playtest as playtest
import aubm_balance1_world_ai as world

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1')
BUILD=ROOT/'build/balance1'
VERSION='27-BALANCE1'
TITLE='India 1933 - 27-BALANCE1 [NEW GAME PLAYTEST]'

def sha(data):return hashlib.sha256(data).hexdigest()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
def safe(root,rel):
    p=(root/rel).resolve()
    if not p.is_relative_to(root.resolve()) or p==root.resolve():raise ValueError('Unsafe relative path: '+rel)
    return p

def registered(files):
    refs=[]
    for p in ('scenarios/1933.eug','db/events.txt'):
        refs.extend(str(v).replace('\\','/') for v in parse(files[p]).all('event'))
    return list(dict.fromkeys(x.lower() for x in refs))

def repair_stock_syntax(files):
    """Retain the installed no-minister-change behaviour; fix the stray brace.

    The donor once appointed minister50336 here, but the installed command was
    removed along with its action opener. Do not guess that removal's intent.
    """
    out=dict(files);p='db/events/ai/ai_ministers.txt';t=out[p]
    marker='# AUBM_BALANCE1_STOCK_SYNTAX'
    if marker in t:return out
    pattern=r'(event\s*=\s*\{\s*id\s*=\s*5200093\b.*?deathdate\s*=\s*\{[^}]*\}\s*)\}(\s*\})'
    matches=list(re.finditer(pattern,t,re.S))
    if len(matches)!=1:raise ValueError('Unexpected malformed minister baseline')
    m=matches[0]
    out[p]=t[:m.start()]+m[1]+marker+'\n action_a = { command = { } }'+m[2]+t[m.end():]
    parse(out[p])
    return out

def collect(mod):
    paths={'scenarios/1933.eug','db/events.txt','config/text.csv','db/tech/teams/teams_ind.csv','scenarios/1933/british raj.inc'}
    basic={p:(mod/p).read_bytes().decode('latin1') for p in ('scenarios/1933.eug','db/events.txt')}
    paths.update(registered(basic))
    for f in (mod/'ai').rglob('*.ai'):paths.add(f.relative_to(mod).as_posix())
    # Include scenario ownership and model inputs for reproducible validation.
    for f in (mod/'scenarios/1933').glob('*.inc'):paths.add(f.relative_to(mod).as_posix())
    for folder in ('db/units/divisions','db/units/brigades'):
        for f in (mod/folder).glob('*.txt'):paths.add(f.relative_to(mod).as_posix())
    result={}
    for p in sorted(paths):
        key=p.lower() if p.lower().startswith('db/events/ai/') else p
        result[key]=safe(mod,p).read_bytes().decode('latin1')
    return result

def snapshot(mod):
    manifest=BUILD/'baseline.json'
    if manifest.exists():
        info=json.loads(manifest.read_text())
        if str(mod.resolve()).lower()!=info['installation'].lower():raise ValueError('Baseline belongs to another installation')
        files={}
        for p,h in info['hashes'].items():
            data=safe(BUILD/'baseline',p).read_bytes()
            if sha(data)!=h:raise ValueError('Immutable baseline changed: '+p)
            files[p]=data.decode('latin1')
        return files
    files=collect(mod)
    for p,t in files.items():
        dest=safe(BUILD/'baseline',p);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(t.encode('latin1'))
    dump(manifest,dict(installation=str(mod.resolve()),created=datetime.now(timezone.utc).isoformat(),hashes={p:sha(t.encode('latin1')) for p,t in files.items()}))
    return files

def identify(files):
    out=dict(files)
    p='scenarios/1933.eug';t=out[p];f=parse(t).get('header').field('name')
    out[p]=replace(t,[(f.value_start,f.end,json.dumps(TITLE))])
    found=0
    for p,t in files.items():
        if not p.startswith('db/events/india_v3/'):continue
        edits=[]
        for e in parse(t).all('event'):
            if e.get('id')!='9270000':continue
            found+=1
            for k,v in [('name','AUBM 27-BALANCE1 - New Campaign'),('desc','BALANCE1: stronger resource production, naval catch-up with a smaller wartime discount, revised political and military choices, and more responsive enemy AI. Start a new campaign. Your old saves are not migrated. Scripts have passed automated checks; native campaign balance and popup rendering still need playtesting.')]:
                f=e.field(k);edits.append((f.value_start,f.end,json.dumps(v)))
        if edits:out[p]=replace(t,edits)
    if found!=1:raise ValueError('Opening version event missing or duplicated')
    p='config/text.csv';lines=out[p].splitlines(keepends=True);count=0
    for i,line in enumerate(lines):
        if line.startswith('FEMAINBTN_SINGLE;'):
            cells=line.split(';');cells[1]='\xa7777 PLAY '+VERSION;lines[i]=';'.join(cells);count+=1
    if count!=1:raise ValueError('Main-menu version label missing or duplicated')
    out[p]=''.join(lines)
    return out

def validation(base,out,mod):
    lookup={p.lower():p for p in out};refs=registered(out)
    event_ids={};old_ids={};events={};warnings=[];errors=[]
    for source,index in ((repair_stock_syntax(base),old_ids),(out,event_ids)):
        keys={p.lower():p for p in source}
        for ref in registered(source):
            if ref not in keys:errors.append('Missing registered script: '+ref);continue
            p=keys[ref]
            for e in parse(source[p]).all('event'):
                eid=int(e.get('id'));index.setdefault(eid,[]).append(p)
                if index is event_ids:events[eid]=e
    for eid,paths in event_ids.items():
        if len(paths)>1:
            if len(old_ids.get(eid,[]))!=len(paths):errors.append(f'New duplicate event {eid}: {paths}')
            else:warnings.append(f'Unchanged inherited duplicate event {eid}: {paths}')
    changed={p:t for p,t in out.items() if base.get(p)!=t}
    for p,t in changed.items():
        if p.endswith(('.txt','.ai','.eug')):parse(t)
        if not (p.startswith(('db/events/','ai/')) or p in ('db/events.txt','scenarios/1933.eug','config/text.csv')):
            errors.append('Out-of-scope install target: '+p)
        if p.startswith('db/events/'):
            for e in parse(t).all('event'):
                for n in walk(e):
                    for c in n.all('command'):
                        if not isinstance(c,Node):continue
                        typ=c.get('type')
                        if typ=='ai':
                            rel='ai/'+c.get('which').replace('\\','/')
                            if rel.lower() not in lookup and not safe(mod,rel).exists():errors.append('Missing AI: '+rel)
    owned=set(economy.PLANS)|{9271111,9271112,9297180,9297181,9297182,9270000}|set().union(*playtest.PATH_IDS.values())|economy.NEW_EVENT_IDS|playtest.NEW_IDS
    owned|=set(range(9318000,9318014))|set(range(9318020,9318025))
    for eid in owned:
        e=events.get(eid)
        if e is None:errors.append('Unregistered changed event '+str(eid));continue
        for k in ('picture','decision_picture'):
            pic=e.get(k)
            if pic and not (mod/'gfx/events_pics'/(pic+'.bmp')).exists():errors.append(f'Missing {eid} {k}: {pic}')
        for k in ('desc','decision_desc'):
            if len(e.get(k,''))>520:errors.append(f'{eid}/{k} over presentation budget')
        for af in economy.actions(e):
            if len(af.value.get('name',''))>100:errors.append(f'{eid} overlong option label')
            for c in af.value.all('command'):
                if c.get('type') in ('event','trigger') and int(c.get('which')) not in event_ids:errors.append(f'{eid} missing event target {c.get("which")}')
    # Province IDs used by this patch must be real map records, not guessed IDs.
    for eid in owned:
        if eid not in events:continue
        for n in walk(events[eid]):
            for c in n.all('command'):
                if c.get('type')=='add_division':
                    unit=c.get('value');p='db/units/divisions/'+unit+'.txt'
                    if p not in out:errors.append('Missing unit definition '+str(unit));continue
                    model=int(c.get('when','-1'))
                    if model>=len(parse(out[p]).all('model')):errors.append(f'{eid}: nonexistent {unit} model {model}')
    return dict(passed=not errors,registered_events=len(event_ids),registered_files=len(refs),changed_files=len(changed),errors=errors,warnings=warnings,native_playtested=False)

def saves(mod):
    folder=mod/'scenarios/save games'
    return {p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file()} if folder.exists() else {}

def install(mod,base,out,report,receipt_name='AUBM_BALANCE1_INSTALL_RECEIPT.json'):
    if not report['passed']:raise ValueError('Cannot install failed validation')
    running=subprocess.run(['powershell','-NoProfile','-Command',"Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^Darkest.?Hour$' } | Select-Object -ExpandProperty Id"],capture_output=True,text=True,check=True)
    if running.stdout.strip():raise ValueError('Close Darkest Hour before installing; nothing changed')
    delta={p:t.encode('latin1') for p,t in out.items() if base.get(p)!=t}
    for p,data in delta.items():
        live=safe(mod,p);old=base.get(p)
        if old is None and live.exists():raise ValueError('New path already exists: '+p)
        if old is not None and (not live.exists() or live.read_bytes()!=old.encode('latin1')):raise ValueError('Live baseline changed; refusing overwrite: '+p)
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S');backup=BUILD/'backups'/stamp
    before=saves(mod);written=[]
    # Complete all backups before changing the first game file.
    for p in delta:
        if p in base:
            dst=safe(backup,p);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(base[p].encode('latin1'))
    dump(backup/'rollback.json',dict(installation=str(mod),existing=[p for p in delta if p in base],new=[p for p in delta if p not in base]))
    try:
        for p,data in delta.items():
            dest=safe(mod,p);dest.parent.mkdir(parents=True,exist_ok=True);written.append(p);dest.write_bytes(data)
            if dest.read_bytes()!=data:raise ValueError('Post-write mismatch '+p)
        if saves(mod)!=before:raise ValueError('Save fingerprint changed during installation')
    except Exception:
        for p in reversed(written):
            dest=safe(mod,p)
            if p in base:dest.write_bytes(base[p].encode('latin1'))
            elif dest.exists():dest.unlink()
        raise
    receipt=dict(version=VERSION,installation=str(mod),backup=str(backup),installed=datetime.now(timezone.utc).isoformat(),files={p:sha(data) for p,data in delta.items()},saves_unchanged=True,save_file_count=len(before),native_playtested=False,validation=report)
    dump(BUILD/'install-receipt.json',receipt)
    dump(safe(mod,receipt_name),receipt)
    return receipt

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mod',type=Path,default=DEFAULT);ap.add_argument('--install',action='store_true');args=ap.parse_args()
    base=snapshot(args.mod);out=repair_stock_syntax(base);records={}
    for name,module in [('world_ai',world),('playtest',playtest),('economy',economy)]:out,records[name]=module.transform(out)
    out=identify(out)
    # Full composition, not only each independent module, must be repeat-safe.
    repeat=out
    for module in (world,playtest,economy):repeat,_=module.transform(repeat)
    repeat=identify(repeat)
    if repeat!=out:raise ValueError('Combined transform is not idempotent')
    report=validation(base,out,args.mod)
    dump(BUILD/'validation.json',report);dump(BUILD/'changes.json',records)
    for p,t in out.items():
        if base.get(p)==t:continue
        dst=safe(BUILD/'delta',p);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(t.encode('latin1'))
    dump(BUILD/'manifest.json',dict(version=VERSION,files={p:sha(t.encode('latin1')) for p,t in out.items() if base.get(p)!=t}))
    print(json.dumps(report,indent=2))
    if not report['passed']:raise SystemExit(1)
    if args.install:
        receipt=install(args.mod,base,out,report)
        print('Installed '+VERSION+'; '+str(len(receipt['files']))+' files; saves unchanged; backup '+receipt['backup'])
    else:print('Staged only; live installation untouched.')

if __name__=='__main__':main()

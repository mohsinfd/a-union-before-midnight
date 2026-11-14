"""Final R15 installed/preservation audit; no game execution."""
import hashlib,json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import build as b
import r15_common as common
import r15_enemy as enemy


def signature(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()


def run():
    b.prepare_catalog()
    names=('r15_common_review.py','r15_enemy_review.py','r15_recovery_review.py','r15_strategy_review.py','r15_cost_review.py')
    def check(name):
        r=subprocess.run([sys.executable,str(b.HERE/name)],cwd=b.HERE,capture_output=True,text=True)
        return dict(script=name,passed=r.returncode==0,output=r.stdout+r.stderr)
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(check,names))
    actual={};duplicates=[]
    for module in {e.module for e in b.EVENTS}:
        for node in b.getall(b.parse(b.read(b.TARGET/'db/events/japan_rising'/(module+'.txt'))),'event'):
            identity=int(b.get(node,'id'))
            if identity in actual:duplicates.append(identity)
            actual[identity]=node
    expected={e.id:b.get(b.parse(b.compiled_event(e)),'event') for e in b.EVENTS}
    parity=[identity for identity,node in expected.items() if actual.get(identity)!=node]
    baseline=json.loads((b.HERE/'R15_BASELINE_EVENT_SIGNATURES.json').read_text(encoding='utf-8'))
    ids={e.key:e.id for e in b.EVENTS}
    legacy=[k for k,v in baseline.items() if ids.get(k)!=v['id'] or signature(actual.get(v['id']))!=v['sha256']]
    english={r.split(';')[0]:r.split(';')[1] for r in b.read(b.TARGET/'config/mods.csv').splitlines() if ';' in r and not r.startswith('#')}
    old=json.loads((b.HERE/'R15_BASELINE_ENGLISH_HASHES.json').read_text(encoding='utf-8'))
    copy_changed=[k for k,v in old.items() if hashlib.sha256(english.get(k,'').encode('utf-8')).hexdigest()!=v]
    gates=[(len(a.gate),e.key) for e in b.EVENTS for a in e.actions if a.name]
    largest=max(gates);size=(b.HERE/'events.json').stat().st_size
    ai=[]
    for row in enemy.REACTIONS:
        p=b.TARGET/'ai/jx'/('r15_'+row['key']+'.ai');node=b.parse(b.read(p))
        assert len(node)==1 and node[0][0]==row['block']
        table='target' if row['block']=='invasion' else 'province_priorities'
        assert [k for k,v in node[0][1]]==[table]
        values=dict(b.get(node[0][1],table))
        assert all(float(values[str(province)])==value for province,value in row['priorities'].items())
        ai.append(str(p.relative_to(b.TARGET)))
    report=dict(version=b.VERSION,passed=all(r['passed'] for r in results) and not duplicates and not parity and not legacy and not copy_changed and largest[0]<3000 and size<60*1024*1024,
        events=len(b.EVENTS),decisions=sum(e.decision for e in b.EVENTS),new_manual_choices=list(common.REPORT),
        preserved_r14_1_ids=len(baseline),legacy_script_changes=legacy,legacy_english_changes=copy_changed,
        event_duplicates=duplicates,installed_mismatches=parity,largest_named_gate=largest,catalogue_bytes=size,
        installed_ai_plans=ai,suites=results,game_run=False,save_edits=False,
        source_spec_sha256=(b.HERE/'SPEC_SHA256.txt').read_text().strip(),
        limits='Offline evidence only. Real enemy fleet grouping/invasion execution, engine convoy routing, rendered tooltips and long-campaign Hard balance remain player tests. Native AI switches can replace a priority plan.')
    (b.HERE/'R15_COLD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('suites','limits')},indent=2))
    for row in results:print(row['script'],'PASS' if row['passed'] else 'FAIL',flush=True)
    return report['passed']


if __name__=='__main__':raise SystemExit(not run())

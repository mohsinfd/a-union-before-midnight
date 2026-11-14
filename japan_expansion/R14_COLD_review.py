"""Final installed R14 check with fresh, independently written scenario suites."""
import hashlib,json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
import build as b


def run():
    b.prepare_catalog()
    scripts=('r14_china_review.py','r14_peace_review.py','r14_afterwar_review.py',
             'r14_balance_review.py','US_CAMPAIGN_review.py','ENDURANCE_review.py','r14_construction_review.py')
    def check(name):
        result=subprocess.run([sys.executable,str(b.HERE/name)],cwd=b.HERE,capture_output=True,text=True)
        return dict(script=name,passed=result.returncode==0,output=result.stdout+result.stderr)
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(check,scripts))
    mismatches=[]
    for module in {e.module for e in b.EVENTS}:
        actual={b.get(n,'id'):n for n in b.getall(b.parse(b.read(b.TARGET/'db/events/japan_rising'/(module+'.txt'))),'event')}
        for e in (e for e in b.EVENTS if e.module==module):
            if actual.get(str(e.id))!=b.get(b.parse(b.compiled_event(e)),'event'):mismatches.append(e.key)
    baseline=json.loads((b.HERE/'R14_BASELINE_IDS.json').read_text(encoding='utf-8'))
    now={e.key:e.id for e in b.EVENTS}
    retained=all(now.get(k)==v for k,v in baseline.items())
    gate_sizes=[(len(a.gate),e.key) for e in b.EVENTS for a in e.actions if a.name]
    maximum=max(gate_sizes)
    catalogue_bytes=(b.HERE/'events.json').stat().st_size
    report=dict(version=b.VERSION,passed=all(r['passed'] for r in results) and not mismatches and retained and maximum[0]<3000 and catalogue_bytes<50*1024*1024,
        game_executed=False,save_edits=False,events=len(b.EVENTS),registered_decisions=sum(e.decision for e in b.EVENTS),
        active_decisions=sum(e.decision and e.gate!='ai = yes ai = no' for e in b.EVENTS),
        original_ids_preserved=retained,original_id_count=len(baseline),installed_mismatches=mismatches,
        catalogue_bytes=catalogue_bytes,
        largest_named_action_gate={'characters':maximum[0],'event':maximum[1]},
        source_spec_sha256=(b.HERE/'SPEC_SHA256.txt').read_text().strip(),suites=results,
        cross_review='China, peace and aftermath authors reviewed each other. Found and repaired cached selections bypassing gates, renewed-war treaty renewal, invalid construction sites and missing partner-war guards. Root checked installed parity, production math and text. Economic reviewer found and corrected stale Matsu copy. Expanded coalition conditions were replaced after root measured unsafe tooltip lengths.',
        limits='Offline evidence only. Startup, actual UI rendering, engine AI regrouping, Hard combat balance, convoy assignment and long-campaign stability require player testing. No game or launcher was run.')
    (b.HERE/'R14_COLD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('suites','cross_review','limits')},indent=2))
    for r in results:print(r['script'], 'PASS' if r['passed'] else 'FAIL',flush=True)
    return report['passed']


if __name__=='__main__':raise SystemExit(not run())

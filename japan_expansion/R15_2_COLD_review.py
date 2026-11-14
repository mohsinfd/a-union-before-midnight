"""Raw-text/native-format and preservation audit for the R15.2 repair."""
import gzip,hashlib,json,re,subprocess,sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import build as b
import purchase_reliability as p

SUITES=('purchase_reliability_review.py','purchase_save_review.py','timer_reliability_review.py',
        'PREWAR_review.py','REGIONAL_CONTENT_review.py','r15_recovery_review.py',
        'r15_strategy_review.py','r15_enemy_review.py','r14_afterwar_review.py','r14_peace_review.py')


def run_suites():
    def check(name):
        r=subprocess.run([sys.executable,str(b.HERE/name)],cwd=b.HERE,capture_output=True,text=True)
        return dict(script=name,passed=r.returncode==0,tail=(r.stdout+r.stderr)[-1600:])
    results=list(ThreadPoolExecutor(max_workers=3).map(check,SUITES))
    (b.HERE/'R15_2_REGRESSION_RESULTS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')


def run():
    b.prepare_catalog()
    if '--run-suites' in sys.argv:run_suites()
    old=json.loads(gzip.decompress((b.HERE/'R15_1_BASELINE_EVENTS.json.gz').read_bytes()))
    current=json.loads((b.HERE/'events.json').read_text(encoding='utf-8'));by={e['key']:e for e in current}
    contract_choices={(r['event'],r['choice']) for r in p.REPORT['contracts']}
    callback_changes=0;policy_changes=[]
    suffix=' NOT = { flag = JX_PAID_US_IMPORTS_CLOSED embargo = { country = USA country = JAP value = 1 } embargo = { country = JAP country = USA value = 1 } }'
    for prior in old:
        e=by[prior['key']];assert e['id']==prior['id'],e['key']
        for name in ('country','gate','ready','year','decision','persistent','triggered','module','offset','start_month','start_day'):
            assert e[name]==prior[name],(e['key'],name)
        assert len(e['actions'])==len(prior['actions'])
        for i,(a,previous) in enumerate(zip(e['actions'],prior['actions'])):
            assert a['name']==previous['name'] and a['chance']==previous['chance']
            if (e['key'],i) in contract_choices:
                assert a['gate']==previous['gate']+suffix
                commands=[c for c in a['commands'] if not re.search(r'which = JX_PAID_US_',c)]
                assert len(commands)==len(previous['commands'])
                for actual,before in zip(commands,previous['commands']):
                    n=b.parse(actual);previous_node=b.parse(before)
                    if b.get(n,'type')=='trade':
                        assert b.get(n,'value')=='1'
                        n=[(k,'0' if k=='value' else v) for k,v in n]
                    assert n==previous_node,(e['key'],i)
                policy_changes.append((e['key'],i))
            else:
                assert a['gate']==previous['gate']
                assert len(a['commands'])==len(previous['commands'])
                for actual,before in zip(a['commands'],previous['commands']):
                    if actual!=before:
                        assert b.parse(actual)==b.parse(before),(e['key'],i,actual)
                        callback_changes+=1
    assert len(current)==len(old)+1 and by['paid_us_imports_end']['id']==28603107
    # Inspect exact installed text. AST equivalence alone is insufficient:
    # the old parser accepted quoted and integer IDs as the same value.
    groups=defaultdict(list)
    dispatches=0
    for e in b.EVENTS:
        groups[e.module].append(e)
        for a in e.actions:
            for command in a.commands:
                command=b.resolve(command);b.check_native_event_target(command)
                if re.search(r'\btype\s*=\s*(event|trigger)\b',command):dispatches+=1
    registry=b.read(b.TARGET/'db/events.txt')
    module_hashes={}
    for module,events in groups.items():
        native='\n\n'.join(b.compiled_event(e) for e in events)+'\n'
        path=b.TARGET/'db/events/japan_rising'/(module+'.txt')
        assert b.read(path)==native,module
        assert registry.count('event = "db\\events\\japan_rising\\'+module+'.txt"')==1,module
        assert not re.search(r'\bwhich\s*=\s*"286\d+"',native),module
        module_hashes[module]=hashlib.sha256(path.read_bytes()).hexdigest()
    results=json.loads((b.HERE/'R15_2_REGRESSION_RESULTS.json').read_text(encoding='utf-8'))
    assert {r['script'] for r in results}==set(SUITES)
    assert all(r['passed'] for r in results),[r['script'] for r in results if not r['passed']]
    save_report=b.HERE/'R15_2_SAVE_REPAIR.json';save_checked=False
    if save_report.exists():
        r=json.loads(save_report.read_text(encoding='utf-8'))
        assert hashlib.sha256(Path(r['source']).read_bytes()).hexdigest()==r['repaired_sha256']
        assert hashlib.sha256(Path(r['load_save']).read_bytes()).hexdigest()==r['repaired_sha256']
        assert hashlib.sha256(Path(r['backup']).read_bytes()).hexdigest()==r['source_sha256']
        assert r['idempotence_passed'] and r['shipping_unchanged'] and r['pending_merchant_delivery_unchanged']
        save_checked=True
    report=dict(version=b.VERSION,passed=True,events=len(current),registered_decisions=sum(e.decision for e in b.EVENTS),
        old_event_ids_preserved=len(old),existing_bills_rewards_durations_preserved=True,
        quoted_callbacks_repaired=callback_changes,raw_native_dispatches_checked=dispatches,
        protected_import_choices=policy_changes,embargo_closure_event=28603107,
        installed_modules_matched=len(groups),installed_native_hashes=module_hashes,
        suites=results,current_save_verified=save_checked,game_run=False,
        source_spec_sha256=(b.HERE/'SPEC_SHA256.txt').read_text().strip(),
        qualification='Raw native integer tokens, saved queues, duplicate prevention and installed text checked offline. No engine launch or long-campaign test.')
    (b.HERE/'R15_2_COLD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('suites','installed_native_hashes')},indent=2))


if __name__=='__main__':run()

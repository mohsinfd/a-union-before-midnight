"""Audit the focused timer repair against the released R15 catalogue/install."""
import json,re,hashlib,gzip,sys,subprocess
import build as b
import timer_reliability as t


def run():
    b.prepare_catalog()
    if '--run-suites' in sys.argv:
        names=('timer_reliability_review.py','PREWAR_review.py','REGIONAL_CONTENT_review.py',
               'r15_recovery_review.py','r15_strategy_review.py','r15_enemy_review.py',
               'r14_afterwar_review.py','r14_peace_review.py')
        results=[]
        for name in names:
            result=subprocess.run([sys.executable,str(b.HERE/name)],cwd=b.HERE,capture_output=True,text=True)
            results.append(dict(script=name,passed=result.returncode==0,tail=(result.stdout+result.stderr)[-1400:]))
        (b.HERE/'R15_1_REGRESSION_RESULTS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    old=json.loads(gzip.decompress((b.HERE/'R15_BASELINE_EVENTS.json.gz').read_bytes()))
    current=json.loads((b.HERE/'events.json').read_text(encoding='utf-8'))
    by={e['key']:e for e in current}; idkeys={str(e['id']):e['key'] for e in current}
    pairs={(str(b.IDS[r['source']]),r['days']):r['flag'] for r in t.REPORT['pairs']}
    history=re.compile(r'event\s*=\s*\{\s*id\s*=\s*"?(\d+)"?\s+days\s*=\s*(\d+)\s*\}')
    def replace(s):return history.sub(lambda m:'flag = JX_'+pairs[(m[1],int(m[2]))],s)
    def ast(s):return b.parse(s)
    altered=[]
    for previous in old:
        e=by[previous['key']];assert e['id']==previous['id']
        assert len(e['actions'])==len(previous['actions'])
        assert ast(e['gate'])==ast(replace(previous['gate'])),e['key']
        assert ast(e['ready'])==ast(replace(previous['ready'])),e['key']
        for a,prior in zip(e['actions'],previous['actions']):
            assert a['name']==prior['name'] and a['chance']==prior['chance'],e['key']
            assert ast(a['gate'])==ast(replace(prior['gate'])),e['key']
            actual=[]
            for text in a['commands']:
                node=ast(text);kind=b.get(node,'type');which=b.get(node,'which','')
                if kind=='clrflag' and which.startswith('JX_TIME_'):continue
                if kind=='event' and idkeys.get(which,'').startswith('time_'):
                    target=by[idkeys[which]]
                    if target['key'].startswith('time_delivery_'):
                        native=b.get(ast(target['actions'][0]['commands'][-1]),'which')
                        node=[(k,native if k=='which' else v) for k,v in node]
                    else:continue
                actual.append(node)
            assert actual==[ast(replace(c)) for c in prior['commands']],e['key']
        if e!=previous:altered.append(e['key'])
    installed={}
    for module in {e.module for e in b.EVENTS}:
        for node in b.getall(b.parse(b.read(b.TARGET/'db/events/japan_rising'/(module+'.txt'))),'event'):
            ident=b.get(node,'id');assert ident not in installed;installed[ident]=node
    for e in b.EVENTS:assert installed[str(e.id)]==b.get(b.parse(b.compiled_event(e)),'event'),e.key
    assert len(installed)==len(current)
    assert not any(history.search(s) for e in current for s in [e['gate'],e['ready']]+[a['gate'] for a in e['actions']]+[c for a in e['actions'] for c in a['commands']])
    results=json.loads((b.HERE/'R15_1_REGRESSION_RESULTS.json').read_text(encoding='utf-8'))
    assert all(row['passed'] for row in results),[r['script'] for r in results if not r['passed']]
    save_record=b.HERE/'R15_1_SAVE_REPAIR.json'
    if save_record.exists():
        save=json.loads(save_record.read_text(encoding='utf-8'))
        assert hashlib.sha256(__import__('pathlib').Path(save['source']).read_bytes()).hexdigest()==save['source_sha256']
        assert hashlib.sha256(__import__('pathlib').Path(save['repaired_save']).read_bytes()).hexdigest()==save['repaired_sha256']
    report=dict(version=b.VERSION,passed=True,events=len(current),registered_decisions=128,
        original_ids_preserved=len(old),original_bills_rewards_choices_and_non_timing_gates_preserved=True,
        history_sources_repaired=len({r['source'] for r in t.REPORT['pairs']}),
        elapsed_checks_repaired=len(t.REPORT['pairs']),changed_events=altered,
        installed_native_events_matched=len(installed),suites=results,game_run=False,
        source_spec_sha256=(b.HERE/'SPEC_SHA256.txt').read_text().strip(),
        qualification='Focused offline timing/state/install checks. No running-engine test; earlier R15 cold audit missed persistent-event history behaviour.')
    (b.HERE/'R15_1_COLD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('suites','changed_events')},indent=2))


if __name__=='__main__':run()

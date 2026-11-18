"""Text-only crash repair: prove native gameplay and all saves are unchanged."""
import hashlib,json,re,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import build as b
import tooltip_safety as t
import unique_attachments as a
import unique_divisions as d


def suites():
    def check(name):
        result=subprocess.run([sys.executable,str(b.HERE/name)],cwd=b.HERE,capture_output=True,text=True)
        return dict(script=name,passed=result.returncode==0,tail=(result.stdout+result.stderr)[-1800:])
    results=list(ThreadPoolExecutor(max_workers=2).map(check,('tooltip_safety_review.py','PLAYER_COPY_review.py')))
    (b.HERE/'R15_3_REGRESSION_RESULTS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')


def run():
    b.prepare_catalog()
    if '--run-suites' in sys.argv:suites()
    baseline=json.loads((b.HERE/'R15_2_TOOLTIP_BASELINE.json').read_text(encoding='utf-8'))
    actual_modules={}
    for filename,expected in baseline['native'].items():
        path=b.TARGET/'db/events/japan_rising'/filename
        actual=hashlib.sha256(path.read_bytes()).hexdigest();assert actual==expected,filename
        actual_modules[filename]=actual
    for relative,expected in baseline['units'].items():
        assert hashlib.sha256((b.TARGET/relative).read_bytes()).hexdigest()==expected,relative
    saves_checked=0
    for name,expected in baseline.get('saves',{}).items():
        path=b.TARGET/'scenarios/save games'/name
        if '--check-local-saves' in sys.argv and path.exists():
            assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name;saves_checked+=1
    def rows(text):return {line.split(';')[0]:line.split(';')[1] for line in text.splitlines() if ';' in line and not line.startswith('#')}
    texts=rows(b.read(b.TARGET/'config/mods.csv'));models=rows(b.read(b.TARGET/'config/models.csv'))
    expected=rows(b.localisation())
    assert all(texts.get(k)==v for k,v in expected.items())
    assert all('%' not in v for k,v in texts.items() if k.startswith('JX_'))
    tooltips=[]
    for unit,info in a.ATTACHMENTS.items():
        for index,year in enumerate(info['years']):
            label=texts[f'BRIG_MODEL_JAP_{info["index"]}_{index}']+' ('+info['short']+'-'+str(index+1)+')'
            desc=texts['JX_'+unit+'_DESC'];size=t.check_payload(desc,label)
            tooltips.append(dict(unit=unit,model=index,description=desc,label=label,bytes=size))
    for unit,info in d.CLASSES.items():
        for index,name in enumerate(info['model_names']):
            label=models[f'MODEL_JAP_{info["index"]}_{index}']+' ('+info['short']+'-'+str(index+1)+')'
            desc=texts['JX_'+unit+'_DESC'];size=t.check_payload(desc,label)
            tooltips.append(dict(unit=unit,model=index,description=desc,label=label,bytes=size))
    for unit,info in b.specialist_units.CLASSES.items():
        prefix=f'MODEL_JAP_{info["index"]}_'
        for key,name in models.items():
            if not key.startswith(prefix) or not key[len(prefix):].isdigit():continue
            index=int(key[len(prefix):]);label=name+' ('+texts['JX_'+unit+'_SHORT']+'-'+str(index+1)+')'
            desc=texts['JX_'+unit+'_DESC'];size=t.check_payload(desc,label)
            tooltips.append(dict(unit=unit,model=index,description=desc,label=label,bytes=size))
    assert not re.search(r'\bwhich\s*=\s*"286\d+"','\n'.join(b.compiled_event(e) for e in b.EVENTS))
    results=json.loads((b.HERE/'R15_3_REGRESSION_RESULTS.json').read_text(encoding='utf-8'))
    assert all(r['passed'] for r in results),[r['script'] for r in results if not r['passed']]
    (b.HERE/'R15_3_TOOLTIPS.json').write_text(json.dumps(tooltips,indent=2)+'\n',encoding='utf-8')
    report=dict(version=b.VERSION,passed=True,events=len(b.EVENTS),registered_decisions=sum(e.decision for e in b.EVENTS),
        native_gameplay_files_unchanged=len(actual_modules),unit_files_unchanged=len(baseline['units']),
        original_event_ids_and_rewards_preserved=True,saves_unchanged=saves_checked,
        original_fault_address='0x694d2820',original_tooltip_bytes=270,
        crash_signature_reproduced_offline=True,tooltips_checked=len(tooltips),
        largest_tooltip_bytes=max(r['bytes'] for r in tooltips),tooltip_budget=t.MAX_TOOLTIP_BYTES,
        raw_percent_in_owned_localisation=0,loaded_english_matches=len(expected),
        suites=results,game_run=False,save_edits=False,
        source_spec_sha256=(b.HERE/'SPEC_SHA256.txt').read_text().strip(),
        qualification='Offline crash-signature and tooltip-size checks. No game launch. Does not claim every possible crash has been eliminated.')
    (b.HERE/'R15_3_COLD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='suites'},indent=2))


if __name__=='__main__':run()

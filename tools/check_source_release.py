"""Check repository source and retained art without a game installation."""
import ast,hashlib,json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
project=ROOT/'japan_expansion'
for path in [*project.glob('*.py'),* (ROOT/'tools').glob('*.py')]:
    ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
expected=set(json.loads((project/'art_inputs.json').read_text()))
for node in ast.parse((project/'build.py').read_text(encoding='utf-8')).body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ART_INPUTS' for t in node.targets):
        expected.update(ast.literal_eval(node.value))
for row in json.loads((project/'UNIQUE_ART_MANIFEST.json').read_text()):
    path=project/'art'/(row['key']+'.png');expected.add(row['key'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],row['key']
for key in expected:
    path=project/'art'/(key+'.png');assert path.is_file(),path
    with Image.open(path) as image:image.verify()
events=json.loads((project/'events.json').read_text())
audit=json.loads((project/'R14_COLD_AUDIT.json').read_text(encoding='utf-8'))
catalogue=ast.parse((project/'catalog.py').read_text(encoding='utf-8'))
version=next(ast.literal_eval(n.value) for n in catalogue.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets))
assert audit['passed'] and audit['version']==version
r15_audit=json.loads((project/'R15_COLD_AUDIT.json').read_text(encoding='utf-8'))
assert r15_audit['passed'] and r15_audit['version']==version and r15_audit['events']==audit['events']
assert len(events)==audit['events'] and len({e['id'] for e in events})==len(events)
assert sum(e['decision'] for e in events)==audit['registered_decisions']
baseline=json.loads((project/'R14_BASELINE_IDS.json').read_text(encoding='utf-8'))
current={e['key']:e['id'] for e in events}
assert all(current.get(k)==v for k,v in baseline.items())
r14_baseline=json.loads((project/'R14_PRESTART_BASELINE_IDS.json').read_text(encoding='utf-8'))
assert all(current.get(k)==v for k,v in r14_baseline.items())
r15_baseline=json.loads((project/'R15_BASELINE_IDS.json').read_text(encoding='utf-8'))
assert all(current.get(k)==v for k,v in r15_baseline.items())
assert not list(ROOT.rglob('*.eug')) and not list(ROOT.rglob('*.dmp'))
assert not (project/'local_paths.json').exists()
manifest=json.loads((ROOT/'SOURCE_RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
assert manifest['version']==audit['version']
for record in manifest['files']:
    path=ROOT/record['path'];raw=path.read_bytes()
    if path.suffix.lower() not in ('.png','.bmp','.jpg','.jpeg'):
        raw=raw.replace(b'\r\r\n',b'\n').replace(b'\r\n',b'\n')
    assert len(raw)==record['bytes'],record['path']
    assert hashlib.sha256(raw).hexdigest()==record['sha256_git_blob_bytes'],record['path']
    assert len(raw)<100*1024*1024,record['path']

print(json.dumps({'python_syntax':'PASS','retained_original_art':len(expected),'events':len(events),'game_run':False}))

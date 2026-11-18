"""Check repository source and retained art without a game installation."""
import ast,hashlib,json,re
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
native_dispatches=0
for event in events:
    for action in event['actions']:
        for command in action['commands']:
            kind=re.search(r'\btype\s*=\s*(event|trigger)\b',command)
            if not kind:continue
            target=re.search(r'\bwhich\s*=\s*(\S+)',command[kind.end():])
            assert target and re.fullmatch(r'[1-9][0-9]*',target[1]),(event['key'],command)
            assert int(target[1])<=2147483647
            native_dispatches+=1
assert hashlib.sha256((project/'events.json').read_text(encoding='utf-8').encode()).hexdigest()==(project/'SPEC_SHA256.txt').read_text().strip()
audit=json.loads((project/'R14_COLD_AUDIT.json').read_text(encoding='utf-8'))
catalogue=ast.parse((project/'catalog.py').read_text(encoding='utf-8'))
version=next(ast.literal_eval(n.value) for n in catalogue.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets))
assert audit['passed']
if version.endswith('R15.3'):
    audit=json.loads((project/'R15_3_COLD_AUDIT.json').read_text(encoding='utf-8'))
elif version.endswith('R15.2'):
    audit=json.loads((project/'R15_2_COLD_AUDIT.json').read_text(encoding='utf-8'))
elif version.endswith('R15.1'):
    audit=json.loads((project/'R15_1_COLD_AUDIT.json').read_text(encoding='utf-8'))
assert audit['version']==version
r15_audit=json.loads((project/'R15_COLD_AUDIT.json').read_text(encoding='utf-8'))
assert r15_audit['passed']
if not version.endswith(('R15.1','R15.2','R15.3')):assert r15_audit['version']==version and r15_audit['events']==audit['events']
if version.endswith('R15.3'):
    tooltip_rows=json.loads((project/'R15_3_TOOLTIPS.json').read_text(encoding='utf-8'))
    for entry in tooltip_rows:
        payload=(entry['description']+'\n'+entry['label']+'\0').encode('latin1')
        assert len(payload)==entry['bytes'] and len(payload)<=224
        assert '%' not in entry['description']+entry['label']
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
    if path.suffix.lower() not in ('.png','.bmp','.jpg','.jpeg','.gz'):
        raw=raw.replace(b'\r\r\n',b'\n').replace(b'\r\n',b'\n')
    assert len(raw)==record['bytes'],record['path']
    assert hashlib.sha256(raw).hexdigest()==record['sha256_git_blob_bytes'],record['path']
    assert len(raw)<100*1024*1024,record['path']

print(json.dumps({'python_syntax':'PASS','retained_original_art':len(expected),'events':len(events),'native_integer_dispatches':native_dispatches,'game_run':False}))

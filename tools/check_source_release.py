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
assert len(events)==1822 and len({e['id'] for e in events})==1822
assert sum(e['decision'] for e in events)==121
assert not list(ROOT.rglob('*.eug')) and not list(ROOT.rglob('*.dmp'))
assert not (project/'local_paths.json').exists()
print(json.dumps({'python_syntax':'PASS','retained_original_art':len(expected),'events':len(events),'game_run':False}))

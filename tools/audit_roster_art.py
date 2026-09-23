"""Read-only roster artwork audit; output reports, never modify game files."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MOD = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1')

def audit():
    entries = []
    specs = [('minister', 'db/ministers/ministers_ind.csv', 0, 2, 9),
             ('leader', 'db/leaders/india.csv', 1, 0, 14),
             ('team', 'db/tech/teams/teams_ind.csv', 0, 1, 2)]
    for kind, rel, idcol, namecol, piccol in specs:
        for line in (MOD / rel).read_text(encoding='latin1').splitlines():
            row = line.split(';')
            if len(row) <= piccol or not row[idcol].isdigit():
                continue
            name = row[piccol]
            path = next((p for root in [MOD, MOD.parents[1]]
                         if (p := root / 'gfx/interface/pics' / (name + '.bmp')).exists()), None)
            item = dict(kind=kind, id=int(row[idcol]), name=row[namecol], picture=name,
                        path=str(path) if path else None)
            if path:
                with Image.open(path) as im:
                    item.update(size=list(im.size), pixel_hash=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest())
            entries.append(item)
    groups = defaultdict(list)
    for e in entries:
        groups[e.get('pixel_hash', 'MISSING')].append(f"{e['kind']}:{e['id']} {e['name']}")
    report = dict(installation=str(MOD), entries=entries,
                  shared_pixels={h: v for h, v in groups.items() if len(v)>1},
                  missing=[e for e in entries if not e['path']])
    out = ROOT / 'build/art1'; out.mkdir(parents=True, exist_ok=True)
    (out / 'audit-before.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    for kind, *_ in specs:
        subset = [e for e in entries if e['kind']==kind]
        print(kind, len(subset), 'entries;', len({e.get('pixel_hash') for e in subset}), 'distinct pixel images')
    print('Missing:', len(report['missing']))
    print('Research teams:', json.dumps([e for e in entries if e['kind']=='team'], indent=2))

if __name__ == '__main__':
    audit()

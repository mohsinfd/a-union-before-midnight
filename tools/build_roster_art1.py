"""Package audited original team art, changing picture references only."""
from pathlib import Path
import argparse
import io
import json
import shutil
from PIL import Image, ImageOps, ImageDraw
import build_balance1 as b
from audit_roster_art import MOD, ROOT

BUILD = ROOT / 'build/art1'
ASSETS = ROOT / 'assets/roster-art1'
REL = 'db/tech/teams/teams_ind.csv'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--install', action='store_true')
    args = ap.parse_args()
    manifest = json.loads((ASSETS / 'manifest.json').read_text())
    receipt = json.loads((MOD / 'AUBM_ROSTER1_INSTALL_RECEIPT.json').read_text())
    original = (MOD / REL).read_bytes()
    if b.sha(original) != receipt['files'][REL]:
        raise ValueError('Live roster differs from verified ROSTER1; no overwrite')
    base = {REL: original.decode('latin1')}
    out = dict(base)
    images = {}
    for item in manifest['assets']:
        source = ASSETS / item['source']
        if not source.exists():
            shutil.copy2(item['generated_path'], source)
        with Image.open(source) as image:
            packed = ImageOps.fit(image.convert('RGB'), (96, 96), method=Image.Resampling.LANCZOS)
        buf = io.BytesIO(); packed.save(buf, format='BMP')
        data = buf.getvalue()
        assert data[:2] == b'BM' and int.from_bytes(data[28:30], 'little') == 24
        name = 'AUBM_ART1_T' + str(item['id'])
        rel = 'gfx/interface/pics/' + name + '.bmp'
        out[rel] = data.decode('latin1')
        images[item['id']] = (name, packed, data)
    assert len(images) == 4
    lines = []
    for line in base[REL].splitlines(keepends=True):
        row = line.split(';')
        if row[0].isdigit() and int(row[0]) in images:
            row[2] = images[int(row[0])][0]
        lines.append(';'.join(row))
    out[REL] = ''.join(lines)
    for old, new in zip(base[REL].splitlines(), out[REL].splitlines(), strict=True):
        a, c = old.split(';'), new.split(';')
        if a != c:
            assert int(a[0]) in images
            a[2] = c[2]
            assert a == c, 'Non-art gameplay field changed'
    hashes = []
    for line in out[REL].splitlines():
        row = line.split(';')
        if not row[0].isdigit(): continue
        rel = 'gfx/interface/pics/' + row[2] + '.bmp'
        data = out[rel].encode('latin1') if rel in out else (MOD / rel).read_bytes()
        with Image.open(io.BytesIO(data)) as im:
            assert im.size == (96, 96)
            hashes.append(b.sha(im.convert('RGB').tobytes()))
    assert len(hashes) == len(set(hashes)) == 35
    preview = Image.new('RGB', (4*220, 245), '#202020')
    draw = ImageDraw.Draw(preview)
    for index, (team, (_, im, _)) in enumerate(images.items()):
        preview.paste(im.resize((192,192), Image.Resampling.NEAREST), (index*220+14,10))
        draw.text((index*220+14,215), str(team), fill='white')
    preview.save(ASSETS / 'preview.png')
    report = dict(passed=True, team_count=35, unique_team_pixel_hashes=35,
                  new_artworks=4, gameplay_fields_unchanged=True,
                  scope='Research teams only; reserve portraits still incomplete', native_playtested=False)
    BUILD.mkdir(parents=True, exist_ok=True)
    b.dump(BUILD / 'team-validation.json', report)
    for rel, text in out.items():
        dst = b.safe(BUILD / 'delta', rel); dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(text.encode('latin1'))
    if args.install:
        b.BUILD = BUILD; b.VERSION = '27-ROSTER1 + ART1 teams'
        result = b.install(MOD, base, out, report, 'AUBM_ART1_INSTALL_RECEIPT.json')
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(report, indent=2))

if __name__ == '__main__': main()

"""Create a deterministic individual-art plan; no game files are changed."""
from pathlib import Path
import hashlib
import json
from collections import Counter
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MOD = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1')
OUT = ROOT / 'assets/roster-art2'

SHAPES = ['long narrow face and pointed chin', 'broad square jaw and flat cheek planes', 'round face and full cheeks', 'high angular cheekbones and a small chin', 'oval face and a strong cleft chin', 'wide forehead and a tapering jaw', 'slender face and a prominent rounded chin', 'heavy jaw and deep-set eyes', 'short broad face and rounded jaw', 'lean weathered face and hollow cheeks', 'long face and a broad chin', 'heart-shaped face and a narrow chin', 'rectangular face with prominent cheekbones']
NOSES = ['a broad straight nose', 'a narrow aquiline nose', 'a short rounded nose', 'a long straight nose', 'a wide nose with a slightly flattened bridge', 'a gently curved prominent nose', 'a small upturned nose']
HAIR = ['neatly side-parted straight hair', 'close-cropped curly hair', 'receding hair at both temples', 'thick wavy hair brushed back', 'a high receding hairline', 'short salt-and-pepper hair', 'a bald crown with short hair at the sides', 'dense short curls', 'closely clipped straight hair', 'silver hair swept back', 'a neat off-centre part']
FACIAL = ['clean-shaven', 'a fine pencil moustache', 'a thick straight moustache', 'a broad neatly clipped moustache', 'a short trim full beard', 'a narrow moustache with slightly downturned ends', 'a full salt-and-pepper beard', 'a small clipped moustache and otherwise clean-shaven face', 'a modest handlebar moustache']
EYES = ['heavy straight eyebrows', 'fine arched eyebrows', 'bushy eyebrows', 'widely spaced eyes and sparse eyebrows', 'deep-set eyes and thick eyebrows', 'narrow alert eyes and curved eyebrows', 'large calm eyes and straight eyebrows']
POSE = ['facing camera directly', 'head turned slightly to the left, eyes toward camera', 'head turned slightly to the right, eyes toward camera', 'almost frontal with chin slightly raised', 'almost frontal with chin slightly lowered']
UNIFORMS = {
    0: ['plain Indian army service tunic with an open collar and tie', 'Indian army officer service dress, simple closed stand collar', 'plain army field shirt with shoulder straps, no medals'],
    1: ['Indian naval officer dark double-breasted jacket, white shirt and black tie', 'Indian naval officer tropical white high-collared tunic', 'plain naval working uniform, open neck, no equipment'],
    2: ['Indian air officer service jacket with shirt and tie', 'Indian air officer plain tropical service shirt with shoulder straps', 'Indian air officer dark tunic, light shirt and narrow tie'],
}


def prompt(index, branch):
    # Mixed-radix traits are deliberately independent; no religion is inferred
    # from a roster surname and no real person's likeness is requested.
    age = 29 + ((index * 17) % 31)
    specs = [SHAPES[index % len(SHAPES)], NOSES[(index // 13 + index * 3) % len(NOSES)],
             HAIR[(index // 7 + index * 5) % len(HAIR)], FACIAL[(index // 11 + index * 2) % len(FACIAL)],
             EYES[(index // 9 + index * 4) % len(EYES)]]
    if index % 6 == 0:
        specs.append('small round wire-rim spectacles, no glare')
    elif index % 11 == 0:
        specs.append('thin oval wire-rim spectacles, no glare')
    skin = ['light-medium', 'medium', 'deep', 'medium-dark', 'dark'][index % 5]
    return (
        'Create ONE original fictional Indian male reserve officer portrait, circa 1933-1945. '
        f'Age {age}, {skin} skin tone; ' + '; '.join(specs) + '. '
        f'{UNIFORMS[branch][(index // 3) % 3]}; bare head. {POSE[index % len(POSE)]}. '
        'Natural individual character, restrained expression, believable period studio photograph, '
        'black-and-white grayscale with subtle film grain, plain medium-gray background, crisp facial contrast. '
        'Tight vertical head-and-shoulders composition, full forehead, ears and chin safely inside frame; '
        'face fills most of image and remains recognizable after reduction to a 36x50-pixel game portrait. '
        'Exactly one person and one image: no collage, no grid, no hands, no text, no border, no watermark, '
        'no modern insignia, no resemblance to a named or famous real person. '
        'This is explicitly a fictional character, not an authentic historical photograph.'
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    kept = []
    for line in (MOD / 'db/leaders/india.csv').read_text(encoding='latin1').splitlines():
        c = line.split(';')
        if len(c) < 16 or not c[1].isdigit() or not 252000 <= int(c[1]) <= 252374:
            continue
        piccol = next(i for i, value in enumerate(c) if value.startswith(('aubm_reserve_', 'aubm_c1_reserve_')))
        leader_id, branch, picture = int(c[1]), int(c[piccol - 1]), c[piccol]
        p = next((root / 'gfx/interface/pics' / f'{picture}.bmp' for root in (MOD, MOD.parents[1])
                  if (root / 'gfx/interface/pics' / f'{picture}.bmp').exists()), None)
        if p is None:
            raise FileNotFoundError(f'{leader_id}: {picture}')
        with Image.open(p) as im:
            digest = hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
        keep = digest not in seen
        seen.add(digest)
        row = dict(id=leader_id, name=c[0], branch=branch, existing_picture=picture,
                   keep=keep, prompt=None if keep else prompt(leader_id - 252000, branch))
        rows.append(row)
        if keep:
            kept.append((row, p, digest))
    assert len(rows) == 375, len(rows)
    assert len(kept) == 64, len(kept)
    assert len({r['prompt'] for r in rows if not r['keep']}) == 311
    (OUT / 'plan.json').write_text(json.dumps({'entries': rows}, indent=2), encoding='utf8')
    # This is a QA sheet assembled from existing art, not a generation shortcut.
    sheet = Image.new('RGB', (8 * 160, 8 * 232), '#dddddd')
    draw = ImageDraw.Draw(sheet)
    for i, (row, p, digest) in enumerate(kept):
        x, y = (i % 8) * 160, (i // 8) * 232
        with Image.open(p) as im:
            sheet.paste(im.convert('RGB').resize((144, 200), Image.Resampling.NEAREST), (x + 8, y))
        draw.text((x + 5, y + 203), f"{row['id']} type {row['branch']}", fill='black')
        draw.text((x + 5, y + 217), row['existing_picture'], fill='black')
    sheet.save(OUT / 'retained64-review.png')
    print(json.dumps({'total': len(rows), 'retained': len(kept), 'new': len(rows)-len(kept),
                     'new_by_branch': dict(Counter(r['branch'] for r in rows if not r['keep'])),
                     'path': str(OUT / 'plan.json')}, indent=2))


if __name__ == '__main__':
    main()

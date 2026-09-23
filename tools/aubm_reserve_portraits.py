"""Package the generated fictional-officer atlas into DH's 36x50 BMP format.

Only reserve IDs receive these portraits. Historical officers are not relabelled
with fictional faces. This is asset slicing, not generative photo editing.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
from PIL import Image, ImageOps
from dh_save_spans import parse, Node, walk, replace

ROOT=Path(__file__).resolve().parents[1]
ATLAS=ROOT/'assets/cleanup1/reserve-officers-atlas.png'
BRANCH_CELLS={0:list(range(24)),1:list(range(24,34)),2:list(range(34,48))}


def roster(raw):
    # CONTINUE1 retains its expanded reserve pool in subsequent cleanup builds.
    from aubm_continue1_portraits import ATLAS as C1_ATLAS, roster as c1_roster
    if C1_ATLAS.exists():
        return c1_roster(raw)
    counts=Counter();mapping={};lines=[]
    for line in raw.splitlines(keepends=True):
        row=line.rstrip(b'\r\n').split(b';')
        if len(row)==19 and row[1].isdigit() and 252000<=int(row[1])<=252374:
            branch=int(row[13]);cells=BRANCH_CELLS[branch]
            cell=cells[counts[branch]%len(cells)];counts[branch]+=1
            picture=f'aubm_reserve_{cell+1:02d}'
            mapping[int(row[1])]=picture
            row[14]=picture.encode('ascii')
            newline=b'\r\n' if line.endswith(b'\r\n') else b'\n'
            line=b';'.join(row)+newline
        lines.append(line)
    if len(mapping)!=375:raise ValueError('Expected the 375-officer reserve; preserve unexpected roster')
    return b''.join(lines),mapping


def migrate_pictures(raw,mapping):
    """Change existing Indian reserve picture fields only, byte-for-byte elsewhere."""
    root=parse(raw);edits=[]
    india=next(c for c in root.all('country') if c.get('tag')=='IND')
    for n in walk(india):
        ident=n.get('id')
        if not isinstance(ident,Node) or ident.get('type')!='6':continue
        eid=int(ident.get('id','-1'))
        if eid not in mapping or not n.get('picture'):continue
        f=n.field('picture')
        edits.append((f.value_start,f.end,('"'+mapping[eid]+'"').encode('ascii')))
    return replace(raw,edits),len(edits)


def build(output):
    im=Image.open(ATLAS).convert('RGB');w,h=im.size
    dest=output/'mod/gfx/interface/pics';dest.mkdir(parents=True,exist_ok=True)
    preview=Image.new('RGB',(8*108,6*150),(0,0,0))
    for n in range(48):
        col,row=n%8,n//8
        tile=im.crop((round(col*w/8),round(row*h/6),round((col+1)*w/8),round((row+1)*h/6)))
        # Preserve the cap, face and uniform; trim a little horizontally to fill
        # the portrait aspect ratio, then resize with no pixel-art substitution.
        tile=ImageOps.fit(tile,(36,50),Image.Resampling.LANCZOS,centering=(.5,.3))
        tile.save(dest/f'aubm_reserve_{n+1:02d}.bmp')
        preview.paste(tile.resize((108,150),Image.Resampling.NEAREST),(col*108,row*150))
    preview.save(output/'reserve-portraits-preview.png')
    from aubm_continue1_portraits import ATLAS as C1_ATLAS, pack as c1_pack
    if C1_ATLAS.exists():
        c1_pack(dest).save(output/'continue1-portraits-preview.png')
    raw,mapping=roster((ROOT/'mod/db/leaders/india.csv').read_bytes())
    dest=output/'mod/db/leaders/india.csv';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    manifest={'atlas_sha256':hashlib.sha256(ATLAS.read_bytes()).hexdigest(),
        'portrait_count':64 if C1_ATLAS.exists() else 48,'officers_mapped':len(mapping),'fictional_reserves_only':True,
        'dimensions':[36,50],'format':'24-bit BMP','mapping':mapping,
        'historical_officers_unchanged':True}
    (output/'portraits.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    if C1_ATLAS.exists():
        manifest['continue1_atlas_sha256']=hashlib.sha256(C1_ATLAS.read_bytes()).hexdigest()
        (output/'portraits.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(f"Packaged {manifest['portrait_count']} fictional portraits for 375 reserve officers; historical portraits unchanged.")


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'build/cleanup1')
    build(ap.parse_args().output)

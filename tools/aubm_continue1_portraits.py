"""Mechanical atlas packing and reserve-only portrait references, no generation."""
from pathlib import Path
from PIL import Image,ImageOps
from dh_save_spans import Node,parse,walk,replace

ROOT=Path(__file__).resolve().parents[1]
ATLAS=ROOT/'assets/continue1/reserve-officers-atlas.png'
OLD={0:list(range(1,25)),1:list(range(25,35)),2:list(range(35,49))}
NEW={0:list(range(9,13)),1:list(range(1,9)),2:list(range(13,17))}
def picture(branch,ordinal):
    old=['aubm_reserve_'+str(i).zfill(2) for i in OLD[branch]]
    new=['aubm_c1_reserve_'+str(i).zfill(2) for i in NEW[branch]]
    pool=[]
    # Spread new faces through the roster, not just the last batch of officers.
    for i,p in enumerate(old):
        pool.append(p)
        if i<len(new):pool.append(new[i])
    pool.extend(new[len(old):])
    return pool[ordinal%len(pool)]

def roster(raw):
    lines=[];mapping={};counts={0:0,1:0,2:0}
    for line in raw.splitlines(keepends=True):
        row=line.rstrip(b'\r\n').split(b';')
        if len(row)==19 and row[1].isdigit() and 252000<=int(row[1])<=252374:
            branch=int(row[13]);pic=picture(branch,counts[branch]);counts[branch]+=1
            mapping[int(row[1])]=pic;row[14]=pic.encode('ascii')
            end=line[len(line.rstrip(b'\r\n')):]
            line=b';'.join(row)+end
        lines.append(line)
    if len(mapping)!=375:raise ValueError('Expected existing 375-officer reserve')
    return b''.join(lines),mapping

def migrate(raw,mapping):
    root=parse(raw);india=next(c for c in root.all('country') if c.get('tag')=='IND');edits=[]
    for n in walk(india):
        ident=n.get('id')
        if not isinstance(ident,Node) or ident.get('type')!='6':continue
        i=int(ident.get('id','-1'))
        if i not in mapping or not n.get('picture'):continue
        f=n.field('picture')
        if f.value!=mapping[i]:edits.append((f.value_start,f.end,('"'+mapping[i]+'"').encode('ascii')))
    return replace(raw,edits),len(edits)

def pack(dest):
    im=Image.open(ATLAS).convert('RGB');w,h=im.size;dest.mkdir(parents=True,exist_ok=True)
    preview=Image.new('RGB',(4*108,4*150))
    for i in range(16):
        x,y=i%4,i//4
        tile=im.crop((round(x*w/4),round(y*h/4),round((x+1)*w/4),round((y+1)*h/4)))
        tile=ImageOps.fit(tile,(36,50),Image.Resampling.LANCZOS,centering=(.5,.3))
        tile.save(dest/f'aubm_c1_reserve_{i+1:02d}.bmp')
        preview.paste(tile.resize((108,150),Image.Resampling.NEAREST),(108*x,150*y))
    return preview

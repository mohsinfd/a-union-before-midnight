"""DH saved games carry their own event-file registry.

Updating db/events.txt alone cannot register a new module in an older campaign.
"""
from pathlib import Path
from audit_japan_baseline import parse,get,getall

def ensure_modules(text,index_text):
    old=getall(parse(text),'event')
    canonical=lambda p:p.replace('\\','/').lower()
    known={canonical(p) for p in old if isinstance(p,str)}
    added=[]
    for path in getall(parse(index_text),'event'):
        if not isinstance(path,str) or '/japan_rising/' not in canonical(path):continue
        if canonical(path) in known:continue
        text+='\nevent = "'+path+'"\n';added.append(path);known.add(canonical(path))
    return text,added

def queued_jx_missing(text,target):
    root=parse(text);ids=set()
    for rel in getall(root,'event'):
        path=Path(target)/rel.replace('\\','/')
        if path.exists():
            ids.update(int(get(e,'id')) for e in getall(parse(path.read_text(encoding='latin1')),'event') if str(get(e,'id')).isdigit())
    queue=get(get(root,'globaldata'),'queued_events',[])
    return [int(get(e,'id')) for e in getall(queue,'event') if str(get(e,'id')).startswith('286') and int(get(e,'id')) not in ids]

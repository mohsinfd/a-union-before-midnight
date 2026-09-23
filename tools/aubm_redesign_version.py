"""Unambiguous test-candidate identification, without changing gameplay."""
from dh_save_spans import parse, replace

BUILD = 'EVENT-REDESIGN-CANDIDATE5'
TITLE = 'AUBM Candidate 5 - Unverified Playtest'


def transform(files):
    output,records=dict(files),{}
    for path,text in files.items():
        edits=[]
        for e in parse(text).all('event'):
            if e.get('id')!='9270000':continue
            f=e.field('name');edits.append((f.value_start,f.end,'"'+TITLE+'"'))
            f=e.field('desc')
            prefix='CANDIDATE 5: new-campaign event redesign; native testing is not complete. '
            description=f.value if f.value.startswith(prefix) else prefix+f.value
            if len(description.encode('latin1'))>500:raise ValueError('Candidate opening description over budget')
            edits.append((f.value_start,f.end,'"'+description+'"'))
            records[9270000]=[dict(dimension='candidate_identification',status='reviewed',engine_tested=False,
                detail='Opening title explicitly identifies the unverified test candidate; no gameplay effects changed.')]
        output[path]=replace(text,edits)
    if not records:raise ValueError('Fresh campaign opening is missing')
    return output,records


def scenario(raw):
    text=raw.decode('latin1');e=parse(text).get('header');f=e.field('name')
    return replace(text,[(f.value_start,f.end,'"India 1933 - AUBM Candidate 5 [UNVERIFIED]"')]).encode('latin1')

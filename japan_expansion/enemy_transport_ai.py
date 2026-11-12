"""R13.1: supported AI settings and existing-ship transport screens.

No invented fleet-ratio directive. The engine can reorganise fleets later;
the initial OOB and future construction priorities are the controllable parts.
"""
from copy import deepcopy
from collections import Counter
from math import ceil
from pathlib import Path
import json,re

TAGS={'USA','ENG','AST','NZL','CAN','FRA','HOL','U05'}
SCREENS={'destroyer','light_cruiser'}
CAPITALS={'battleship','battlecruiser','heavy_cruiser','carrier','light_carrier','escort_carrier'}
REPORT={}


def get(node,key,default=None):
    return next((v for k,v in node if k and k.casefold()==key.casefold()),default)


def allv(node,key):return [v for k,v in node if k and k.casefold()==key.casefold()]


def counts(fleet):return Counter(get(d,'type') for d in allv(fleet,'division'))


def floor(fleet):
    types=counts(fleet);tp=types['transport']
    transport_floor=(max(2,ceil(tp/3)) if tp>1 else tp)
    return max(sum(types[k] for k in CAPITALS),transport_floor,1)


def regroup(country):
    """Move only surplus screens at the same port; never add or delete ships."""
    fleets=allv(country,'navalunit');moves=[]
    targets=sorted((f for f in fleets if counts(f)['transport']),key=lambda f:-counts(f)['transport'])
    for target in targets:
        while sum(counts(target)[t] for t in SCREENS)<floor(target):
            choices=[]
            for donor in fleets:
                if donor is target or get(donor,'location')!=get(target,'location'):continue
                if sum(counts(donor)[t] for t in SCREENS)<=floor(donor):continue
                for pair in donor:
                    if pair[0] and pair[0].casefold()=='division' and get(pair[1],'type') in SCREENS:
                        choices.append((get(pair[1],'type')!='destroyer',donor,pair));break
            if not choices:break
            _,donor,pair=min(choices,key=lambda v:v[0]);donor.remove(pair);target.append(pair)
            moves.append({'ship':get(pair[1],'name'),'id':get(pair[1],'id'),
                          'from':get(donor,'name'),'to':get(target,'name'),'port':get(target,'location')})
    return moves


def profile(text,parse,serialise):
    tree=parse(text);military=get(tree,'military')
    if military is None:return text,None
    tp=get(military,'transports',get(military,'transport'))
    dd=get(military,'destroyer')
    if tp is None or dd is None:return text,None
    transfer=min(3,int(float(tp)//4))
    if transfer<=0:return text,None
    before={k:float(v) for k,v in military if k in {'transports','transport','destroyer'}}
    for i,(k,v) in enumerate(military):
        if k in {'transports','transport'}:military[i]=(k,f'{float(v)-transfer:g}')
        elif k=='destroyer':military[i]=(k,f'{float(v)+transfer:g}')
    return serialise(tree)+'\n',{'before':before,'transferred_to_destroyers':transfer}


def install(source,target,read,write,parse,serialise):
    scenarios=[];profiles=[]
    for src in sorted((source/'scenarios/1933').glob('*.inc')):
        root=parse(read(src));countries=allv(root,'country')
        if not any(get(c,'tag') in TAGS for c in countries):continue
        path=target/src.relative_to(source)
        # Restore only the naval fleets from the clean baseline. Preserve any
        # other installed country changes, including unrelated land/air data.
        current=parse(read(path)) if path.exists() else deepcopy(root)
        for clean in countries:
            tag=get(clean,'tag')
            if tag not in TAGS:continue
            dest=next(c for c in allv(current,'country') if get(c,'tag')==tag)
            fleets=[(k,deepcopy(v)) for k,v in clean if k and k.casefold()=='navalunit']
            dest[:]=[(k,v) for k,v in dest if not(k and k.casefold()=='navalunit')]+fleets
            moves=regroup(dest)
            scenarios.append({'file':str(path.relative_to(target)),'country':tag,'moves':moves,
                              'unescorted_groups':sum(counts(f)['transport']>0 and sum(counts(f)[t] for t in SCREENS)==0 for f in allv(dest,'navalunit'))})
        write(path,serialise(current)+'\n')
    for src in sorted((source/'ai').rglob('*.ai')):
        if not re.match(r'^(usa|eng|ast|nzl|can|fra|hol|u05)(?:_|\.)',src.name,re.I):continue
        text=read(src)
        if src.name.casefold()=='usa_1942.ai':
            from model_names_and_ai import allied_invasion_ai
            text=allied_invasion_ai(text,src.name)
        result,change=profile(text,parse,serialise)
        if change:
            path=target/src.relative_to(source);write(path,result)
            profiles.append({'file':str(path.relative_to(target)),**change})
    REPORT.update(scenarios=scenarios,profiles=profiles,moved_screens=sum(len(x['moves']) for x in scenarios),
                  engine_limit='Initial groups may be reorganised by the hardcoded naval AI; no minimum-screen scripting switch is claimed.',game_launched=False)
    (Path(__file__).parent/'ENEMY_TRANSPORT_AI_REPORT.json').write_text(json.dumps(REPORT,indent=2)+'\n',encoding='utf-8')
    return REPORT

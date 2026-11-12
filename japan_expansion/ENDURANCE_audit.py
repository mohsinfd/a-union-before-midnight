"""Read-only baseline/save evidence and reproducible planning arithmetic."""
import csv
import hashlib
import json
import re
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'tools'))
from audit_japan_baseline import ROOT, BASE, TOKEN, parse, get, getall, units, unit_type
from endurance_economy import STAGES


def block(text,start):
    depth=0
    for tok in TOKEN.finditer(text,text.index('{',start)):
        if tok.group()=='{':depth+=1
        elif tok.group()=='}':
            depth-=1
            if depth==0:return text[start:tok.end()]
    raise ValueError('Unclosed block')


def run():
    rows={int(r['Id']):r for r in csv.DictReader((ROOT/'map/Map_1/province.csv').read_text(encoding='latin1').splitlines(),delimiter=';') if r['Id'].isdigit()}
    c=get(parse((BASE/'scenarios/1933/japan.inc').read_text(encoding='latin1')),'country')
    owned={int(v) for _,v in get(c,'ownedprovinces')};cores={int(v) for _,v in get(c,'nationalprovinces')}
    fields=('Energy','Metal','Rare Materials','Oil')
    raw={k:sum(float(rows[p][k] or 0)*(1 if p in cores else .8) for p in owned) for k in fields}
    effective={k:round(v*.9,3) for k,v in raw.items()}
    plans=[]
    for choice in (0,1):
        totals=[effective[k] for k in fields]
        for stage in STAGES:
            key,year,cash,stock,metal,days,mine,options=stage
            for i,v in enumerate(options[choice]):totals[i]+=v*.9
            totals[0]-=20*.9
            ic=100 if key=='home_fuel' else 150
            consumption=[2*ic,ic,.5*ic,0]
            plans.append({'choice':('balanced','fuel priority')[choice], 'completed_stage':key,
                          'illustrative_effective_IC':ic,'daily_resources':dict(zip(fields,map(lambda v:round(v,3),totals))),
                          'after_industry':dict(zip(fields,[round(v-u,3) for v,u in zip(totals,consumption)])),
                          'energy_after_industry_and_standard_batch':round(totals[0]-2*ic-12000/90,3),
                          'energy_after_industry_and_large_batch':round(totals[0]-2*ic-24000/90,3),
                          'note':'Native conversion, other JX programmes, imports and conquest excluded.'})
    saves=ROOT/'Mods/Japan Rising JX1 Alpha2/scenarios/save games'
    latest=max(saves.glob('*.eug'),key=lambda p:p.stat().st_mtime)
    data=latest.read_bytes();text=data.decode('latin1')
    start=next(m.start() for m in re.finditer(r'(?m)^country = \{',text) if re.search(r'\btag\s*=\s*JAP\b',text[m.start():m.start()+200]))
    c=get(parse(block(text,start)),'country')
    force=[]
    for kind in ('landunit','navalunit','airunit'):
        ds=units(c,kind,'division')
        force.append({'kind':kind,'formations':len(ds),
                      'full_strength_saved_template_oil':round(sum(float(get(d,'all')[8][1]) for d in ds),3),
                      'saved_template_supply':round(sum(float(get(d,'all')[7][1]) for d in ds),3)})
    header=get(parse(block(text,text.index('header = {'))),'header')
    report={'baseline_source':str(BASE),'baseline_territorial_raw':raw,'baseline_effective_at_0_9':effective,
            'plans':plans,'save':str(latest),'save_sha256':hashlib.sha256(data).hexdigest(),
            'save_date':dict(get(header,'startdate')),
            'save_resources':{k:float(get(c,k,0)) for k in ('manpower','oil','energy','metal','rare_materials','supplies','money')},
            'force_consumption_templates':force,
            'captured_sites_base_oil':{p:float(rows[p]['Oil']) for p in (1636,1632,1653,1642)},
            'occupied_three_project_output_at_0_9':(11+60)*.65*.9,
            'limitations':['Planning arithmetic is not an observed engine daily ledger.',
                           'Province.csv and 1933 owned/core membership are the baseline; other JX rewards are intentionally excluded.',
                           'Template consumption excludes duty, strength, combat multipliers and transport timing.',
                           'No game launch, installation, or save modification.']}
    (HERE/'ENDURANCE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':run()

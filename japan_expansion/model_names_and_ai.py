"""Deterministic model localisation and nonduplicating Axis port priorities."""
import re


def remove_generic_model_conflicts(text,classes,model_years):
    keys={f'MODEL_{info["index"]}_{i}' for unit,info in classes.items() for i,year in enumerate(model_years(unit))}
    return '\n'.join(l for l in text.splitlines() if l.split(';')[0] not in keys)+'\n'


def model_names(base,classes,model_years):
    records={f'MODEL_JAP_41_{i}':f'Imperial Guards Field Division {year}'
             for i,year in enumerate((1935,1939,1942,1945,1948))}
    existing={l.split(';')[0] for l in base.splitlines() if not l.startswith('#')}
    for unit,info in classes.items():
        for i,year in enumerate(model_years(unit)):
            value=f'{info["name"]} {year}'
            records[f'MODEL_JAP_{info["index"]}_{i}']=value
            generic=f'MODEL_{info["index"]}_{i}'
            if generic not in existing:records[generic]=value
    # Idempotent if a generated file is supplied; retain all native translations.
    clean='\n'.join(l for l in base.splitlines() if l.split(';')[0] not in records)+'\n'
    rows='\n'.join(';'.join([k,v]+['']*9+['X']) for k,v in records.items())+'\n'
    stop=re.search(r'(?m)^#EOF',clean);pos=stop.start() if stop else len(clean)
    return clean[:pos]+rows+clean[pos:]


def axis_ai(base,name):
    result=re.sub(r'(?m)^reinforcement\s*=.*$','reinforcement = 1.0',base)
    result=re.sub(r'(?m)^max_garrison_prop\s*=.*$','max_garrison_prop = 0.35',result)
    result=re.sub(r'(?m)^min_garrison_prop\s*=.*$','min_garrison_prop = 0.20',result)
    wanted={483:100,488:75,495:100} if name.lower().startswith('ger_') else {377:100,750:120,761:100,765:100}
    def merge(m):
        values={}
        for line in m[2].splitlines():
            line=line.split('#',1)[0].strip()
            if not line:continue
            found=re.fullmatch(r'(\d+)\s*=\s*([\d.]+)',line)
            assert found,(name,line)
            key=int(found[1]);values[key]=max(values.get(key,0),float(found[2]))
        for key,weight in wanted.items():values[key]=max(weight,values.get(key,0))
        return m[1]+'\n'+''.join(f'        {key} = {value:g}\n' for key,value in values.items())+m[3]
    result,count=re.subn(r'(\bgarrison\s*=\s*\{[\s\S]*?\bprovince_priorities\s*=\s*\{)([^{}]*)(\})',merge,result,count=1)
    # Some historical files have no garrison block; retain them unchanged apart
    # from the original top-level allocation settings.
    assert count in {0,1}
    return result


def allied_invasion_ai(base, name):
    """Reduce low-value US island raids without disabling major landings."""
    if name.lower() != 'usa_1942.ai':
        return base
    result = base
    values = {'island': 0.8, 'enemy': 1.5, 'adjacentenemy': 0.8}
    for key, value in values.items():
        pattern = rf'(?m)^(\s*{key}\s*=\s*)[-+]?\d+(?:\.\d+)?(\s*(?:#.*)?)$'
        result, count = re.subn(pattern, rf'\g<1>{value:g}\g<2>', result, count=1)
        if count != 1:
            raise ValueError(f'{name}: expected one invasion {key} value, found {count}')
    return result

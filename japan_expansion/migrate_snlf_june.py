"""Migrate the inspected June L3 save into a separate L4 copy, without a game."""
import copy
import hashlib
import json
from pathlib import Path
import re
from build import HERE,TARGET,SOURCE,read,parse,get,getall,serialise,prepare_catalog,EVENTS
from repair_completion_save import block_end
from cabinet_expansion import rows as cabinet_rows,APPOINTMENTS,POSITIONS


def replace(node,key,value):
    node[:]=[(k,v) for k,v in node if k!=key];node.append((key,value))


def field(chunk,key,value):
    m=re.search(r'(?m)^\t'+re.escape(key)+r' = \{',chunk);assert m,key
    end=block_end(chunk,m.start())
    return chunk[:m.start()]+'\t'+serialise([(key,value)],0)+chunk[end:]


def migrate():
    prepare_catalog()
    source=TARGET/'scenarios/save games/JAPAN_R5_L3_1937_June_1.eug'
    original=source.read_bytes();prior=json.loads((HERE/'PROGRAMME_SAVE_REPAIR.json').read_text())
    assert hashlib.sha256(original).hexdigest()==prior['repaired_sha256'],'Reaudit a changed June source first'
    s=original.decode('latin1').replace('\r\n','\n')
    dest=source.with_name('JAPAN_R5_L4_1937_June_1.eug');assert not dest.exists(),'Do not overwrite a played save'
    personalities=getall(parse(read(TARGET/'db/ministers/minister_personalities.txt')),'minister')
    traits={get(n,'trait'):get(n,'id') for n in personalities}
    rows=cabinet_rows(SOURCE,read)
    reports=[];changes=[];jap_before=None;jap_after=None
    # Append registry entries; do not shift any existing packed unit indexes.
    for match in re.finditer(r'(?m)^country = \{',s):
        end=block_end(s,match.start());chunk=s[match.start():end]
        c=get(parse(chunk),'country');tag=get(c,'tag');expected=copy.deepcopy(c)
        upgrade=copy.deepcopy(get(c,'upgrade'));mods=copy.deepcopy(get(c,'modifiers'))
        assert get(upgrade,'d_12') is None and get(mods,'d_12') is None
        marine=copy.deepcopy(get(upgrade,'marine',[]))
        if tag=='JAP':
            assert get(get(c,'allowed_divisions'),'d_10')=='yes'
            assert '1590' in {v for _,v in get(c,'techapps')}
            # Replace the temporary L3 Marine reward with the dedicated SNLF one.
            old=copy.deepcopy(get(upgrade,'marine'));assert float(get(old,'buildtime',0))==-30
            replace(old,'buildtime','0');replace(upgrade,'marine',old)
            replace(marine,'buildtime','-60')
            jap_before=c
        upgrade.append(('d_12',marine))
        terrain=copy.deepcopy(get(mods,'marine',[]));assert terrain
        for key in ('shore_attack','river_attack'):
            replace(terrain,key,f'{float(get(terrain,key,0))+5:g}')
        mods.append(('d_12',terrain))
        replace(expected,'upgrade',upgrade);replace(expected,'modifiers',mods)
        allowed=copy.deepcopy(get(c,'allowed_divisions'));allowed.append(('d_12','yes' if tag=='JAP' else 'no'))
        replace(expected,'allowed_divisions',allowed)
        changed={'upgrade':upgrade,'modifiers':mods,'allowed_divisions':allowed}
        if tag=='JAP':
            models=copy.deepcopy(get(c,'models'));assert get(models,'d_12') is None
            # Model zero is implicit in DH; listing it explicitly creates a
            # duplicate-zero warning when the engine initialises the class.
            replace(expected,'models',models);changed['models']=models
            existing={int(get(get(n,'id'),'id')) for n in getall(c,'minister')}
            added=[]
            for r in rows:
                assert int(r[0]) not in existing
                n=[('id',[('type','9'),('id',r[0])]),('name',r[2]),('picture',r[9]),
                   ('position',POSITIONS[r[1]]),('category','paternal_autocrat'),
                   ('cabinet','replacement'),('trait',traits[r[7]]),('year',r[3]),('ry',r[4])]
                expected.append(('minister',n));added.append(n)
        else:added=[]
        for key,value in changed.items():chunk=field(chunk,key,value)
        if added:chunk=chunk[:-1]+serialise([('minister',n) for n in added],1)+'\n}'
        actual=get(parse(chunk),'country')
        # Field order is not gameplay. No other country state may change.
        def grouped(node):
            result={}
            for k,v in node:result.setdefault(k,[]).append(v)
            return result
        assert grouped(actual)==grouped(expected),tag
        unchanged=[(k,v) for k,v in actual if k not in changed and not (k=='minister' and int(get(get(v,'id'),'id')) in {r[0] for r in APPOINTMENTS})]
        assert unchanged==[(k,v) for k,v in c if k not in changed],('Unintended mutation',tag)
        if tag=='JAP':jap_after=actual
        reports.append({'tag':tag,'existing_unit_and_queue_fields_unchanged':True,'SNLF_unlocked':tag=='JAP'})
        changes.append((match.start(),end,chunk))
    for start,end,chunk in reversed(changes):s=s[:start]+chunk+s[end:]
    # Once-only unlock: prevents a future completion from applying tech effects twice.
    gm=re.search(r'(?m)^globaldata = \{',s);ge=block_end(s,gm.start());g=s[gm.start():ge]
    fm=re.search(r'(?m)^\tflags = \{',g);fe=block_end(g,fm.start())
    assert 'JX_SNLF_FORCE' not in g
    g=g[:fe-1]+'\n\t\tJX_SNLF_FORCE = 1\n\t'+g[fe-1:]
    s=s[:gm.start()]+g+s[ge:]
    s=re.sub(r'^name = "[^"]*"','name = "Japan Rising R5 L4 - 1 June 1937 SNLF and cabinet"',s,count=1)
    assert source.read_bytes()==original and jap_before is not None and jap_after is not None
    dest.write_bytes(s.replace('\n','\r\n').encode('latin1'))
    backup=Path((HERE/'SNLF_CABINET_BACKUP.txt').read_text())
    old=json.loads((backup/'sources/events.json').read_text());by={e.key:e.id for e in EVENTS}
    assert all(by[e['key']]==e['id'] for e in old)
    report={'result':'PASS','source':str(source),'source_sha256':hashlib.sha256(original).hexdigest(),
            'save':str(dest),'save_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
            'date':'1 June 1937','new_class':'d_12','new_class_index':52,'new_class_current_model':0,
            'new_1937_appointments':len(rows),'countries_with_registry_migration':len(reports),
            'old_event_ids_preserved':len(old),'original_saves_unchanged':True,'game_executed':False,
            'changes':['SNLF unlocked with saved Marine research and terrain effects copied once',
                       'Marine -30 temporary reward replaced with SNLF -60 days',
                       'Ten replacement cabinet profiles added; incumbents unchanged'],
            'unchanged':['All existing units and serial queues','Resources and manpower','IC','Wars, alliances, treaties and ownership','Research projects and current cabinet'],
            'countries':reports}
    (HERE/'SNLF_JUNE_MIGRATION.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='countries'}))


if __name__=='__main__':migrate()

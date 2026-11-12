"""Retrofit earned time reductions into a copy; keep all units/queues intact."""
import copy
import hashlib
import json
from pathlib import Path
import re
from build import HERE,TARGET,GAME,read,parse,get,getall,serialise,prepare_catalog
from repair_completion_save import block_end,industry_totals
from audit_1937_playtest import snapshot
import production_programmes


def run():
    prepare_catalog();path,raw,s,date,c,g,log=snapshot()
    audit=json.loads((HERE/'PLAYTEST_1937_AUDIT.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==audit['source_sha256'],'Audit a changed save before repairing it'
    assert date=={'year':'1937','month':'june','day':'0','hour':'0'}
    done={r['key']:r['selected_completions'] for r in audit['completed_paid_programmes']}
    rows=[r for r in production_programmes.REPORT if r['option'] in done.get(r['parent'],[])]
    assert {(r['parent'],r['option']) for r in rows}=={('snlf',0),('base_force_orders',0)},'Unexpected programme choices; review before patching'
    flags=dict(get(g,'flags'));upgrades=copy.deepcopy(get(c,'upgrade'));changes=[]
    for row in rows:
        assert row['marker'] not in flags or flags[row['marker']]=='0','Already migrated'
        for b in row['benefits']:
            unit=get(upgrades,b['unit']);assert unit is not None
            old=float(get(unit,'buildtime',0));new=old-b['days']+b['previous_eight_days']
            unit[:]=[(k,v) for k,v in unit if k!='buildtime'];unit.append(('buildtime',f'{new:g}'))
            changes.append({'programme':row['parent'],'unit':b['unit'],'old_modifier_days':old,'new_modifier_days':new,
                            'additional_reduction':old-new,'replaces_previous_eight_day_bonus':bool(b['previous_eight_days'])})
    m=next(m for m in re.finditer(r'(?m)^country = \{',s) if re.search(r'(?m)^\s*tag = JAP\s*$',s[m.start():m.start()+500]))
    cstart=m.start();cend=block_end(s,cstart);chunk=s[cstart:cend]
    u=re.search(r'(?m)^\tupgrade = \{',chunk);assert u
    uend=block_end(chunk,u.start())
    patched=chunk[:u.start()]+'\t'+serialise([('upgrade',upgrades)])+chunk[uend:]
    cc=get(parse(patched),'country');expected=copy.deepcopy(c)
    expected[:]=[(k,upgrades if k=='upgrade' else v) for k,v in expected]
    assert cc==expected,'Unexpected country, unit, IC, manpower or queue mutation'
    result=s[:cstart]+patched+s[cend:]
    gs=re.search(r'(?m)^globaldata = \{',result);ge=block_end(result,gs.start());globaltext=result[gs.start():ge]
    fm=re.search(r'(?m)^\tflags = \{',globaltext);assert fm
    fe=block_end(globaltext,fm.start())
    insert='\n'+''.join('\t\t'+r['marker']+' = 1\n' for r in rows)+'\t'
    globaltext=globaltext[:fe-1]+insert+globaltext[fe-1:]
    result=result[:gs.start()]+globaltext+result[ge:]
    result=re.sub(r'^name = "[^"]*"','name = "Japan Rising R5 L3 - 1 June 1937 programme repair"',result,count=1)
    destination=path.with_name('JAPAN_R5_L3_1937_June_1.eug');assert not destination.exists()
    destination.write_bytes(result.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))
    assert path.read_bytes()==raw,'Original save was not stable; review the new save'
    report={'result':'PASS','source':str(path),'source_sha256':hashlib.sha256(raw).hexdigest(),
            'repaired_save':str(destination),'repaired_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
            'date':date,'changes':changes,'all_units_manpower_resources_and_queues_preserved':True,
            'no_cost_charged_again':True,'no_free_units_added':True,'game_executed':False,
            'note':'Discounts affect basic unit construction time. Existing zero-progress lines are preserved; cancel/reorder through the game for native manpower refunds if desired.'}
    (HERE/'PROGRAMME_SAVE_REPAIR.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))


if __name__=='__main__':run()

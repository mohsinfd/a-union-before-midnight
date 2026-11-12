"""Structural and price review of the two newly registered unit classes."""
import json
from PIL import Image
from build import SOURCE,TARGET,HERE,VERSION,read,parse,get,getall,num
from specialist_units import CLASSES,YEARS,MODEL_TECHS,models,MIRRORS,model_years


def run():
    types=parse(read(TARGET/'db/units/division_types.txt'))
    order=[k for k,v in types if k!='eyr'];assert len(order)==53
    assert order[-4:]==['d_09','d_10','d_11','d_12']
    original=Image.open(SOURCE/'gfx/map/hoi_counter_strip.bmp')
    installed=Image.open(TARGET/'gfx/map/hoi_counter_strip.bmp')
    assert installed.size==(53*32,34)
    assert installed.crop((0,0,1600,34)).convert('RGB').tobytes()==original.convert('RGB').tobytes()
    for slot,native in ((50,9),(51,0),(52,7)):
        assert installed.crop((slot*32,0,(slot+1)*32,34)).convert('RGB').tobytes()==original.crop((native*32,0,(native+1)*32,34)).convert('RGB').tobytes()
    lines=read(TARGET/'db/units/modifiers.csv').splitlines();header=lines[0].split(';')
    assert header[-4:]==['d_10','d_11','d_12','X']
    terrain={}
    for line in lines[1:]:
        c=line.split(';')
        if not c[0] or c[0]=='EOF':continue
        assert len(c)==len(header),(c[0],len(c),len(header))
        terrain[c[0]]={u:float(c[header.index(u)]) for u in CLASSES}
    assert terrain['ATT_JUNGLE']['d_11']==-50
    assert terrain['MOV_JUNGLE']['d_11']==-20
    assert terrain['ATT_RIVER']['d_11']==-30
    assert terrain['ATT_SHORE']['d_12']==float(next(l for l in read(SOURCE/'db/units/modifiers.csv').splitlines() if l.startswith('ATT_SHORE;')).split(';')[8])+5
    rows=[]
    for unit,info in CLASSES.items():
        assert get(get(types,unit),'production')=='no'
        assert get(get(types,unit),'type')==info['base']
        current=getall(parse(read(TARGET/'db/units/divisions'/(unit+'.txt'))),'model')
        if unit=='d_12':
            attachments=getall(parse(read(TARGET/'db/units/divisions/d_12.txt')),'allowed_brigades')
            assert attachments==['artillery','anti_air','engineer','amph_armor']
            assert all((TARGET/'db/units/brigades'/(b+'.txt')).exists() for b in attachments)
        assert current==models(unit)
        assert len(current)==5
        for i,m in enumerate(current):
            assert 0<num(m,'cost') and 0<num(m,'buildtime') and 0<num(m,'manpower')
            assert num(m,'morale')<100
            assert (num(m,'maxspeed')==0) == (unit=='d_10')
            for f,size in ((f'ill_div_JAP_{info["index"]}_{i}.bmp',(192,104)),(f'JAP_model_{info["index"]}_{i}.bmp',(67,44))):
                with Image.open(TARGET/'gfx/interface/models'/f) as im:assert im.size==size;im.load()
            rows.append({'unit':unit,'name':info['name'],'year':model_years(unit)[i],'model':i,
                         **{k:num(m,k) for k in ('cost','buildtime','manpower','maxspeed','softattack','hardattack','defensiveness','supplyconsumption')},
                         'template_ic_days':num(m,'cost')*num(m,'buildtime')})
    guards=getall(parse(read(TARGET/'db/units/divisions/d_01.txt')),'model')
    assert num(guards[1],'morale')==50
    # Every model hook is guarded by both nation and the class unlock.
    tree=parse(read(TARGET/'db/tech/infantry_tech.txt'))
    hooks=0
    for t in getall(tree,'technology'):
        for a in getall(t,'application'):
            for c in getall(get(a,'effects',[]),'command'):
                u=get(c,'which')
                if u not in CLASSES:continue
                trig=get(c,'trigger',[])
                assert get(trig,'country')=='JAP'
                assert get(trig,'flag')=='JX_'+CLASSES[u]['flag']
                if get(c,'type')=='new_model':hooks+=1
    assert hooks==12
    report={'result':'PASS','version':VERSION,'new_classes':3,'models':len(rows),'registered_types':53,
            'counter_atlas_size':installed.size,'old_counter_pixels_preserved':True,
            'infantry_model_upgrade_hooks':hooks,'mirrored_technology_effects':len(MIRRORS),
            'guard_morale_typo_corrected':True,'rows':rows,'engine_tested':False}
    (HERE/'SPECIALIST_REVIEW.json').write_text(json.dumps(report,indent=2))
    doc=['# Specialist force review','',
         'Offline structure and template arithmetic, not an engine combat or Hard balance test. Three optional alternate-history force structures are registered as separate unit classes.','',
         '| Class | Year | IC | Days | IC-days | MP | Speed | Soft attack | Hard attack | Defence | Supply |',
         '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        doc.append(f"| {r['name']} | {r['year']} | {r['cost']:g} | {r['buildtime']:g} | {r['template_ic_days']:g} | {r['manpower']:g} | {r['maxspeed']:g} | {r['softattack']:g} | {r['hardattack']:g} | {r['defensiveness']:g} | {r['supplyconsumption']:g} |")
    doc+=['','Naval Base Forces cost 950 template IC-days versus the native garrison\'s 640, use 8 rather than 10 manpower, and cannot march. Their defensive/AA advantage comes with weaker attack and higher construction cost. They do not replace field infantry.',
          'Jungle Light Infantry cost 1,980 template IC-days versus infantry\'s 1,450, use 11 rather than 13 manpower, have reduced attack/defence and lower supply use. Jungle attack is -50 rather than ordinary infantry -70; jungle movement is -20 rather than -35. River and opposed-landing penalties remain those of infantry. Attachments have their own modifiers and costs.',
          '', 'Five model stages catch up completed infantry research on activation and follow new research thereafter. Specific unconditioned native infantry/garrison technology effects are mirrored for the appropriate class, under a JAP plus class-unlock gate. Generic land effects remain generic; effects already conditional on other flags/countries are not blindly copied.',
          '', 'The SNLF is a separate mobile assault class. It uses 12 manpower, 360 base construction days and 9 base IC. It has 10 percent less soft attack, about 15 percent less defence, 10 percent less supply use and 20 percent less transport weight than its Marine model. Landing and river attack modifiers are five points better. The funded throughput option reduces SNLF time by another 60 days. Models follow Marine research in 1937, 1940, 1943, 1946 and 1949.',
          '', 'The counter atlas has 53 cells. All 50 original cells are unchanged; native garrison/infantry/Marine symbols occupy the appended cells. All classes use inherited sprites and distinct original generated illustrations. No new animated sprites are claimed.',
          '', 'The d_01 model-one morale typo 540 is corrected to 50 in this Japan installation. It was shared by all users of that B&I template; the source installation is untouched.',
          '', 'The separately prepared L4 June save includes explicit SNLF model, modifier and cabinet migration. Other old saves have not been migrated or engine-tested. No game was run.']
    (HERE/'SPECIALIST_REVIEW.md').write_text('\n'.join(doc)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))


if __name__=='__main__':run()

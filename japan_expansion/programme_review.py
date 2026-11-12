"""Check the selected manual-order policy and vanilla decision-card layout."""
import json
from PIL import Image
from build import HERE,TARGET,SOURCE,VERSION,EVENTS,prepare_catalog,parse,get,compiled_event
import production_programmes


def run():
    prepare_catalog();by={e.key:e for e in EVENTS}
    assert production_programmes.REPORT
    for row in production_programmes.REPORT:
        e=by[row['finish']];parent=by[row['parent']]
        commands=[parse(c) for c in e.actions[0].commands]
        assert not any(get(c,'type') in {'build_division','build_brigade','add_brigade','add_division'} for c in commands)
        assert 'manpower =' not in parent.actions[row['option']].gate
        for b in row['benefits']:
            found=[c for c in commands if get(c,'type')=='build_time' and get(c,'which')==b['unit']]
            assert len(found)==1 and float(get(found[0],'value'))==-b['days']
            cap=60 if row['parent']=='snlf' and b['unit']=='d_12' else 30
            assert get(found[0],'when')=='on_upgrade' and 0<b['days']<=cap
        assert row['marker'] in str(commands)
        assert 'no formations or queue entries' in parent.desc
    banners=list((TARGET/'gfx/events_pics').glob('jx_decision_*.bmp'))
    for p in banners:
        with Image.open(p) as im:
            assert im.size==(224,48) and im.mode=='RGB'
            assert all(im.getpixel((x,y))==(0,255,0) for y in range(14) for x in range(224)),p.name
    report={'result':'PASS','version':VERSION,'hotfix':'L3','policy':'Player places units; paid programmes award base-time reductions',
            'converted_alternatives':len(production_programmes.REPORT),
            'converted_programmes':len({r['parent'] for r in production_programmes.REPORT}),
            'decision_banners_with_vanilla_title_transparency':len(banners),
            'game_executed':False,'programmes':production_programmes.REPORT}
    (HERE/'PROGRAMME_REVIEW.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='programmes'}))


if __name__=='__main__':run()

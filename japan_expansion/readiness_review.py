"""Verify the cold-review corrections against the installed scripts."""
import json
from build import HERE,SOURCE,TARGET,EVENTS,VERSION,prepare_catalog,parse,get,getall,read,resolve
import release_support,construction_safety


def run():
    prepare_catalog()
    by={e.key:e for e in EVENTS}
    assert len(release_support.META)>200
    assert 'JAP' not in release_support.META and 'MAN' not in release_support.META
    assert all(not e.desc and not e.decision for e in EVENTS if e.module=='release_support')
    for e in EVENTS:
        if e.module=='settlements' and e.key.endswith('_local'):
            text=' '.join(e.actions[0].commands)
            assert '_NAVAL_AID' not in text and 'type = add_division' not in text
            assert '@relief_'+e.country in text
    # Protect every receiver, including the alternate stock war-demand caller.
    native={get(e,'id'):e for e in getall(parse(read(TARGET/'db/events/japan.txt')),'event')}
    for eid in ('2011009','2059001','2011010','2011011'):
        e=native[eid];assert 'JX_thailand_PENDING' in str(get(e,'trigger'))
        for a in getall(e,'action')+getall(e,'action_a')+getall(e,'action_b')+getall(e,'action_c'):
            assert 'JX_thailand_PENDING' in str(get(a,'trigger'))
    synthetic=by['synthetic_finish_0']
    energy=[parse(c) for c in synthetic.actions[0].commands if get(parse(c),'type')=='add_prov_resource' and get(parse(c),'where')=='energy']
    assert len(energy)==1 and get(energy[0],'which')=='1550' and get(energy[0],'value')=='-20'
    for key in ('hawaii','singapore','hongkong'):
        for i in (0,1):assert not any(get(parse(c),'type')=='construct' for c in by[key+'_finish_'+str(i)].actions[0].commands)
    assert len(construction_safety.REPORT)==33
    for r in construction_safety.REPORT:
        assert 'owned = {' in r['eligibility'] and 'control = {' in r['eligibility']
        assert r['snapshot_event'] in by and r['receipt_event'] in by
    # Existing IDs stay fixed; technical receivers are appended after R2.
    old_path=HERE/'backups/r2-before-readiness-20261031-163941/sources/events.json'
    old=json.loads(old_path.read_text(encoding='utf8'))
    assert all(by[e['key']].id==e['id'] for e in old)
    report={'result':'PASS','version':VERSION,'prior_ids_preserved':len(old),
            'release_country_policies':len(release_support.META),
            'construction_alternatives_protected':len(construction_safety.REPORT),
            'thai_native_events_guarded':[2011009,2059001,2011010,2011011],
            'synthetic_energy_province':1550,'game_executed':False,
            'support_tiers':release_support.META,'construction_transactions':construction_safety.REPORT}
    (HERE/'READINESS_REVIEW.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'support_tiers','construction_transactions'}}))


if __name__=='__main__':run()

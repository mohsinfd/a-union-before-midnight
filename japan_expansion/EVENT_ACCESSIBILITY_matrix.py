"""Cold compiled-offer witnesses and delivery graph for every active human offer.

The fixtures are explicit counterfactual campaign positions, not an engine
playthrough. They preserve legal ownership in occupation cases.
"""
import json
import copy
from pathlib import Path
from EVENT_ACCESSIBILITY_review import HumanWorld, available
from build import EVENTS, parse, get, resolve, source_country
from simulate import BY_KEY


class AuditWorld(HumanWorld):
    def command(self,node,actor):
        condition=get(node,'trigger')
        if not condition or self.test(condition,actor):
            if hasattr(self,'executed'):self.executed.append((actor,node))
            if get(node,'type') in {'surface_detection','shore_attack','trickleback_mod','speed'}:
                self.properties[actor,get(node,'type'),get(node,'which'),get(node,'where')]+=float(get(node,'value',0))
                return
        return super().command(node,actor)

    def test(self, node, actor):
        results=[]
        for k,v in node:
            if k=='division_exists':
                results.append(int(get(v,'type'))==28632 and 1<=int(get(v,'id'))<=31)
            elif k=='carrier':
                who=get(v,'country',actor);results.append(self.types[who,'carrier']>=float(get(v,'value')))
            elif k=='losses':
                results.append(False)
            elif k=='month':
                months='january february march april may june july august september october november december'.split()
                results.append(self.month>=months.index(v))
            else:results.append(super().test([(k,v)],actor))
        return all(results)


PROFILES = (
    ('opening',1933), ('home',1933), ('home',1934), ('home',1935),
    ('home',1936), ('home',1938), ('home',1940),
    ('china',1937), ('prewar_owned',1939), ('prewar_owned',1940),
    ('early_chinese_partner',1938), ('early_chinese_partner',1939),
    ('pacific_opening',1941), ('pacific_occupied',1941), ('pacific_occupied',1942), ('friendly_thai',1942),
    ('pacific_fueled',1942), ('us_campaign',1942), ('us_frontier',1942),
    ('regional_puppets',1943), ('regional_neutrals',1943),
    ('pacific_owned',1943), ('partners',1943), ('regional',1943),
    ('second_callup',1943), ('third_callup',1944),
    ('peace_owned',1945), ('peace_partners',1947), ('peace_owned',1947),
    ('peace_owned',1950), ('soviet_choice',1942), ('broken_hold',1943),
)


def fixture(profile, year):
    w=AuditWorld();w.year=year;w.month=11;w.day=max(0,(year-1933)*360)
    w.resources['JAP'].update(money=10000,supplies=100000,energy=100000,metal=10000,oil=0)
    w.armies['JAP']=100;w.types['JAP','carrier']=8
    w.national_losses={t:0 for t in w.countries};w.vp_losses={t:0 for t in w.countries}
    w.wars.clear();w.flags.pop('JX_PACIFIC',None)
    w.native_events.update(('2011006','9300220'))
    if profile=='opening':w.flags.clear()
    if profile=='home':w.resources['JAP']['oil']=5000
    if profile in {'china','prewar_owned'}:
        w.addwar('JAP','CHI');w.national_losses['CHI']=80;w.vp_losses['CHI']=80
        for p,t in list(w.owned.items()):
            if t=='CHI':w.controlled[p]='JAP'
    if profile=='prewar_owned':
        for p in (1337,1338):w.owned[p]=w.controlled[p]='JAP'
        w.addwar('GER','ENG')
    if profile not in {'opening','home','china','prewar_owned','early_chinese_partner'}:
        w.flags['JX_PACIFIC']=1
        w.history[str(BY_KEY['pacific_open'].id)]=max(0,w.day-900)
        w.history[str(BY_KEY['national_callup_1941'].id)]=max(0,w.day-900)
        w.history[str(BY_KEY['national_callup_1942'].id)]=max(0,w.day-400)
        w.flags['JX_home_fuel_DONE']=1
        w.flags['JX_LAND_AIR_REORG_DONE']=1
        for t in list(w.countries):
            if t not in {'JAP','MAN','GER','ITA'}:
                w.addwar('JAP',t);w.national_losses[t]=80;w.vp_losses[t]=80
        for p in w.owned:w.controlled[p]='JAP'
    if profile in {'pacific_owned','peace_owned'}:
        for p in w.owned:w.owned[p]='JAP'
    if profile in {'partners','regional','peace_partners'}:
        for tag in ('U87','IND'):
            w.countries.add(tag);w.masters[tag]='JAP';w.groups[tag]='Japan'
            _,ps=source_country(tag)
            for p in ps:w.owned[p]=w.controlled[p]=tag
            w.wars={pair for pair in w.wars if tag not in pair}
        for p in (1337,1338,1378,1390):w.owned[p]=w.controlled[p]='U87'
        if profile=='regional':
            w.countries.discard('CGX');w.countries.discard('CYN')
    if profile.startswith('peace'):
        w.wars.clear()
    if profile=='soviet_choice':
        w.wars={pair for pair in w.wars if 'SOV' not in pair}
    if profile=='pacific_opening':w.flags.pop('JX_PACIFIC',None)
    if profile=='friendly_thai':
        w.groups['SIA']='Japan';w.masters['SIA']='JAP'
        w.wars={pair for pair in w.wars if 'SIA' not in pair}
    if profile=='second_callup':w.flags['JX_NATIONAL_CALLUP_1941_DONE']=1
    if profile=='third_callup':w.flags.update(JX_NATIONAL_CALLUP_1941_DONE=1,JX_NATIONAL_CALLUP_1942_DONE=1)
    if profile=='broken_hold':
        w.flags['JX_US_PENDING']=1;w.controlled[1734]='USA'
    if profile=='pacific_fueled':w.resources['JAP']['oil']=10000
    if profile=='early_chinese_partner':
        w.countries.discard('CHI');w.countries.add('U87');w.masters['U87']='JAP';w.groups['U87']='Japan'
        _,ps=source_country('U87')
        for p in ps:w.owned[p]=w.controlled[p]='U87'
        w.owned[1337]=w.controlled[1337]='U87';w.flags['JX_china_SETTLED']=1
    if profile in {'regional_puppets','regional_neutrals'}:
        for tag,key in (('PHI','philippines'),('INO','indonesia'),('MLY','malaya')):
            w.countries.add(tag)
            w.wars={pair for pair in w.wars if tag not in pair}
            w.access.update({('JAP',tag),(tag,'JAP')})
            _,ps=source_country(tag)
            for p in ps:w.owned[p]=w.controlled[p]=tag
            if profile=='regional_puppets':
                w.masters[tag]='JAP';w.groups[tag]='Japan'
            else:
                w.masters.pop(tag,None);w.groups.pop(tag,None)
                w.flags['JX_'+key+'_NEUTRAL']=1;w.flags['JX_'+key+'_SETTLED']=1
    if profile in {'us_campaign','us_frontier'}:
        w.flags['JX_USC_LANDING_DONE']=1
        w.history[str(BY_KEY['usc_landing'].id)]=w.day-300
        if profile=='us_frontier':
            for p in (1908,1896,1900,1914,1832,1809):w.owned[p]=w.controlled[p]='USA'
    return w


def effect_graph(e, seen=None):
    seen=set() if seen is None else seen
    if e.key in seen:return set()
    seen=seen|{e.key};effects=set()
    for a in e.actions:
        for c in a.commands:
            n=parse(c);kind=get(n,'type')
            if kind in {'event','trigger'}:
                target=str(get(n,'which')).removeprefix('@')
                if target in BY_KEY:effects |= effect_graph(BY_KEY[target],seen)
            elif kind not in {None,'setflag','clrflag','local_setflag','local_clrflag'}:
                effects.add(kind)
    return effects


def audit():
    rows=[];uncovered=[];unfundable=[];empty_action_sets=[];delivery_failures=[]
    all_roots=[e for e in EVENTS if (e.country=='JAP' or (e.country=='USA' and e.module=='us_campaign_content')) and not e.triggered and e.gate!='ai = yes ai = no']
    # R12 free issues/model resolvers need native implicit-model and research-
    # order simulation, supplied by the independent companion audit. Do not
    # claim the older campaign fixtures cover those newly registered classes.
    unique_roots=[e for e in all_roots if e.module in {'unique_unit_introductions','unique_unit_upgrades'}]
    roots=[e for e in all_roots if e not in unique_roots]
    worlds={(profile,year):fixture(profile,year) for profile,year in PROFILES}
    for e in sorted(roots,key=lambda x:(x.year,x.id)):
        witnesses=[];fundable=[];action_witnesses=[]
        for profile,year in PROFILES:
            w=worlds[profile,year]
            if available(w,e.key):
                witnesses.append(profile+' '+str(year))
                for i,a in enumerate(e.actions):
                    if not a.gate or w.test(parse(resolve(a.gate)),e.country):
                        action_witnesses.append((profile,year,i))
                    if a.commands and (not a.gate or w.test(parse(resolve(a.gate)),e.country)):
                        if any(get(parse(c),'type') in {'money','supplies'} and float(get(parse(c),'value',0))<0 for c in a.commands):
                            fundable.append((profile,year,i))
        paid=any(get(parse(c),'type')=='event' and '_finish_' in c for a in e.actions for c in a.commands)
        if not witnesses:uncovered.append(e.key)
        if witnesses and not action_witnesses:empty_action_sets.append(e.key)
        if paid and not fundable:unfundable.append(e.key)
        delivered=None;delivery_effects=[]
        if paid and fundable:
            profile,year,index=fundable[0]
            w=copy.deepcopy(worlds[profile,year])
            try:
                assert w.action(e.key,index), 'Witness could not select its funded action'
                w.executed=[]
                delay=max(int(get(parse(c),'when',0)) for c in e.actions[index].commands if get(parse(c),'type')=='event')
                w.advance(delay+2)
                delivered=bool(w.flags.get('JX_'+e.key+'_DONE'))
                if not delivered:delivery_failures.append((e.key,'No completion receipt'))
                for actor,node in w.executed:
                    kind=get(node,'type')
                    if kind in {'setflag','clrflag','event','trigger',None,'ai'}:continue
                    if kind in {'money','supplies','oilpool','manpowerpool'} and float(get(node,'value',0))<=0:continue
                    delivery_effects.append(actor+': '+kind+' '+str(get(node,'which',''))+' '+str(get(node,'value','')))
                if not delivery_effects:delivery_failures.append((e.key,'Completion contained no applied gameplay award'))
            except (AssertionError,KeyError,ValueError) as ex:
                delivered=False;delivery_failures.append((e.key,str(ex)))
        rows.append(dict(key=e.key,id=e.id,country=e.country,year=e.year,mode='manual decision' if e.decision else 'automatic',
                         witnesses=witnesses,fundable=fundable,effects=sorted(effect_graph(e)),paid_project=paid,delivery_checked=delivered,delivery_effects=delivery_effects))
    companion=Path(__file__).with_name('UNIQUE_UNIT_COLD_AUDIT.json')
    unique_audit=json.loads(companion.read_text()) if companion.exists() else {'passed':False,'reason':'Companion review has not run'}
    return dict(coverage_scope='Legacy campaign offers; all current specialist introductions and model resolvers are covered by the companion native-class audit',
                total_active_entries=len(all_roots),legacy_entries=len(roots),
                unique_entries=[e.key for e in unique_roots],unique_companion_file=companion.name,unique_companion=unique_audit,
                profiles=PROFILES,offers=rows,uncovered=uncovered,unfundable=unfundable,empty_action_sets=empty_action_sets,delivery_failures=delivery_failures)


if __name__=='__main__':
    report=audit()
    path=Path(__file__).with_name('EVENT_ACCESSIBILITY_MATRIX.json')
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    assert not report['uncovered'], report['uncovered']
    assert not report['unfundable'], report['unfundable']
    assert not report['empty_action_sets'], report['empty_action_sets']
    assert not report['delivery_failures'], report['delivery_failures']
    assert not report['unique_entries'] or report['unique_companion'].get('passed'), report['unique_companion']
    print(json.dumps(dict(offers=len(report['offers']),uncovered=report['uncovered'],unfundable=report['unfundable'],empty_action_sets=report['empty_action_sets'],delivery_failures=report['delivery_failures'],path=str(path))))

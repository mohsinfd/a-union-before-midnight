"""Offline event-state tests; these do not start or emulate the game engine.

The small model verifies declared flags, costs, receipts, ownership and war
relationships under the documented command contract. Engine behaviour is still
for the user's playtest, especially government changes and alliance peace.
"""
from collections import defaultdict
import copy
import heapq
import json
from pathlib import Path
import unittest
import csv
from build import prepare_catalog,EVENTS,IDS,resolve,parse,get,getall,SOURCE,TARGET,GAME,read,source_country

prepare_catalog()
BY_KEY={e.key:e for e in EVENTS}
BY_ID={str(e.id):e for e in EVENTS}
BASE_OWNED={};BASE_BUILDINGS={}
MAP_AREAS=defaultdict(set)
for row in csv.DictReader(read(GAME/'map/Map_1/Province.csv').splitlines(),delimiter=';'):
    if not str(row.get('Id','')).isdigit():continue
    p=int(row['Id']);BASE_BUILDINGS[p,'ic']=float(row.get('IC') or 0);BASE_BUILDINGS[p,'infrastructure']=float(row.get('Infrastructure') or 0)
    MAP_AREAS[row['Area']].add(p)
for path in SOURCE.glob('scenarios/1933/*.inc'):
    root=parse(read(path))
    for c in getall(root,'country'):
        for _,p in get(c,'ownedprovinces',[]):BASE_OWNED[int(p)]=get(c,'tag')
    for pv in getall(root,'province'):
        p=int(get(pv,'id'))
        for kind in ('ic','infrastructure','air_base','naval_base','anti_air','coastalfort','landfort','radar_station'):
            v=get(pv,kind)
            if v is None:continue
            key={'anti_air':'flak','coastalfort':'coastal_fort','landfort':'land_fort'}.get(kind,kind)
            if isinstance(v,list):BASE_BUILDINGS[p,key]=float(get(v,'size',0))
            elif kind=='ic':BASE_BUILDINGS[p,key]=BASE_BUILDINGS.get((p,key),0)+float(v)
            else:BASE_BUILDINGS[p,key]=float(v)


class World:
    def __init__(self):
        self.countries=set("JAP ENG USA SOV GER ITA MAN U02 CHI SIA INO PHI AST NZL PER IRQ EGY".split())
        self.flags={"JX_ACTIVE":1,"JX_PACIFIC":1}
        self.owned={};self.controlled={};self.cores={}
        self.resources=defaultdict(lambda:{"money":10000.,"supplies":100000.,"oil":10000.,"manpower":500.,"energy":10000.,"metal":10000.,"rare_materials":10000.})
        self.armies=defaultdict(int);self.navies=defaultdict(int);self.types=defaultdict(int)
        self.masters={"MAN":"JAP","U02":"ENG","INO":"HOL","PHI":"USA"}
        self.access=set();self.groups={"JAP":"Japan","MAN":"Japan","ENG":"Allies","USA":"Allies","AST":"Allies","NZL":"Allies","U02":"Allies","GER":"Axis","ITA":"Axis","SOV":"Comintern"}
        self.wars=set();self.queue=[];self.sequence=0;self.day=0;self.orders=[];self.received=[];self.history={};self.native_events=set();self.trades=[];self.properties=defaultdict(float)
        self.technologies=None;self.models=defaultdict(set);self.activated=set()
        self.deployed_units=[];self.current_corps={}
        self.country_tech={};self.buildings=defaultdict(float,BASE_BUILDINGS);self.blocked_buildings=set();self.unsupplied=set();self.free_ic=defaultdict(float)
        self.national_losses={};self.vp_losses={};self.year=None;self.blocked_transfers=set();self.native_triggered=[]
        for tag in ("JAP","ENG","SOV","USA","U02","CHI","SIA","INO","PHI","AST","NZL","PER","IRQ","EGY"):
            try:_,provs=source_country(tag)
            except Exception:provs=[]
            self.cores[tag]=set(provs)
        self.owned.update(BASE_OWNED);self.controlled.update(BASE_OWNED)
        self.addwar("JAP","ENG");self.addwar("JAP","USA");self.addwar("JAP","SOV");self.addwar("GER","SOV")

    def group(self,tag):
        return {t for t,g in self.groups.items() if g==self.groups.get(tag)} if tag in self.groups else {tag}

    def addwar(self,a,b):
        self.wars.update(frozenset((x,y)) for x in self.group(a) for y in self.group(b) if x!=y)

    def atwar(self,a,b):return frozenset((a,b)) in self.wars

    def test(self,node,actor):
        checks=[]
        for k,v in node:
            if k=="AND":checks.append(self.test(v,actor))
            elif k=="OR":checks.append(any(self.test([(k2,v2)],actor) for k2,v2 in v))
            elif k=="NOT":checks.append(not any(self.test([(k2,v2)],actor) for k2,v2 in v))
            elif k=="flag":
                if isinstance(v,list):
                    actual=self.flags.get(get(v,'which'));want=int(get(v,'value',1));mode=int(get(v,'when',1))
                    checks.append(actual is not None and {-2:actual<want,-1:actual<=want,0:actual==want,1:actual>=want,2:actual>want}[mode] if actual is not None else False)
                else:checks.append(bool(self.flags.get(v)))
            elif k=="exists":checks.append(v in self.countries)
            elif k=="ispuppet":checks.append(v in self.masters)
            elif k=="puppet":
                tags=getall(v,"country");checks.append(self.masters.get(tags[0])==tags[1])
            elif k=="alliance":
                tags=getall(v,"country");checks.append(tags[1] in self.group(tags[0]))
            elif k=="access":
                tags=getall(v,"country");checks.append(tuple(tags) in self.access)
            elif k=="war":
                tags=getall(v,"country");checks.append(self.atwar(*tags))
            elif k in {"control","owned"}:
                pv=int(get(v,"province"));tag=get(v,"data",actor)
                owner=(self.controlled if k=="control" else self.owned).get(pv)
                checks.append(owner in self.group(actor) if tag=="-3" else owner==(actor if tag=="-1" else tag))
            elif k in {"money","supplies","manpower","oil","energy","metal","rare_materials"}:checks.append(self.resources[actor][k]>=float(v))
            elif k=='ic':
                who=get(v,'country',actor) if isinstance(v,list) else actor;need=float(get(v,'value',0)) if isinstance(v,list) else float(v)
                checks.append(sum(self.buildings[p,'ic'] for p,t in self.owned.items() if t==who and self.controlled.get(p)==who)+self.free_ic[who]>=need)
            elif k=='building':checks.append(self.buildings[int(get(v,'province')),get(v,'type')]+1e-8>=float(get(v,'value')))
            elif k in {'convoypool','escortpool'}:checks.append(self.properties[(actor,'transport_pool' if k=='convoypool' else 'escort_pool','-1',None)]>=float(v))
            elif k in {'transport','destroyer','garrison','infantry'}:checks.append(self.types[actor,k]>=float(get(v,'value')))
            elif k in {"army","navy"}:
                tag=get(v,"country",actor) if isinstance(v,list) else actor
                size=float(get(v,"size",0)) if isinstance(v,list) else float(v)
                checks.append((self.armies if k=="army" else self.navies)[tag]>=size)
            elif k=='event':
                eid=get(v,'id') if isinstance(v,list) else v
                recorded=self.history.get(eid,0 if eid in self.native_events else None)
                checks.append(recorded is not None and self.day-recorded>=int(get(v,'days',0) if isinstance(v,list) else 0))
            elif k=='country':checks.append(actor==v)
            elif k=='technology':
                who=get(v,'country',actor) if isinstance(v,list) else actor;tech=get(v,'value') if isinstance(v,list) else str(v)
                known=self.country_tech.get(who,self.technologies)
                checks.append(True if known is None else str(tech) in known)
            elif k=='atwar':checks.append(any(actor in w for w in self.wars)==(v=='yes'))
            elif k=='area':
                ps=MAP_AREAS[get(v,'area')];who=get(v,'country',actor)
                checks.append(bool(ps) and all(self.controlled.get(p)==who for p in ps))
            elif k=='year':checks.append(True if self.year is None else self.year>=int(v))
            elif k=='lost_national':
                who=get(v,'country',actor)
                checks.append(True if who not in self.national_losses else self.national_losses[who]>=float(get(v,'value')))
            elif k=='lost_VP':checks.append(self.vp_losses.get(get(v,'country',actor),0)>=float(get(v,'value')))
            elif k in {"carrier","losses","ai","local_flag","technology"}:
                # These tests exercise triggered transitions; scenario eligibility
                # and engine counters are checked separately in static/QA docs.
                checks.append(True)
            else:raise AssertionError("Unmodelled predicate "+str(k))
        return all(checks)

    def action(self,key,index=0):
        e=BY_KEY[key];actor=e.country
        if actor not in self.countries:return False
        a=e.actions[index]
        if a.gate and not self.test(parse(resolve(a.gate)),actor):return False
        for text in a.commands:self.command(parse(resolve(text)),actor)
        self.received.append(key)
        self.history[str(e.id)]=self.day
        return True

    def dispatch(self,key):
        e=BY_KEY[key]
        for i,a in enumerate(e.actions):
            if (not a.gate or self.test(parse(resolve(a.gate)),e.country)) and (a.chance>0 or not a.name):
                return self.action(key,i)
        # A single available fallback is the engine's effective choice even if
        # its AI chance is zero; choices with multiple alternatives need policy.
        valid=[i for i,a in enumerate(e.actions) if not a.gate or self.test(parse(resolve(a.gate)),e.country)]
        if len(valid)==1:return self.action(key,valid[0])
        raise AssertionError("Ambiguous or empty action set: "+key+" "+str(valid))

    def command(self,n,actor):
        condition=get(n,"trigger")
        if condition and not self.test(condition,actor):return
        typ=get(n,"type");value=get(n,"value");which=get(n,"which")
        if typ in {"money","supplies","manpowerpool","oilpool","energypool","metalpool","rarematerialspool"}:
            key={"manpowerpool":"manpower","oilpool":"oil","energypool":"energy","metalpool":"metal","rarematerialspool":"rare_materials"}.get(typ,typ);self.resources[actor][key]+=float(value)
        elif typ=='free_ic':self.free_ic[actor]+=float(value)
        elif typ in {'free_manpower','wartime_ic_mod','repair_mod'}:
            self.properties[actor,typ,which,get(n,'where')]+=float(value)
        elif typ=='construct':
            p=int(get(n,'where'));delta=float(value);key=(p,which)
            if delta>0 and (self.owned.get(p)!=actor or self.controlled.get(p)!=actor or key in self.blocked_buildings or p in self.unsupplied):return
            if delta>0:
                cap=200 if which=='ic' else 100 if which=='infrastructure' else 10
                if self.buildings[key]+delta>cap:return
            self.buildings[key]=max(0,self.buildings[key]+delta)
            self.properties[(actor,typ,which,get(n,'where'))]+=delta
        elif typ=='new_model':self.models[(actor,which)].add(int(value))
        elif typ=='scrap_model':self.models[(actor,which)].discard(int(value))
        elif typ=='activate_unit_type':self.activated.add((actor,which))
        elif typ=='deactivate_unit_type':self.activated.discard((actor,which))
        elif typ=="setflag":self.flags[which]=int(value or 1)
        elif typ=="clrflag":self.flags.pop(which,None)
        elif typ=="event":
            key=BY_ID[which].key;self.sequence+=1
            heapq.heappush(self.queue,(self.day+int(get(n,"when",0)),self.sequence,key))
        elif typ=="trigger":
            if which in BY_ID:self.dispatch(BY_ID[which].key)
            else:
                # The three retained stock helpers revoke US access only.
                tags={'2066001':'PHI','2077001':'LIB','2049064':'CUB'}
                assert which in tags,'Unmodelled native receiver '+str(which)
                self.native_triggered.append(which);self.access.discard((tags[which],'USA'))
        elif typ=="end_puppet":self.masters.pop(actor,None)
        elif typ=='end_mastery':self.masters.pop(which,None)
        elif typ=="leave_alliance":
            self.groups.pop(actor,None)
            if get(n,"when")=="1":
                enemies={next(iter(w-{actor})) for w in self.wars if actor in w}
                self.wars={w for w in self.wars if actor not in w}
                for p,owner in self.owned.items():
                    if owner==actor and self.controlled.get(p) in enemies:self.controlled[p]=actor
        elif typ=="peace":
            if value=="1":self.wars.discard(frozenset((actor,which)))
            else:
                a,b=self.group(actor),self.group(which)
                self.wars={w for w in self.wars if not any(x in w and y in w for x in a for y in b)}
        elif typ=="country":
            self.countries.discard(actor);self.countries.add(which)
            self.owned={p:which if t==actor else t for p,t in self.owned.items()}
            self.controlled={p:which if t==actor else t for p,t in self.controlled.items()}
            old_resources=self.resources[actor]
            self.resources.pop(actor)
            self.resources[which]=old_resources
            self.armies[which]=self.armies.pop(actor,0)
            self.navies[which]=self.navies.pop(actor,0)
            for (t,unit),count in list(self.types.items()):
                if t==actor:self.types[which,unit]+=count;self.types.pop((t,unit),None)
        elif typ=="inherit":
            self.countries.discard(which)
            self.owned={p:actor if t==which else t for p,t in self.owned.items()}
            self.controlled={p:actor if t==which else t for p,t in self.controlled.items()}
            old_army=self.armies.pop(which,0);old_navy=self.navies.pop(which,0)
            if value=='1':self.armies[actor]+=old_army;self.navies[actor]+=old_navy
            for (t,unit),count in list(self.types.items()):
                if t==which:
                    if value=='1':self.types[actor,unit]+=count
                    self.types.pop((t,unit),None)
            self.wars={w for w in self.wars if which not in w}
            self.groups.pop(which,None);self.masters.pop(which,None)
        elif typ=="independence":
            if which in self.countries:return
            node=get(parse(read(TARGET/'db/revolt.txt')),which)
            provs=[int(p) for field in ('minimum','extra') for _,p in get(node,field,[])]
            cap=int(get(node,"capital"))
            if self.owned.get(cap)!=actor:return
            self.countries.add(which)
            for p in provs:
                if self.owned.get(p)==actor:self.owned[p]=which;self.controlled[p]=which
        elif typ=="make_puppet":
            if which not in self.countries:return
            self.masters[which]=actor;self.groups[which]=self.groups.get(actor,"group_"+actor)
            for w in list(self.wars):
                if actor in w:self.wars.add(frozenset((which,next(iter(w-{actor})))))
        elif typ=="secedeprovince":
            p=int(value)
            if p in self.blocked_transfers:return
            if self.owned.get(p)==actor:self.owned[p]=which
            if self.controlled.get(p)==actor:self.controlled[p]=which
        elif typ=="access":self.access.add((actor,which))
        elif typ=='end_access':self.access.discard((actor,which))
        elif typ in {'dissent','set_relation','set_domestic','domestic'}:
            key=(actor,typ,which,None)
            if typ.startswith('set_'):self.properties[key]=float(value)
            else:self.properties[key]+=float(value)
        elif typ=="build_division":self.orders.append((actor,which,int(get(n,"when",1))))
        elif typ=="add_division":
            self.types[actor,value]+=1
            if value in {"destroyer","transport"}:self.navies[actor]+=1
            else:self.armies[actor]+=1
            where=get(n,'where');damage=float(where) if where is not None and str(where).replace('.','',1).lstrip('-').isdigit() else 0
            self.deployed_units.append({'country':actor,'name':which,'type':value,'model':int(get(n,'when',0)),
                                        'strength':max(0,100+min(0,damage)),'max_strength':100,
                                        'location':self.current_corps.get(actor)})
        elif typ=='add_corps':self.current_corps[actor]=int(get(n,'where'))
        elif typ=='damage_division':
            targets=[u for u in self.deployed_units if u['country']==value and u['name']==which]
            if not targets:raise AssertionError('Named strength command has no matching formation: '+str(which))
            for unit in targets:
                unit['strength']=max(0,min(unit['max_strength'],unit['strength']-unit['max_strength']*float(get(n,'where'))/100))
        elif typ=='max_amphib_mod':
            slot=(actor,typ,which,get(n,'where'))
            self.properties[slot]=self.properties[slot]+float(value) if get(n,'when','0')=='1' else float(value)
        elif typ=="addcore":self.cores.setdefault(actor,set()).add(int(which))
        elif typ=="removecore":self.cores.setdefault(actor,set()).discard(int(which))
        elif typ=='trade':
            flows={key:float(get(n,key,0)) for key in ('money','supplies','oil','metal','energy','rare_materials')}
            self.trades.append({'which':which,'where':get(n,'where'),'start':self.day,'end':self.day+int(get(n,'when')),'flows':flows,'cancelled':False})
        elif typ=='end_trades':
            for t in self.trades:
                if {t['which'],t['where']}=={which,get(n,'where')}:t['cancelled']=True
        elif typ in {"construct","transport_pool","escort_pool","build_time","build_cost","industrial_modifier","tc_mod","attrition_mod","range","max_organization","morale","fuel_consumption","research_mod","frozen_move","frozen_defense","river_attack","urban_attack","naval_defense","naval_attack","hard_attack","add_prov_resource","stockpile","surface_detection","shore_attack","max_amphib_mod","trickleback_mod","speed"} or typ in {get(c,'type') for _,_,_,c in __import__('specialist_units').MIRRORS}:
            self.properties[(actor,typ,which,get(n,"where"))]+=float(value or 0)
        elif typ in {"ai","non_aggression","add_corps","removecore","headofstate","headofgovernment","chiefofstaff","gain_tech","activate_unit_type","new_model","add_brigade","sleepevent"}:pass
        else:raise AssertionError("Unmodelled command "+str(typ))

    def apply_trade_ledger(self,start,end):
        # This is arithmetic under full delivery, not an engine trade simulator.
        for tag in self.countries:
            self.resources[tag]['manpower']+=(end-start)*self.properties.get((tag,'free_manpower',None,None),0)
        for t in self.trades:
            if self.atwar(t['which'],t['where']):t['cancelled']=True
            if t['cancelled']:continue
            duration=max(0,min(end,t['end'])-max(start,t['start']))
            for key,amount in t['flows'].items():
                self.resources[t['where']][key]-=duration*amount
                self.resources[t['which']][key]+=duration*amount

    def advance(self,days):
        until=self.day+days
        while self.queue and self.queue[0][0]<=until:
            when,_,key=heapq.heappop(self.queue)
            self.apply_trade_ledger(self.day,when);self.day=when
            if BY_KEY[key].country in self.countries:self.dispatch(key)
        self.apply_trade_ledger(self.day,until)
        self.day=until


class EventTests(unittest.TestCase):
    def legacy_action(self,w,key,index=0):
        """Seed an older save's funded state without claiming a live offer.

        Retired parents cannot be selected in a new campaign. Their registered
        completion/expiry receivers must still honour work already paid for.
        """
        self.assertEqual(BY_KEY[key].gate,'ai = yes ai = no',key)
        for text in BY_KEY[key].actions[index].commands:
            w.command(parse(resolve(text)),BY_KEY[key].country)
        return True

    def legacy_paid_project(self,w,key,index=0,*,cash,stock,days):
        """Load an already-paid pending state after its parent became inert."""
        self.assertEqual(BY_KEY[key].gate,'ai = yes ai = no',key)
        self.assertTrue(all(not a.commands for a in BY_KEY[key].actions),key)
        w.resources['JAP']['money']-=cash
        w.resources['JAP']['supplies']-=stock
        w.flags['JX_'+key+'_PENDING']=1
        w.command(parse(resolve(f'type = event which = @{key}_finish_{index} where = JAP when = {days}')),'JAP')

    def fresh_partner(self,tag):
        w=World();w.countries.add(tag);w.masters[tag]='JAP';w.groups[tag]='Japan'
        w.wars={pair for pair in w.wars if tag not in pair}
        w.resources[tag]={k:0. for k in w.resources[tag]}
        return w

    def test_manual_indonesian_puppet_gets_distinct_convoys_and_naval_transports(self):
        w=self.fresh_partner('INO');w.owned[1647]=w.controlled[1647]='INO'
        w.dispatch('relief_INO');w.advance(1)
        self.assertEqual(w.properties[('INO','transport_pool','-1',None)],120)
        self.assertEqual(w.properties[('INO','escort_pool','-1',None)],25)
        self.assertEqual(w.types['INO','transport'],1);self.assertEqual(w.types['INO','destroyer'],1)
        self.assertEqual(w.armies['INO'],2)
        self.assertTrue(w.flags['JX_AID_INO_NAVY_DONE'])

    def test_existing_destroyer_does_not_block_the_missing_transport(self):
        w=self.fresh_partner('PHI');w.owned[1565]=w.controlled[1565]='PHI'
        w.navies['PHI']=1;w.types['PHI','destroyer']=1
        w.dispatch('relief_PHI');w.advance(63)
        self.assertEqual(w.types['PHI','destroyer'],1);self.assertEqual(w.types['PHI','transport'],1)
        self.assertEqual(w.navies['PHI'],2)

    def test_retained_manila_uses_treaty_port_and_other_home_province_for_army(self):
        w=self.fresh_partner('PHI');w.owned[1565]=w.controlled[1565]='JAP'
        w.flags['JX_philippines_BASES']=1
        from release_support import META
        from build import source_country
        _,provs=source_country('PHI');other=next(p for p in provs if p!=1565)
        w.owned[other]=w.controlled[other]='PHI'
        w.dispatch('relief_PHI');w.advance(1)
        self.assertEqual(w.owned[1565],'JAP');self.assertEqual(w.types['PHI','transport'],1)
        self.assertEqual(w.armies['PHI'],2)
        self.assertTrue(w.flags['JX_AID_PHI_NAVY_DONE'])

    def test_large_inherited_force_and_merchant_pools_are_not_duplicated(self):
        w=self.fresh_partner('INO');w.armies['INO']=30;w.navies['INO']=12
        w.types['INO','transport']=3;w.types['INO','destroyer']=9
        w.properties['INO','transport_pool','-1',None]=300;w.properties['INO','escort_pool','-1',None]=80
        w.dispatch('relief_INO');w.advance(1)
        self.assertEqual(w.armies['INO'],30);self.assertEqual(w.navies['INO'],12)
        self.assertEqual(w.properties['INO','transport_pool','-1',None],300)
        self.assertEqual(w.properties['INO','escort_pool','-1',None],80)

    def test_release_support_cannot_repeat_after_reannexation(self):
        w=self.fresh_partner('INO');w.dispatch('relief_INO');w.advance(1)
        before=w.resources['INO'].copy();shipping=dict(w.properties);army=w.armies['INO']
        w.dispatch('relief_INO');w.dispatch('relief_INO_army');w.dispatch('relief_INO_navy');w.advance(90)
        self.assertEqual(w.resources['INO'],before);self.assertEqual(dict(w.properties),shipping)
        self.assertEqual(w.armies['INO'],army)

    def test_small_coastal_state_gets_garrison_and_japanese_harbour_fallback(self):
        w=self.fresh_partner('BRU');w.owned[1625]=w.controlled[1625]='BRU'
        w.buildings[1625,'naval_base']=0
        w.dispatch('relief_BRU');w.advance(1)
        self.assertEqual(w.types['BRU','garrison'],1);self.assertEqual(w.types['BRU','infantry'],0)
        self.assertEqual(w.types['BRU','transport'],1)
        self.assertEqual(w.properties[('BRU','transport_pool','-1',None)],40)

    def test_no_port_delivery_retries_are_finite_and_do_not_claim_success(self):
        w=self.fresh_partner('PHI')
        for p,k in list(w.buildings):
            if k=='naval_base':w.buildings[p,k]=0
        w.dispatch('relief_PHI');w.advance(65)
        self.assertNotIn('JX_AID_PHI_NAVY_DONE',w.flags)
        self.assertTrue(w.flags['JX_AID_PHI_NAVY_CLOSED']);self.assertFalse(w.queue)

    def test_delayed_defence_does_not_support_a_new_enemy(self):
        w=self.fresh_partner('PHI')
        for p,owner in list(w.owned.items()):
            if owner=='PHI':w.controlled[p]='USA'
        w.dispatch('relief_PHI');w.masters.pop('PHI');w.addwar('JAP','PHI');w.advance(65)
        self.assertEqual(w.armies['PHI'],0);self.assertTrue(w.flags['JX_AID_PHI_ARMY_CLOSED'])

    def test_lost_ownership_before_completion_refunds_without_construction(self):
        w=World();before=w.resources['JAP'].copy();w.action('first_industry')
        original=w.buildings[1552,'ic'];w.owned[1554]='CHI';w.advance(270)
        self.assertEqual(w.buildings[1552,'ic'],original)
        self.assertEqual(w.resources['JAP'],before);self.assertNotIn('JX_first_industry_DONE',w.flags)

    def test_enemy_owned_base_cannot_take_building_payment(self):
        w=World();w.owned[1726]='AST';w.controlled[1726]='JAP';before=w.resources['JAP'].copy()
        self.assertFalse(w.action('rabaul_workshops',0));self.assertEqual(w.resources['JAP'],before)
        self.assertTrue(w.action('rabaul_workshops',1));w.advance(150)
        self.assertEqual(w.properties[('JAP','transport_pool','-1',None)],40)

    def test_verified_neutral_gets_starter_aid_without_inheriting_japanese_wars(self):
        w=World();w.masters.pop('SIA',None);w.groups.pop('SIA',None)
        w.flags.update(JX_thailand_NEUTRAL=1,JX_thailand_SETTLED=1)
        w.access.update({('SIA','JAP'),('JAP','SIA')});w.resources['SIA']['supplies']=0
        w.dispatch('relief_SIA');w.advance(1)
        self.assertTrue(w.flags['JX_AID_SIA_MAIN_DONE'])
        self.assertNotIn('SIA',w.masters);self.assertFalse(w.atwar('SIA','USA'))

    def test_allied_country_without_puppet_or_treaty_does_not_receive_release_aid(self):
        w=World();w.countries.add('ITA');w.groups['ITA']='Japan';before=w.resources['ITA'].copy()
        w.dispatch('relief_ITA');self.assertEqual(w.resources['ITA'],before)
        self.assertNotIn('JX_AID_ITA_MAIN_DONE',w.flags)

    def test_overseas_programmes_keep_a_deliverable_choice_under_occupation(self):
        for key,choice,p,days in [('suez',0,900,150),('forward_air',1,1653,120),('siberian_rail',0,1191,180),
                                  ('thai_connection',0,1415,150),('outer_oil',0,1089,180),('sumatra_oil',0,1636,120),
                                  ('borneo_oil',0,1632,120),('java_oil',0,1653,120)]:
            with self.subTest(project=key):
                w=World();w.owned[p]='ENG';w.controlled[p]='JAP';w.groups['SIA']='Japan'
                for q in [1191,1190,1169]:w.controlled[q]='JAP'
                w.action(key,choice);w.advance(days)
                self.assertTrue(w.flags.get('JX_'+key+'_DONE'))
                self.assertEqual(w.owned[p],'ENG')
                self.assertFalse(any(k[0]=='JAP' and k[1]=='construct' and v for k,v in w.properties.items()))

    def test_retired_class_cannot_be_recruited_after_late_research(self):
        w=World();w.technologies={'1100','1110','1120','1130'}
        self.assertEqual(BY_KEY['introduce_d_11'].gate,'ai = yes ai = no')
        w.dispatch('activate_d_11')
        self.assertNotIn(('JAP','d_11'),w.activated)

    def test_retired_base_force_receiver_does_not_unlock_recruitment(self):
        w=World();w.technologies={'1100'};w.dispatch('activate_d_10')
        self.assertNotIn(('JAP','d_10'),w.activated)

    def test_opening_deactivates_custom_production_without_removing_native_or_deployed_units(self):
        w=World();w.flags.pop('JX_ACTIVE')
        ordinary={'garrison','infantry','bergsjaeger','marine'}
        w.activated={('JAP',u) for u in ordinary|{'d_10','d_11','d_12'}}
        w.types['JAP','d_10']=2;w.types['JAP','marine']=3
        before=w.resources['JAP'].copy();types=dict(w.types)
        self.assertTrue(w.action('welcome'))
        self.assertEqual(w.activated,{('JAP',u) for u in ordinary})
        self.assertEqual(dict(w.types),types)
        self.assertEqual(w.resources['JAP'],before)
        self.assertTrue(w.flags['JX_ACTIVE'])

    def test_new_class_future_upgrade_is_japanese_and_flag_guarded(self):
        tree=parse(read(TARGET/'db/tech/infantry_tech.txt'))
        app=next(a for t in getall(tree,'technology') for a in getall(t,'application') if get(a,'id')=='1120')
        commands=[c for c in getall(get(app,'effects'),'command') if get(c,'which')=='d_11']
        self.assertEqual(len([c for c in commands if get(c,'type')=='new_model']),1)
        w=World();w.models[('JAP','d_11')]={1}
        for c in commands:w.command(c,'JAP')
        self.assertEqual(w.models[('JAP','d_11')],{1})
        w.flags['JX_JUNGLE_FORCE']=1
        for c in commands:w.command(c,'GER')
        self.assertFalse(w.models[('GER','d_11')])
        for c in commands:w.command(c,'JAP')
        self.assertEqual(w.models[('JAP','d_11')],{2})

    def test_legacy_base_force_payment_delivers_only_normal_garrison_tooling(self):
        w=World();w.resources['JAP']['manpower']=0;before=w.resources['JAP'].copy()
        self.legacy_paid_project(w,'base_force_orders',cash=70,stock=400,days=90)
        w.advance(90)
        self.assertEqual(w.resources['JAP']['money'],before['money']-70)
        self.assertEqual(w.resources['JAP']['supplies'],before['supplies']-400)
        self.assertEqual(w.resources['JAP']['manpower'],0)
        self.assertEqual(w.properties[('JAP','build_time','garrison',None)],-25)
        self.assertNotIn(('JAP','d_10'),w.activated)
        self.assertFalse(w.orders)
        before=dict(w.properties);w.dispatch('base_force_orders_finish_0')
        self.assertEqual(dict(w.properties),before)

    def test_thai_connection_refunds_when_alliance_ends(self):
        w=World();w.countries.add('SIA');w.groups['SIA']='Japan';w.controlled[1415]='JAP'
        before=w.resources['JAP'].copy();w.action('thai_connection')
        w.groups.pop('SIA');w.advance(150)
        self.assertEqual(w.resources['JAP'],before)
        self.assertFalse(w.properties[('JAP','tc_mod',None,None)])

    def test_remote_base_loss_refunds_instead_of_false_completion(self):
        w=World();w.controlled[2174]='JAP';before=w.resources['JAP'].copy()
        w.action('northern_station');w.controlled[2174]='USA';w.advance(180)
        self.assertEqual(w.resources['JAP'],before)
        self.assertNotIn('JX_northern_station_DONE',w.flags)

    def test_manchurian_contract_has_finite_paid_delivery(self):
        w=World();w.action('manchurian_contract');w.advance(90)
        before=w.resources['JAP'].copy();w.advance(720)
        self.assertAlmostEqual(w.resources['JAP']['energy']-before['energy'],6*720)
        self.assertAlmostEqual(w.resources['JAP']['supplies']-before['supplies'],-720)
        after=w.resources['JAP'].copy();w.advance(10)
        self.assertEqual(w.resources['JAP'],after)

    def test_nine_live_activities_are_manual_and_retired_offers_stay_unavailable(self):
        activities=[e for e in EVENTS if e.module=='activities' and not e.triggered]
        self.assertEqual(len(activities),18)
        live=[e for e in activities if e.gate!='ai = yes ai = no']
        self.assertEqual({e.key for e in live},{'island_depth','manchurian_contract','merchant_reserve',
            'berlin_barter','thai_connection','rabaul_workshops','colombo_station','northern_station',
            'homefront_breathing_space'})
        self.assertEqual(len(activities)-len(live),9)
        self.assertTrue(all(e.decision and getattr(e,'manual_only',False) for e in live))
        for e in live:
            self.assertEqual(len(e.actions),4)
            self.assertEqual(e.actions[2].commands,[])
        for e in activities:
            self.assertNotIn('ROUTE',e.gate)

    def test_island_activity_lost_base_refunds_and_does_not_fortify(self):
        w=World();w.controlled[1667]=w.controlled[1685]='JAP'
        before=w.resources['JAP'].copy();self.assertTrue(w.action('island_depth'))
        w.controlled[1667]='USA';w.advance(180)
        self.assertEqual(w.resources['JAP'],before)
        self.assertFalse(w.properties[('JAP','construct','coastal_fort','1667')])
        self.assertNotIn('JX_island_depth_DONE',w.flags)

    def test_legacy_airborne_training_has_real_discounts_and_cannot_deliver_twice(self):
        w=World();self.legacy_action(w,'airborne_force');w.advance(60)
        self.assertFalse(w.orders)
        self.assertEqual(w.properties[('JAP','build_time','paratrooper',None)],-30)
        self.assertEqual(w.properties[('JAP','build_time','transport_plane',None)],-30)
        self.assertFalse(w.action('airborne_force_finish_0'))
        self.assertEqual(w.properties[('JAP','build_time','paratrooper',None)],-30)

    def test_legacy_airborne_training_does_not_spend_recruitment_reserve(self):
        w=World();before=w.resources['JAP'].copy();self.legacy_action(w,'airborne_force')
        w.resources['JAP']['manpower']=0;w.advance(60)
        self.assertEqual(w.resources['JAP']['money'],before['money']-80)
        self.assertEqual(w.resources['JAP']['supplies'],before['supplies']-450)
        self.assertEqual(w.resources['JAP']['manpower'],0)
        self.assertFalse(w.orders)

    def test_legacy_air_defence_completions_need_no_manpower(self):
        w=World();w.controlled[1552]=w.controlled[1554]='JAP';w.resources['JAP']['manpower']=0
        self.legacy_action(w,'home_air_defence',1);w.advance(120)
        self.assertEqual(w.properties[('JAP','construct','flak','1552')],2)
        self.assertFalse(w.orders)
        v=World();v.resources['JAP']['manpower']=0;self.legacy_action(v,'home_air_defence',0);v.advance(120)
        self.assertEqual(v.properties[('JAP','build_time','interceptor',None)],-18)

    def test_legacy_activity_dismissal_and_cooldown_do_not_close_other_activities(self):
        w=World();self.legacy_action(w,'airborne_force',3);self.legacy_action(w,'mobile_columns',2)
        self.assertTrue(w.flags['JX_airborne_force_DISMISSED'])
        self.assertTrue(w.flags['JX_mobile_columns_WAIT']);w.advance(90)
        self.assertNotIn('JX_mobile_columns_WAIT',w.flags)
        self.assertTrue(w.flags['JX_airborne_force_DISMISSED'])
        self.assertNotIn('JX_island_depth_DISMISSED',w.flags)

    def test_legacy_medicine_recruitment_is_finite(self):
        w=World();before=w.resources['JAP']['manpower'];self.legacy_action(w,'field_medicine',1)
        w.advance(120);self.assertEqual(w.resources['JAP']['manpower'],before+18)
        self.assertFalse(w.action('field_medicine_finish_1'))
        self.assertEqual(w.resources['JAP']['manpower'],before+18)

    def test_industry_completes_once(self):
        w=World();self.assertTrue(w.action("first_industry"));w.advance(270)
        self.assertTrue(w.flags.get("JX_first_industry_DONE"));self.assertFalse(w.flags.get("JX_first_industry_PENDING"))
        before=dict(w.properties);self.assertFalse(w.action("first_industry_finish_0"));self.assertEqual(before,dict(w.properties))

    def test_one_lost_site_refunds(self):
        w=World();before=w.resources['JAP'].copy();w.action("first_industry");w.controlled[1554]='USA';w.advance(270)
        self.assertEqual(w.resources['JAP'],before);self.assertFalse(w.flags.get("JX_first_industry_DONE"))

    def test_legacy_marine_training_finishes_with_empty_recruitment_reserve(self):
        w=World();before=w.resources['JAP'].copy()
        self.legacy_paid_project(w,'snlf',cash=150,stock=900,days=60)
        w.resources['JAP']['manpower']=0;w.advance(60)
        self.assertEqual(w.resources['JAP']['money'],before['money']-150)
        self.assertEqual(w.resources['JAP']['supplies'],before['supplies']-900)
        self.assertEqual(w.properties[('JAP','build_time','marine',None)],-60)
        self.assertEqual(w.resources['JAP']['manpower'],0)
        self.assertNotIn(('JAP','d_12'),w.activated)
        self.assertFalse(w.orders)
        before=dict(w.properties);w.dispatch('snlf_finish_0')
        self.assertEqual(dict(w.properties),before)

    def test_retired_materials_and_college_offers_cannot_reopen_from_native_history(self):
        for key in ('materials1938','colleges1936'):
            gate=parse(BY_KEY[key].gate)
            self.assertEqual(getall(gate,'ai'),['yes','no'])
            # No possible AI state, including human Japan, satisfies both.
            for ai_value in ('yes','no'):
                self.assertFalse(all(v==ai_value for v in getall(gate,'ai')))

    def test_legacy_marine_completion_preserves_native_models_without_custom_reactivation(self):
        w=World();w.technologies={'1590','1600','1610'}
        w.models[('JAP','marine')]={5}
        self.legacy_paid_project(w,'snlf',cash=150,stock=900,days=60);w.advance(60)
        self.assertEqual(w.models[('JAP','marine')],{5})
        self.assertFalse(w.models[('JAP','d_12')])
        self.assertNotIn(('JAP','d_12'),w.activated)
        before=dict(w.properties);w.dispatch('activate_d_12')
        self.assertEqual(dict(w.properties),before)
        self.assertEqual(w.models[('JAP','marine')],{5})
        self.assertNotIn(('JAP','d_12'),w.activated)

    def test_snlf_research_hooks_are_gated_and_preserve_other_countries(self):
        tree=parse(read(TARGET/'db/tech/infantry_tech.txt'))
        app=next(a for t in getall(tree,'technology') for a in getall(t,'application') if get(a,'id')=='1620')
        commands=[c for c in getall(get(app,'effects'),'command') if get(c,'which')=='d_12']
        w=World();w.models[('JAP','d_12')]={2}
        for c in commands:w.command(c,'JAP')
        self.assertEqual(w.models[('JAP','d_12')],{2})
        w.flags['JX_SNLF_FORCE']=1
        for c in commands:w.command(c,'JAP');w.command(c,'GER')
        self.assertEqual(w.models[('JAP','d_12')],{3})
        self.assertFalse(w.models[('GER','d_12')])

    def test_legacy_snlf_training_alternative_trades_output_for_organisation(self):
        w=World();w.technologies={'1590'}
        self.legacy_paid_project(w,'snlf',1,cash=150,stock=900,days=60);w.advance(60)
        self.assertNotIn(('JAP','d_12'),w.activated)
        self.assertEqual(w.properties[('JAP','build_time','marine',None)],-30)
        self.assertEqual(w.properties[('JAP','max_organization','marine',None)],3)
        self.assertEqual(w.properties[('JAP','build_time','engineer',None)],-22)
        self.assertFalse(w.orders)
        before=dict(w.properties);w.dispatch('snlf_finish_1')
        self.assertEqual(dict(w.properties),before)

    def test_legacy_landing_rehearsal_awards_normal_marines_once_in_either_order(self):
        for first in (True,False):
            for legacy_flag in (True,False):
                with self.subTest(rehearsal_first=first,legacy_snlf_flag=legacy_flag):
                    w=World();w.technologies={'1590'}
                    if legacy_flag:w.flags['JX_SNLF_FORCE']=1
                    if first:self.legacy_action(w,'landing_rehearsal');w.advance(120)
                    self.legacy_paid_project(w,'snlf',cash=150,stock=900,days=60);w.advance(60)
                    if not first:self.legacy_action(w,'landing_rehearsal');w.advance(120)
                    self.assertEqual(w.properties[('JAP','river_attack','marine',None)],3)
                    self.assertEqual(w.properties[('JAP','build_time','marine',None)],-60)
                    self.assertNotIn(('JAP','d_12'),w.activated)
                    before=dict(w.properties)
                    w.dispatch('landing_rehearsal_finish_0');w.dispatch('activate_d_12')
                    self.assertEqual(dict(w.properties),before)

    def test_legacy_land_and_air_training_completions_do_not_require_manpower(self):
        for option,unit in ((0,'marine'),(1,'tactical_bomber')):
            w=World();w.resources['JAP']['manpower']=0
            self.legacy_action(w,'australian_prep',option);w.advance(60)
            self.assertTrue(w.flags['JX_australian_prep_DONE'])
            self.assertFalse(w.orders)
            self.assertEqual(w.properties[('JAP','build_time',unit,None)],-30 if unit=='marine' else -18)

    def test_legacy_med_training_and_building_alternatives_need_no_recruitment_reserve(self):
        for option in (0,1):
            w=World();w.resources['JAP']['manpower']=0
            w.owned[789]=w.controlled[789]='JAP';w.controlled[900]='JAP';w.buildings[789,'naval_base']=5
            self.legacy_action(w,'med_expedition',option);w.advance(90)
            self.assertTrue(w.flags.get('JX_med_expedition_DONE'))

    def test_poor_player_can_delay_or_dismiss(self):
        w=World();w.resources['JAP'].update(money=0,supplies=0,manpower=0)
        # A nonempty readiness block prevents the native engine's fallback to
        # the AI-disabled automatic trigger, while imposing no payment here.
        self.assertEqual(BY_KEY['first_industry'].ready,'year = 1933')
        self.assertFalse(w.action('first_industry',0));self.assertFalse(w.action('first_industry',1))
        self.assertTrue(w.action('first_industry',2))
        self.assertEqual(w.resources['JAP']['money'],0);self.assertEqual(w.resources['JAP']['supplies'],0)
        v=World();v.resources['JAP'].update(money=0,supplies=0,manpower=0)
        self.assertTrue(v.action('first_industry',3));self.assertTrue(v.flags['JX_first_industry_DISMISSED'])

    def commercial_world(self):
        w=World();w.flags.pop('JX_PACIFIC');w.wars={pair for pair in w.wars if not ('JAP' in pair and 'USA' in pair)}
        return w

    def test_early_trade_is_paid_and_has_correct_direction(self):
        w=self.commercial_world();before=w.resources['JAP'].copy();w.action('fx1933',0);w.advance(30)
        self.assertAlmostEqual(w.resources['JAP']['metal']-before['metal'],360)
        self.assertAlmostEqual(w.resources['JAP']['oil']-before['oil'],720)
        self.assertAlmostEqual(w.resources['JAP']['supplies']-before['supplies'],-120)
        self.assertAlmostEqual(w.resources['JAP']['money']-before['money'],-110)

    def test_early_trade_expires_without_auto_renewal(self):
        w=self.commercial_world();w.action('fx1933');w.advance(720);before=w.resources['JAP'].copy();w.advance(100)
        self.assertEqual(w.resources['JAP'],before);self.assertEqual(len(w.trades),1)
        self.assertFalse(w.action('fx1933'))

    def test_embargo_blocks_new_american_contract(self):
        w=self.commercial_world();w.native_events.add('2049026');before=w.resources['JAP'].copy()
        self.assertFalse(w.action('fx1933'));self.assertFalse(w.action('oil1934',0));self.assertEqual(w.resources['JAP'],before)

    def test_retired_staff_college_keeps_registered_ids_after_either_coup(self):
        for native in ('2011006','9300220'):
            w=self.commercial_world();w.native_events.add(native)
            self.assertEqual(BY_KEY['colleges1936'].gate,'ai = yes ai = no')
            self.assertIn('colleges1936_reconsider',BY_KEY)
            self.assertNotIn('JX_EARLY_colleges1936_DONE',w.flags)

    def test_embargo_trade_closure_stops_the_payment_ledger(self):
        w=self.commercial_world();w.action('fx1933');w.advance(30)
        w.command(parse('type = end_trades which = USA where = JAP'),'JAP');before=w.resources['JAP'].copy();w.advance(100)
        self.assertEqual(w.resources['JAP'],before)

    def test_legacy_allocation_costs_reverse_exactly_once(self):
        w=World();self.legacy_action(w,'allocations1933',0)
        self.assertEqual(w.properties[('JAP','build_cost','naval','relative')],-4)
        self.assertEqual(w.properties[('JAP','build_cost','land','relative')],4)
        w.advance(720)
        self.assertEqual(w.properties[('JAP','build_cost','naval','relative')],0)
        self.assertEqual(w.properties[('JAP','build_cost','land','relative')],0)
        w.dispatch('alloc_navy_expiry');self.assertEqual(w.properties[('JAP','build_cost','naval','relative')],0)

    def test_stability_delay_expires_and_defence_remains(self):
        w=World();w.action('tomozuru1934',0);w.advance(180)
        self.assertEqual(w.properties[('JAP','build_time','destroyer',None)],0)
        self.assertEqual(w.properties[('JAP','naval_defense','destroyer',None)],-.5)

    def test_lost_china_rail_site_refunds_both_payments(self):
        w=self.commercial_world();w.addwar('JAP','CHI')
        w.controlled[1337]=w.controlled[1338]='JAP'
        before=w.resources['JAP'].copy();self.assertTrue(w.action('procurement1937',1))
        self.assertLess(w.resources['JAP']['money'],before['money'])
        w.controlled[1337]='CHI';w.advance(120)
        self.assertEqual(w.resources['JAP'],before);self.assertNotIn('JX_procurement1937_DONE',w.flags)

    def test_legacy_materials_completion_adds_metal_with_energy_cost(self):
        w=World();self.legacy_action(w,'materials1938');w.advance(270)
        self.assertEqual(w.properties[('JAP','add_prov_resource','1221','metal')],2)
        self.assertEqual(w.properties[('JAP','add_prov_resource','1221','energy')],-4)

    def test_new_story_events_do_not_choose_wars_or_alliances(self):
        forbidden={'war','alliance','peace','country','independence','make_puppet','inherit'}
        for e in BY_KEY.values():
            if e.module=='early':
                for a in e.actions:
                    for command in a.commands:self.assertNotIn(get(parse(resolve(command)),'type'),forbidden,e.key)

    def test_new_story_events_add_no_ic_or_divisions(self):
        for e in BY_KEY.values():
            if e.module!='early':continue
            for a in e.actions:
                for command in a.commands:
                    node=parse(resolve(command));typ=get(node,'type')
                    self.assertNotIn(typ,{'free_ic','add_division','build_division'},e.key)
                    self.assertFalse(typ=='construct' and get(node,'which')=='ic',e.key)

    def test_delay_has_no_payment(self):
        w=World();before=w.resources['JAP'].copy();w.action('first_industry',2);w.advance(90)
        self.assertEqual(w.resources['JAP'],before);self.assertNotIn('JX_first_industry_WAIT',w.flags)

    def test_permanent_refusal_stays(self):
        w=World();w.action('first_industry',3);w.advance(1000)
        self.assertTrue(w.flags['JX_first_industry_DISMISSED']);self.assertFalse(w.queue)

    def test_two_projects_do_not_close_each_other(self):
        w=World();w.action('first_industry');w.action('merchant_prewar');w.advance(270)
        self.assertTrue(w.flags['JX_first_industry_DONE']);self.assertTrue(w.flags['JX_merchant_prewar_DONE'])

    def existing_settlement(self,key,old,tag,base=None,choice=0):
        w=World();w.addwar('JAP',old)
        # An existing 1941 national government owns its homeland; 1933's
        # colonial province owners are not the fixture for this branch.
        _,homeland=source_country(old)
        for pv in homeland:w.owned[pv]=old
        for pv,owner in list(w.owned.items()):
            if owner==old:w.controlled[pv]='JAP'
        if base:w.owned[base]=old;w.controlled[base]='JAP'
        w.national_losses[old]=80;w.vp_losses[old]=80
        self.assertTrue(w.action(key,choice));w.advance(10)
        return w

    def test_thai_puppet_keeps_us_and_soviet_wars(self):
        w=self.existing_settlement('thailand','SIA','SIA')
        self.assertEqual(w.masters['SIA'],'JAP');self.assertTrue(w.atwar('JAP','USA'));self.assertTrue(w.atwar('JAP','SOV'));self.assertTrue(w.flags['JX_thailand_SETTLED'])

    def test_neutral_thailand_does_not_inherit_wars(self):
        w=self.existing_settlement('thailand','SIA','SIA',choice=2)
        self.assertNotIn('SIA',w.masters);self.assertFalse(w.atwar('SIA','USA'));self.assertIn(('SIA','JAP'),w.access)

    def test_indian_tag_change_and_bombay(self):
        w=self.existing_settlement('india','U02','IND',1517)
        self.assertNotIn('U02',w.countries);self.assertEqual(w.masters['IND'],'JAP');self.assertEqual(w.owned[1517],'JAP');self.assertTrue(w.flags['JX_india_SETTLED'])

    def test_returning_ports_really_returns_port(self):
        w=self.existing_settlement('india','U02','IND',1517,1)
        self.assertEqual(w.owned[1517],'IND');self.assertTrue(w.flags['JX_india_SETTLED'])

    def test_chinese_tag_change_preserves_army(self):
        w=World();w.armies['CHI']=68;w.addwar('JAP','CHI')
        w.national_losses['CHI']=80;w.vp_losses['CHI']=80
        for p,t in list(w.owned.items()):
            if t=='CHI':w.controlled[p]='JAP'
        self.assertTrue(w.action('china'));w.advance(40)
        self.assertEqual(w.armies['U87'],68);self.assertEqual(w.masters['U87'],'JAP');self.assertTrue(w.atwar('JAP','USA'))

    def test_existing_nanjing_state_does_not_leave_nationalist_rump(self):
        w=World();w.countries.add('U87');w.masters['U87']='JAP';w.groups['U87']='Japan'
        w.armies['CHI']=68;w.armies['U87']=5;w.owned[1337]='U87'
        w.national_losses['CHI']=80;w.vp_losses['CHI']=80
        w.addwar('JAP','CHI')
        for p,t in list(w.owned.items()):
            if t in {'CHI','U87'}:w.controlled[p]='JAP'
        self.assertTrue(w.action('china'));w.advance(40)
        self.assertNotIn('CHI',w.countries);self.assertNotIn('CHI',w.owned.values())
        self.assertEqual(w.armies['U87'],73);self.assertEqual(w.owned[1338],'JAP')
        self.assertTrue(w.flags['JX_china_SETTLED']);self.assertTrue(w.atwar('JAP','USA'))
        self.assertIn(('JAP','U87'),w.access);self.assertIn(('U87','JAP'),w.access)

    def test_existing_puppet_can_receive_neutral_terms(self):
        w=World();w.countries.add('U87');w.masters['U87']='JAP';w.groups['U87']='Japan'
        w.addwar('JAP','CHI');w.addwar('JAP','USA')
        w.national_losses['CHI']=80;w.vp_losses['CHI']=80
        for p,t in list(w.owned.items()):
            if t in {'CHI','U87'}:w.controlled[p]='JAP'
        self.assertTrue(w.action('china',2));w.advance(10)
        self.assertNotIn('CHI',w.countries);self.assertNotIn('U87',w.masters)
        self.assertNotIn('U87',w.group('JAP'));self.assertFalse(w.atwar('U87','USA'))
        self.assertTrue(w.atwar('JAP','USA'));self.assertTrue(w.flags['JX_china_SETTLED'])

    def test_existing_indonesia_receives_dutch_rump(self):
        w=World();w.countries.add('U05');w.groups['U05']='Allies';w.armies['U05']=8;w.armies['INO']=4
        w.addwar('JAP','U05')
        for p in [1647,1653]:w.owned[p]='U05';w.controlled[p]='JAP'
        w.action('indonesia');w.advance(10)
        self.assertNotIn('U05',w.countries);self.assertEqual(w.armies['INO'],12)
        self.assertEqual(w.owned[1653],'JAP');self.assertTrue(w.flags['JX_indonesia_SETTLED'])

    def test_existing_india_receives_raj_rump(self):
        w=World();w.countries.add('IND');w.armies['U02']=20;w.armies['IND']=6;w.addwar('JAP','U02')
        w.owned[1459]='U02';w.controlled[1459]='JAP';w.owned[1517]='U02';w.controlled[1517]='JAP'
        w.action('india');w.advance(10)
        self.assertNotIn('U02',w.countries);self.assertEqual(w.armies['IND'],26)
        self.assertEqual(w.owned[1517],'JAP');self.assertTrue(w.flags['JX_india_SETTLED'])

    def test_settlement_cannot_confirm_without_reciprocal_access(self):
        w=World();w.flags.update({'JX_thailand_PENDING':1,'JX_thailand_PUPPET':1})
        w.masters['SIA']='JAP';w.access.add(('SIA','JAP'));w.dispatch('thailand_verify')
        self.assertNotIn('JX_thailand_SETTLED',w.flags)

    def test_settlement_cannot_confirm_while_recipient_at_war_with_japan(self):
        w=World();w.flags.update({'JX_thailand_PENDING':1,'JX_thailand_PUPPET':1})
        w.masters['SIA']='JAP';w.access.update({('SIA','JAP'),('JAP','SIA')});w.addwar('JAP','SIA')
        w.dispatch('thailand_verify');self.assertNotIn('JX_thailand_SETTLED',w.flags)

    def test_indonesian_base_transfer(self):
        w=self.existing_settlement('indonesia','INO','INO',1653)
        self.assertEqual(w.owned[1653],'JAP');self.assertTrue(w.flags['JX_indonesia_SETTLED'])

    def test_dutch_east_indies_change_into_indonesia(self):
        w=World();w.countries.discard('INO');w.countries.update({'U05','HOL'})
        w.groups['U05']='Allies';w.masters['U05']='HOL';w.armies['U05']=8;w.navies['U05']=3;w.addwar('JAP','U05')
        w.types['U05','destroyer']=2;w.types['U05','transport']=1
        for p in [1647,1653,1654]:w.owned[p]='U05';w.controlled[p]='JAP'
        w.action('indonesia');w.advance(10)
        self.assertNotIn('U05',w.countries);self.assertEqual(w.masters['INO'],'JAP')
        self.assertEqual(w.armies['INO'],8);self.assertEqual(w.navies['INO'],3)
        self.assertEqual(w.owned[1653],'JAP');self.assertTrue(w.atwar('JAP','USA'))

    def test_indonesia_release_without_jogjakarta(self):
        w=World();w.countries.discard('INO');w.countries.add('HOL');w.groups['HOL']='Allies';w.addwar('JAP','HOL')
        for p in [1647,1653]:w.owned[p]='HOL';w.controlled[p]='JAP'
        w.owned[1654]='HOL';w.controlled[1654]='HOL'
        w.action('indonesia');w.advance(10)
        self.assertTrue(w.flags['JX_indonesia_SETTLED']);self.assertEqual(w.owned[1654],'HOL');self.assertEqual(w.owned[1653],'JAP')

    def test_cambodia_release_needs_phnom_penh_not_siem_reap(self):
        w=World();w.countries.add('FRA');w.groups['FRA']='Allies';w.addwar('JAP','FRA')
        w.owned[1400]='FRA';w.controlled[1400]='JAP';w.owned[1401]='FRA';w.controlled[1401]='FRA'
        w.action('cambodia',1);w.advance(10)
        self.assertEqual(w.masters['CMB'],'JAP');self.assertTrue(w.flags['JX_cambodia_SETTLED'])

    def test_malayan_colonial_release(self):
        w=World();w.countries.discard('MLY')
        for p in [1432,1438]:w.owned[p]='ENG';w.controlled[p]='JAP'
        w.action('malaya');w.advance(10)
        self.assertEqual(w.masters['MLY'],'JAP');self.assertEqual(w.owned[1432],'JAP');self.assertTrue(w.atwar('JAP','ENG'))

    def test_owner_transfer_cannot_steal_ally_land(self):
        w=World();w.owned[1432]='GER';w.controlled[1432]='JAP';w.dispatch('malaya_land_ENG')
        self.assertEqual(w.owned[1432],'GER')

    def test_parallel_settlements_are_independent(self):
        w=World();w.addwar('JAP','SIA');w.addwar('JAP','PER')
        for p,t in list(w.owned.items()):
            if t in {'SIA','PER'}:w.controlled[p]='JAP'
        w.national_losses['SIA']=w.national_losses['PER']=80
        self.assertTrue(w.action('thailand'));self.assertTrue(w.action('persia'));w.advance(10)
        self.assertTrue(w.flags['JX_thailand_SETTLED']);self.assertTrue(w.flags['JX_persia_SETTLED']);self.assertTrue(w.atwar('JAP','SOV'))

    def test_failed_base_is_not_announced_as_success(self):
        w=World();w.flags.update({'JX_indonesia_PENDING':1,'JX_indonesia_PUPPET':1,'JX_indonesia_BASES':1,'JX_indonesia_HELD_1653':1});w.masters['INO']='JAP';w.access.add(('INO','JAP'));w.owned[1653]='ENG'
        w.dispatch('indonesia_verify');w.advance(1)
        self.assertNotIn('JX_indonesia_SETTLED',w.flags);self.assertIn('indonesia_failed',w.received)

    def test_duplicate_local_receipt_no_extra_supplies(self):
        w=self.existing_settlement('indonesia','INO','INO',1653);before=w.resources['INO'].copy();w.dispatch('indonesia_local')
        self.assertEqual(w.resources['INO'],before)

    def test_recovery_does_not_duplicate_large_army(self):
        w=World();w.armies['INO']=20;w.controlled[1647]='INO';before=w.armies['INO'];w.dispatch('indonesia_army')
        self.assertEqual(w.armies['INO'],before)

    def test_allied_pacific_peace_preserves_europe_and_soviets(self):
        w=World();w.flags['JX_US_PENDING']=1;w.dispatch('us_finish');w.advance(2)
        self.assertFalse(w.atwar('JAP','USA'));self.assertFalse(w.atwar('JAP','ENG'));self.assertTrue(w.atwar('GER','SOV'));self.assertTrue(w.atwar('JAP','SOV'));self.assertTrue(w.flags['JX_US_PEACE'])

    def test_pacific_peace_blocked_in_axis(self):
        w=World();w.groups['JAP']='Axis';self.assertFalse(w.action('us_finish'))

    def test_broken_hold_stays_broken_after_recapture(self):
        w=World();w.flags['JX_US_PENDING']=1;w.controlled[1734]='USA';w.dispatch('us_watch');w.controlled[1734]='JAP'
        self.assertTrue(w.flags['JX_US_HOLD_BROKEN'])

    def test_china_decisive_gate_available_before_pearl(self):
        w=World();w.flags.pop('JX_PACIFIC');w.addwar('JAP','CHI')
        w.vp_losses['CHI']=65
        for p in [1337,1338,1299]:w.controlled[p]='JAP'
        self.assertTrue(w.test(parse(resolve(BY_KEY['china'].gate)),'JAP'))

    def test_limited_china_peace_preserves_other_japanese_wars(self):
        w=World();w.addwar('JAP','CHI');w.action('china_limited_accept');w.advance(3)
        self.assertFalse(w.atwar('JAP','CHI'));self.assertTrue(w.atwar('JAP','SOV'));self.assertTrue(w.atwar('JAP','USA'))
        self.assertNotIn('CHI',w.masters);self.assertIn(('CHI','JAP'),w.access);self.assertTrue(w.flags['JX_CHINA_LIMITED_DONE'])

    def test_limited_refusal_resets_after_90_days(self):
        w=World();w.flags['JX_CHINA_LIMITED_PENDING']=1;w.dispatch('china_limited_refused');w.advance(89)
        self.assertTrue(w.flags['JX_CHINA_LIMITED_WAIT']);w.advance(1)
        self.assertNotIn('JX_CHINA_LIMITED_WAIT',w.flags);self.assertNotIn('JX_CHINA_LIMITED_PENDING',w.flags)

    def test_china_cannot_apply_two_different_settlements_together(self):
        w=World();w.addwar('JAP','CHI');w.flags['JX_CHINA_LIMITED_PENDING']=1
        w.vp_losses['CHI']=65
        for p in [1337,1338,1299]:w.controlled[p]='JAP'
        self.assertFalse(w.test(parse(resolve(BY_KEY['china'].gate)),'JAP'))

    def test_china_puppet_needs_deeper_victory_than_key_cities_alone(self):
        w=World();w.addwar('JAP','CHI')
        for p in [1337,1338,1299]:w.controlled[p]='JAP'
        w.vp_losses['CHI']=64.99
        self.assertFalse(w.test(parse(resolve(BY_KEY['china'].gate)),'JAP'))
        w.vp_losses['CHI']=65
        self.assertTrue(w.test(parse(resolve(BY_KEY['china'].gate)),'JAP'))

    def test_regional_china_keeps_japanese_base_and_access(self):
        w=World();w.countries.add('U87');w.countries.discard('CHI');w.masters['U87']='JAP';w.groups['U87']='Japan'
        node=get(parse(read(TARGET/'db/revolt.txt')),'CGX')
        for field in ('minimum','extra'):
            for _,p in get(node,field,[]):w.owned[int(p)]='U87';w.controlled[int(p)]='U87'
        w.owned[1338]='JAP';w.controlled[1338]='JAP'
        w.action('guangxi_autonomy');w.advance(8)
        self.assertEqual(w.masters['CGX'],'JAP');self.assertIn(('CGX','JAP'),w.access)
        self.assertEqual(w.owned[1338],'JAP');self.assertTrue(w.flags['JX_guangxi_REGIONAL_DONE'])

    def test_lost_regional_capital_refunds_without_release(self):
        w=World();w.countries.add('U87');w.owned[1390]='U87';w.controlled[1390]='U87';before=w.resources['JAP'].copy()
        w.action('yunnan_autonomy');w.controlled[1390]='CHC';w.advance(3)
        self.assertEqual(w.resources['JAP'],before);self.assertNotIn('CYN',w.countries);self.assertNotIn('JX_yunnan_REGIONAL_PENDING',w.flags)

    def test_indian_recovery_does_not_duplicate_large_army(self):
        w=World();w.countries.add('IND');w.masters['IND']='JAP';w.armies['IND']=30;w.action('india_recovery')
        self.assertFalse(w.orders);self.assertEqual(w.resources['IND']['manpower'],500)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(EventTests)
    from construction_safety_review import ConstructionTests
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ConstructionTests))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'scope':'Offline documented-command event-state model; not engine playtesting','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()}
    (Path(__file__).parent/'EVENT_STATE_TESTS.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

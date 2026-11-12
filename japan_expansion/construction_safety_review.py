"""Focused model tests for construction delivery, not an engine launch test.

Run after the builder has loaded its base catalogue. The model deliberately
allows construct to fail on a selected site, unlike the old unconditional model.
This file writes no source, install, save, report or game configuration files.
"""
import unittest
from collections import defaultdict
import build
import construction_safety
from audit_japan_baseline import parse,get,num

build.prepare_catalog()
construction_safety.apply()
BY_KEY={e.key:e for e in build.EVENTS}
BY_ID={str(e.id):e for e in build.EVENTS}


class Model:
    def __init__(self):
        self.flags={'JX_ACTIVE':1,'JX_PACIFIC':1}
        self.owned=defaultdict(lambda:'JAP');self.control=defaultdict(lambda:'JAP')
        self.tech=defaultdict(lambda:{'5800','5950'})
        self.stock=defaultdict(lambda:{'money':10000.,'supplies':100000.,'manpower':500.,'oil':10000.})
        self.sizes=defaultdict(float);self.blocked=set();self.properties=defaultdict(float)
        self.masters={'U87':'JAP','IND':'JAP'};self.scheduled=[]
        self.countries={'JAP','CHI','USA','ENG','U87','IND','AST'}
        self.wars={frozenset(('JAP',t)) for t in ('CHI','USA','ENG')}
        self.groups={'JAP':'Japan','U87':'Japan','IND':'Japan','USA':'Allies','ENG':'Allies'}
        self.year=1943;self.history=set()
        self.sizes[(1552,'ic')]=10;self.sizes[(1554,'ic')]=7
        for p in (1552,1554,1337,1459):self.sizes[(p,'infrastructure')]=80

    def test(self,node,actor):
        result=[]
        for k,v in node:
            if k=='AND':r=self.test(v,actor)
            elif k=='OR':r=any(self.test([(x,y)],actor) for x,y in v)
            elif k=='NOT':r=not any(self.test([(x,y)],actor) for x,y in v)
            elif k=='flag':
                if isinstance(v,list):
                    key=get(v,'which');actual=self.flags.get(key);want=int(get(v,'value',1));when=int(get(v,'when',1))
                    r=actual is not None and {-2:actual<want,-1:actual<=want,0:actual==want,1:actual>=want,2:actual>want}[when]
                else:r=bool(self.flags.get(v))
            elif k=='building':r=self.sizes[(int(get(v,'province')),get(v,'type'))]+1e-9>=float(get(v,'value'))
            elif k in {'owned','control'}:
                owner=get(v,'data',actor);owner=actor if owner=='-1' else owner
                r=(self.owned if k=='owned' else self.control)[int(get(v,'province'))]==owner
            elif k=='technology':r=(get(v,'value') in self.tech[get(v,'country',actor)]) if isinstance(v,list) else v in self.tech[actor]
            elif k in {'money','supplies','manpower','oil'}:r=self.stock[actor][k]>=float(v)
            elif k=='puppet':r=self.masters.get(get(v,'country'))==v[1][1]
            elif k=='ispuppet':r=v in self.masters
            elif k=='ai':r=v==('no' if actor=='JAP' else 'yes')
            elif k=='exists':r=v in self.countries
            elif k=='year':r=self.year>=int(v)
            elif k=='atwar':r=any(actor in pair for pair in self.wars)==(v=='yes')
            elif k=='war':r=frozenset(y for x,y in v if x=='country') in self.wars
            elif k=='alliance':
                tags=[y for x,y in v if x=='country']
                r=all(t in self.groups for t in tags) and self.groups[tags[0]]==self.groups[tags[1]]
            elif k=='event':r=(get(v,'id') if isinstance(v,list) else v) in self.history
            else:raise AssertionError('Unmodelled predicate '+str(k))
            result.append(r)
        return all(result)

    def command(self,text,actor):
        c=parse(text);gate=get(c,'trigger')
        if gate and not self.test(gate,actor):return
        typ=get(c,'type');which=get(c,'which');value=get(c,'value')
        if typ=='setflag':self.flags[which]=int(value or 1)
        elif typ=='clrflag':self.flags.pop(which,None)
        elif typ=='trigger':self.dispatch(which.removeprefix('@') if which.startswith('@') else BY_ID[which].key)
        elif typ=='event':self.scheduled.append(which)
        elif typ in {'money','supplies','manpowerpool','oilpool'}:
            self.stock[actor][{'manpowerpool':'manpower','oilpool':'oil'}.get(typ,typ)]+=float(value)
        elif typ=='construct':
            p=int(get(c,'where'));key=(p,which);delta=float(value)
            if delta>0 and (key in self.blocked or self.owned[p]!=actor or self.control[p]!=actor):return
            scale=.01 if which=='infrastructure' and self.sizes[key]<2 else 1
            self.sizes[key]+=delta*scale
        else:self.properties[(actor,typ,which)]+=float(value or 0)

    def action(self,key,index=0):
        e=BY_KEY[key];a=e.actions[index]
        if not self.test(parse(a.gate),e.country):return False
        for text in a.commands:self.command(text,e.country)
        return True

    def dispatch(self,key):
        e=BY_KEY[key]
        for i,a in enumerate(e.actions):
            if self.test(parse(a.gate),e.country) and (a.chance>0 or not a.name):return self.action(key,i)
        valid=[i for i,a in enumerate(e.actions) if self.test(parse(a.gate),e.country)]
        if len(valid)==1:return self.action(key,valid[0])
        raise AssertionError('No unambiguous receiver: '+key+' '+str(valid))


class ConstructionTests(unittest.TestCase):
    def test_native_award_completes_once_and_cannot_repeat(self):
        w=Model();w.action('first_industry');w.action('first_industry_finish_0')
        self.assertEqual(w.sizes[(1552,'ic')],13)
        self.assertEqual(w.sizes[(1554,'ic')],10)
        self.assertTrue(w.flags['JX_first_industry_DONE'])
        self.assertFalse(w.action('first_industry_finish_0'))
        self.assertEqual(w.sizes[(1552,'ic')],13)

    def test_lost_required_site_refunds_before_any_native_construction(self):
        w=Model();before=w.stock['JAP'].copy();w.action('first_industry')
        w.owned[1554]='CHI';w.dispatch('first_industry_finish_0')
        self.assertEqual(w.sizes[(1552,'ic')],10)
        self.assertEqual(w.sizes[(1554,'ic')],7)
        self.assertEqual(w.stock['JAP'],before)
        self.assertNotIn('JX_first_industry_DONE',w.flags)
        self.assertTrue(w.flags['JX_first_industry_WAIT'])

    def test_lost_construction_research_refunds_without_award(self):
        w=Model();before=w.stock['JAP'].copy();w.action('first_industry')
        w.tech['JAP']=set();w.dispatch('first_industry_finish_0')
        self.assertEqual(w.stock['JAP'],before)
        self.assertNotIn('JX_first_industry_DONE',w.flags)

    def test_duplicate_refund_receiver_cannot_pay_again(self):
        w=Model();before=w.stock['JAP'].copy();w.action('first_industry')
        w.owned[1554]='CHI';w.dispatch('first_industry_finish_0')
        self.assertEqual(w.stock['JAP'],before)
        transaction=next(x for x in construction_safety.REPORT if x['event']=='first_industry_finish_0')
        refund=transaction['receipt_event'].replace('_verify','_refund')
        w.dispatch(refund);w.dispatch(refund)
        self.assertEqual(w.stock['JAP'],before)

    def test_occupied_rabaul_building_unavailable_shipping_still_available(self):
        w=Model();w.owned[1726]='AST';before=w.stock['JAP'].copy()
        self.assertFalse(w.action('rabaul_workshops',0));self.assertEqual(w.stock['JAP'],before)
        self.assertTrue(w.action('rabaul_workshops',1));w.action('rabaul_workshops_finish_1')
        self.assertEqual(w.properties[('JAP','transport_pool','-1')],40)

    def test_partner_construction_uses_partner_research_and_refunds_japan(self):
        w=Model();w.owned[1337]=w.control[1337]='U87';w.tech['U87']=set()
        self.assertFalse(w.action('china_rebuild'))
        w.tech['U87']={'5800'};before=w.stock['JAP'].copy();partner=w.stock['U87'].copy()
        self.assertTrue(w.action('china_rebuild'));w.tech['U87']=set()
        w.action('china_rebuild_finish_0')
        self.assertEqual(w.stock['JAP'],before);self.assertEqual(w.stock['U87'],partner)
        self.assertNotIn('JX_china_rebuild_DONE',w.flags)

    def test_partner_success_does_not_complete_before_recipient_work(self):
        w=Model();w.owned[1337]=w.control[1337]='U87'
        w.action('china_rebuild');self.assertNotIn('JX_china_rebuild_DONE',w.flags)
        w.action('china_rebuild_finish_0')
        self.assertEqual(w.sizes[(1337,'ic')],4)
        self.assertTrue(w.flags['JX_china_rebuild_DONE'])

    def test_infrastructure_receipt_accepts_fractional_and_percent_conventions(self):
        for raw in (False,True):
            w=Model();w.sizes[(1337,'infrastructure')]=.6 if raw else 60
            w.flags.pop('JX_PACIFIC')
            w.sizes[(1338,'infrastructure')]=.7 if raw else 70
            w.action('procurement1937');w.action('procurement1937_finish_0')
            self.assertTrue(w.flags['JX_procurement1937_DONE'])
            self.assertAlmostEqual(w.sizes[(1337,'infrastructure')],.7 if raw else 70)

    def test_puppeted_player_and_lost_partner_cannot_pay(self):
        w=Model();before=w.stock['JAP'].copy();w.masters['JAP']='USA'
        self.assertFalse(w.action('first_industry'));self.assertEqual(w.stock['JAP'],before)
        w.masters.pop('JAP');w.masters.pop('U87')
        self.assertFalse(w.action('china_rebuild'));self.assertEqual(w.stock['JAP'],before)

    def test_lost_offer_site_cannot_pay_but_manual_close_stays_free(self):
        w=Model();w.control[1734]='USA';before=w.stock['JAP'].copy()
        self.assertFalse(w.action('hawaii'));self.assertEqual(w.stock['JAP'],before)
        w.control[1734]='JAP'
        close=next(i for i,a in enumerate(BY_KEY['hawaii'].actions) if a.name=='Leave this proposal available')
        self.assertTrue(w.action('hawaii',close));self.assertEqual(w.stock['JAP'],before)
        self.assertFalse(w.scheduled)

    def test_prewar_railway_cannot_take_money_after_pacific_opening(self):
        w=Model();before=w.stock['JAP'].copy()
        self.assertFalse(w.action('procurement1937'));self.assertEqual(w.stock['JAP'],before)

    def test_hawaii_support_delivers_without_claiming_capped_construction(self):
        w=Model();w.owned[1734]='USA';w.sizes[(1734,'air_base')]=10;w.sizes[(1734,'naval_base')]=10
        self.assertTrue(w.action('hawaii'));w.action('hawaii_finish_0')
        self.assertEqual(w.properties[('JAP','transport_pool','-1')],100)
        self.assertEqual(w.sizes[(1734,'naval_base')],10)


    def test_empty_factory_site_needs_no_zero_size_snapshot(self):
        w=Model();w.sizes[1554,'ic']=0
        w.action('first_industry');w.action('first_industry_finish_0')
        self.assertEqual(w.sizes[1554,'ic'],3)
        self.assertTrue(w.flags['JX_first_industry_DONE'])
        self.assertFalse(any('BEFORE' in key for key in w.flags))

    def test_native_awards_do_not_enter_legacy_snapshot_helpers(self):
        for r in construction_safety.REPORT:
            a=BY_KEY[r['event']].actions[r['action']]
            self.assertFalse(any(get(parse(c),'type')=='trigger' and r['snapshot_event'] in c for c in a.commands))
            self.assertEqual(sum(get(parse(c),'type')=='construct' for c in a.commands),len(r['buildings']))


if __name__=='__main__':unittest.main(verbosity=2)

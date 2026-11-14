"""Offline Chinese surrender/army regressions. Never starts Darkest Hour."""
import copy
import tempfile
from pathlib import Path
import unittest

import build
from simulate import World, BY_KEY, BY_ID
import r14_china as fix

fix.apply()
BY_KEY.update({e.key:e for e in build.EVENTS})
BY_ID.update({str(e.id):e for e in build.EVENTS})


class ChinaWorld(World):
    def __init__(self):
        super().__init__();self.formations=[]
    def test(self,node,actor):
        other=[]
        for k,v in node:
            if k=='army':
                tag=build.get(v,'country',actor)
                # Own deployed troops include those lent abroad; foreign loans,
                # dormant templates and factory orders aren't surviving armies.
                n=sum(d['owner']==tag and d['deployed'] for d in self.formations)
                if n<int(build.get(v,'size')):return False
            elif k=='division_exists':
                if not any(d.get('id')==(int(build.get(v,'type')),int(build.get(v,'id'))) for d in self.formations):return False
            elif k=='ai':
                actual=actor!='JAP' if v in ('yes','no') else v!='JAP'
                if actual != (v!='no'):return False
            else:other.append((k,v))
        return super().test(other,actor)
    def army(self,tag,n):
        self.formations=[d for d in self.formations if d['owner']!=tag]
        self.formations += [dict(owner=tag,deployed=True,id=(1,i),earned=i>=40) for i in range(n)]


class ChinaReview(unittest.TestCase):
    def battle(self,n=60):
        w=ChinaWorld();w.year=1938;w.addwar('JAP','CHI');w.army('CHI',n)
        for p in (1337,1338,1299,1317):w.controlled[p]='JAP'
        w.national_losses['CHI']=55;w.vp_losses['CHI']=65
        return w
    def eligible(self,w,key='china'):
        e=BY_KEY[key]
        # Evaluate the final compiled decision condition, not a copied threshold.
        compiled=build.get(build.parse(build.compiled_event(e)),'event')
        return w.test(build.get(compiled,'decision',build.get(compiled,'trigger',[])),e.country)
    def settled(self,n):
        w=ChinaWorld();w.countries.add('U87');w.masters['U87']='JAP';w.flags['JX_china_SETTLED']=1
        w.controlled[1337]='U87';w.army('U87',n)
        w.formations += [dict(owner='U87',deployed=False,id=(28631,i)) for i in range(1,97)]
        return w
    def test_original_failure_small_army_grows_years_later(self):
        old=fix.ORIGINAL_REORGANISE
        self.assertIsNotNone(old)
        w=self.settled(40)
        self.assertFalse(w.test(build.parse(build.resolve(old.gate)),'U87'))
        w.day=1500;w.army('U87',130)
        w.formations += [dict(owner='U87',deployed=False,id=(28631,i)) for i in range(1,97)]
        self.assertTrue(w.test(build.parse(build.resolve(old.gate)),'U87'))
        self.assertEqual(sum('type = remove_units' in c for c in old.actions[0].commands),6)
        self.assertEqual(sum('type = activate_division' in c for c in old.actions[0].commands),96)
    def test_exact_army_threshold_and_city_vp_requirements(self):
        self.assertTrue(self.eligible(self.battle(60)))
        self.assertFalse(self.eligible(self.battle(61)))
        for vp in (0,64):
            w=self.battle();w.vp_losses['CHI']=vp;self.assertFalse(self.eligible(w))
        for p in (1337,1338,1299):
            w=self.battle();w.controlled[p]='CHI';self.assertFalse(self.eligible(w))
        w=self.battle();w.national_losses['CHI']=54;self.assertFalse(self.eligible(w))
    def test_dormant_templates_orders_and_foreign_loans_do_not_block(self):
        w=self.battle()
        w.formations += [dict(owner='CHI',deployed=False,id=(28631,i)) for i in range(1,97)]
        w.formations += [dict(owner='CHI',deployed=False,construction=True) for i in range(20)]
        w.formations += [dict(owner='CGX',deployed=True,controller='CHI') for i in range(20)]
        self.assertTrue(self.eligible(w))
        w.formations.append(dict(owner='CHI',deployed=True,controller='SOV'))
        self.assertFalse(self.eligible(w))
        self.assertIn('which = 1',BY_KEY['china'].gate)
    def test_successor_enemy_has_same_hard_surrender(self):
        w=self.battle();w.countries.remove('CHI');w.countries.add('U87');w.addwar('JAP','U87')
        w.army('U87',60);w.national_losses['U87']=55;w.vp_losses['U87']=65
        self.assertTrue(self.eligible(w))
        w.army('U87',61);self.assertFalse(self.eligible(w))
        w.army('U87',60);w.vp_losses['U87']=64;self.assertFalse(self.eligible(w))
    def test_postwar_assessment_closes_without_mutating_any_army(self):
        for n in (0,40,60,130):
            for war in (False,True):
                w=self.settled(n)
                if war:w.addwar('U87','USA')
                before=copy.deepcopy(w.formations)
                self.assertTrue(w.action('cn_reorganise'))
                self.assertEqual(w.formations,before)
                self.assertTrue(w.flags['JX_CN_ASSESSED_R14'])
                w.day=2000;w.army('U87',170);before=copy.deepcopy(w.formations)
                self.assertFalse(w.action('cn_reorganise'))
                self.assertEqual(w.formations,before)
    def test_assessment_closes_after_independence_and_without_nanjing(self):
        w=self.settled(40);del w.masters['U87'];w.controlled[1337]='JAP'
        self.assertTrue(w.action('cn_reorganise'));self.assertEqual(len(w.formations),136)
    def test_stale_decisive_receiver_cannot_bypass_army_limit(self):
        w=self.battle(100);w.flags['JX_china_PENDING']=1
        before=copy.deepcopy((w.formations,w.wars,w.owned,w.masters))
        w.dispatch('china_withdraw')
        self.assertEqual((w.formations,w.wars,w.owned,w.masters),before)
        w=self.battle(60);w.flags['JX_china_PENDING']=1;w.controlled[1299]='CHI'
        w.dispatch('china_withdraw');self.assertTrue(w.atwar('JAP','CHI'))
    def cached(self,w,key,index=0):
        for text in BY_KEY[key].actions[index].commands:
            w.command(build.parse(build.resolve(text)),BY_KEY[key].country)
    def test_cached_clicks_recheck_before_any_peace_or_identity_change(self):
        for key in ('china_withdraw','china_withdraw_existing','china_limited_accept','china_limited_signed','china_limited_refused'):
            w=self.battle(100);w.countries.add('U87');w.addwar('JAP','U87')
            before=copy.deepcopy((w.countries,w.wars,w.owned,w.masters,w.flags))
            self.cached(w,key)
            self.assertEqual((w.countries,w.wars,w.owned,w.masters,w.flags),before,key)
        w=self.battle(100);w.flags['JX_china_PENDING']=1
        self.cached(w,'china_withdraw');self.assertIn('CHI',w.countries);self.assertTrue(w.atwar('JAP','CHI'))
        w=self.battle(140);w.flags['JX_CHINA_LIMITED_PENDING']=1
        self.cached(w,'china_limited_accept');self.assertTrue(w.atwar('JAP','CHI'))
    def test_limited_peace_remains_independent_and_distinct(self):
        w=self.battle(140);w.national_losses['CHI']=35;w.vp_losses['CHI']=0
        self.assertTrue(self.eligible(w,'china_limited'));self.assertFalse(self.eligible(w))
        w.flags['JX_CHINA_LIMITED_PENDING']=1
        w.action('china_limited_offer',0);w.advance(3)
        self.assertFalse(w.atwar('JAP','CHI'));self.assertNotIn('CHI',w.masters)
        self.assertTrue(w.atwar('JAP','USA'));self.assertTrue(w.atwar('JAP','SOV'))
        self.assertTrue(w.flags['JX_CHINA_LIMITED_DONE'])
        self.assertEqual(sum(d['deployed'] for d in w.formations),140)
    def test_stale_limited_accept_is_inert(self):
        for pending,consent in ((False,False),(True,False),(False,True)):
            w=self.battle(140)
            if pending:w.flags['JX_CHINA_LIMITED_PENDING']=1
            if consent:w.flags['JX_CHINA_LIMITED_ACCEPTED_R14']=1
            before=copy.deepcopy((w.owned,w.wars,w.masters))
            w.dispatch('china_limited_accept')
            self.assertEqual((w.owned,w.wars,w.masters),before)
    def test_changing_front_cancels_limited_offer_without_leaving_pending(self):
        w=self.battle(140);w.flags['JX_CHINA_LIMITED_PENDING']=1
        w.action('china_limited_offer',0);w.controlled[1338]='CHI';w.advance(1)
        self.assertTrue(w.atwar('JAP','CHI'));self.assertFalse(w.flags.get('JX_CHINA_LIMITED_PENDING'))
        self.assertTrue(w.flags['JX_CHINA_LIMITED_WAIT'])

    def test_annexed_china_closes_early_and_accepted_negotiations(self):
        for accepted in (False,True):
            w=self.battle(140);w.national_losses['CHI']=35
            self.assertTrue(w.action('china_limited',0))
            if accepted:
                self.assertTrue(w.action('china_limited_offer',0))
            w.countries.discard('CHI');w.wars={p for p in w.wars if 'CHI' not in p}
            before=copy.deepcopy((w.owned,w.wars,w.masters))
            w.dispatch('r14_china_limited_interrupted')
            self.assertFalse(w.flags.get('JX_CHINA_LIMITED_PENDING'))
            self.assertFalse(w.flags.get('JX_CHINA_LIMITED_ACCEPTED_R14'))
            self.assertFalse(w.flags.get('JX_CHINA_LIMITED_DONE'))
            self.assertTrue(w.flags['JX_CHINA_LIMITED_WAIT'])
            self.assertEqual((w.owned,w.wars,w.masters),before)
            snapshot=copy.deepcopy(w.flags)
            self.cached(w,'r14_china_limited_interrupted')
            self.assertEqual(w.flags,snapshot)
            # Recreating China cannot give its stale callback authority to end
            # a new war or award the old settlement.
            w.countries.add('CHI');w.addwar('JAP','CHI')
            self.cached(w,'china_limited_accept')
            self.assertTrue(w.atwar('JAP','CHI'))
            self.assertFalse(w.flags.get('JX_CHINA_LIMITED_DONE'))
            w.advance(90)
            self.assertFalse(w.flags.get('JX_CHINA_LIMITED_WAIT'))

    def test_china_interruption_does_not_cancel_live_talks(self):
        w=self.battle(140);w.flags['JX_CHINA_LIMITED_PENDING']=1
        before=copy.deepcopy(w.flags);self.cached(w,'r14_china_limited_interrupted')
        self.assertEqual(w.flags,before)
    def test_native_stock_receivers_and_roots_cannot_bypass_jx(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp);p=target/'db/events/japan.txt';p.parent.mkdir(parents=True)
            build.write(p,build.read(build.SOURCE/'db/events/japan.txt'))
            fix.install(build.SOURCE,target,build.read,build.write,build.parse,build.serialise)
            first=build.read(p)
            fix.install(build.SOURCE,target,build.read,build.write,build.parse,build.serialise)
            self.assertEqual(build.read(p),first)
            w=self.battle(140)
            for e in build.getall(build.parse(first),'event'):
                if int(build.get(e,'id')) not in fix.NATIVE_CHAIN:continue
                actor=build.get(e,'country')
                guards=[(k,v) for k,v in build.get(e,'trigger') if (k,v)==('NOT',[('flag','JX_ACTIVE')])]
                self.assertTrue(guards);self.assertFalse(w.test(guards,actor))
                for key,a in e:
                    if key=='action' or key.startswith('action_'):
                        action_guard=[(k,v) for k,v in build.get(a,'trigger',[]) if (k,v)==('NOT',[('flag','JX_ACTIVE')])]
                        if not action_guard:
                            self.assertEqual(build.get(a,'trigger'),[('flag','JX_ACTIVE')])
                            self.assertTrue(all(not c for c in build.getall(a,'command')))
    def test_no_new_ids_and_no_destructive_or_replacement_postwar_commands(self):
        baseline=__import__('json').loads((build.HERE/'R14_BASELINE_IDS.json').read_text())
        expected=baseline.get('ids',baseline) if isinstance(baseline,dict) else baseline
        if isinstance(expected,dict):
            for key,eid in expected.items():self.assertEqual(BY_KEY[key].id,eid)
        released=__import__('json').loads((build.HERE/'R14_PRESTART_BASELINE_IDS.json').read_text(encoding='utf-8'))
        for key,eid in released.items():self.assertEqual(BY_KEY[key].id,eid)
        self.assertEqual(BY_KEY['r14_china_limited_interrupted'].id,max(released.values())+1)
        for e in build.EVENTS:
            if e.module=='campaign_balance' and e.key.startswith('cn_'):
                for a in e.actions:
                    for c in a.commands:
                        self.assertNotIn(build.get(build.parse(c),'type'),('remove_units','activate_division','add_division'))


if __name__=='__main__':unittest.main()

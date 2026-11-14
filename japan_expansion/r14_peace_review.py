"""Adversarial R14 peace tests. Pure file/state checks; never starts the game."""
import copy
import unittest
import build
import simulate
from catalog import EVENTS
import r14_peace

r14_peace.apply()
build.IDS.update({e.key:e.id for e in EVENTS})
simulate.BY_KEY.update({e.key:e for e in EVENTS})
simulate.BY_ID.update({str(e.id):e for e in EVENTS})
BY=simulate.BY_KEY


class ColdWorld(simulate.World):
    def test(self,node,actor):
        results=[]
        for k,v in node:
            if k=='ai':results.append((actor=='JAP') if v=='no' else (actor!='JAP') if v=='yes' else v!='JAP')
            elif k=='carrier':results.append(self.types[build.get(v,'country',actor),'carrier']>=float(build.get(v,'value')))
            elif k=='losses':results.append(self.types[build.get(v,'country',actor),'lost_'+build.get(v,'type')]>=float(build.get(v,'value')))
            else:results.append(super().test([(k,v)],actor))
        return all(results)

    def command(self,n,actor):
        trigger=build.get(n,'trigger')
        if trigger and not self.test(trigger,actor):return
        if build.get(n,'type')=='secedeprovince' and build.get(n,'when')=='2':
            p=int(build.get(n,'value'))
            if p not in self.blocked_transfers:self.owned[p]=self.controlled[p]=build.get(n,'which')
        elif build.get(n,'type')=='relation':self.properties[actor,'relation',build.get(n,'which'),None]+=float(build.get(n,'value'))
        else:super().command(n,actor)

    def cached(self,key,index=0):
        """Native cached selection: deliberately bypass the action gate."""
        for c in BY[key].actions[index].commands:self.command(build.parse(build.resolve(c)),BY[key].country)


def ready():
    w=ColdWorld();w.year=1944;w.day=800
    w.history[str(BY['pacific_open'].id)]=0
    for p in (1734,1432,1565):w.controlled[p]='JAP'
    w.owned[1734]='USA';w.owned[1432]='ENG';w.owned[1565]='USA'
    w.types['JAP','carrier']=10;w.types['USA','carrier']=2
    w.national_losses['JAP']=0;w.national_losses['USA']=10
    return w


def live(w,key):return w.test(build.parse(build.resolve(BY[key].gate)),BY[key].country)


class PeaceReview(unittest.TestCase):
    def test_every_created_partner_is_supported_in_coalition_settlements(self):
        expected={e.country for e in EVENTS if e.module=='settlements' and e.key.endswith('_local') and e.country!='JAP'}
        self.assertTrue(expected<=set(r14_peace.PARTNERS),expected-set(r14_peace.PARTNERS))

    def test_cached_national_snapshot_preserves_existing_claims(self):
        w=ready();w.flags.update(JX_US_INV_PENDING=1,JX_US_INV_ACCEPTED=1,JX_US_INV_SNAPSHOT_READY=1,JX_US_INV_CLAIM_1734=1,JX_US_INV_LAND_1734_JAP=1,JX_US_INV_PEACE_ISSUED=1)
        before={k:v for k,v in w.flags.items() if k.startswith('JX_US_INV')}
        w.cached('us_inv_snapshot',0)
        self.assertEqual({k:v for k,v in w.flags.items() if k.startswith('JX_US_INV')},before)

    def test_stale_transfer_authority_is_refreshed_before_cached_secession(self):
        w=ready();w.flags.update(JX_US_PENDING=1,JX_R14_US_ACCEPTED=1,JX_US_RETURN_HAWAII=1,JX_R14_AUTH_1565=1,JX_R14_US_LAND_USA_1565=1)
        w.controlled[1565]='USA'
        w.cached('us_transfer_USA',0)
        self.assertEqual(w.owned[1565],'USA');self.assertNotIn('JX_R14_AUTH_1565',w.flags)

    def test_return_hawaii_full_chain_and_independent_wars(self):
        w=ready();self.assertTrue(w.action('us_peace',0));w.advance(195)
        self.assertIn('JX_US_PEACE',w.flags)
        self.assertNotIn('JX_US_PENDING',w.flags)
        self.assertEqual(w.owned[1734],'USA')
        self.assertEqual(w.owned[1432],'JAP')
        self.assertEqual(w.owned[1565],'JAP')
        self.assertEqual(w.properties['JAP','relation','USA',None],35)
        self.assertTrue(w.atwar('GER','SOV'));self.assertTrue(w.atwar('JAP','SOV'))
        self.assertFalse(w.atwar('JAP','USA'));self.assertFalse(w.atwar('JAP','ENG'))

    def test_keep_hawaii_is_a_distinct_hostile_bargain(self):
        w=ready();w.flags['JX_US_PENDING']=1
        self.assertTrue(w.action('us_terms',1));w.advance(15)
        self.assertEqual(w.owned[1734],'JAP');self.assertIn('JX_US_KEEP_HAWAII',w.flags)
        self.assertNotIn('JX_US_RETURN_HAWAII',w.flags)
        self.assertEqual(w.properties['JAP','relation','USA',None],-60)
        self.assertIn('JX_US_PEACE',w.flags)
        self.assertFalse(any(x[2]=='us_treaty_expiry' for x in w.queue))

    def test_rebuilt_us_carriers_invalidate_old_loss_counter(self):
        w=ready();w.types['USA','lost_carrier']=20;w.types['USA','carrier']=12
        self.assertFalse(live(w,'us_peace'))
        w.types['USA','carrier']=8;w.national_losses['USA']=14
        self.assertFalse(live(w,'us_peace'))
        w.national_losses['USA']=15;self.assertTrue(live(w,'us_peace'))
        w.flags['JX_US_PENDING']=1;self.assertFalse(w.action('us_terms',1))

    def test_late_axis_entry_cancels_without_cross_war_peace(self):
        w=ready();w.flags.update(JX_US_PENDING=1,JX_R14_US_ACCEPTED=1,JX_US_RETURN_HAWAII=1)
        w.groups['JAP']='Axis'
        w.cached('us_implement',0);w.dispatch('us_implement')
        self.assertNotIn('JX_US_PENDING',w.flags)
        self.assertNotIn('JX_US_PEACE',w.flags)
        self.assertTrue(w.atwar('GER','SOV'));self.assertTrue(w.atwar('JAP','USA'))

    def test_formal_axis_cached_action_blocked_while_pending(self):
        w=ready();w.flags['JX_US_PENDING']=1
        w.cached('formal_axis',0)
        self.assertNotEqual(w.groups.get('JAP'),w.groups.get('GER'))

    def test_external_peace_does_not_grant_retroactive_gifts(self):
        w=ready();w.flags.update(JX_US_PENDING=1,JX_R14_US_ACCEPTED=1,JX_US_KEEP_HAWAII=1)
        w.wars={x for x in w.wars if not ('JAP' in x and 'USA' in x)}
        old=copy.deepcopy(w.owned);w.cached('us_transfer_USA',0);w.dispatch('us_implement')
        self.assertEqual(w.owned,old);self.assertNotIn('JX_US_PENDING',w.flags);self.assertNotIn('JX_US_PEACE',w.flags)

    def test_transfer_failure_never_signs_and_partial_delivery_survives(self):
        w=ready();w.flags.update(JX_US_PENDING=1,JX_R14_US_ACCEPTED=1,JX_US_RETURN_HAWAII=1)
        w.blocked_transfers.add(1565);self.assertTrue(w.action('us_implement',0));w.advance(20)
        self.assertEqual(w.owned[1432],'JAP');self.assertEqual(w.owned[1565],'USA')
        self.assertTrue(w.atwar('JAP','USA'));self.assertNotIn('JX_US_PEACE',w.flags);self.assertNotIn('JX_US_PENDING',w.flags)

    def test_duplicate_success_receiver_cannot_repeat_dissent_or_relations(self):
        w=ready();w.action('us_peace',0);w.advance(195)
        before=copy.deepcopy(w.properties);w.cached('us_signed',0);w.dispatch('us_signed')
        self.assertEqual(w.properties,before)

    def test_independent_ally_cannot_lose_its_own_territory(self):
        w=ready();w.flags.update(JX_US_PENDING=1,JX_R14_US_ACCEPTED=1,JX_US_RETURN_HAWAII=1,JX_R14_CONSENT_GER=1)
        # GER remains an independent ally of a different war; no forced takeover.
        w.owned[1432]='GER';w.controlled[1432]='JAP';w.action('us_implement',0);w.advance(15)
        self.assertEqual(w.owned[1432],'GER')

    def test_partner_held_colonial_land_requires_consent(self):
        for consent in (False,True):
            w=ready();w.countries.add('IND');w.groups['IND']=w.groups['JAP'];w.controlled[1565]='IND'
            w.flags.update(JX_US_PENDING=1,JX_R14_US_ACCEPTED=1,JX_US_RETURN_HAWAII=1)
            if consent:w.flags['JX_R14_CONSENT_IND']=1
            w.action('us_implement',0);w.advance(15)
            self.assertEqual(w.owned[1565],'JAP' if consent else 'USA')

    def test_friendly_nonallied_neutral_does_not_count(self):
        w=ready();w.countries.add('IND');w.controlled[1734]='IND'
        w.flags['JX_R14_CONSENT_IND']=1
        self.assertFalse(live(w,'us_peace'))

    def test_consent_refusal_and_stale_consent_response(self):
        w=ready();w.countries.add('IND');w.groups['IND']=w.groups['JAP']
        self.assertTrue(w.action('r14_consent_IND',1));self.assertIn('JX_R14_REFUSED_IND',w.flags)
        self.assertNotIn('JX_R14_CONSENT_IND',w.flags)
        w.advance(180);w.groups.pop('IND');w.cached('r14_consent_IND',0)
        self.assertNotIn('JX_R14_CONSENT_IND',w.flags)

    def test_indian_settlement_accepts_actual_partner_objectives(self):
        w=ready();w.countries.add('IND');w.groups['IND']=w.groups['JAP'];w.national_losses['U02']=80
        w.controlled[1459]=w.controlled[1447]='IND'
        # Remove recipient to test the old Indian enemy government's offer.
        w.countries.discard('IND');w.countries.add('MEN');w.groups['MEN']=w.groups['JAP']
        w.controlled[1459]=w.controlled[1447]='MEN'
        w.dispatch('r14_capture_1459');w.dispatch('r14_capture_1447')
        self.assertTrue(live(w,'india'))

    def test_stale_coalition_flag_cannot_commit_any_treaty(self):
        w=ready();w.flags['JX_R14_CAPTURE_1734']=1;w.controlled[1734]='USA'
        before=copy.deepcopy(w.owned);w.cached('us_peace',0)
        self.assertEqual(w.owned,before);self.assertNotIn('JX_US_PENDING',w.flags)
        x=ready();x.flags.update(JX_US_PENDING=1,JX_US_RETURN_HAWAII=1,JX_R14_CAPTURE_1734=1);x.controlled[1734]='USA'
        x.cached('us_offer',0)
        self.assertNotIn('JX_US_PENDING',x.flags);self.assertNotIn('JX_R14_US_ACCEPTED',x.flags)

    def test_cached_soviet_root_cannot_reset_accepted_talks(self):
        w=ready()
        for p in (1191,1190,1169,1162,1142):w.controlled[p]='JAP'
        w.flags.update(JX_SOV_TERMS_PENDING=1,JX_R14_SOV_ACCEPTED=1,JX_R14_SOV_LAND_1191=1)
        before=copy.deepcopy(w.flags);w.cached('soviet_terms',0)
        self.assertEqual(w.flags,before)
        w.flags.pop('JX_SOV_TERMS_PENDING');w.controlled[1191]='SOV'
        before=copy.deepcopy(w.flags);w.cached('soviet_terms',0)
        self.assertEqual(w.flags,before)

    def test_stale_country_resolution_cannot_puppet_neutral_state(self):
        w=ready();w.countries.add('SIA');w.flags.update(JX_thailand_PENDING=1,JX_thailand_PUPPET=1)
        w.wars={x for x in w.wars if not ('JAP' in x and 'SIA' in x)}
        before=copy.deepcopy((w.masters,w.wars,w.groups));w.cached('thailand_withdraw',0);w.cached('thailand_commit',0)
        self.assertEqual((w.masters,w.wars,w.groups),before)

    def test_indonesia_colonial_creation_needs_batavia_not_jogjakarta(self):
        w=ready();w.countries.discard('INO');w.countries.discard('U05');w.countries.add('HOL');w.groups['HOL']='Allies';w.addwar('JAP','HOL')
        for p in (1647,1653):w.owned[p]='HOL';w.controlled[p]='JAP'
        w.owned[1654]=w.controlled[1654]='HOL'
        self.assertTrue(w.action('indonesia',0));w.advance(10)
        self.assertEqual(w.masters.get('INO'),'JAP');self.assertIn('JX_indonesia_SETTLED',w.flags)
        self.assertEqual(w.owned[1654],'HOL');self.assertEqual(w.owned[1653],'JAP')

    def test_cambodia_colonial_creation_needs_phnom_penh(self):
        w=ready();w.countries.discard('CMB');w.countries.add('FRA');w.groups['FRA']='Allies';w.addwar('JAP','FRA')
        w.owned[1400]='FRA';w.controlled[1400]='JAP';w.owned[1401]=w.controlled[1401]='FRA'
        self.assertTrue(w.action('cambodia',1));w.advance(10)
        self.assertEqual(w.masters.get('CMB'),'JAP');self.assertIn('JX_cambodia_SETTLED',w.flags)
        self.assertEqual(w.owned[1401],'FRA')

    def test_every_colonial_create_requires_its_declared_capital(self):
        for rootkey in r14_peace.REPORT['country_roots']:
            w=ready();e=BY[rootkey+'_create']
            capital=int(__import__('re').search(r'owned\s*=\s*\{\s*province\s*=\s*(\d+)',e.actions[0].gate)[1])
            w.flags['JX_'+rootkey+'_PENDING']=1
            # Remove all possible existing recipients/predecessors explicitly.
            for tag in __import__('re').findall(r'exists\s*=\s*(\w+)',e.actions[0].gate):w.countries.discard(tag)
            w.owned[capital]=w.controlled[capital]='ENG'
            before=copy.deepcopy(w.countries);w.cached(rootkey+'_create',0)
            self.assertEqual(w.countries,before,rootkey)
            self.assertNotIn('JX_R14_'+rootkey+'_CREATED',w.flags)
            w.owned[capital]=w.controlled[capital]='JAP'
            self.assertTrue(w.action(rootkey+'_create',0),rootkey)
            self.assertIn(BY[rootkey+'_local'].country,w.countries,rootkey)
            self.assertIn('JX_R14_'+rootkey+'_CREATED',w.flags,rootkey)

    def test_annexed_usa_clears_unanswered_national_talks(self):
        w=ready();w.flags['JX_US_INV_PENDING']=1;w.countries.discard('USA')
        w.wars={p for p in w.wars if 'USA' not in p}
        self.assertTrue(w.dispatch('r14_us_national_interrupted'))
        self.assertNotIn('JX_US_INV_PENDING',w.flags);self.assertNotIn('JX_US_INV_DONE',w.flags)

    def test_peace_renewal_never_appears_during_renewed_war(self):
        w=ready();w.flags.update(JX_US_PEACE=1,JX_US_RETURN_HAWAII=1)
        w.history[str(BY['us_signed'].id)]=0;w.day=1900
        before=copy.deepcopy(w.properties);w.cached('us_treaty_expiry',0)
        self.assertEqual(w.properties,before);self.assertNotIn('JX_R14_US_RENEWED',w.flags)

    def test_visible_actions_remain_compact(self):
        for e in EVENTS:
            for a in e.actions:
                if a.name:self.assertLess(len(a.gate),3000,e.key+' '+str(len(a.gate)))

    def test_soviet_full_chain_and_cached_axis_interruption(self):
        w=ready()
        for p in (1191,1190,1169,1162,1142):w.controlled[p]='JAP'
        w.owned[1191]='SOV'
        self.assertTrue(w.action('soviet_terms',0));w.advance(15)
        self.assertIn('JX_SOV_TERMS_DONE',w.flags);self.assertNotIn('JX_SOV_TERMS_PENDING',w.flags)
        self.assertEqual(w.owned[1191],'JAP');self.assertFalse(w.atwar('JAP','SOV'));self.assertTrue(w.atwar('GER','SOV'));self.assertTrue(w.atwar('JAP','USA'))
        x=ready();x.flags.update(JX_SOV_TERMS_PENDING=1,JX_R14_SOV_ACCEPTED=1);x.groups['JAP']='Axis'
        old=copy.deepcopy(x.owned);x.cached('soviet_land',0);x.dispatch('soviet_land')
        self.assertEqual(x.owned,old);self.assertNotIn('JX_SOV_TERMS_PENDING',x.flags);self.assertTrue(x.atwar('GER','SOV'))

    def test_final_script_has_single_command_triggers_and_stable_ids(self):
        for e in EVENTS:
            if e.key.startswith('r14_') or e.key in ('us_peace','us_terms','us_implement','us_finish','us_signed','soviet_land','soviet_signed'):
                for a in e.actions:
                    for c in a.commands:
                        self.assertLessEqual(len(build.getall(build.parse(build.resolve(c)),'trigger')),1,e.key)
            self.assertEqual(e.id,build.IDS[e.key])


if __name__=='__main__':unittest.main(verbosity=2)

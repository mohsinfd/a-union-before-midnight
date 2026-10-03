"""Script-state transaction tests; intentionally not a native queue emulator."""
import copy
from pathlib import Path
import unittest
from dh_save_spans import Node, parse, walk
import aubm_redesign_route_finish as finish
import aubm_redesign_navigation as navigation


def state():
    return dict(flags={"ind_aubm_commitment_japan", "ind_aubm_jp_partnership"},
        year=1942, ai=False, exists={"IND", "JAP", "GER", "SOV"}, puppets=set(),
        wars={frozenset(("IND","SOV")), frozenset(("GER","SOV"))},
        alliances=set(), control={163:"GER",713:"IND",709:"IND"},
        stocks={"IND":{"supplies":2000,"oil":1000,"money":1000,"dissent":5},
                "GER":{"supplies":10,"oil":10,"money":1000,"dissent":5}}, queued=[])


def evaluate(node, s, country="IND"):
    def one(key, value):
        if key in ("AND","OR","NOT"):
            results=[one(f.key,f.value) for f in value.fields]
            return all(results) if key=="AND" else any(results) if key=="OR" else not any(results)
        if key=="flag":return value in s["flags"]
        if key=="exists":return value in s["exists"]
        if key=="ispuppet":return value in s["puppets"]
        if key=="year":return s["year"]>=int(value)
        if key=="ai":return s["ai"]==(value=="yes")
        if key=="atwar":return any(country in pair for pair in s["wars"])==(value=="yes")
        if key in ("alliance","war"):
            return frozenset(value.all("country")) in s["alliances" if key=="alliance" else "wars"]
        if key=="control":return s["control"].get(int(value.get("province")))==value.get("data")
        if key in ("supplies","oil","money","dissent"):
            return s["stocks"][country][key]>=float(value)
        raise AssertionError("Unknown predicate "+key)
    return all(one(f.key,f.value) for f in node.fields)


def apply(action, s, country="IND"):
    assert evaluate(action.get("trigger"),s,country)
    for command in action.all("command"):
        kind=command.get("type")
        if kind=="setflag":s["flags"].add(command.get("which"))
        elif kind=="clrflag":s["flags"].discard(command.get("which"))
        elif kind=="event":s["queued"].append((int(command.get("which")),command.get("where"),int(command.get("when"))))
        elif kind in ("supplies","oilpool","money","dissent"):
            stock="oil" if kind=="oilpool" else kind
            s["stocks"][country][stock]+=float(command.get("value"))
        else:raise AssertionError(kind)


def index(files):
    return {int(ev.get("id")):ev for text in files.values() for ev in parse(text).all("event")}


class RouteFinishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]/"mod/db/events/aubm_v4"
        cls.source={p.name:p.read_text(encoding="cp1252") for p in root.glob("*.txt")}
        cls.previous,_=navigation.transform(cls.source)
        cls.output,cls.records=finish.transform(cls.previous)
        cls.before,cls.after=index(cls.previous),index(cls.output)

    def aa(self,eid):return [a.value for a in finish.actions(self.after[eid])]

    def effect_action(self,eid,kind):
        return next(a for a in self.aa(eid) if any(c.get("type")==kind for c in a.all("command")))

    def test_routefree_partner_variants_and_real_context(self):
        paid=self.aa(9289649)[0]
        for route in (None,"allied","german","soviet","japan","sovereign"):
            s=state()
            if route:s["flags"].add("ind_aubm_route_"+route)
            self.assertTrue(evaluate(paid.get("trigger"),s))
        ally=state();ally["flags"].clear();ally["alliances"].add(frozenset(("IND","JAP")))
        self.assertTrue(evaluate(paid.get("trigger"),ally))
        for change in ("no_partner","hostile_japan","hostile_germany","lost_baku","germany_peace","india_peace","puppet_india","puppet_japan","puppet_germany"):
            s=state()
            if change=="no_partner":s["flags"].clear()
            elif change.startswith("hostile"):s["wars"].add(frozenset(("IND","JAP" if change.endswith("japan") else "GER")))
            elif change=="lost_baku":s["control"][713]="SOV"
            elif change=="germany_peace":s["wars"].discard(frozenset(("GER","SOV")))
            elif change=="india_peace":s["wars"].discard(frozenset(("IND","SOV")))
            else:s["puppets"].add({"puppet_india":"IND","puppet_japan":"JAP","puppet_germany":"GER"}[change])
            self.assertFalse(evaluate(paid.get("trigger"),s),change)

    def test_affordability_defer_decline_and_one_payment(self):
        paid,cancel,decline=self.aa(9289649)
        for stock,cost in (("supplies",1200),("oil",500)):
            s=state();s["stocks"]["IND"][stock]=cost-1
            self.assertFalse(evaluate(paid.get("trigger"),s))
        s=state();before=copy.deepcopy(s);apply(cancel,s);self.assertEqual(s,before)
        apply(decline,s);self.assertIn(finish.DECLINED,s["flags"])
        self.assertFalse(evaluate(paid.get("trigger"),s))
        s=state();apply(paid,s)
        self.assertEqual(s["stocks"]["IND"]["supplies"],800)
        self.assertEqual(s["stocks"]["IND"]["oil"],500)
        self.assertFalse(evaluate(paid.get("trigger"),s))
        self.assertEqual(s["queued"],[(9289650,"GER",2),(9289651,"IND",4)])

    def test_unpaid_foreign_or_ack_callbacks_cannot_award_anything(self):
        s=state()
        for eid,country in ((9289650,"GER"),(9289651,"IND")):
            for a in self.aa(eid):
                if a.all("command"):self.assertFalse(evaluate(a.get("trigger"),s,country))
        self.assertIsNone(self.after[9289650].get("trigger"))
        self.assertIsNone(self.after[9289651].get("trigger"))
        self.assertEqual(self.after[9289650].get("country"),"GER")
        self.assertEqual(self.after[9289651].get("country"),"IND")

    def test_success_delivers_once_and_credits_without_refund(self):
        s=state();apply(self.aa(9289649)[0],s)
        receive=self.aa(9289650)[0];apply(receive,s,"GER")
        self.assertEqual(s["stocks"]["GER"]["supplies"],910)
        self.assertEqual(s["stocks"]["GER"]["oil"],360)
        self.assertFalse(evaluate(receive.get("trigger"),s,"GER"))
        # Receipt is a fact, not a live political eligibility check.
        s["flags"].discard("ind_aubm_commitment_japan")
        s["flags"].discard("ind_aubm_jp_partnership")
        s["wars"].add(frozenset(("IND","GER")));s["control"][713]="SOV"
        ack,refund,_=self.aa(9289651)
        self.assertTrue(evaluate(ack.get("trigger"),s))
        self.assertFalse(evaluate(refund.get("trigger"),s))
        apply(ack,s)
        self.assertEqual(s["stocks"]["IND"]["supplies"],800)
        self.assertIn(finish.DELIVERED,s["flags"])
        self.assertIn("ind_aubm_coalition_credit",s["flags"])
        self.assertFalse(evaluate(ack.get("trigger"),s))
        self.assertFalse(evaluate(refund.get("trigger"),s))

    def test_failed_or_missing_germany_refunds_once_and_can_retry(self):
        for failure in ("lost_corridor","germany_missing","hostile"):
            s=state();apply(self.aa(9289649)[0],s)
            if failure=="lost_corridor":s["control"][713]="SOV"
            elif failure=="germany_missing":s["exists"].remove("GER")
            else:s["wars"].add(frozenset(("IND","GER")))
            self.assertFalse(evaluate(self.aa(9289650)[0].get("trigger"),s,"GER"))
            refund=self.aa(9289651)[1];apply(refund,s)
            self.assertEqual(s["stocks"]["IND"]["supplies"],2000)
            self.assertEqual(s["stocks"]["IND"]["oil"],1000)
            self.assertEqual(s["stocks"]["GER"]["supplies"],10)
            self.assertFalse(evaluate(refund.get("trigger"),s))
            self.assertFalse(evaluate(self.aa(9289650)[0].get("trigger"),s,"GER"))
            s["control"][713]="IND";s["exists"].add("GER");s["wars"].discard(frozenset(("IND","GER")))
            self.assertTrue(evaluate(self.aa(9289649)[0].get("trigger"),s))

    def test_grand_campaign_requires_every_earned_milestone_once(self):
        e=self.after[9289652]
        milestones={f.value for n in walk(e.get("trigger")) for f in n.fields if f.key=="flag" and
                    (str(f.value).startswith("ind_aubm_japan_grand_") or f.value==finish.DELIVERED)}
        milestones.discard("ind_aubm_japan_grand_campaign_complete")
        s=state();s["flags"]|=milestones|{"ind_aubm_regional_victory_chi"}
        reward=self.effect_action(9289652,"money")
        self.assertTrue(evaluate(reward.get("trigger"),s))
        for flag in milestones:
            missing=copy.deepcopy(s);missing["flags"].remove(flag)
            self.assertFalse(evaluate(reward.get("trigger"),missing),flag)
        apply(reward,s)
        self.assertEqual(s["stocks"]["IND"]["money"],1200)
        self.assertEqual(s["stocks"]["IND"]["supplies"],2300)
        self.assertEqual(s["stocks"]["IND"]["dissent"],3)
        self.assertFalse(evaluate(reward.get("trigger"),s))

    def test_chapter_milestone_effects_preserved_and_no_navigation_completion(self):
        for eid in range(9289645,9289649):
            def effects(event):return [(c.get("type"),c.get("which"),c.get("value")) for a in finish.actions(event)
                                     for c in a.value.all("command") if c.get("type")!="event"]
            self.assertEqual(effects(self.before[eid]),effects(self.after[eid]))
        for eid in (9281001,9289645):
            for a in self.aa(eid):
                self.assertTrue(all(c.get("type")=="event" for c in a.all("command")))

    def test_no_new_ids_no_direct_callback_decisions_and_text_bounds(self):
        self.assertEqual(set(self.before),set(self.after))
        self.assertEqual(len(self.records),124)
        for eid in range(9289645,9289653):
            e=self.after[eid]
            self.assertIsNone(e.get("decision"))
            self.assertLessEqual(len(e.get("desc")),500)
            self.assertLessEqual(len(e.get("name")),58)
            for a in finish.actions(e):self.assertLessEqual(len(a.value.get("name")),58)
            for root in finish.predicate_roots(e):
                for n in walk(root):
                    self.assertFalse(any(f.key=="flag" and f.value in finish.OLD_ACCESS_FLAGS for f in n.fields))

    def test_idempotent_and_unrelated_effect_nodes_not_changed(self):
        again,_=finish.transform(self.output);self.assertEqual(again,self.output)
        def canon(n):return tuple((f.key,canon(f.value) if isinstance(f.value,Node) else f.value) for f in n.fields)
        for eid in set(self.before)-set(finish.EVENT_IDS):self.assertEqual(canon(self.before[eid]),canon(self.after[eid]),eid)

    def test_fixed_reply_owner_and_no_new_war_or_unit_commands(self):
        callers=[]
        for eid,e in self.after.items():
            for a in finish.actions(e):
                for c in a.value.all("command"):
                    if c.get("type")=="event" and c.get("which")=="9289651":
                        callers.append((eid,c.get("where"),c.get("when")))
                    if eid in range(9289645,9289653):
                        self.assertIn(c.get("type"),{"event","setflag","clrflag","supplies","oilpool","money","dissent"})
        self.assertEqual(callers,[(9289649,"IND","4")])

    def family_state(self, family):
        s = state(); s['flags'].clear()
        s['exists'].update({'ENG','USA','ITA','CHC','CHI','SIA'})
        s['wars'].add(frozenset(('IND','HOL')))
        if family != 'sovereign':
            tag = dict(allied='ENG', german='GER', soviet='SOV', japan='JAP')[family]
            s['alliances'].add(frozenset(('IND',tag)))
            s['wars'].discard(frozenset(('IND',tag)))
        return s

    def test_all_five_selectors_current_state_and_route_independence(self):
        for eid, family in finish.SELECTORS.items():
            e = self.after[eid]
            for route in (None, *finish.BASES):
                s = self.family_state(family)
                if route: s['flags'].add('ind_aubm_route_' + route)
                self.assertTrue(evaluate(e.get('decision'), s), (eid,route))
                a = self.aa(eid)[0]
                self.assertTrue(evaluate(a.get('trigger'),s))
                apply(a,s)
                self.assertFalse(evaluate(e.get('decision'),s))
                self.assertIn('ind_aubm_bespoke_route_contract_alpha23',s['flags'])
                self.assertIn('ind_aubm_route_charter_'+family,s['flags'])
            for other, flags in finish.COMPACTS.items():
                if other == family: continue
                for flag in flags:
                    s = self.family_state(family);s['flags'].add(flag)
                    self.assertFalse(evaluate(e.get('decision'),s),(eid,flag))

    def test_focus_preserves_effects_costs_and_all_local_milestones(self):
        def effects(a):
            return [tuple((f.key,finish.canon(f.value)) for f in c.fields if f.key!='trigger')
                    for c in a.all('command')]
        for eid in finish.FOCUS_IDS:
            before = [a.value for a in finish.actions(self.before[eid])]
            after = self.aa(eid)
            self.assertEqual([effects(a) for a in before], [effects(a) for a in after[:len(before)]],eid)
            for ba,aa in zip(before,after):
                if ba.get('trigger'):
                    for node in walk(ba.get('trigger')):
                        for f in node.fields:
                            if f.key in ('money','supplies','oil','manpower'):
                                self.assertIn((f.key,f.value),[(x.key,x.value) for n in walk(aa.get('trigger')) for x in n.fields],eid)
            ev = self.after[eid]
            predicate_flags = {f.value for r in finish.predicate_roots(ev) for n in walk(r)
                               for f in n.fields if f.key=='flag'}
            self.assertFalse(predicate_flags & {'ind_aubm_route_'+x for x in finish.BASES},eid)
            self.assertNotIn('ind_aubm_bespoke_route_contract_alpha23',predicate_flags,eid)
            self.assertNotIn('ind_aubm_wartime_framework',predicate_flags,eid)
            if ev.get('trigger'):
                oldflags = {f.value for n in walk(self.before[eid].get('trigger')) for f in n.fields if f.key=='flag'}
                local = {f for f in oldflags if 'focus_' in f or f in ('ind_aubm_route_war_achievement','ind_aubm_postwar_congress_completed')}
                self.assertTrue(local <= predicate_flags,(eid,local-predicate_flags))

    def test_twenty_focus_activations_and_twenty_earned_rewards(self):
        def positive_flags(node):
            found=set()
            for f in node.fields:
                if f.key=='flag':found.add(f.value)
                elif isinstance(f.value,Node) and f.key!='NOT':found.update(positive_flags(f.value))
            return found
        for family,base in finish.BASES.items():
            for offset in (*range(5,9),*range(17,21)):
                eid=base+offset;s=self.family_state(family)
                positives=positive_flags(self.before[eid].get('trigger'))
                s['flags'].update(f for f in positives if f not in
                    {'ind_aubm_route_'+x for x in finish.BASES} and f not in
                    {'ind_aubm_bespoke_route_contract_alpha23','ind_aubm_wartime_framework'})
                root=self.after[eid].get('trigger')
                self.assertTrue(evaluate(root,s),eid)
                focus=next(f for f in positives if f.startswith('ind_aubm_route_focus_'))
                s['flags'].discard(focus);self.assertFalse(evaluate(root,s),eid)
                s['flags'].add(focus);s['flags'].add('ind_aubm_route_war_achievement')
                self.assertFalse(evaluate(root,s),eid)

    def test_binding_compacts_supported_without_historical_route(self):
        for family,flags in finish.COMPACTS.items():
            predicate=parse(finish.CURRENT[family])
            for flag in flags:
                s=self.family_state(family);s['alliances'].clear();s['flags'].add(flag)
                self.assertTrue(evaluate(predicate,s),(family,flag))
                primary=dict(allied='ENG',german='GER',soviet='SOV',japan='JAP')[family]
                s['puppets'].add(primary)
                if family=='allied':s['puppets'].add('USA')
                self.assertFalse(evaluate(predicate,s),(family,flag))

    def test_free_choice_cancel_and_no_new_bookkeeping_clicks(self):
        for eid,family in finish.FOCUS_IDS.items():
            offset = eid-finish.BASES[family]
            e = self.after[eid]
            if eid in finish.SELECTORS or offset==4 or 13<=offset<=16:
                self.assertEqual(e.get('persistent'),'yes')
                self.assertIsNone(e.get('date'))
                cancel = self.aa(eid)[-1]
                self.assertEqual(cancel.all('command'),[])
                self.assertTrue(evaluate(cancel.get('trigger'),self.family_state(family)))
            elif 5<=offset<=20:
                self.assertEqual(finish.canon(e.get('date')),finish.canon(self.before[eid].get('date')))
                self.assertEqual(len(self.aa(eid)),len(finish.actions(self.before[eid])))
            else:
                self.assertIsNone(e.get('decision'))

    def test_logical_negative_substitution_and_regional_acceptance(self):
        for family, old in (('soviet',finish.OLD_SOV),('sovereign',finish.OLD_INDEPENDENT)):
            raw = 'event = { id = 1 trigger = { NOT = { '+old+' } } }'
            result = finish.substitute_focus(raw,family)
            pred = parse(result).get('event').get('trigger')
            yes = self.family_state(family)
            self.assertFalse(evaluate(pred,yes))
            yes['puppets'].add('IND');self.assertTrue(evaluate(pred,yes))
        s=self.family_state('sovereign');s['flags'].add('ind_v3_delhi_pact')
        e=self.after[9289664]
        self.assertFalse(evaluate(e.get('trigger'),s))
        s['flags'].add('ind_v43_nam_siam_partner')
        self.assertTrue(evaluate(e.get('trigger'),s))
        s['wars'].add(frozenset(('IND','SIA')))
        self.assertFalse(evaluate(e.get('trigger'),s))

    def test_collapse_fallback_and_owned_reply_invalidation(self):
        for family, primary, fallback in (('german','GER','ITA'),('soviet','SOV','CHC'),('japan','JAP','SIA')):
            s=self.family_state(family);s['exists'].discard(primary);s['alliances'].clear()
            s['flags'].add('ind_aubm_commitment_'+family)
            e=self.after[finish.BASES[family]+4]
            self.assertTrue(evaluate(e.get('trigger'),s),family)
            s['wars'].add(frozenset(('IND',fallback)))
            self.assertFalse(evaluate(e.get('trigger'),s),family)
        for family,base in finish.BASES.items():
            pending='ind_aubm_bespoke_partner_response_'+family+'_pending'
            done='ind_aubm_bespoke_partner_response_'+family+'_done'
            s=self.family_state(family);s['flags'].add(pending)
            reply=self.aa(base+22)
            self.assertTrue(evaluate(reply[0].get('trigger'),s),family)
            s['puppets'].add('IND')
            self.assertFalse(evaluate(reply[0].get('trigger'),s))
            self.assertTrue(evaluate(reply[-2].get('trigger'),s))
            apply(reply[-2],s)
            self.assertIn(done,s['flags']);self.assertNotIn(pending,s['flags'])
            self.assertTrue(evaluate(reply[-1].get('trigger'),s))


if __name__=="__main__":unittest.main()

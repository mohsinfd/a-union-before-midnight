"""Script-state tests; not a simulation of native event polling or combat."""
import copy
import unittest
from dh_save_spans import Node, parse
import aubm_redesign_campaign_stories as s


def fresh():
    return dict(flags=set(), exists={'IND', 'GER', 'ITA', 'ENG', 'USA', 'SOV', 'PER', 'AFG'},
                puppets=set(), wars=set(), alliances=set(), control={}, owned={}, garrison={},
                stocks=dict(money=5000, supplies=10000, oil=5000, dissent=10, manpower=100), effects=[])


def evaluate(node, state):
    def one(k, v):
        if k in ('AND', 'OR', 'NOT'):
            values = [one(f.key, f.value) for f in v.fields]
            return all(values) if k == 'AND' else any(values) if k == 'OR' else not any(values)
        if k == 'flag': return v in state['flags']
        if k == 'ai': return v == 'no'
        if k == 'year': return 1942 >= int(v)
        if k == 'exists': return v in state['exists']
        if k == 'ispuppet': return v in state['puppets']
        if k in ('war', 'alliance'): return frozenset(v.all('country')) in state['wars' if k == 'war' else 'alliances']
        if k == 'atwar': return any('IND' in p for p in state['wars']) == (v == 'yes')
        if k in ('control', 'owned'): return state[k].get(int(v.get('province'))) == v.get('data')
        if k == 'garrison': return state['garrison'].get(int(v.get('province')), 0) >= int(v.get('size'))
        if k in state['stocks']: return state['stocks'][k] >= int(v)
        raise AssertionError(k)
    return all(one(f.key, f.value) for f in node.fields)


def apply(a, state):
    assert evaluate(a.get('trigger'), state)
    for c in a.all('command'):
        kind = c.get('type')
        if kind == 'setflag': state['flags'].add(c.get('which'))
        elif kind == 'clrflag': state['flags'].discard(c.get('which'))
        elif kind in ('money', 'supplies', 'oilpool', 'manpowerpool', 'dissent'):
            key = {'oilpool': 'oil', 'manpowerpool': 'manpower'}.get(kind, kind)
            state['stocks'][key] += int(c.get('value'))
        else: state['effects'].append((kind, c.get('which'), c.get('where'), c.get('value')))


class CampaignStoriesTests(unittest.TestCase):
    def events(self, c): return parse(s.render(c)).all('event')

    def prepared(self, c, choice=0):
        st = fresh(); family = c['family']
        if family != 'sovereign': st['alliances'].add(frozenset(('IND', {'allied':'ENG','german':'GER','soviet':'SOV'}[family])))
        st['wars'].add(frozenset(('IND', {'allied':'GER','german':'SOV','soviet':'GER','sovereign':'PER'}[family])))
        st['control'].update({163:'GER',195:'GER',1517:'IND',1447:'IND'})
        st['owned'].update({1517:'IND',1447:'IND'})
        apply(self.events(c)[0].all('action')[choice], st)
        return st

    def accomplish(self, c, st, choice=0):
        if c['family'] == 'allied': provinces = (419,377) if choice == 0 else (900,419)
        elif c['family'] == 'soviet': provinces = (163,195) if choice == 0 else (419,377)
        elif c['family'] == 'german': provinces = (713,706,663) if choice == 0 else (1103,1138)
        else:
            provinces = (1053,900,842) if choice == 0 else ()
            if choice:
                st['flags'].update(('ind_aubm_regional_victory_per','ind_aubm_regional_victory_afg'))
                st['wars'].clear()
        st['control'].update({p:'IND' for p in provinces})
        st['garrison'].update({p:6 for p in provinces})

    def test_transform_idempotent_and_exact_registry(self):
        source = {s.MODULE: 'event = { id = 1 country = IND }'}
        out, records = s.transform(source)
        self.assertEqual(out, s.transform(out)[0])
        self.assertEqual(set(records), set(s.NEW_EVENT_IDS))
        self.assertEqual(len(parse(out[s.MODULE]).all('event')), 9)
        self.assertNotIn(s.MARKER, source[s.MODULE])

    def test_collision_rejected(self):
        with self.assertRaises(ValueError): s.transform({s.MODULE:'event = { id = 9398500 }'})

    def test_registry_has_no_cross_feature_collision(self):
        from build_aubm_redesign import registered_new_ids
        self.assertTrue(set(s.NEW_EVENT_IDS) <= registered_new_ids())

    def test_all_eight_plans_have_reachable_once_only_endings(self):
        for c in s.CAMPAIGNS:
            for choice in (0,1):
                for reward in (0,1):
                    with self.subTest(c=c['key'],choice=choice,reward=reward):
                        st = self.prepared(c,choice)
                        self.assertFalse(evaluate(parse(s.victory_gate(c)), st))
                        self.accomplish(c,st,choice)
                        end = self.events(c)[1].all('action')[reward]
                        self.assertTrue(evaluate(end.get('trigger'),st))
                        apply(end,st)
                        self.assertFalse(evaluate(end.get('trigger'),st))
                        self.assertNotIn(s.BUSY,st['flags'])
                        self.assertFalse(evaluate(parse(s.start_gate(c)),st))

    def test_defer_has_no_effect_and_abandon_cannot_restart(self):
        for c in s.CAMPAIGNS:
            st = self.prepared(c); original = copy.deepcopy(st)
            end = self.events(c)[1].all('action')
            apply(end[-2],st); self.assertEqual(original,st)
            apply(end[-1],st)
            self.assertNotIn(s.BUSY,st['flags'])
            self.assertFalse(evaluate(parse(s.start_gate(c)),st))

    def test_one_campaign_at_a_time(self):
        st = self.prepared(s.CAMPAIGNS[0])
        other = s.CAMPAIGNS[1]
        st['alliances'] = {frozenset(('IND','GER'))}; st['wars'] = {frozenset(('IND','SOV'))}
        self.assertFalse(evaluate(parse(s.start_gate(other)),st))

    def test_affordability_and_factory_ownership(self):
        for c in s.CAMPAIGNS:
            st = self.prepared(c); self.accomplish(c,st)
            for a in self.events(c)[1].all('action')[:2]:
                if any(x.get('type') == 'construct' for x in a.all('command')):
                    for p in (1517,1447):
                        bad = copy.deepcopy(st); bad['owned'][p] = 'ENG'
                        self.assertFalse(evaluate(a.get('trigger'),bad))
                for cmd in a.all('command'):
                    kind = cmd.get('type')
                    if kind in ('money','supplies','oilpool') and int(cmd.get('value')) < 0:
                        bad = copy.deepcopy(st); bad['stocks'][{'oilpool':'oil'}.get(kind,kind)] = -int(cmd.get('value')) - 1
                        self.assertFalse(evaluate(a.get('trigger'),bad))

    def test_axis_collapse_rescue_and_continued_victory(self):
        c = s.CAMPAIGNS[1]; st = self.prepared(c)
        st['control'][713] = 'IND'
        self.assertFalse(evaluate(parse(s.rescue_gate(c)),st))
        st['exists'].remove('GER'); st['alliances'].clear()
        self.assertTrue(evaluate(parse(s.rescue_gate(c)),st))
        completed = copy.deepcopy(st); self.accomplish(c,completed)
        self.assertTrue(evaluate(parse(s.victory_gate(c)),completed))
        self.assertFalse(evaluate(parse(s.rescue_gate(c)),completed))
        apply(self.events(c)[1].all('action')[2],st)
        self.assertEqual(st['stocks']['manpower'],120)
        self.assertFalse(evaluate(parse(s.rescue_gate(c)),st))

    def test_hostile_alignment_and_conflicting_choices_block_rewards(self):
        for c in s.CAMPAIGNS:
            st = self.prepared(c); self.accomplish(c,st)
            st['flags'].add(s.names(c)[3][1])
            self.assertFalse(evaluate(parse(s.victory_gate(c)),st))
            st['flags'].remove(s.names(c)[3][1])
            if c['family'] != 'sovereign':
                st['wars'].add(frozenset(('IND',{'allied':'ENG','german':'GER','soviet':'SOV'}[c['family']])))
            else: st['alliances'].add(frozenset(('IND','JAP')))
            self.assertFalse(evaluate(parse(s.victory_gate(c)),st))

    def test_coalition_occupation_needs_indian_deployment(self):
        c=s.CAMPAIGNS[0]; st=self.prepared(c);self.accomplish(c,st)
        st['control'].update({419:'ENG',377:'ENG'})
        self.assertTrue(evaluate(parse(s.victory_gate(c)),st))
        st['garrison'][419]=5
        self.assertFalse(evaluate(parse(s.victory_gate(c)),st))

    def test_manual_only_no_diplomatic_mutations_and_text_budget(self):
        for c in s.CAMPAIGNS:
            for event in self.events(c):
                for key in ('trigger','date','offset','deathdate'): self.assertIsNone(event.get(key))
                self.assertLessEqual(len(event.get('desc').encode('latin1')),500)
                self.assertLessEqual(len(event.get('name')),58)
                for a in event.all('action'):
                    self.assertLessEqual(len(a.get('name')),58)
                    for effect in a.all('command'):
                        self.assertNotIn(effect.get('type'),('event','peace','war','alliance','independence','make_puppet','secedeprovince','access'))


if __name__ == '__main__': unittest.main()

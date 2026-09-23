"""ROSTER1 regression tests on immutable, installed BALANCE1 inputs."""
from pathlib import Path
from collections import Counter
import unittest
import json
import aubm_roster1 as r
import build_roster1 as build
from dh_save_spans import parse,walk,Node

def norm(node):
    return [(f.key,norm(f.value) if isinstance(f.value,Node) else f.value) for f in node.fields]

class RosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest=json.loads((build.BUILD/'baseline.json').read_text())
        cls.base={p:(build.BUILD/'baseline'/p).read_bytes().decode('latin1') for p in manifest['hashes']}
        cls.out,cls.changes=r.transform(cls.base)
        cls.teams={int(row[0]):row for row in r.rows(cls.out[r.TEAMS])}
        cls.ministers={int(row[0]):row for row in r.rows(cls.out[r.MINISTERS])}
        cls.before=r.research_audit(cls.base,cls.base[r.TEAMS])
        cls.after=r.research_audit(cls.out,cls.out[r.TEAMS])

    def test_idempotent_and_partial_rejected(self):
        again,changes=r.transform(self.out)
        self.assertEqual(again,self.out);self.assertEqual(changes,{})
        broken=dict(self.out);broken[r.TEAMS]=self.base[r.TEAMS]
        with self.assertRaisesRegex(ValueError,'Partial'):r.transform(broken)

    def test_minister_clone_removal_and_same_office(self):
        old={int(row[0]):row for row in r.rows(self.base[r.MINISTERS])}
        self.assertEqual(len(self.ministers),84)
        for alias,canonical in r.ALIASES.items():
            self.assertNotIn(alias,self.ministers)
            self.assertEqual(old[alias][1],self.ministers[canonical][1])
        identities=[(row[1],row[2].lower()) for row in self.ministers.values()]
        self.assertEqual(len(identities),len(set(identities)))

    def test_minister_and_team_id_namespaces_separate(self):
        p='db/events/test.txt'
        raw='event = { id = 1 country = IND action = { command = { type = headofstate which = 250001 } command = { type = waketeam which = 250001 } command = { type = wakeleader which = 250001 } } }'
        out,_=r.minister_references({p:raw})
        commands=parse(out[p]).all('event')[0].get('action').all('command')
        self.assertEqual([c.get('which') for c in commands],['251001','250001','250001'])

    def test_appointment_references_and_all_event_ids(self):
        old=build.index_events(self.base);new=build.index_events(self.out)
        self.assertEqual(old.keys(),new.keys())
        changed=sum(x['references'] for x in self.changes['minister_reference_changes'])
        self.assertEqual(changed,45)
        for eid,e in old.items():
            before=[norm(c) for n in walk(e) for c in n.all('command') if c.get('type') not in r.OFFICES]
            after=[norm(c) for n in walk(new[eid]) for c in n.all('command') if c.get('type') not in r.OFFICES]
            self.assertEqual(before,after,str(eid))

    def test_service_chiefs_have_distinct_early_choices(self):
        for office in ('Chief of Navy','Chief of Army','Chief of Air Force','Minister of Security','Minister of Armament','Head of Government'):
            early=[row for row in self.ministers.values() if row[1]==office and int(row[3])<=1933 and row[6] in ('SD','SL','LWR')]
            self.assertGreaterEqual(len({row[7] for row in early}),3,office)

    def test_no_new_universal_industry_or_research_buff(self):
        for eid,(_,_,description,commands) in r.TRAITS.items():
            self.assertLessEqual(len(description),250)
            for c in parse(' '.join('command = '+x for x in commands)).all('command'):
                self.assertFalse(c.get('type')=='research' and c.get('which')=='all')
                if c.get('type')=='production' and c.get('which')=='production':self.assertLessEqual(float(c.get('value')),0)
                if c.get('type')=='unit' and c.get('when')=='time':self.assertGreaterEqual(float(c.get('value')),0)

    def test_commander_count_ranks_skills_and_portraits_unchanged(self):
        def leaders(t):return {int(row.split(';')[1]):row.split(';') for row in t.splitlines()[1:] if row and not row.startswith('#')}
        old=leaders(self.base[r.LEADERS]);new=leaders(self.out[r.LEADERS])
        self.assertEqual(len(new),512);self.assertEqual(old.keys(),new.keys())
        for eid,row in old.items():
            for i in set(range(len(row)))-{0,9}:self.assertEqual(row[i],new[eid][i],(eid,i))
        for eid in r.LEADER_ROLES:self.assertLessEqual(int(new[eid][9]).bit_count(),3)
        reserve=[row[0] for eid,row in new.items() if eid>=252000]
        self.assertEqual(len(reserve),375);self.assertEqual(len(set(reserve)),375)
        self.assertTrue(all(name.endswith('(R)') for name in reserve))

    def test_research_specialties_not_lost(self):
        old={s for row in r.rows(self.base[r.TEAMS]) for s in row[6:-1] if s}
        new={s for row in self.teams.values() for s in row[6:-1] if s}
        self.assertLessEqual(old,new)
        self.assertEqual(len(self.teams),35)
        for eid in set(r.TEAM_PLAN)|set(r.NEW_TEAMS):
            row=self.teams[eid];self.assertLessEqual(len([x for x in row[6:-1] if x]),7)
            self.assertLessEqual(int(row[3]),8)

    def test_every_team_has_a_matching_niche(self):
        winners={i for tech in self.after for i in tech['best']}
        self.assertEqual(winners,set(self.teams))

    def test_research_examples_match_intended_roles(self):
        apps={a['id']:a for a in self.after}
        expectations={4030:250013,4140:250033,4190:250033,4250:250008,4930:250033,8960:250023,81870:250022,81700:250022,82310:250032,82510:250030,9040:250034,9140:250035,9190:250025}
        for eid,team in expectations.items():
            self.assertIn(team,apps[eid]['best'],(eid,apps[eid]['name']))
            self.assertEqual(apps[eid]['top'][0]['coverage'],1.0)

    def test_doctrine_monopolies_reduced(self):
        def count(rows,category,team):return sum(team in a['best'] for a in rows if a['category']==category)
        self.assertEqual(count(self.before,'air_doctrines',250025),47)
        self.assertLess(count(self.after,'air_doctrines',250025),20)
        self.assertEqual(count(self.before,'land_doctrines',250027),43)
        self.assertLess(count(self.after,'land_doctrines',250027),15)

    def test_build_validation_and_visible_identification(self):
        out=build.identify(self.out)
        report=build.validate(self.base,out,build.b.DEFAULT)
        self.assertTrue(report['passed'],report['errors'])
        self.assertIn('27-ROSTER1',parse(out['scenarios/1933.eug']).get('header').get('name'))
        self.assertIn('PLAY 27-ROSTER1',out['config/text.csv'])
        self.assertIn('27-ROSTER1',build.index_events(out)[9270000].get('name'))

if __name__=='__main__':unittest.main()

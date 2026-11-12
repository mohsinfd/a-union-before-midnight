"""Offline checks against the actual installed naval AI/OOB changes."""
from collections import Counter
from copy import deepcopy
import json,unittest
import build as b
import enemy_transport_ai as a


class EnemyTransportReview(unittest.TestCase):
    def test_profile_changes_are_only_existing_production_fields(self):
        report=json.loads((b.HERE/'ENEMY_TRANSPORT_AI_REPORT.json').read_text())
        self.assertGreater(len(report['profiles']),0)
        for entry in report['profiles']:
            relative=entry['file'];base=b.read(b.SOURCE/relative)
            if (b.SOURCE/relative).name.casefold()=='usa_1942.ai':base=b.model_names_and_ai.allied_invasion_ai(base,'usa_1942.ai')
            old=b.parse(base);new=b.parse(b.read(b.TARGET/relative))
            before=a.get(old,'military');after=a.get(new,'military')
            total=lambda node:sum(float(v) for k,v in node if isinstance(v,str) and k not in {'relative_build_scheme'})
            self.assertAlmostEqual(total(before),total(after))
            self.assertGreater(float(a.get(after,'destroyer')),float(a.get(before,'destroyer')))
            for index,(key,value) in enumerate(before):
                if key in {'destroyer','transport','transports'}:after[index]=(key,value)
            self.assertEqual(old,new,relative)

    def test_starting_ships_stats_IDs_ports_and_other_country_data_are_preserved(self):
        report=json.loads((b.HERE/'ENEMY_TRANSPORT_AI_REPORT.json').read_text())
        for entry in report['scenarios']:
            relative=entry['file'];tag=entry['country']
            old=b.parse(b.read(b.SOURCE/relative));new=b.parse(b.read(b.TARGET/relative))
            co=next(c for c in a.allv(old,'country') if a.get(c,'tag')==tag)
            cn=next(c for c in a.allv(new,'country') if a.get(c,'tag')==tag)
            def ships(country):
                return {str(a.get(d,'id')):(d,a.get(f,'location')) for f in a.allv(country,'navalunit') for d in a.allv(f,'division')}
            self.assertEqual(ships(co),ships(cn),relative)
            def other(country):
                result=[]
                for key,value in country:
                    if key and key.casefold()=='navalunit':continue
                    if key=='allowed_brigades':
                        value=[(k,v) for k,v in value if k not in {'b_01','b_02','b_03'}]
                        if not value:continue
                    result.append((key,value))
                return result
            self.assertEqual(other(co),other(cn),relative)
            self.assertEqual(Counter(str(a.get(f,'id')) for f in a.allv(co,'navalunit')),Counter(str(a.get(f,'id')) for f in a.allv(cn,'navalunit')))
            for before,after in zip(a.allv(co,'navalunit'),a.allv(cn,'navalunit')):
                metadata=lambda f:[(k,v) for k,v in f if not(k and k.casefold()=='division')]
                self.assertEqual(metadata(before),metadata(after))

    def test_eight_existing_screens_reassigned_without_stripping_capital_coverage(self):
        report=json.loads((b.HERE/'ENEMY_TRANSPORT_AI_REPORT.json').read_text())
        self.assertEqual(report['moved_screens'],8)
        self.assertEqual(sum(len(x['moves']) for x in report['scenarios'] if x['country']=='USA'),5)
        self.assertEqual(sum(len(x['moves']) for x in report['scenarios'] if x['country']=='ENG'),3)
        for entry in report['scenarios']:
            for move in entry['moves']:
                country=next(c for c in a.allv(b.parse(b.read(b.TARGET/entry['file'])),'country') if a.get(c,'tag')==entry['country'])
                donor=next(f for f in a.allv(country,'navalunit') if a.get(f,'name')==move['from'])
                receiver=next(f for f in a.allv(country,'navalunit') if a.get(f,'name')==move['to'])
                self.assertEqual(a.get(donor,'location'),a.get(receiver,'location'))
                self.assertGreaterEqual(sum(a.counts(donor)[k] for k in a.SCREENS),a.floor(donor))
                self.assertGreater(sum(a.counts(receiver)[k] for k in a.SCREENS),0)

    def test_transform_is_repeatable_from_clean_input_and_never_touches_Japan(self):
        for name in ('usa.inc','united kingdom.inc'):
            country=a.get(b.parse(b.read(b.SOURCE/'scenarios/1933'/name)),'country')
            first=a.regroup(country);snapshot=deepcopy(country);second=a.regroup(country)
            self.assertTrue(first);self.assertFalse(second);self.assertEqual(country,snapshot)
        self.assertNotIn('JAP',a.TAGS)
        self.assertFalse(any('escort_ratio' in b.read(b.TARGET/e['file']) for e in json.loads((b.HERE/'ENEMY_TRANSPORT_AI_REPORT.json').read_text())['profiles']))


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EnemyTransportReview))
    (b.HERE/'ENEMY_TRANSPORT_AI_AUDIT.json').write_text(json.dumps({'version':b.VERSION,'passed':result.wasSuccessful(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'game_launched':False},indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)

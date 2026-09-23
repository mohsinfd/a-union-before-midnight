import hashlib
import unittest
from collections import Counter

import aubm_command_reserve as reserve
from dh_save_spans import parse,replace,walk,Node
from install_aubm_liberator3 import ai_edits,coalesce_insertions


class CommandReserveTests(unittest.TestCase):
    def test_existing_137_leaders_are_byte_preserved(self):
        original=reserve.existing_prefix(reserve.ROSTER.read_bytes())
        self.assertEqual(hashlib.sha256(original).hexdigest(),
            '1813292c943176a45c935e95628117ac30a9a8e08de3fba67de57e6d15d35b0c')

    def test_generation_is_idempotent_and_current(self):
        raw=reserve.ROSTER.read_bytes();self.assertEqual(raw,reserve.apply_to_bytes(raw))
        self.assertEqual(raw,reserve.apply_to_bytes(reserve.apply_to_bytes(raw)))

    def test_pool_and_growth_headroom(self):
        raw=reserve.ROSTER.read_bytes()
        for year,minimum in ((1939,{0:240,1:80,2:95}),(1944,{0:280,1:90,2:115})):
            actual=reserve.counts(raw,year)
            for b,n in minimum.items():self.assertGreaterEqual(actual[b],n)

    def test_unique_ids_and_names_and_anonymous_portraits(self):
        rows=reserve.reserve_rows()
        self.assertEqual(len(rows),375)
        self.assertEqual(len({r[1] for r in rows}),len(rows));self.assertEqual(len({r[0] for r in rows}),len(rows))
        for r in rows:
            self.assertEqual(len(r),19);self.assertEqual(r[14],'unknown')
            self.assertTrue(r[0].endswith('(R)'));self.assertIn(int(r[10]),(2,3))
            self.assertLessEqual(int(r[8]),6)

    def test_specialists_scale_with_larger_forces(self):
        counts=Counter()
        for r in reserve.reserve_rows():
            if int(r[15])>1939:continue
            for bit in reserve.TRAITS:
                if int(r[9])&bit:counts[(int(r[13]),bit)]+=1
        for branch,bit,minimum in ((0,256,24),(0,128,24),(0,524288,12),
            (0,4194304,12),(0,8388608,12),(0,8,12),(1,1024,24),
            (1,4096,24),(1,2048,12),(2,131072,20),(2,16384,20),(2,32768,20)):
            self.assertGreaterEqual(counts[(branch,bit)],minimum)

    def test_all_added_traits_match_their_service(self):
        masks={0:sum((1,2,4,8,16,32,64,128,256,262144,524288,2097152,4194304,8388608)),
            1:1024|2048|4096|8192,2:4096|8192|16384|32768|65536|131072}
        for r in reserve.reserve_rows():self.assertEqual(int(r[9])&~masks[int(r[13])],0)

    def test_save_records_preserve_start_dates_and_skills(self):
        for r in reserve.reserve_rows():
            n=parse(reserve.save_block(r,1941)).get('leader')
            self.assertEqual(n.get('startyear'),r[15]);self.assertEqual(n.get('skill'),r[10])
            self.assertEqual(n.get('category'),('general','admiral','commander')[int(r[13])])
            self.assertEqual(n.get('id').get('id'),r[1])

    def test_lossless_parser_keeps_undefined_cp1252_and_repeated_keys(self):
        raw=b'# original\r\ncountry = { tag = IND name = "\x81\xff" y = 1933 y = 1934 list = { 1 2 } }\r\n'
        t=parse(raw);c=t.get('country');self.assertEqual(c.all('y'),['1933','1934'])
        self.assertEqual(c.get('list').atoms(),['1','2'])
        f=c.field('tag');changed=replace(raw,[(f.value_start,f.end,b'JAP')])
        self.assertEqual(changed.replace(b'JAP',b'IND'),raw)

    def test_ai_fragment_clears_blacklist_but_preserves_unrelated_settings(self):
        raw=b'ai = { war = 0 military = { infantry = 27 } befriend = { IND = 200 XYZ = 50 } front = { passivity = { IND = 100 } other = 123 } admiral = { ignore = { "Bay of Bengal" } min_org = 90 } }'
        fragment=parse(b'befriend = { IND = 0 } front = { passivity = { IND = 20 HOL = 0 } } admiral = { ignore = { } }')
        result=replace(raw,coalesce_insertions(ai_edits(raw,parse(raw).get('ai'),fragment)))
        ai=parse(result).get('ai')
        self.assertEqual(ai.get('war'),'0');self.assertEqual(ai.get('military').get('infantry'),'27')
        self.assertEqual(ai.get('befriend').get('XYZ'),'50');self.assertEqual(ai.get('befriend').get('IND'),'0')
        self.assertEqual(ai.get('front').get('other'),'123');self.assertEqual(ai.get('front').get('passivity').get('HOL'),'0')
        self.assertEqual(ai.get('admiral').get('ignore').atoms(),[])
        self.assertEqual(ai.get('admiral').get('min_org'),'90')


if __name__=='__main__':unittest.main()

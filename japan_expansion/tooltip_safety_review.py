"""Reproduce the crash bytes and enforce compact native tooltip text."""
import struct,unittest
import build as b
import tooltip_safety as t
import unique_attachments as a
import unique_divisions as d

b.prepare_catalog()


class TooltipReview(unittest.TestCase):
    def test_original_payload_matches_the_crash_instruction_address(self):
        original=a.ATTACHMENTS['b_02']['desc']
        label='Dokuritsu Konsei Mixed Brigade 1937 (Mixed Bde-1)'
        payload=(original+'\n'+label).encode('latin1')
        self.assertEqual(len(payload),270)
        self.assertEqual(struct.unpack('<I',payload[256:260])[0],0x694d2820)
        fixed=t.player_text('JX_b_02_DESC',original)
        self.assertLess(t.check_payload(fixed,label),224)

    def test_every_specialist_model_fits_with_margin(self):
        rows={line.split(';')[0]:line.split(';')[1] for line in b.localisation().splitlines() if ';' in line and not line.startswith('#')}
        for unit,info in a.ATTACHMENTS.items():
            desc=rows['JX_'+unit+'_DESC']
            for i,year in enumerate(info['years']):
                label=info['name']+' '+str(year)+' ('+info['short']+'-'+str(i+1)+')'
                self.assertLessEqual(t.check_payload(desc,label),224)
        for unit,info in d.CLASSES.items():
            desc=rows['JX_'+unit+'_DESC']
            for i,name in enumerate(info['model_names']):
                label=name+' ('+info['short']+'-'+str(i+1)+')'
                self.assertLessEqual(t.check_payload(desc,label),224)

    def test_owned_narrative_has_no_raw_percent_or_colour_codes(self):
        for line in b.localisation().splitlines():
            if line.startswith('JX_'):
                key,value=line.split(';')[:2]
                self.assertNotIn('%',value,key);self.assertNotIn('\xa7',value,key)
        self.assertEqual(t.player_text('JX_example_DESC','Cost +15%, time -5%.'),'Cost +15 percent, time -5 percent.')
        self.assertEqual(t.player_text('VANILLA_FORMAT','%s: %.1f'),' %s: %.1f'.lstrip())

    def test_future_oversized_text_fails_instead_of_shipping(self):
        with self.assertRaises(ValueError):t.player_text('JX_d_99_DESC','x'*141)
        with self.assertRaises(ValueError):t.check_payload('x'*140,'y'*90)


if __name__=='__main__':unittest.main(verbosity=2)

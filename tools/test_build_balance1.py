"""Installer safety tests run in temporary directories, not the game folder."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import build_balance1 as b
from dh_save_spans import parse

class BuildSafetyTests(unittest.TestCase):
    def test_resolved_path_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.assertEqual(b.safe(root,'db/events/x.txt'),(root/'db/events/x.txt').resolve())
            for value in ('../outside.txt','.'):
                with self.assertRaises(ValueError):b.safe(root,value)

    def test_stock_repair_is_no_effect_and_idempotent(self):
        p='db/events/ai/ai_ministers.txt'
        raw=(b.BUILD/'baseline'/p).read_bytes().decode('latin1')
        fixed=b.repair_stock_syntax({p:raw})
        e=next(e for e in parse(fixed[p]).all('event') if e.get('id')=='5200093')
        self.assertEqual(e.get('action_a').all('command')[0].fields,[])
        self.assertEqual(b.repair_stock_syntax(fixed),fixed)

    def fixture(self,root):
        mod=root/'mod';(mod/'config').mkdir(parents=True)
        (mod/'config/text.csv').write_bytes(b'original\r\n')
        save=mod/'scenarios/save games/test.eug';save.parent.mkdir(parents=True);save.write_bytes(b'not parsed or migrated')
        return mod,{'config/text.csv':'original\r\n'},{'config/text.csv':'new\r\n','ai/new.ai':'front = { }'}

    def test_backup_hash_install_and_save_preservation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);mod,base,out=self.fixture(root)
            with patch.object(b,'BUILD',root/'build'),patch.object(b.subprocess,'run',return_value=SimpleNamespace(stdout='')):
                receipt=b.install(mod,base,out,{'passed':True})
            self.assertEqual((mod/'config/text.csv').read_bytes(),b'new\r\n')
            self.assertEqual((Path(receipt['backup'])/'config/text.csv').read_bytes(),b'original\r\n')
            self.assertTrue(receipt['saves_unchanged'])
            self.assertEqual(receipt['save_file_count'],1)

    def test_preimage_conflict_and_running_game_refuse(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);mod,base,out=self.fixture(root)
            with patch.object(b,'BUILD',root/'build'),patch.object(b.subprocess,'run',return_value=SimpleNamespace(stdout='123')):
                with self.assertRaisesRegex(ValueError,'Close Darkest'):b.install(mod,base,out,{'passed':True})
            (mod/'config/text.csv').write_bytes(b'new user change')
            with patch.object(b,'BUILD',root/'build'),patch.object(b.subprocess,'run',return_value=SimpleNamespace(stdout='')):
                with self.assertRaisesRegex(ValueError,'baseline changed'):b.install(mod,base,out,{'passed':True})
            self.assertFalse((mod/'ai/new.ai').exists())
            self.assertEqual((mod/'config/text.csv').read_bytes(),b'new user change')

    def test_post_write_failure_rolls_back_exact_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);mod,base,out=self.fixture(root)
            with patch.object(b,'BUILD',root/'build'),patch.object(b.subprocess,'run',return_value=SimpleNamespace(stdout='')),patch.object(b,'saves',side_effect=[{'x':'a'},{'x':'b'}]):
                with self.assertRaisesRegex(ValueError,'Save fingerprint changed'):b.install(mod,base,out,{'passed':True})
            self.assertEqual((mod/'config/text.csv').read_bytes(),b'original\r\n')
            self.assertFalse((mod/'ai/new.ai').exists())
            self.assertEqual((mod/'scenarios/save games/test.eug').read_bytes(),b'not parsed or migrated')

if __name__=='__main__':unittest.main()

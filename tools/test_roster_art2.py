"""Fast unit tests for artwork-only packaging and refusal guarantees."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main, mock
import io
import json
from PIL import Image
import build_roster_art2 as art

HEADER = 'Name;ID;Country;Rank 3 Year;Rank 2 Year;Rank 1 Year;Rank 0 Year;Ideal Rank;Max Skill;Traits;Skill;Experience;Loyalty;Type;Picture;Start Year;End Year;Retirement Year;x\r\n'
ROW = 'Officer (R);252000;IND;1933;1940;1945;1999;3;7;64;2;0;5;0;old_face;1933;1970;1999;x\r\n'


class ArtworkTests(TestCase):
    def test_native_header(self):
        _, col, records = art.rows(HEADER + ROW)
        self.assertEqual(col['picture'], 14)
        self.assertEqual(col['type'], 13)
        self.assertEqual(len(records), 1)

    def test_only_picture_and_exact_newlines(self):
        old = HEADER + ROW
        new = art.change_pictures(old, {252000:'AUBM_R2_252000'})
        self.assertEqual(new, old.replace(';old_face;', ';AUBM_R2_252000;'))
        art.verify_picture_only(old, new, {252000})
        self.assertEqual(art.change_pictures(new, {252000:'AUBM_R2_252000'}), new)

    def test_gameplay_mutation_refused(self):
        with self.assertRaises(ValueError):
            art.verify_picture_only(HEADER + ROW, (HEADER + ROW).replace(';64;', ';128;'), {252000})

    def test_unapproved_picture_refused(self):
        with self.assertRaises(ValueError):
            art.verify_picture_only(HEADER + ROW, (HEADER + ROW).replace('old_face', 'new_face'), set())

    def test_duplicate_or_malformed_rows_refused(self):
        for text in (HEADER + ROW + ROW, HEADER + ROW.replace(';old_face', ';extra;old_face')):
            with self.assertRaises(ValueError):
                art.rows(text)

    def test_invalid_reference_refused(self):
        for name in ('../danger', 'foo/bar', 'foo.bmp', 'C:\\outside'):
            with self.assertRaises(ValueError):
                art.change_pictures(HEADER + ROW, {252000:name})

    def test_pack_native_format_and_determinism(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source.png'
            Image.new('RGBA', (300,500), (70,80,90,255)).save(source)
            packed = art.pack(source)
            self.assertEqual(packed, art.pack(source))
            self.assertEqual(int.from_bytes(packed[28:30], 'little'), 24)
            image, digest, _ = art.image_metrics(packed)
            self.assertEqual(image.size, (36,50))
            self.assertEqual(image.mode, 'RGB')
            self.assertEqual(len(digest), 64)
            with self.assertRaises(ValueError):
                art.pack(source, [0,0,2,1])

    def test_wrong_native_size_refused(self):
        buf = io.BytesIO()
        Image.new('RGB', (96,96)).save(buf, format='BMP')
        with self.assertRaises(ValueError):
            art.image_metrics(buf.getvalue())

    def test_path_bounds(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                art.b.safe(Path(tmp), '../escape.bmp')

    def test_base_game_fallback(self):
        with TemporaryDirectory() as tmp:
            game = Path(tmp)
            mod = game / 'Mods/Example'
            mod.mkdir(parents=True)
            fallback = game / 'gfx/interface/pics/old_face.bmp'
            fallback.parent.mkdir(parents=True)
            fallback.write_bytes(b'base')
            self.assertEqual(art.picture_path(mod, 'old_face'), fallback.resolve())
            preferred = mod / 'gfx/interface/pics/old_face.bmp'
            preferred.parent.mkdir(parents=True)
            preferred.write_bytes(b'mod')
            self.assertEqual(art.picture_path(mod, 'old_face'), preferred.resolve())

    def test_snapshot_immutable_and_scoped(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            mod, build = root/'mod', root/'build'
            source = mod/art.REL
            source.parent.mkdir(parents=True)
            source.write_bytes((HEADER+ROW).encode('latin1'))
            saved = art.snapshot(mod, build)
            source.write_bytes(b'changed live')
            self.assertEqual(art.snapshot(mod, build), saved)
            with self.assertRaises(ValueError):
                art.snapshot(root/'other', build)
            (build/'baseline'/art.REL).write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                art.snapshot(mod, build)

    def test_partial_install_always_refused(self):
        with mock.patch.object(art.b, 'install') as install:
            for report in ({'passed':False}, {'passed':True,'partial':True}):
                with self.assertRaises(ValueError):
                    art.install(Path('unused'), {}, {}, report)
            install.assert_not_called()

    def test_repeat_install_no_writes(self):
        with TemporaryDirectory() as tmp:
            mod = Path(tmp)
            file = mod/art.REL
            file.parent.mkdir(parents=True)
            file.write_bytes(b'finished')
            with mock.patch.object(art.b, 'install') as install:
                result = art.install(mod, {art.REL:'original'}, {art.REL:'finished'}, {'passed':True,'partial':False})
                self.assertTrue(result['already_installed'])
                install.assert_not_called()

    def test_installer_restores_shared_globals_on_failure(self):
        with TemporaryDirectory() as tmp:
            original = art.b.BUILD, art.b.VERSION
            with mock.patch.object(art.b, 'install', side_effect=ValueError('guard')):
                with self.assertRaises(ValueError):
                    art.install(Path(tmp), {art.REL:'old'}, {art.REL:'new'}, {'passed':True}, Path(tmp)/'build')
            self.assertEqual((art.b.BUILD, art.b.VERSION), original)

    def fixture(self, root, include_source=True):
        mod, build, assets = root/'Mods/test', root/'build', root/'assets/roster-art2'
        csv = mod/art.REL
        csv.parent.mkdir(parents=True)
        second = ROW.replace('252000', '252001').replace('Officer (R)', 'Second (R)')
        historical = ROW.replace('252000', '250001').replace('Officer (R)', 'Historical')
        csv.write_bytes((HEADER+ROW+second+historical).encode('latin1'))
        old = mod/'gfx/interface/pics/old_face.bmp'
        old.parent.mkdir(parents=True)
        Image.new('RGB', (36,50), '#808080').save(old)
        assets.mkdir(parents=True)
        entries = [dict(id=252000,name='Officer (R)',existing_picture='old_face',keep=True),
                   dict(id=252001,name='Second (R)',existing_picture='old_face',keep=False,prompt='fictional')]
        (assets/'plan.json').write_text(json.dumps({'entries':entries}), encoding='utf8')
        reserves = assets/'reserves'
        reserves.mkdir()
        if include_source:
            Image.new('RGB', (100,200), '#336699').save(reserves/'252001.png')
            (reserves/'252001.json').write_text(json.dumps({'id':252001,'mode':'built-in image_gen','prompt':'fictional'}), encoding='utf8')
        historical_source = assets/'historical.png'
        Image.new('RGB', (100,200), '#997733').save(historical_source)
        hist = root/'historical.json'
        hist.write_text(json.dumps({'entries':[dict(id=250001,name='Historical',identity_verified=True,
             source='assets/roster-art2/historical.png')]}), encoding='utf8')
        return mod, build, assets, hist

    def test_complete_stage_end_to_end(self):
        with TemporaryDirectory() as tmp, mock.patch.object(art,'RESERVE_IDS',{252000,252001}), \
                mock.patch.object(art,'KEEP_COUNT',1), mock.patch.object(art,'HISTORICAL_IDS',{250001}):
            root = Path(tmp)
            mod, build, assets, hist = self.fixture(root)
            live_before = (mod/art.REL).read_bytes()
            with mock.patch.object(art,'ROOT',root):
                base, out, report = art.stage(mod,build,assets,hist)
            self.assertTrue(report['passed'])
            self.assertEqual(report['unique_pixel_hashes'],3)
            self.assertEqual(report['reserves_generated'],1)
            self.assertEqual((mod/art.REL).read_bytes(),live_before)
            self.assertEqual(set(out)-set(base), {'gfx/interface/pics/AUBM_R2_252001.bmp',
                                                'gfx/interface/pics/AUBM_R2_H250001.bmp'})

    def test_incomplete_stage_cannot_install(self):
        with TemporaryDirectory() as tmp, mock.patch.object(art,'RESERVE_IDS',{252000,252001}), \
                mock.patch.object(art,'KEEP_COUNT',1), mock.patch.object(art,'HISTORICAL_IDS',{250001}):
            root = Path(tmp)
            mod, build, assets, hist = self.fixture(root,include_source=False)
            with mock.patch.object(art,'ROOT',root):
                base, out, report = art.stage(mod,build,assets,hist)
            self.assertFalse(report['passed'])
            self.assertIn('Reserve 252001',report['pending'])
            with self.assertRaises(ValueError):
                art.install(mod,base,out,report,build)

    def test_duplicate_pixels_rejected_after_completion(self):
        with TemporaryDirectory() as tmp, mock.patch.object(art,'RESERVE_IDS',{252000,252001}), \
                mock.patch.object(art,'KEEP_COUNT',1), mock.patch.object(art,'HISTORICAL_IDS',{250001}):
            root = Path(tmp)
            mod, build, assets, hist = self.fixture(root)
            Image.new('RGB',(100,200),'#808080').save(assets/'reserves/252001.png')
            with mock.patch.object(art,'ROOT',root):
                _, _, report = art.stage(mod,build,assets,hist)
            self.assertFalse(report['passed'])
            self.assertIn('Exact duplicate portrait pixels remain',report['errors'])

    def test_generation_provenance_required(self):
        valid = {'id':252000, 'mode':'built-in image_gen', 'prompt':'fictional portrait'}
        art.validate_generation_metadata(valid,252000)
        for change in ({'id':252001},{'mode':'API'},{'prompt':''},{'prompt':None}):
            with self.assertRaises(ValueError):
                art.validate_generation_metadata(dict(valid,**change),252000)

    def test_public_package_removes_private_binary_and_reference(self):
        old = HEADER+ROW
        base = {art.REL:old}
        out = {art.REL:art.change_pictures(old,{252000:'AUBM_R2_H252000'}),
               'gfx/interface/pics/AUBM_R2_H252000.bmp':'private binary'}
        report = {'provenance':[{'id':252000,'picture':'AUBM_R2_H252000',
                                'metadata':{'redistributable':False}}]}
        self.assertEqual(art.public_output(base,out,report),base)

    def test_historical_id_substitution_refused(self):
        with TemporaryDirectory() as tmp, mock.patch.object(art,'RESERVE_IDS',{252000,252001}), \
                mock.patch.object(art,'KEEP_COUNT',1), mock.patch.object(art,'HISTORICAL_IDS',{999999}):
            root = Path(tmp)
            mod,build,assets,hist = self.fixture(root)
            with mock.patch.object(art,'ROOT',root), self.assertRaises(ValueError):
                art.stage(mod,build,assets,hist)


if __name__ == '__main__':
    main()

"""Fast synthetic checks for the local prototype's encoding and raster inputs."""
import unittest
from pathlib import Path

import numpy as np

import aubm_hybrid_terrain as hybrid
import aubm_hybrid_world as world
from aubm_lightmap import ParsedBlock, encode_block, parse_block, raster_block


class HybridTests(unittest.TestCase):
    def roundtrip(self, owners, colors):
        block = ParsedBlock((1, 0x8002), hybrid.tree_from_arrays(owners, colors), (), (), (), 0)
        decoded = parse_block(encode_block(block, preserve_padding=False))
        oo, cc = raster_block(decoded)
        self.assertEqual(decoded.province_words, block.province_words)
        np.testing.assert_array_equal(np.asarray(oo).reshape(32, 32), owners)
        np.testing.assert_array_equal(np.asarray(cc).reshape(32, 32), colors)

    def test_uniform_block(self):
        self.roundtrip(np.zeros((32, 32), int), np.full((32, 32), 19, np.uint8))

    def test_mixed_owners_and_full_shades(self):
        rng = np.random.default_rng(828)
        self.roundtrip(rng.integers(0, 2, (32, 32)), rng.integers(0, 64, (32, 32), dtype=np.uint8))

    def test_art_is_repeatable_and_within_native_shade_range(self):
        for terrain in hybrid.NEW:
            for level in range(1, 5):
                first = hybrid.atlas_field(terrain, level, (123, 456, 150, 90))
                second = hybrid.atlas_field(terrain, level, (123, 456, 150, 90))
                np.testing.assert_array_equal(first, second)
                self.assertGreaterEqual(int(first.min()), 0)
                self.assertLessEqual(int(first.max()), 63)
                self.assertGreater(len(np.unique(first)), 12)

    def test_crop_phase_does_not_change_art(self):
        for terrain in hybrid.NEW:
            a = hybrid.atlas_field(terrain, 2, (100, 200, 160, 120))
            b = hybrid.atlas_field(terrain, 2, (130, 220, 80, 60))
            np.testing.assert_array_equal(a[20:80, 30:110], b)

    def test_compiler_rejects_live_destination(self):
        with self.assertRaises(ValueError):
            hybrid.compile_region(Path("not-read"), hybrid.LIVE)

    def test_world_compiler_rejects_installations(self):
        for target in (hybrid.LIVE, hybrid.DONOR, hybrid.REPO / "mod", hybrid.CORE):
            with self.assertRaises(ValueError):
                world.safe_output(target)

    def test_world_tiles_cover_every_block_exactly_once(self):
        for level, (width, height) in world.SPECS.items():
            visited = np.zeros((height, width), np.uint8)
            for _, x, y, w, h in world.jobs_for(level, 16):
                self.assertEqual(x % 32 + y % 32 + w % 32 + h % 32, 0)
                visited[y // 32:(y + h) // 32, x // 32:(x + w) // 32] += 1
            self.assertTrue(np.all(visited == 1))

    def test_world_halo_prevents_art_or_label_seams(self):
        rng = np.random.default_rng(42)
        core = rng.integers(15, 55, (192, 256), dtype=np.uint8)
        donor = rng.integers(10, 44, core.shape, dtype=np.uint8)
        terrain = rng.integers(-1, 8, core.shape, dtype=np.int8)
        full, protected = hybrid.compose(2, (0, 0, 256, 192), core, donor, terrain)
        # A tile with the production halo must reproduce an unbroken raster.
        sub = np.s_[32:160, 32:224]
        tile, _ = hybrid.compose(2, (32, 32, 192, 128), core[sub], donor[sub], terrain[sub])
        np.testing.assert_array_equal(tile[32:-32, 32:-32], full[64:128, 64:192])
        np.testing.assert_array_equal(full[protected], core[protected])

    def test_world_fast_fields_match_pilot(self):
        world.initialize()
        try:
            for level in range(1, 5):
                scale = 2 ** (level - 1)
                rect = (22000 // scale, 4200 // scale, 48, 40)
                for actual, expected in zip(world.fields(level, rect), hybrid.fields(level, rect)):
                    np.testing.assert_array_equal(actual, expected)
        finally:
            world.close_maps()

    def test_donor_font_removed_but_separate_forest_symbols_survive(self):
        core = np.full((80, 160), 19, np.uint8)
        donor = core.copy()
        terrain = np.full(core.shape, hybrid.TERRAINS.index("Forest"), np.int8)
        core[20:34, 25:28] = 60
        donor[21:35, 23:26] = 60  # offset imported glyph
        donor[45:60, 115:122] = 60  # separate dark tree silhouette
        cleaned = hybrid.strip_donor_ink(donor, core, terrain, 1)
        self.assertTrue(np.all(cleaned[21:35, 23:26] == 19))
        np.testing.assert_array_equal(cleaned[45:60, 115:122], donor[45:60, 115:122])
        final, protected = hybrid.compose(1, (0, 0, 160, 80), core, cleaned, terrain)
        np.testing.assert_array_equal(final[protected], core[protected])

    def test_lettering_cleanup_has_no_tile_seam_with_world_halo(self):
        rng = np.random.default_rng(17)
        core = rng.integers(10, 64, (320, 384), dtype=np.uint8)
        donor = rng.integers(10, 64, core.shape, dtype=np.uint8)
        terrain = rng.integers(1, 4, core.shape, dtype=np.int8)
        full = hybrid.strip_donor_ink(donor, core, terrain, 1)
        sub = np.s_[32:288, 32:352]
        tile = hybrid.strip_donor_ink(donor[sub], core[sub], terrain[sub], 1)
        halo = world.HALO
        np.testing.assert_array_equal(tile[halo:-halo, halo:-halo],
                                      full[32 + halo:288 - halo, 32 + halo:352 - halo])


if __name__ == "__main__":
    unittest.main()

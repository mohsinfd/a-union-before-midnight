import unittest
from pathlib import Path

from install_aubm_pale_jade import FORMER_USERS, country_bytes, palette_bytes


ROOT = Path(__file__).resolve().parents[1]


class PaleJadeTests(unittest.TestCase):
    def test_palette_has_dark_pale_jade_ramp(self):
        source = (ROOT / "mod/map/Map_1/colorscales.csv").read_bytes()
        result = palette_bytes(source).decode("cp1252")
        self.assertIn("169;205;182;0", result)
        self.assertIn("144;179;157;20", result)
        self.assertIn("116;150;130;40", result)

    def test_india_exclusively_owns_slot(self):
        source = (ROOT / "mod/db/country.csv").read_bytes()
        result = country_bytes(source).decode("cp1252")
        self.assertIn("IND;UserColor2;", result)
        self.assertEqual(1, result.count(";UserColor2;"))
        for tag in FORMER_USERS:
            self.assertIn(f"{tag};LightBlue;", result)


if __name__ == "__main__":
    unittest.main()

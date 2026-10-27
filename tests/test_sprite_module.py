#!/usr/bin/env python3
"""Review gates for the sprite 95 module recipe."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_sprite_module as sprite


@unittest.skipUnless((Path("/home/harp/projects/sfc/brutalmario-recomp/local/content-versions/7hero/rom.sfc")).exists()
                     and (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").exists(),
                     "requires pinned local donor and recipient assets")
class SpriteModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = sprite.read_recipe()
        cls.donor = sprite.prepare_donor(ROOT / cls.recipe["donor_manifest"])
        cls.base = (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").read_bytes()

    def test_review_pins(self):
        code, audit = sprite.build_code(self.donor, self.base, self.recipe)
        self.assertEqual(len(code), 5144)
        self.assertEqual(audit["local_entry_states"], 52)
        self.assertEqual(audit["instruction_variants"], 2086)
        self.assertEqual(len(audit["reviewed_dispatch_tables"]), 1)
        self.assertEqual(audit["reviewed_dispatch_tables"][0]["count"], 17)
        self.assertEqual(audit["source_bank_jsl_sites"], [])
        self.assertEqual(audit["outside_calls"], self.recipe["external_calls"])

    def test_record_and_native_adaptation(self):
        record = sprite.check_record(self.donor, self.recipe)
        self.assertEqual(record["raw"], "013600003f0399641ae42039e5200000")
        self.assertEqual(record["native_raw"], "013600003f0399641ae4a339e5a30000")
        self.assertEqual(record["rooms"], ["16B", "16C", "16D", "16E", "16F", "172", "1CC"])

    def test_dispatch_table_change_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe["dispatch_tables"][0]["sha256"] = "00"*32
        with self.assertRaisesRegex(ValueError, "dispatch table"):
            sprite.build_code(self.donor, self.base, recipe)

    def test_outside_call_change_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe["external_calls"] = recipe["external_calls"][:-1]
        with self.assertRaisesRegex(ValueError, "outside call set"):
            sprite.build_code(self.donor, self.base, recipe)

    def test_record_mismatch_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe["record"]["raw"] = "00"*16
        with self.assertRaisesRegex(ValueError, "record differs from the review"):
            sprite.check_record(self.donor, recipe)


if __name__ == "__main__":
    unittest.main()

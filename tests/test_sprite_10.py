#!/usr/bin/env python3
"""Review gates for the sprite 10 gap recipe and target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_sprite_module as sprite
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/content-versions/cheap-demo/rom.sfc").exists()
                     and (ROOT / "local/restoration/demo11-native-sprite10/rom.sfc").exists(),
                     "requires the pinned cheap-demo donor and the built target")
class Sprite10ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = sprite.read_recipe(ROOT / "config/native-content/sprite10-module.json")
        cls.donor = sprite.prepare_donor(ROOT / "config/cheap-demo-donor.json")
        cls.base = (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").read_bytes()
        cls.target = (ROOT / "local/restoration/demo11-native-sprite10/rom.sfc").read_bytes()

    def test_review_pins(self):
        code, audit = sprite.build_code(self.donor, self.base, self.recipe)
        self.assertEqual(len(code), 2589)
        self.assertEqual(audit["local_entry_states"], 21)
        self.assertEqual(audit["instruction_variants"], 963)
        self.assertEqual(audit["reviewed_dispatch_tables"], [])
        self.assertEqual(audit["outside_calls"], self.recipe["external_calls"])

    def test_record_and_native_adaptation(self):
        record = sprite.check_record(self.donor, self.recipe)
        self.assertEqual(record["raw"], "01360080398391002ea61ad1a61a0000")
        self.assertEqual(record["native_raw"], "01360080398391002ea6a4d1a6a40000")
        self.assertEqual(record["rooms"], ["12D", "156", "157", "15B", "15C"])

    def test_only_the_bank_byte_changes(self):
        donor = self.recipe["record"]["raw"]
        native = self.recipe["record"]["native_raw"]
        self.assertEqual(len(donor), len(native))
        self.assertEqual(donor[:16], native[:16])
        self.assertEqual(donor[28:], native[28:])
        self.assertEqual(donor[16:22], "2ea61a")
        self.assertEqual(native[16:22], "2ea6a4")

    def test_target_carries_the_record(self):
        cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite10.json").read_text())
        verify(self.target, cfg["output"], "sprite 10 target ROM")
        patch = self.recipe["unapplied_rom_patches"][0]
        record = bytes.fromhex(self.recipe["record"]["native_raw"])
        offset = patch["offset"]
        self.assertEqual(offset, 1606514)
        self.assertEqual(self.target[offset:offset+len(record)], record)


if __name__ == "__main__":
    unittest.main()
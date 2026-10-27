#!/usr/bin/env python3
"""Review gates for the combined sprite 10 to 14 gap target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_sprite_gap as gap
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/restoration/demo11-native-sprite10-14/rom.sfc").exists(),
                     "requires the built combined target")
class CombinedGapTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite10-14.json").read_text())
        cls.pairs = gap.settings("demo11-native-sprite10-14")[1]
        cls.rom = (ROOT / "local/restoration/demo11-native-sprite10-14/rom.sfc").read_bytes()

    def test_five_recipes_are_admitted(self):
        self.assertEqual(len(self.pairs), 5)
        self.assertEqual([recipe["record"]["slot"] for _, recipe in self.pairs],
                         ["10", "11", "12", "13", "14"])
        self.assertEqual(self.cfg["native_sprite_gap"]["manifests"],
                         [path for path, _ in self.pairs])

    def test_pack_layout_holds_seven_packs(self):
        packs = gap.packs("demo11-native-sprite10-14")
        self.assertEqual([pack["variable"] for pack in packs],
                         ["BM_SEVEN_CODE_PACK", "BM_SEVEN_CODE_PACK_2",
                          "BM_SEVEN_CODE_PACK_3", "BM_SEVEN_CODE_PACK_4",
                          "BM_SEVEN_CODE_PACK_5", "BM_NATIVE_SPRITE_PACK",
                          "BM_NATIVE_GRAPHICS_PACK"])
        self.assertEqual([int(pack["address"], 16) >> 16 for pack in packs],
                         [0xA4, 0xAA, 0xAB, 0xAC, 0xAD, 0xA5, 0xB6])

    def test_module_directories_are_distinct(self):
        names = [path.name for path in gap.module_dirs("demo11-native-sprite10-14")]
        self.assertEqual(len(names), 5)
        self.assertEqual(len(set(names)), 5)

    def test_target_carries_every_record(self):
        verify(self.rom, self.cfg["output"], "combined gap target ROM")
        for _, recipe in self.pairs:
            record = bytes.fromhex(recipe["record"]["native_raw"])
            offset = recipe["unapplied_rom_patches"][0]["offset"]
            self.assertEqual(self.rom[offset:offset+len(record)], record)

    def test_recipes_keep_low_bits(self):
        for _, recipe in self.pairs:
            donor = recipe["record"]["raw"]
            native = recipe["record"]["native_raw"]
            self.assertEqual(len(donor), len(native))
            self.assertEqual(donor[:16], native[:16])
            self.assertEqual(donor[28:], native[28:])
            self.assertEqual(int(recipe["code"]["native_address"], 16) & 0xffff,
                             int(recipe["code"]["source_address"], 16) & 0xffff)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite1014-final.json").exists(),
                         "requires the combined qualification report")
    def test_qualification_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite1014-final.json").read_text())
        self.assertEqual(len(report["records"]), 5)
        self.assertEqual(sorted(report["exact_rooms"]), ["12D", "158", "15C"])
        self.assertEqual(report["rooms"]["12D"]["exact"], 3)
        self.assertEqual(report["rooms"]["15C"]["exact"], 3)
        self.assertGreaterEqual(len(report["module_views"]), 5)


if __name__ == "__main__":
    unittest.main()

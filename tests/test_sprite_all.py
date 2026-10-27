#!/usr/bin/env python3
"""Review gates for the eleven-record gap target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_sprite_gap as gap
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/restoration/demo11-native-sprite-all/rom.sfc").exists(),
                     "requires the built eleven-record target")
class AllGapTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite-all.json").read_text())
        cls.pairs = gap.settings("demo11-native-sprite-all")[1]
        cls.rom = (ROOT / "local/restoration/demo11-native-sprite-all/rom.sfc").read_bytes()

    def test_eleven_recipes_are_admitted(self):
        self.assertEqual(len(self.pairs), 11)
        slots = [recipe["record"]["slot"] for _, recipe in self.pairs]
        self.assertEqual(slots, ["10", "11", "12", "13", "14",
                                 "0F", "19", "22", "3B", "55", "92"])

    def test_pack_layout_holds_thirteen_packs(self):
        packs = gap.packs("demo11-native-sprite-all")
        self.assertEqual(len(packs), 13)
        self.assertEqual(packs[0]["variable"], "BM_SEVEN_CODE_PACK")
        self.assertEqual(packs[10]["variable"], "BM_SEVEN_CODE_PACK_11")
        self.assertEqual(packs[-1]["variable"], "BM_NATIVE_GRAPHICS_PACK")
        banks = [int(pack["address"], 16) >> 16 for pack in packs]
        self.assertEqual(len(set(banks)), 13)
        self.assertEqual(banks[0], 0xA4)
        self.assertEqual(banks[-1], 0xB6)

    def test_every_record_is_installed(self):
        verify(self.rom, self.cfg["output"], "eleven-record target ROM")
        for _, recipe in self.pairs:
            record = bytes.fromhex(recipe["record"]["native_raw"])
            offset = recipe["unapplied_rom_patches"][0]["offset"]
            self.assertEqual(self.rom[offset:offset+len(record)], record)

    def test_every_recipe_keeps_low_bits(self):
        for _, recipe in self.pairs:
            self.assertEqual(int(recipe["code"]["native_address"], 16) & 0xffff,
                             int(recipe["code"]["source_address"], 16) & 0xffff)
            self.assertEqual(recipe["dispatch_tables"], [])
            self.assertEqual(recipe["code_patches"], [])

    @unittest.skipUnless((ROOT / "local/reports/native-sprite-all-final.json").exists(),
                         "requires the eleven-record qualification report")
    def test_qualification_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite-all-final.json").read_text())
        self.assertEqual(len(report["records"]), 11)
        self.assertEqual(sorted(report["exact_rooms"]),
                         ["12D", "155", "158", "15C"])
        self.assertEqual(report["rooms"]["155"]["exact"], 4)
        self.assertGreaterEqual(len(report["module_views"]), 13)


    @unittest.skipUnless((ROOT / "local/reports/native-sprite-all-final.json").exists(),
                         "requires the eleven-record qualification report")
    def test_phase_offsets_are_measured(self):
        report = json.loads((ROOT / "local/reports/native-sprite-all-final.json").read_text())
        phase = report["phase"]
        self.assertEqual(sorted(phase), ["156", "157", "159", "15B"])
        for room in ("156", "159", "15B"):
            self.assertTrue(phase[room]["phase_exact"], room)
            self.assertLess(phase[room]["offset"], 0, room)
            self.assertEqual(phase[room]["steady_frames"], 20, room)
        self.assertEqual(phase["157"]["steady_mismatches"], 1)
        self.assertEqual(phase["157"]["mismatch_frames"], [302])


if __name__ == "__main__":
    unittest.main()
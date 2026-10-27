#!/usr/bin/env python3
"""Review gates for the merged product target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_sprite_gap as gap
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/restoration/demo11-native-product/rom.sfc").exists(),
                     "requires the built product target")
class ProductTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / "config/restorations/demo11-native-product.json").read_text())
        cls.pairs = gap.settings("demo11-native-product")[1]
        cls.rom = (ROOT / "local/restoration/demo11-native-product/rom.sfc").read_bytes()

    def test_thirty_five_records_are_admitted(self):
        self.assertEqual(len(self.pairs), 36)
        slots = [recipe["record"]["slot"] for _, recipe in self.pairs]
        self.assertNotIn("2A", slots)

    def test_pack_layout_holds_forty_two_packs(self):
        packs = gap.packs("demo11-native-product")
        self.assertEqual(len(packs), 43)
        banks = sorted(int(pack["address"], 16) >> 16 for pack in packs)
        self.assertEqual(len(set(banks)), 43)
        self.assertIn(0xA2, banks)
        self.assertIn(0xA6, banks)
        self.assertIn(0xA5, banks)
        self.assertIn(0xB6, banks)
        for bank in (0xCB, 0xCC, 0xCD, 0xA0):
            self.assertIn(bank, banks)

    def test_slot_80_record_is_installed(self):
        record = bytes.fromhex("012800003f039944e9a8a000aaa00000")
        offset = 1608306
        self.assertEqual(self.rom[offset:offset+len(record)], record)

    def test_target_rom_identity(self):
        verify(self.rom, self.cfg["output"], "product target ROM")

    def test_seven_record_holds_slot_2a(self):
        record = bytes.fromhex("0136000035a299440f80a28d80a20000")
        offset = 1606930
        self.assertEqual(self.rom[offset:offset+len(record)], record)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite-full-regression-product.json").exists(),
                         "requires the product regression report")
    def test_unchanged_routes_match_the_baseline(self):
        report = json.loads((ROOT / "local/reports/native-sprite-full-regression-product.json").read_text())
        self.assertEqual(report["gap"], "demo11-native-product")
        self.assertEqual(report["equal"], report["total"])
        self.assertGreaterEqual(report["total"], 30)


    def test_launcher_lists_every_pack(self):
        import subprocess
        result = subprocess.run([sys.executable, "tools/play_native_target.py",
                                 "--print-env"], cwd=ROOT, capture_output=True,
                                text=True, check=True)
        variables = [line.split("=")[0] for line in result.stdout.splitlines()
                     if line.startswith("BM_")]
        self.assertEqual(len(variables), 43)
        self.assertEqual(len(set(variables)), 43)

if __name__ == "__main__":
    unittest.main()
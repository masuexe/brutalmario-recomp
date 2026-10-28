#!/usr/bin/env python3
"""Review gates for the all-levels completion cheat."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = ROOT / "recomp/inputs/cheat-complete-all.script"
DOC = ROOT / "docs/completion-cheat-product.md"


class CompletionCheatTests(unittest.TestCase):
    def test_script_writes_the_pinned_fields(self):
        text = SCRIPT.read_text()
        self.assertIn("poke 1ea2 " + "9f" * 0x60, text)
        self.assertIn("poke 1f02 " + "ff" * 0x0f, text)
        self.assertIn("poke 1f27 01010101", text)
        self.assertIn("poke 1f2e 60", text)
        self.assertIn("poke 1f2f " + "ff" * 12, text)
        self.assertIn("poke 1182c " + "00" * 24, text)

    def test_script_waits_for_the_map_and_reloads(self):
        text = SCRIPT.read_text()
        self.assertLess(text.index("until 0100 == 0e"), text.index("poke 1ea2"))
        self.assertIn("poke 0100 0b", text)
        self.assertNotIn("quit", text)

    def test_launcher_offers_the_cheat(self):
        text = (ROOT / "tools/play_native_target.py").read_text()
        self.assertIn("--complete-all", text)
        self.assertIn("cheat-complete-all.script", text)
        self.assertIn("save.srm.before-cheat", text)

    def test_document_records_the_measured_result(self):
        doc = DOC.read_text()
        self.assertIn("23964 pixels", doc)
        self.assertIn("cheat-verify2", doc)
        self.assertIn("mode `$14`", doc)


    def test_special_zone_script_uses_the_lower_inner_warp(self):
        text = (ROOT / "recomp/inputs/cheat-special-zone.script").read_text()
        self.assertIn("poke 1f17 7801c8017801c801", text)
        self.assertIn("until 1f11 == 03 900", text)
        self.assertNotIn("quit", text)

    def test_launcher_offers_special_zone(self):
        text = (ROOT / "tools/play_native_target.py").read_text()
        self.assertIn("--special-zone", text)
        self.assertIn("cheat-special-zone.script", text)

    def test_document_explains_center_versus_warp(self):
        doc = DOC.read_text()
        self.assertIn("## Warp into the Special Zone", doc)
        self.assertIn("$0178/$01A8", doc)
        self.assertIn("$0178/$01C8", doc)
        self.assertIn("--special-zone", doc)

if __name__ == "__main__":
    unittest.main()
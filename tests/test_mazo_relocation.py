#!/usr/bin/env python3
"""Review gates for the mazo 9B/9C relocation finding."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))


class MazoRelocationTests(unittest.TestCase):
    def test_product_mounts_9b_and_9c_off_the_source_bank(self):
        cfg = json.loads((ROOT / "config/restorations/demo11-native-product.json").read_text())
        recipes = {}
        for manifest in cfg["native_sprite_gap"]["manifests"]:
            recipe = json.loads((ROOT / manifest).read_text())
            slot = recipe.get("record", {}).get("slot")
            if slot in ("9B", "9C"):
                recipes[slot] = recipe
        self.assertEqual(set(recipes), {"9B", "9C"})
        self.assertEqual(recipes["9B"]["code"]["native_address"], "C8EFAE")
        self.assertEqual(recipes["9C"]["code"]["native_address"], "C98000")
        # The mount bank does not match the source bank of either module.
        for slot, recipe in recipes.items():
            source = int(recipe["code"]["source_address"], 16) >> 16
            native = int(recipe["code"]["native_address"], 16) >> 16
            self.assertNotEqual(source & 0x7F, native & 0x7F, slot)

    def test_relocation_document_records_the_evidence(self):
        doc = (ROOT / "docs/native-mazo-9bc-relocation.md").read_text()
        for token in ("1,227,003", "422,392", "218", "does not claim the cause"):
            self.assertIn(token, doc)

    def test_a2_probe_config_is_pinned(self):
        cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite9c-a2-probe.json").read_text())
        manifest = cfg["native_sprite_gap"]["manifests"][0]
        recipe = json.loads((ROOT / manifest).read_text())
        self.assertEqual(recipe["code"]["native_address"], "A28000")


if __name__ == "__main__":
    unittest.main()

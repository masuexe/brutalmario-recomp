#!/usr/bin/env python3
"""Review gates for the product descendant that carries the 1E6 stream."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

PRODUCT = ROOT / "config/restorations/demo11-native-product.json"
R2 = ROOT / "config/restorations/demo11-native-product-r2.json"
R2_ROM = ROOT / "local/restoration/demo11-native-product-r2/rom.sfc"

STREAM = "mazo extended gfx 1E6 stream"
POINTER = "extended gfx 1E6 pointer"


class DescendantConfigTests(unittest.TestCase):
    """The descendant must stay the product plus the two 1E6 patches."""

    @classmethod
    def setUpClass(cls):
        cls.product = json.loads(PRODUCT.read_text())
        cls.r2 = json.loads(R2.read_text())

    def test_identity(self):
        self.assertEqual(self.r2["id"], "demo11-native-product-r2")
        self.assertEqual(self.r2["base_restoration"], self.product["base_restoration"])

    def test_only_the_two_patches_differ(self):
        base = [p["role"] for p in self.product["native_sprite_gap"]["extra_patches"]]
        extra = [p["role"] for p in self.r2["native_sprite_gap"]["extra_patches"]]
        self.assertEqual(extra[:len(base)], base)
        self.assertEqual(extra[len(base):], [STREAM, POINTER])

    def test_output_digest_differs_from_the_product(self):
        self.assertNotEqual(self.r2["output"]["sha256"], self.product["output"]["sha256"])

    def test_patch_shape(self):
        added = {p["role"]: p for p in self.r2["native_sprite_gap"]["extra_patches"]
                 if p["role"] in (STREAM, POINTER)}
        self.assertEqual(len(added[STREAM]["after"]) // 2, 2506)
        self.assertEqual(added[STREAM]["offset"], 0x1B0008)


@unittest.skipUnless(R2_ROM.is_file(), "requires the built r2 target")
class DescendantRomTests(unittest.TestCase):
    """The built ROM must match its declared digest and hold the stream."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(R2.read_text())
        cls.rom = R2_ROM.read_bytes()

    def test_digest_matches_the_receipt(self):
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(), self.cfg["output"]["sha256"])

    def test_stream_is_present(self):
        window = self.rom[0x1B0008:0x1B0008 + 2506]
        self.assertGreater(sum(1 for b in window if b), 2000)

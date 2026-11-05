#!/usr/bin/env python3
"""Review gates for the external sprite graphics provider."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_sprite_graphics as graphics
import patch_sprite_graphics
import prepare_sprite_graphics_pack

TARGET = 'demo11-native-product-r21'
MANIFEST = ROOT / 'config/native-content/sprite-graphics-175-obj.json'


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(MANIFEST.read_text())

    def test_manifest_pins_the_payload(self):
        self.assertEqual(self.spec['schema'], 1)
        self.assertEqual(self.spec['slot'], '175')
        self.assertEqual(self.spec['rooms'], ['175'])
        self.assertEqual(self.spec['ranges'], [{'vram': '6000', 'words': 8192}])
        self.assertEqual(self.spec['size'], 4 + 4 + 8192 * 2)
        self.assertTrue(self.spec['persist'])

    def test_pack_matches_its_pin(self):
        import hashlib
        directory = ROOT / self.spec['source_directory']
        data = (directory / self.spec['pack_file']).read_bytes()
        self.assertEqual(len(data), self.spec['size'])
        self.assertEqual(hashlib.sha256(data).hexdigest(), self.spec['sha256'])
        count = struct.unpack_from('<I', data, 0)[0]
        self.assertEqual(count, 1)
        address, words = struct.unpack_from('<HH', data, 4)
        self.assertEqual((address, words), (0x6000, 8192))

    def test_pack_bytes_equal_the_reviewed_vram(self):
        directory = ROOT / self.spec['source_directory']
        data = (directory / self.spec['pack_file']).read_bytes()
        capture = ROOT / 'local/captures' / self.spec['source']['capture']
        vram = (capture / (self.spec['source']['frame'] + '.vram.bin')).read_bytes()
        self.assertEqual(data[8:], vram[0x6000 * 2:(0x6000 + 8192) * 2])


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(MANIFEST.read_text())

    def check(self, **changes):
        spec = dict(self.spec, **changes)
        return graphics.reviewed(spec)

    def test_review_accepts_the_manifest(self):
        row = graphics.reviewed(self.spec)
        self.assertEqual(row['rooms'], [0x175])
        self.assertEqual(row['ranges'], [[0x6000, 0x6000 + 8192]])
        self.assertTrue(row['persist'])
        bitmap = bytes.fromhex(row['bitmap'])
        self.assertEqual(bitmap[0x175 >> 3], 1 << (0x175 & 7))

    def test_size_must_match_the_ranges(self):
        with self.assertRaises(ValueError):
            self.check(size=self.spec['size'] + 2)

    def test_range_must_stay_inside_vram(self):
        with self.assertRaises(ValueError):
            self.check(ranges=[{'vram': '7FFF', 'words': 4}], size=4 + 4 + 8)

    def test_ranges_must_not_overlap(self):
        with self.assertRaises(ValueError):
            self.check(ranges=[{'vram': '3000', 'words': 4096},
                               {'vram': '3100', 'words': 16}],
                       size=4 + 8 + 4096 * 2 + 32)

    def test_empty_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check(rooms=[])

    def test_room_must_be_a_room_id(self):
        with self.assertRaises(ValueError):
            self.check(rooms=['2000'])


class HeaderTests(unittest.TestCase):
    def test_header_names_the_variable(self):
        text = graphics.header(TARGET)
        self.assertIn('BM_SPRITE_GRAPHICS_PACKS 1u', text)
        self.assertIn('"BM_SPRITE_GRAPHICS_PACK",16392u,1u', text)
        expected = ','.join(str(n) for n in bytes.fromhex(self.spec_digest()))
        self.assertIn('{' + expected + '}', text)

    def spec_digest(self):
        spec = json.loads(MANIFEST.read_text())
        return spec['sha256']

    def test_target_without_graphics_has_no_header(self):
        self.assertEqual(graphics.header('demo11-native-product-r20'), '')
        self.assertEqual(graphics.packs('demo11-native-product-r20'), [])


class PatchTests(unittest.TestCase):
    def test_patch_is_idempotent(self):
        text = ('#include "native_content.h"' + chr(10) +
                '  bm_content_load(cart->rom, cart->romSize);' + chr(10) +
                '  if (bank == 0x7e || bank == 0x7f) return NULL;' + chr(10))
        once, changed = patch_sprite_graphics.patch(text)
        self.assertTrue(changed)
        self.assertIn('bm_sprite_graphics_mount();', once)
        self.assertIn('bm_sprite_graphics_tick();', once)
        twice, changed_again = patch_sprite_graphics.patch(once)
        self.assertFalse(changed_again)
        self.assertEqual(twice, once)

    def test_patch_rejects_a_foreign_cartridge(self):
        with self.assertRaises(ValueError):
            patch_sprite_graphics.patch('#include "cart.h"' + chr(10))


class PackBuildTests(unittest.TestCase):
    def test_build_pack_layout(self):
        vram = bytes(range(256)) * 256
        pack = prepare_sprite_graphics_pack.build_pack(vram, [(0x10, 4)])
        self.assertEqual(struct.unpack_from('<I', pack, 0)[0], 1)
        self.assertEqual(struct.unpack_from('<HH', pack, 4), (0x10, 4))
        self.assertEqual(pack[8:], vram[0x20:0x28])

    def test_build_pack_rejects_a_bad_range(self):
        vram = bytes(0x10000)
        with self.assertRaises(ValueError):
            prepare_sprite_graphics_pack.build_pack(vram, [(0x7FFF, 4)])
        with self.assertRaises(ValueError):
            prepare_sprite_graphics_pack.build_pack(vram[:0x8000], [(0, 4)])


@unittest.skipUnless((ROOT / 'config/restorations' / (TARGET + '.json')).exists(),
                     'requires the prepared r21 target')
class TargetTests(unittest.TestCase):
    def test_target_inherits_the_parent_image(self):
        config = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
        parent = json.loads((ROOT / 'config/restorations/demo11-native-product-r20.json').read_text())
        self.assertEqual(config['base_restoration'], 'demo11-native-product-r20')
        self.assertEqual(config['output'], parent['output'])
        self.assertEqual(config['native_sprite_graphics'],
                         ['config/native-content/sprite-graphics-175-obj.json'])
        self.assertEqual(config['native_sprite_gap']['frozen_manifests'],
                         config['native_sprite_gap']['manifests'])

    def test_pack_range_stays_in_vram(self):
        rows = graphics.packs(TARGET)
        self.assertEqual(len(rows), 1)
        start, end = rows[0]['ranges'][0]
        self.assertLessEqual(end, 0x8000)
        self.assertEqual(rows[0]['persist'], True)


R22_TARGET = "demo11-native-product-r22"
R167_MANIFEST = ROOT / "config/native-content/sprite-graphics-167-obj.json"


class Room167ManifestTests(unittest.TestCase):
    """The room 167 pack supplies the object character slot at VRAM word 7800."""

    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(R167_MANIFEST.read_text())

    def test_manifest_pins_the_payload(self):
        self.assertEqual(self.spec["schema"], 1)
        self.assertEqual(self.spec["slot"], "167")
        self.assertEqual(self.spec["rooms"], ["167"])
        self.assertEqual(self.spec["ranges"], [{"vram": "7800", "words": 2048}])
        self.assertEqual(self.spec["size"], 4 + 4 + 2048 * 2)
        self.assertTrue(self.spec["persist"])

    def test_pack_matches_its_pin(self):
        import hashlib
        directory = ROOT / self.spec["source_directory"]
        data = (directory / self.spec["pack_file"]).read_bytes()
        self.assertEqual(len(data), self.spec["size"])
        self.assertEqual(hashlib.sha256(data).hexdigest(), self.spec["sha256"])
        count = struct.unpack_from("<I", data, 0)[0]
        self.assertEqual(count, 1)
        address, words = struct.unpack_from("<HH", data, 4)
        self.assertEqual((address, words), (0x7800, 2048))

    def test_pack_holds_graphics_11_object_tiles(self):
        import room_gfx_audit
        directory = ROOT / self.spec["source_directory"]
        data = (directory / self.spec["pack_file"]).read_bytes()
        rom = (ROOT / "local/restoration/demo11-native-product-r20/rom.sfc").read_bytes()
        expected = room_gfx_audit.load_gfx(rom, 0x11)
        self.assertEqual(len(expected), 4096)
        self.assertEqual(data[8:], expected)

    def test_graphics_11_is_identical_in_the_donor(self):
        import room_gfx_audit
        product = (ROOT / "local/restoration/demo11-native-product-r20/rom.sfc").read_bytes()
        donor = (ROOT / "local/content-versions/cheap-demo/rom.sfc").read_bytes()
        self.assertEqual(room_gfx_audit.load_gfx(product, 0x11),
                         room_gfx_audit.load_gfx(donor, 0x11))

    def test_graphics_02_differs_from_the_donor(self):
        import room_gfx_audit
        product = (ROOT / "local/restoration/demo11-native-product-r20/rom.sfc").read_bytes()
        donor = (ROOT / "local/content-versions/cheap-demo/rom.sfc").read_bytes()
        self.assertNotEqual(room_gfx_audit.load_gfx(product, 0x02),
                            room_gfx_audit.load_gfx(donor, 0x02))

    def test_review_accepts_the_manifest(self):
        row = graphics.reviewed(self.spec)
        self.assertEqual(row["rooms"], [0x167])
        self.assertEqual(row["ranges"], [[0x7800, 0x7800 + 2048]])
        self.assertTrue(row["persist"])
        bitmap = bytes.fromhex(row["bitmap"])
        self.assertEqual(bitmap[0x167 >> 3], 1 << (0x167 & 7))


@unittest.skipUnless((ROOT / "config/restorations" / (R22_TARGET + ".json")).exists(),
                     "requires the prepared r22 target")
class Room167TargetTests(unittest.TestCase):
    def test_target_inherits_the_parent_image(self):
        config = json.loads((ROOT / "config/restorations" / (R22_TARGET + ".json")).read_text())
        parent = json.loads((ROOT / "config/restorations/demo11-native-product-r21.json").read_text())
        self.assertEqual(config["base_restoration"], "demo11-native-product-r21")
        self.assertEqual(config["output"], parent["output"])
        self.assertEqual(config["native_sprite_graphics"], [
            "config/native-content/sprite-graphics-175-obj.json",
            "config/native-content/sprite-graphics-167-obj.json",
        ])

    def test_both_packs_are_named(self):
        rows = graphics.packs(R22_TARGET)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["variable"], "BM_SPRITE_GRAPHICS_PACK")
        self.assertEqual(rows[1]["variable"], "BM_SPRITE_GRAPHICS_PACK_2")
        self.assertEqual(rows[0]["rooms"], [0x175])
        self.assertEqual(rows[1]["rooms"], [0x167])

    def test_header_declares_two_packs(self):
        text = graphics.header(R22_TARGET)
        self.assertIn("BM_SPRITE_GRAPHICS_PACKS 2u", text)
        self.assertIn('"BM_SPRITE_GRAPHICS_PACK",16392u,1u', text)
        self.assertIn('"BM_SPRITE_GRAPHICS_PACK_2",4104u,1u', text)

    def test_overlapping_ranges_name_different_rooms(self):
        # The room 175 pack covers words 6000 to 7FFF and the room 167 pack
        # covers words 7800 to 7FFF. The ranges overlap, so the packs must
        # never apply in the same room.
        rows = graphics.packs(R22_TARGET)
        for index, first in enumerate(rows):
            for second in rows[index + 1:]:
                if set(first["rooms"]) & set(second["rooms"]):
                    raise AssertionError("packs with overlapping ranges name one room")



if __name__ == '__main__':
    unittest.main()

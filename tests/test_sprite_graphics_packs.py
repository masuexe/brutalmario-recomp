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


if __name__ == '__main__':
    unittest.main()

"""Bound the C2 integration to its official program and three admission bytes."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_native_type3_c2 as c2


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-type3-shooters-v1/rom.sfc').exists(),
                     'requires pinned parent and official donor assets')
class NativeC2Review(unittest.TestCase):
    def test_official_block_and_bounded_adapter(self):
        result = c2.review()
        self.assertEqual(len(result['adapter_changed_offsets']), 3)
        self.assertEqual(result['sources']['boss']['block_sha256'], result['sources']['7hero']['block_sha256'])

    def test_adapter_logic_change_rejected(self):
        adapter = c2.load(c2.ADAPTER)
        body = bytearray.fromhex(adapter['code']['raw_payload'])
        body[0] ^= 1
        adapter['code']['raw_payload'] = body.hex()
        with self.assertRaisesRegex(ValueError, 'three C2 admission thresholds'):
            c2.review(adapter=adapter)

    def test_source_program_change_rejected(self):
        block = c2.load(c2.BLOCK)
        body = bytearray.fromhex(block['code']['raw_payload'])
        body[0x25] ^= 1
        block['code']['raw_payload'] = body.hex()
        with self.assertRaisesRegex(ValueError, 'protected C2 program'):
            c2.review(block=block)

    def test_bank_without_low_mirrors_rejected(self):
        block = c2.load(c2.BLOCK)
        block['code']['native_address'] = 'CDDD21'
        with self.assertRaisesRegex(ValueError, 'low-mirror allocation'):
            c2.review(block=block)


if __name__ == '__main__':
    unittest.main()

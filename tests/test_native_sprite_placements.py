"""Keep native-pack list pointers from becoming false missing-sprite reports."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_native_sprite_placements import audit, decode_list


class BoundedSpriteLists(unittest.TestCase):
    def test_list_does_not_read_past_its_native_allocation(self):
        with self.assertRaisesRegex(ValueError, 'leaves its mapped allocation'):
            decode_list(bytes.fromhex('00499095'))

    def test_incomplete_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'incomplete sprite record'):
            decode_list(bytes.fromhex('004990'))

    @unittest.skipUnless((ROOT / 'local/restoration/demo11-native-sprite-product-v1/rom.sfc').exists(),
                         'requires the pinned cumulative native candidate')
    def test_census_resolves_external_lists_instead_of_lorom_aliases(self):
        result = audit('demo11-native-sprite-product-v1')
        self.assertEqual(result['custom_slot_count'], 164)
        self.assertEqual(set(result['placeholder_slots']),
                         {'96', '97', '99', 'A1', 'A5', 'A6', 'E8', 'E9', 'EA', 'F5'})
        self.assertEqual(result['rooms']['184']['custom_slots'], ['A9', 'A9'])
        self.assertEqual(result['rooms']['192']['custom_slots'], ['A9'])
        self.assertEqual({room for room, row in result['rooms'].items()
                          if row['origin']['kind'] == 'external-pack'}, {'183', '184', '191', '192'})


if __name__ == '__main__':
    unittest.main()

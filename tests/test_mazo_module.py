"""Review gates for the mazo 9C module recipe."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_mazo_module as mazo
from prepare_rom import verify


@unittest.skipUnless((ROOT / 'local/content-versions/mazo/rom.sfc').exists() and
                    (ROOT / 'local/restoration/demo11-native-sprite9e/rom.sfc').exists(),
                    'requires pinned local donor and recipient assets')
class MazoModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = mazo.read_recipe()
        cls.donor = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
        cls.base = (ROOT / 'local/restoration/demo11-native-sprite9e/rom.sfc').read_bytes()
        pin = json.loads((ROOT / 'config/mazo-donor.json').read_text())
        verify(cls.donor, pin['output'], 'test mazo donor')
        verify(cls.base, cls.recipe['base_output'], 'test recipient')

    def test_review_pins_and_counts(self):
        code, audit = mazo.build_code(self.donor, self.base, self.recipe)
        self.assertEqual(len(code), 12412)
        self.assertEqual(len(audit['reviewed_dispatch_tables']), 3)
        self.assertEqual(len(audit['source_bank_jsl_sites']), 72)
        self.assertEqual(len(audit['scheduler_sites']), 71)
        self.assertEqual(audit['outside_calls'], self.recipe['external_calls'])
        self.assertEqual(audit['local_entry_states'], 159)
        self.assertEqual(audit['instruction_variants'], 4734)

    def test_missing_call_patch_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        del recipe['code_patches'][-1]
        with self.assertRaisesRegex(ValueError, 'call adaptations'):
            mazo.build_code(self.donor, self.base, recipe)

    def test_dispatch_table_change_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['dispatch_tables'][0]['sha256'] = '00'*32
        with self.assertRaisesRegex(ValueError, 'dispatch table'):
            mazo.build_code(self.donor, self.base, recipe)

    def test_adapted_hash_mismatch_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['code']['adapted_sha256'] = '00'*32
        with self.assertRaisesRegex(ValueError, 'adapted program hash'):
            mazo.build_code(self.donor, self.base, recipe)

    def test_native_target_installation(self):
        from restore_star_world_1 import sha
        cfg = json.loads((ROOT / 'config/restorations/demo11-native-mazo-9c.json').read_text())
        projected = bytearray(self.base)
        for patch in self.recipe['unapplied_rom_patches']:
            offset = patch['offset']
            before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
            self.assertEqual(projected[offset:offset+len(before)], before)
            projected[offset:offset+len(after)] = after
        self.assertEqual(sha(bytes(projected)), cfg['output']['sha256'])
        self.assertEqual(cfg['native_seven']['manifest'], 'config/native-content/mazo-9c-module.json')
        rom = (ROOT / 'local/restoration/demo11-native-mazo-9c/rom.sfc').read_bytes()
        verify(rom, cfg['output'], 'mazo native ROM')
        self.assertEqual(rom[patch['offset']:patch['offset']+16].hex(), patch['after'])

    def test_9b_review_pins(self):
        recipe = json.loads((ROOT / 'config/native-content/mazo-9b-module.json').read_text())
        code, audit = mazo.build_code(self.donor, self.base, recipe)
        self.assertEqual(len(code), 3399)
        self.assertEqual(audit['local_entry_states'], 28)
        self.assertEqual(audit['instruction_variants'], 1277)
        self.assertEqual(audit['source_bank_jsl_sites'], [])
        self.assertEqual(audit['outside_calls'], recipe['external_calls'])
        self.assertEqual(recipe['code']['adapted_sha256'], recipe['code']['sha256'])

    def test_9b_native_target_installation(self):
        from restore_star_world_1 import sha
        recipe = json.loads((ROOT / 'config/native-content/mazo-9b-module.json').read_text())
        cfg = json.loads((ROOT / 'config/restorations/demo11-native-mazo-9b.json').read_text())
        projected = bytearray(self.base)
        for patch in recipe['unapplied_rom_patches']:
            offset = patch['offset']
            before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
            self.assertEqual(projected[offset:offset+len(before)], before)
            projected[offset:offset+len(after)] = after
        self.assertEqual(sha(bytes(projected)), cfg['output']['sha256'])
        rom = (ROOT / 'local/restoration/demo11-native-mazo-9b/rom.sfc').read_bytes()
        verify(rom, cfg['output'], 'mazo 9B native ROM')
        self.assertEqual(rom[patch['offset']:patch['offset']+16].hex(), patch['after'])

    def test_record_mismatch_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['record']['raw'] = '00'*16
        with self.assertRaisesRegex(ValueError, '9C record'):
            mazo.check_record(self.donor, recipe)


if __name__ == '__main__':
    unittest.main()

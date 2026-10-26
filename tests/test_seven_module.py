"""Review gates and actual donor CPU boundary checks for the Seven module."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_seven_module as seven
from prepare_rom import verify


@unittest.skipUnless((ROOT / 'local/content-versions/boss/rom.sfc').exists() and
                    (ROOT / 'local/restoration/demo11-native-sprite9e/rom.sfc').exists(),
                    'requires pinned local donor and recipient assets')
class SevenModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = seven.read_recipe(ROOT / 'config/native-content/seven-font-module.json')
        cls.donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
        cls.base = (ROOT / 'local/restoration/demo11-native-sprite9e/rom.sfc').read_bytes()
        pin = json.loads((ROOT / cls.recipe['donor_manifest']).read_text())
        verify(cls.donor, pin['output'], 'test donor')
        verify(cls.base, cls.recipe['base_output'], 'test recipient')

    def test_missing_deferred_call_adaptation_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        # First site is the actual scheduler's inline JSL, not a direct call.
        self.assertEqual(recipe['code_patches'][0]['address'], '2281D3')
        del recipe['code_patches'][0]
        with self.assertRaisesRegex(ValueError, 'call adaptations'):
            seven.build(self.donor, self.base, recipe)

    def test_unknown_dispatch_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        del recipe['dispatch_tables'][-1]
        with self.assertRaisesRegex(ValueError, 'indirect jump'):
            seven.build(self.donor, self.base, recipe)

    def test_retained_recipient_hook_mismatch_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['recipient_adaptations'][0]['recipient_bytes'] = '00000000'
        with self.assertRaisesRegex(ValueError, 'recipient hook'):
            seven.build(self.donor, self.base, recipe)

    def test_native_namespace_collision_is_rejected(self):
        from restore_star_world_1 import lorom, sha
        recipe = copy.deepcopy(self.recipe)
        base = bytearray(self.base)
        offset = lorom(0x14ad08)
        base[offset:offset+4] = bytes.fromhex('0180e00f')
        recipe['base_output']['sha256'] = sha(base)
        with self.assertRaisesRegex(ValueError, 'existing room references'):
            seven.build(self.donor, base, recipe)

    @unittest.skipUnless(shutil.which('cc'), 'requires a C compiler')
    def test_actual_donor_init_and_deferred_ram_callback(self):
        import native_seven
        code, graphics, audit = seven.build(self.donor, self.base, self.recipe)
        self.assertEqual(len(audit['reviewed_dispatch_tables']), 3)
        self.assertEqual(len(audit['source_bank_jsl_sites']), 39)
        with tempfile.TemporaryDirectory(prefix='bm-seven-') as directory:
            path = Path(directory)
            (path / 'code.bin').write_bytes(code)
            (path / 'graphics.bin').write_bytes(graphics)
            (path / 'native_seven_manifest.h').write_text(native_seven.header(native_seven.TARGET))
            candidate = bytearray(self.base)
            for patch in self.recipe['unapplied_rom_patches']:
                offset, data = patch['offset'], bytes.fromhex(patch['after'])
                candidate[offset:offset+len(data)] = data
            cfg, _ = native_seven.settings(native_seven.TARGET)
            verify(candidate, cfg['output'], 'boundary candidate')
            (path / 'rom.sfc').write_bytes(candidate)
            engine = ROOT / 'local/upstream/snesrecomp/runner/src'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-DBOUNDARY_CODE_SIZE='+str(len(code)),
                '-DBOUNDARY_GRAPHICS_SIZE='+str(len(graphics)),
                '-I'+str(engine), '-I'+str(engine / 'snes'), '-I'+str(ROOT / 'recomp'),
                '-I'+str(path),
                str(ROOT / 'tests/seven_module_boundary_test.c'),
                str(ROOT / 'recomp/native_seven.c'), str(engine / 'sha256.c'),
                str(engine / 'snes/interp816.c'), '-o', str(path / 'boundary')], check=True)
            env = os.environ.copy()
            for pack in native_seven.packs(native_seven.TARGET):
                parent = ROOT / 'local/restoration/demo11-native-sprite9e'
                source = (path / 'code.bin' if pack['variable'] == 'BM_SEVEN_CODE_PACK' else
                          path / 'graphics.bin' if pack['variable'] == 'BM_SEVEN_GRAPHICS_PACK' else
                          parent / pack['pack_file'])
                env[pack['variable']] = str(source)
            command = [str(path / 'boundary'), str(path / 'rom.sfc'),
                       str(path / 'code.bin'), str(path / 'graphics.bin')]
            subprocess.run(command, env=env, check=True)
            for variable in ('BM_SEVEN_CODE_PACK', 'BM_SEVEN_GRAPHICS_PACK',
                             'BM_NATIVE_SPRITE_PACK', 'BM_NATIVE_GRAPHICS_PACK'):
                invalid = env.copy()
                invalid.pop(variable)
                result = subprocess.run(command, env=invalid, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('rejected: '+variable, result.stderr)
            corrupt = path / 'corrupt.bin'
            corrupt.write_bytes(bytes(len(code)))
            invalid = dict(env, BM_SEVEN_CODE_PACK=str(corrupt))
            result = subprocess.run(command, env=invalid, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('pack SHA-256 differs', result.stderr)


if __name__ == '__main__':
    unittest.main()

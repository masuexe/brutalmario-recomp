"""Namespace rejection gates and real child-code CPU comparisons."""
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
import native_seven_child as child
from prepare_rom import verify


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-seven-font-entry/rom.sfc').is_file(),
                     'requires pinned parent content')
class SevenChildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.recipe = child.settings(child.TARGET)
        cls.parent = ROOT / 'local/restoration' / cls.cfg['base_restoration']
        cls.base = (cls.parent / 'rom.sfc').read_bytes()
        cls.master = (cls.parent / 'seven-code.bin').read_bytes()
        cls.donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
        verify(cls.donor, json.loads((ROOT / cls.recipe['donor_manifest']).read_text())['output'], 'test donor')

    def test_custom_id_hook_is_required(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['master_patches'].pop()
        with self.assertRaisesRegex(ValueError, 'adaptation site set'):
            child.build(self.donor, self.base, self.master, recipe)

    def test_normal_id_recognition_must_stay_original(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['preserved_master_sites'][1]['bytes'] = 'c9e0'
        with self.assertRaisesRegex(ValueError, 'normal-ID contract'):
            child.build(self.donor, self.base, self.master, recipe)

    def test_namespace_collision_is_rejected(self):
        from restore_star_world_1 import sha
        base = bytearray(self.base)
        offset = self.recipe['record']['destination_offset']
        base[offset] = 1
        recipe = copy.deepcopy(self.recipe)
        recipe['parent_output']['sha256'] = sha(base)
        with self.assertRaisesRegex(ValueError, 'record/namespace'):
            child.build(self.donor, base, self.master, recipe)

    def test_changed_preserved_6a_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['preserved_recipient_6a']['record'] = '00'*16
        with self.assertRaisesRegex(ValueError, 'existing recipient 6A'):
            child.build(self.donor, self.base, self.master, recipe)

    @unittest.skipUnless(shutil.which('cc'), 'requires a C compiler')
    def test_actual_donor_child_and_cumulative_boundary(self):
        fixture = ROOT / 'local/captures/seven-opening-v1-donor/attack1200.wram.bin'
        if not fixture.is_file():
            self.skipTest('requires the pinned source WRAM fixture; see the child qualification document')
        verify(fixture.read_bytes(), {'size': 0x20000,
            'sha256': '74fb4823ead68901af132ef89ce9d5a9508b93a47f3eea780b593e01ca8a2b06'}, 'source CPU fixture')
        rom, master, code, audit = child.build(self.donor, self.base, self.master, self.recipe)
        verify(rom, self.cfg['output'], 'test descendant')
        self.assertEqual(len(audit['entry_states']), 32)
        self.assertEqual(audit['instruction_variants'], 1426)
        with tempfile.TemporaryDirectory(prefix='bm-seven-child-') as directory:
            path = Path(directory)
            (path / 'rom.sfc').write_bytes(rom)
            (path / 'seven-code.bin').write_bytes(master)
            (path / 'seven-child6a.bin').write_bytes(code)
            graphics = child.graphics_payload(self.recipe, self.parent)
            (path / 'seven-graphics.bin').write_bytes(graphics)
            (path / 'native_seven_manifest.h').write_text(child.header(child.TARGET))
            engine = ROOT / 'local/upstream/snesrecomp/runner/src'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-DBOUNDARY_CODE_SIZE='+str(len(master)), '-DBOUNDARY_GRAPHICS_SIZE='+str(len(graphics)),
                '-I'+str(engine), '-I'+str(engine / 'snes'), '-I'+str(ROOT / 'recomp'), '-I'+str(path),
                str(ROOT / 'tests/seven_child_boundary_test.c'), str(ROOT / 'recomp/native_seven.c'),
                str(engine / 'sha256.c'), str(engine / 'snes/interp816.c'), '-o', str(path / 'boundary')], check=True)
            env = os.environ.copy()
            for pack in child.packs(child.TARGET):
                source = path / pack['pack_file']
                if not source.exists():
                    source = self.parent / pack['pack_file']
                env[pack['variable']] = str(source)
            command = [str(path / 'boundary'), str(path / 'rom.sfc'), str(path / 'seven-code.bin'),
                str(path / 'seven-graphics.bin'), str(ROOT / 'local/content-versions/boss/rom.sfc'),
                str(fixture)]
            subprocess.run(command, env=env, check=True)
            for variant, data, reason in (
                ('missing', None, 'BM_SEVEN_CHILD_PACK'), ('short', code[:-1], 'pack size differs'),
                ('long', code+b'\0', 'pack size differs'), ('corrupt', bytes(len(code)), 'pack SHA-256 differs'),
            ):
                invalid = env.copy()
                invalid.pop('BM_SEVEN_CHILD_PACK')
                if data is not None:
                    pack = path / (variant+'.bin')
                    pack.write_bytes(data)
                    invalid['BM_SEVEN_CHILD_PACK'] = str(pack)
                result = subprocess.run(command, env=invalid, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('rejected: '+reason, result.stderr)


if __name__ == '__main__':
    unittest.main()

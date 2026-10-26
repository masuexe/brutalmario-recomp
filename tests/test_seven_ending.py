"""Bounded defeat-stop adaptation and actual recipient music dispatch."""
import copy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_seven_ending as ending
from prepare_rom import verify


@unittest.skipUnless((ROOT / 'local/restoration' / ending.PARENT / 'rom.sfc').is_file(),
                     'requires the pinned parent target')
class SevenEndingTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.recipe = ending.child.settings(ending.TARGET)
        parent = ROOT / 'local/restoration' / ending.PARENT
        self.rom = (parent / 'rom.sfc').read_bytes()
        self.master = (parent / 'seven-code.bin').read_bytes()
        self.donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()

    def test_only_defeat_stop_immediate_changes(self):
        result = ending.adapt(self.rom, self.master, self.donor, self.recipe)
        self.assertEqual([i for i, pair in enumerate(zip(self.master, result))
                          if pair[0] != pair[1]], [0x384])
        self.assertEqual(result[0x384], 0x80)
        verify(self.rom, self.cfg['output'], 'unchanged descendant ROM')

    def test_corrupt_parent_is_rejected(self):
        broken = bytearray(self.master)
        broken[0x384] ^= 1
        with self.assertRaises(ValueError):
            ending.adapt(self.rom, broken, self.donor, self.recipe)

    def test_unreviewed_patch_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['ending_stop']['after'] = 'a9008dfb1d'
        with self.assertRaisesRegex(ValueError, 'unreviewed'):
            ending.adapt(self.rom, self.master, self.donor, recipe)

    @unittest.skipUnless(shutil.which('cc'), 'requires a C compiler')
    def test_actual_modern_driver_stop_and_upload_branches(self):
        with tempfile.TemporaryDirectory(prefix='bm-seven-stop-') as temporary:
            path = Path(temporary)
            (path / 'native_seven_manifest.h').write_text(ending.child.header(ending.TARGET))
            engine = ROOT / 'local/upstream/snesrecomp/runner/src'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-DBOUNDARY_CODE_SIZE=28880', '-DBOUNDARY_GRAPHICS_SIZE=27261',
                '-I'+str(engine), '-I'+str(engine / 'snes'), '-I'+str(ROOT / 'recomp'), '-I'+str(path),
                str(ROOT / 'tests/seven_stop_boundary_test.c'), str(ROOT / 'recomp/native_seven.c'),
                str(engine / 'sha256.c'), str(engine / 'snes/interp816.c'),
                '-o', str(path / 'stop')], check=True)
            subprocess.run([str(path / 'stop'), str(ROOT / 'local/restoration' /
                            ending.PARENT / 'rom.sfc')], check=True)

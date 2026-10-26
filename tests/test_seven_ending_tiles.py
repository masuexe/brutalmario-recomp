"""Room-local FG2 resource clone and ending font boundary checks."""
import copy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_seven_ending_tiles as graphics
import native_seven_ending_test as ending
from restore_star_world_1 import lorom, lz2


@unittest.skipUnless((ROOT / 'local/restoration' / graphics.TARGET / 'rom.sfc').is_file(),
                     'requires pinned ending targets')
class SevenEndingGraphicsTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.recipe = graphics.child.settings(graphics.TARGET)
        parent = ROOT / 'local/restoration' / graphics.PARENT
        self.rom = (parent / 'rom.sfc').read_bytes()
        self.master = (parent / 'seven-code.bin').read_bytes()
        self.graphics = (parent / 'seven-graphics.bin').read_bytes()
        self.donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()

    def test_only_reviewed_graphics_record_and_pointer_change(self):
        rom, payload = graphics.adapt(self.rom, self.graphics, self.donor, self.recipe)
        expected = bytearray(self.rom)
        for patch in self.recipe['ending_graphics']['rom_patches']:
            offset = lorom(int(patch['address'],16))
            data = bytes.fromhex(patch['after'])
            expected[offset:offset+len(data)] = data
        self.assertEqual(rom, expected)
        self.assertEqual(payload[:len(self.graphics)], self.graphics)
        overlay = bytearray(rom)
        start = lorom(0xa68000)
        overlay[start:start+len(payload)] = payload
        decoded, _ = lz2(overlay,0xa6ea7d,limit=4096)
        original, _ = lz2(self.rom,0x0a97b6,limit=4096)
        changed = {i//32+0x80 for i,(a,b) in enumerate(zip(decoded,original)) if a != b}
        self.assertEqual(changed,{0xa4,0xa5,0xa6,0xa7,0xb4,0xb5,0xb6,0xb7})
        for tile in changed:
            self.assertEqual(decoded[(tile-0x80)*32:(tile-0x80+1)*32],bytes(32))

    def test_unreviewed_room_or_namespace_is_rejected(self):
        for key in ('room','namespace_id'):
            recipe = copy.deepcopy(self.recipe)
            recipe['ending_graphics'][key] = '00'
            with self.assertRaisesRegex(ValueError,'unreviewed'):
                graphics.adapt(self.rom,self.graphics,self.donor,recipe)

    def test_t_room_recipe_is_reproducible(self):
        cfg, recipe = ending.child.settings(ending.TARGET)
        parent = ROOT / 'local/restoration' / ending.PARENT
        result = ending.adapt((parent/'rom.sfc').read_bytes(), (parent/'seven-code.bin').read_bytes(), self.donor, recipe)
        self.assertEqual(result, (self.rom, self.master))

    @unittest.skipUnless(shutil.which('cc'), 'requires a C compiler')
    def test_real_font_exit(self):
        with tempfile.TemporaryDirectory(prefix='bm-seven-ending-') as temporary:
            path = Path(temporary)
            (path/'native_seven_manifest.h').write_text(graphics.child.header(graphics.TARGET))
            engine = ROOT/'local/upstream/snesrecomp/runner/src'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-DBOUNDARY_CODE_SIZE=28880', '-DBOUNDARY_GRAPHICS_SIZE=31366',
                '-I'+str(engine), '-I'+str(engine/'snes'), '-I'+str(ROOT/'recomp'), '-I'+str(path),
                str(ROOT/'tests/seven_ending_font_boundary_test.c'), str(ROOT/'recomp/native_seven.c'),
                str(engine/'sha256.c'), str(engine/'snes/interp816.c'), '-o', str(path/'boundary')], check=True)
            env = os.environ.copy()
            graphics.child.environment(graphics.TARGET, env)
            subprocess.run([str(path/'boundary'), str(ROOT/'local/restoration'/graphics.TARGET/'rom.sfc')],
                           env=env, check=True)

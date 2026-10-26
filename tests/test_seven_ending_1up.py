"""Official hidden mushroom checkpoint code and bounded room guard."""
import copy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import native_seven_ending_1up as mushroom


@unittest.skipUnless((ROOT/'local/restoration'/mushroom.TARGET/'rom.sfc').is_file(),
                     'requires pinned mushroom descendant')
class SevenEndingMushroomTests(unittest.TestCase):
    def setUp(self):
        self.cfg,self.recipe = mushroom.child.settings(mushroom.TARGET)
        parent = ROOT/'local/restoration'/mushroom.PARENT
        self.rom = (parent/'rom.sfc').read_bytes()
        self.master = (parent/'seven-code.bin').read_bytes()
        self.donor = (ROOT/'local/content-versions/boss/rom.sfc').read_bytes()

    def test_only_reviewed_checkpoint_hook_and_bounded_extension(self):
        rom,payload = mushroom.adapt(self.rom,self.master,self.donor,self.recipe)
        self.assertEqual([i for i,(a,b) in enumerate(zip(rom,self.rom)) if a != b],list(range(0x7294,0x7299)))
        self.assertEqual(payload[:len(self.master)],self.master)
        self.assertEqual(len(payload),28965)

    def test_unreviewed_room_is_rejected(self):
        recipe = copy.deepcopy(self.recipe)
        recipe['ending_1up']['room'] = '0174'
        with self.assertRaisesRegex(ValueError,'unreviewed'):
            mushroom.adapt(self.rom,self.master,self.donor,recipe)

    @unittest.skipUnless(shutil.which('cc'),'requires a C compiler')
    def test_real_checkpoint_continuation_and_spawn(self):
        with tempfile.TemporaryDirectory(prefix='bm-seven-mushroom-') as temporary:
            path = Path(temporary)
            (path/'native_seven_manifest.h').write_text(mushroom.child.header(mushroom.TARGET))
            engine = ROOT/'local/upstream/snesrecomp/runner/src'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',
                '-DBOUNDARY_CODE_SIZE=28965','-DBOUNDARY_GRAPHICS_SIZE=31366',
                '-I'+str(engine),'-I'+str(engine/'snes'),'-I'+str(ROOT/'recomp'),'-I'+str(path),
                str(ROOT/'tests/seven_ending_mushroom_boundary_test.c'),str(ROOT/'recomp/native_seven.c'),
                str(engine/'sha256.c'),str(engine/'snes/interp816.c'),'-o',str(path/'boundary')],check=True)
            env = os.environ.copy()
            mushroom.child.environment(mushroom.TARGET,env)
            subprocess.run([str(path/'boundary'),str(ROOT/'local/content-versions/boss/rom.sfc'),
                str(ROOT/'local/restoration'/mushroom.PARENT/'rom.sfc'),
                str(ROOT/'local/restoration'/mushroom.TARGET/'rom.sfc')],env=env,check=True)

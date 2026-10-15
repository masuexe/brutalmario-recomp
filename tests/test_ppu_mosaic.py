"""Exercise synthetic pixel output through the locally patched PPU."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_patches import prepare_runtime


class PpuMosaicTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc') and
                         (ROOT / 'local/upstream/snesrecomp/runner/src/snes/ppu.c').is_file(),
                         'requires the pinned local runtime checkout and a C compiler')
    def test_visible_only_scanout_and_mosaic_size_changes(self):
        self.compile_and_run('ppu_mosaic_test.c')

    @unittest.skipUnless(shutil.which('cc') and
                         (ROOT / 'local/upstream/snesrecomp/runner/src/snes/ppu.c').is_file(),
                         'requires the pinned local runtime checkout and a C compiler')
    def test_raster_replay_preserves_late_writes_and_latches(self):
        self.compile_and_run('ppu_raster_restore_test.c')

    def compile_and_run(self, test_source):
        ppu = prepare_runtime()[0]
        engine = ROOT / 'local/upstream/snesrecomp'
        with tempfile.TemporaryDirectory(prefix='mosaic-test-') as directory:
            executable = Path(directory) / 'mosaic-test'
            build = subprocess.run([
                'cc', '-std=c11', '-O2', '-DSNESRECOMP_REVERSE_DEBUG=0',
                '-I' + str(engine / 'runner/src'), '-I' + str(engine / 'runner/src/snes'),
                str(ROOT / 'tests' / test_source), str(ppu),
                str(engine / 'runner/src/snes/ppu_legacy.c'), '-lm', '-o', str(executable),
            ], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

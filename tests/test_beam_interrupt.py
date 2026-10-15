"""Verify field scheduling with an interrupt that outlasts a hardware field."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_patches import prepare_runtime


class BeamInterruptTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc') and
                         (ROOT / 'local/upstream/snesrecomp/runner/src/beam_frame_driver.c').is_file(),
                         'requires the pinned runtime and a C compiler')
    def test_long_interrupt_resumes_across_fields(self):
        driver = next(p for p in prepare_runtime() if p.name == 'beam_frame_driver.c')
        include = ROOT / 'local/upstream/snesrecomp/runner/src'
        with tempfile.TemporaryDirectory(prefix='beam-test-') as directory:
            executable = Path(directory) / 'beam-test'
            build = subprocess.run([
                'cc', '-std=c11', '-O2', '-ffunction-sections', '-fdata-sections',
                '-Wl,--gc-sections', '-I' + str(include),
                str(ROOT / 'tests/beam_interrupt_test.c'), str(driver),
                '-o', str(executable),
            ], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

"""Exercise echo RAM isolation and snapshot compatibility without a ROM."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_patches import prepare_runtime


class DspEchoTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc') and
                         (ROOT / 'local/upstream/snesrecomp/runner/src/snes/dsp.c').is_file(),
                         'requires the pinned runtime and a C compiler')
    def test_shared_ram_default_and_legacy_echo_isolation(self):
        dsp = next(p for p in prepare_runtime() if p.name == 'dsp.c')
        include = ROOT / 'local/upstream/snesrecomp/runner/src'
        with tempfile.TemporaryDirectory(prefix='echo-test-') as directory:
            executable = Path(directory) / 'echo-test'
            build = subprocess.run([
                'cc', '-std=c11', '-O2', '-I' + str(include), '-I' + str(include / 'snes'),
                str(ROOT / 'tests/dsp_echo_test.c'), str(dsp), '-o', str(executable),
            ], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

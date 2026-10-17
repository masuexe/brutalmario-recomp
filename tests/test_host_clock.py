"""Verify wall-clock scheduling against synthetic jitter and overload."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_patches import prepare_runtime


class HostClockTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc') and
                         (ROOT / 'local/upstream/snesrecomp/runner/src/desktop/host_clock.c').is_file(),
                         'requires the pinned runtime and a C compiler')
    def test_jitter_catchup_and_sustained_overload(self):
        source = next(p for p in prepare_runtime() if p.name == 'host_clock.c')
        with tempfile.TemporaryDirectory(prefix='host-clock-test-') as directory:
            binary = Path(directory) / 'host-clock-test'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-I' + str(ROOT / 'local/upstream/snesrecomp/runner/src/desktop'),
                            str(ROOT / 'tests/host_clock_test.c'), str(source),
                            '-lm', '-o', str(binary)], check=True, capture_output=True, text=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

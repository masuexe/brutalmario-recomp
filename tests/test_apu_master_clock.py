"""Check elapsed-time APU pacing and the unchanged legacy opt-out."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_patches import prepare_runtime


class ApuMasterClockTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc') and shutil.which('pkg-config') and
                         (ROOT / 'local/upstream/snesrecomp/runner/src/common_rtl.c').is_file(),
                         'requires the pinned runtime and a C compiler')
    def test_partial_field_long_loader_rounding_and_legacy_default(self):
        source = next(p for p in prepare_runtime() if p.name == 'common_rtl.c')
        include = ROOT / 'local/upstream/snesrecomp/runner/src'
        flags = subprocess.run(['pkg-config', '--cflags', 'sdl2'], capture_output=True, text=True)
        if flags.returncode:
            self.skipTest('requires SDL2 development headers')
        with tempfile.TemporaryDirectory(prefix='apu-clock-test-') as directory:
            executable = Path(directory) / 'apu-clock-test'
            result = subprocess.run([
                'cc', '-std=gnu11', '-O2', '-DSNESRECOMP_REVERSE_DEBUG=0',
                '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
                '-I' + str(include), '-I' + str(include / 'snes'),
                '-I' + str(include / 'desktop'),
                *flags.stdout.split(),
                '-DM1_RUNTIME_SOURCE="' + str(source) + '"',
                str(ROOT / 'tests/apu_master_clock_test.c'), '-lm', '-o', str(executable),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for mode in ('0', '1'):
                result = subprocess.run([str(executable), mode], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

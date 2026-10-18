"""Exercise device-backlog recovery without changing emulated DSP state."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_patches import prepare_runtime


class AudioBacklogTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc') and shutil.which('pkg-config') and
                         (ROOT / 'local/upstream/snesrecomp/runner/src/common_rtl.c').is_file(),
                         'requires the pinned runtime and SDL2 development files')
    def test_recent_audio_and_unchanged_dsp_state(self):
        sources = {p.name: p for p in prepare_runtime()}
        include = ROOT / 'local/upstream/snesrecomp/runner/src'
        flags = subprocess.run(['pkg-config', '--cflags', 'sdl2'], capture_output=True, text=True)
        if flags.returncode:
            self.skipTest('requires SDL2 development headers')
        with tempfile.TemporaryDirectory(prefix='audio-backlog-test-') as temporary:
            binary = Path(temporary) / 'audio-backlog-test'
            result = subprocess.run([
                'cc', '-std=gnu11', '-O2', '-DSNESRECOMP_REVERSE_DEBUG=0',
                '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
                '-I' + str(include), '-I' + str(include / 'snes'),
                '-I' + str(include / 'desktop'), *flags.stdout.split(),
                '-DM1_RUNTIME_SOURCE="' + str(sources['common_rtl.c']) + '"',
                str(ROOT / 'tests/audio_backlog_test.c'), str(sources['dsp.c']),
                '-lm', '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

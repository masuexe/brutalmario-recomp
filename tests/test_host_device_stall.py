"""A stalled SDL audio callback must not stall guest frame execution."""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_patches import patch_plan

BINARY = ROOT / 'local/build/demo-only-1/BrutalMarioDemoOnly1SNESRecomp'
ROM = ROOT / 'local/roms/demo-only-1.sfc'


class HostDeviceStallTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith('linux') and shutil.which('cc') and
                         shutil.which('pkg-config') and BINARY.is_file() and ROM.is_file(),
                         'requires a local Linux SDL2 host, ROM, and C compiler')
    def test_callback_stalls_do_not_throttle_video(self):
        receipt = json.loads((BINARY.parent / 'm1-build.json').read_text())
        self.assertEqual(receipt['runtime_patches'], patch_plan(), 'rebuild demo-only-1 first')
        self.assertEqual(receipt['binary_sha256'], hashlib.sha256(BINARY.read_bytes()).hexdigest())
        flags = subprocess.run(['pkg-config', '--cflags', 'sdl2'], capture_output=True, text=True)
        if flags.returncode:
            self.skipTest('requires SDL2 development headers')
        with tempfile.TemporaryDirectory(prefix='audio-device-stall-') as temporary:
            directory = Path(temporary)
            shim = directory / 'device-stall.so'
            build = subprocess.run([
                'cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                *flags.stdout.split(), str(ROOT / 'tests/host_audio_stall.c'),
                '-ldl', '-o', str(shim)], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            config = directory / 'config.ini'
            config.write_text('[Graphics]\nOutputMethod=SDL-Software\nWindowScale=1\n'
                              'NewRenderer=1\nVSync=0\n[Sound]\nEnableAudio=1\n'
                              'AudioFreq=32000\nAudioSamples=512\n')
            trace = directory / 'frame-timing.csv'
            env = os.environ.copy()
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                       SNESRECOMP_RUN_FRAMES='360', SNESRECOMP_FRAME_TIMING=str(trace),
                       LD_PRELOAD=str(shim))
            result = subprocess.run([str(BINARY), '--no-launcher', '--rom', str(ROM),
                                     '--config', str(config)], cwd=directory, env=env,
                                    capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn('exit: RUN_FRAMES reached after 360 frames', output)
            totals = re.search(r'audio totals: .*dropped=(\d+).*backlog_discarded=(\d+)', output)
            self.assertIsNotNone(totals, output)
            self.assertEqual(int(totals[1]), 0, output)
            self.assertGreater(int(totals[2]), 0, output)
            with trace.open() as stream:
                guest_ms = sorted(float(row['guest_ms']) for row in csv.DictReader(stream))
            self.assertEqual(len(guest_ms), 360)
            # The old audio backpressure adds repeated 250 ms waits here.
            # Leave broad headroom for unrelated host scheduling jitter.
            self.assertLess(guest_ms[int(len(guest_ms)*.99)], 100, output)

"""Run the built desktop host through optional-audio startup failures."""
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_patches import patch_plan

BINARY = ROOT / 'local/build/demo-only-1/BrutalMarioDemoOnly1SNESRecomp'
ROM = ROOT / 'local/roms/demo-only-1.sfc'


@unittest.skipUnless(BINARY.is_file() and ROM.is_file(),
                     'requires the locally built demoOnly1 host and ROM')
class HostAudioStartupTests(unittest.TestCase):
    def run_host(self, driver, enabled=True, alsa_config=None, script=None, frames=5, extra_env=None):
        # Check the binary receipt so an old build cannot silently test old code.
        receipt = json.loads((BINARY.parent / 'm1-build.json').read_text())
        self.assertEqual(receipt['runtime_patches'], patch_plan(), 'rebuild demo-only-1 first')
        self.assertEqual(receipt['binary_sha256'], hashlib.sha256(BINARY.read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory(prefix='host-audio-test-') as temporary:
            directory = Path(temporary)
            config = directory / 'config.ini'
            config.write_text('[Graphics]\nOutputMethod=SDL-Software\nVSync=0\n'
                              'WindowScale=1\n[Sound]\nEnableAudio=' +
                              str(int(enabled)) + '\n')
            trace = directory / 'state.csv'
            env = os.environ.copy()
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER=driver,
                       SNESRECOMP_RUN_FRAMES=str(frames), SNESRECOMP_STATE_TRACE=str(trace))
            if extra_env:
                for key, value in extra_env.items():
                    if value is None:
                        env.pop(key, None)
                    else:
                        env[key] = value
            if alsa_config is not None:
                alsa = directory / 'alsa.conf'
                alsa.write_text(alsa_config)
                env['ALSA_CONFIG_PATH'] = str(alsa)
            command = [str(BINARY), '--no-launcher', '--rom', str(ROM),
                       '--config', str(config)]
            if script is not None:
                path = directory / 'input.script'
                path.write_text(script)
                command += ['--script', str(path)]
            result = subprocess.run(command, cwd=directory,
                                    env=env, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn(f'exit: RUN_FRAMES reached after {frames} frames', output)
            self.assertTrue(trace.is_file(), output)
            self.assertEqual(trace.read_text().splitlines()[-1].split(',')[0], str(frames))
            self.assertIn('EnableAudio=' + str(int(enabled)), config.read_text())
            return output

    def test_missing_audio_driver_continues_to_run_frames(self):
        output = self.run_host('nonexistent-audio-driver')
        self.assertIn('audio init FAILED:', output)
        self.assertIn('continuing without sound', output)

    def test_missing_audio_device_continues_to_run_frames(self):
        # Force ALSA to select a nonexistent PCM, independent of host hardware.
        output = self.run_host('alsa', alsa_config='pcm.!default { type missing_test_pcm }\n')
        self.assertIn('audio device open FAILED:', output)
        self.assertIn('continuing without sound', output)

    def test_working_audio_device_still_opens(self):
        self.assertIn('audio device opened:', self.run_host('dummy'))

    def test_repeated_fast_forward_release_discards_stale_audio(self):
        output = self.run_host('dummy', script=(
            'turbo on\nwait 900\nturbo off\nwait 90\n'
            'turbo on\nwait 100\nturbo off\nwait 90\n'), frames=1180)
        self.assertEqual(output.count('audio timeline: fast-forward -> realtime'), 2, output)
        totals = re.search(r'audio totals: .*fast_forward_discarded=(\d+).*queued=(\d+)', output)
        self.assertIsNotNone(totals, output)
        self.assertGreater(int(totals[1]), 4000, output)
        self.assertLess(int(totals[2]), 4096, output)

    @unittest.skipUnless(sys.platform.startswith('linux') and shutil.which('cc') and
                         shutil.which('pkg-config'), 'requires a Linux SDL2 development environment')
    def test_rdp_native_output_and_opt_out(self):
        flags = subprocess.run(['pkg-config', '--cflags', 'sdl2'], capture_output=True, text=True)
        if flags.returncode:
            self.skipTest('requires SDL2 development headers')
        with tempfile.TemporaryDirectory(prefix='rdp-audio-test-') as temporary:
            shim = Path(temporary) / 'rdp-audio.so'
            build = subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                                    *flags.stdout.split(), str(ROOT / 'tests/host_rdp_audio.c'),
                                    '-o', str(shim)], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            output = self.run_host('dummy', extra_env={'LD_PRELOAD': str(shim),
                                                     'SNESRECOMP_RDP_AUDIO': '1'})
            self.assertIn('RDP audio compatibility: rate=44100 samples=2048', output)
            self.assertIn('audio device opened: freq=44100 (want 44100) ch=2 samples=2048', output)
            self.assertIn('audio queue: native_prefill=2978 high_water=5000', output)
            output = self.run_host('dummy', extra_env={'LD_PRELOAD': str(shim),
                                                     'SNESRECOMP_RDP_AUDIO': '0'})
            self.assertNotIn('RDP audio compatibility:', output)
            self.assertIn('audio device opened: freq=32040 (want 32040) ch=2 samples=512', output)

    def test_disabled_audio_does_not_initialize_missing_driver(self):
        output = self.run_host('nonexistent-audio-driver', enabled=False)
        self.assertIn('audio disabled in config', output)
        self.assertNotIn('audio init FAILED:', output)


if __name__ == '__main__':
    unittest.main()

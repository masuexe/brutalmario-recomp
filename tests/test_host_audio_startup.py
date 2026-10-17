"""Run the built desktop host through optional-audio startup failures."""
import hashlib
import json
import os
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
    def run_host(self, driver, enabled=True, alsa_config=None):
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
                       SNESRECOMP_RUN_FRAMES='5', SNESRECOMP_STATE_TRACE=str(trace))
            if alsa_config is not None:
                alsa = directory / 'alsa.conf'
                alsa.write_text(alsa_config)
                env['ALSA_CONFIG_PATH'] = str(alsa)
            result = subprocess.run([str(BINARY), '--no-launcher', '--rom', str(ROM),
                                     '--config', str(config)], cwd=directory,
                                    env=env, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn('exit: RUN_FRAMES reached after 5 frames', output)
            self.assertTrue(trace.is_file(), output)
            self.assertEqual(trace.read_text().splitlines()[-1].split(',')[0], '5')
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

    def test_disabled_audio_does_not_initialize_missing_driver(self):
        output = self.run_host('nonexistent-audio-driver', enabled=False)
        self.assertIn('audio disabled in config', output)
        self.assertNotIn('audio init FAILED:', output)


if __name__ == '__main__':
    unittest.main()

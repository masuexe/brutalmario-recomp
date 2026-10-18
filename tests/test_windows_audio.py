"""Exercise native audio pipe ownership, device stalls, and helper failure."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import windows_audio
from runtime_patches import patch_plan

BINARY = ROOT / 'local/build/demo-only-1/BrutalMarioDemoOnly1SNESRecomp'
ROM = ROOT / 'local/roms/demo-only-1.sfc'


class WindowsAudioTests(unittest.TestCase):
    def test_explicit_driver_and_audio_opt_out_take_precedence(self):
        env = dict(WSL_INTEROP='/run/WSL/test', PULSE_SERVER='unix:/mnt/wslg/PulseServer')
        with mock.patch.object(Path, 'is_file', return_value=True):
            self.assertTrue(windows_audio.available(ROOT, env))
            self.assertFalse(windows_audio.available(ROOT, dict(env, SDL_AUDIODRIVER='alsa')))
            self.assertFalse(windows_audio.available(ROOT, dict(env, SNESRECOMP_WINDOWS_AUDIO='0')))

    @unittest.skipUnless(sys.platform == 'linux' and BINARY.is_file() and ROM.is_file(),
                         'requires a locally built Linux host and ROM')
    def test_native_pipe_slow_device_and_device_exit(self):
        receipt = json.loads((BINARY.parent / 'm1-build.json').read_text())
        self.assertEqual(receipt['runtime_patches'], patch_plan(), 'rebuild demo-only-1 first')
        self.assertEqual(receipt['binary_sha256'], hashlib.sha256(BINARY.read_bytes()).hexdigest())
        real_popen = subprocess.Popen
        for mode in ('slow', 'exit', 'stalled'):
            with self.subTest(device=mode), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                helper = directory / 'device.py'
                helper.write_text('''import select, sys, time
print('READY 1 44100 512 3', flush=True)
blocks = 0
while True:
    if blocks >= 3:
        if MODE == 'exit':
            sys.exit(7)
        if MODE == 'stalled':
            # No more credits: only closing the host PCM fd can wake us.
            # A watchdog also makes a deadlocked old host fail finitely.
            if not select.select([sys.stdin.buffer], [], [], 6)[0]:
                sys.exit(8)
            assert sys.stdin.buffer.read(1) == b''
            break
        # A slow device must throttle only the audio consumer.
        time.sleep(.06)
        print('CREDIT', flush=True)
    block = sys.stdin.buffer.read(2048)
    if not block:
        break
    assert len(block) == 2048
    blocks += 1
print('complete blocks=' + str(blocks), file=sys.stderr)
'''.replace('MODE', repr(mode)))
                config = directory / 'config.ini'
                config.write_text('[Graphics]\nOutputMethod=SDL-Software\nWindowScale=1\n'
                                  'VSync=0\n[Sound]\nEnableAudio=1\n')
                trace = directory / 'frames.csv'
                env = dict(os.environ, SDL_VIDEODRIVER='dummy', SNESRECOMP_RUN_FRAMES='90',
                           SNESRECOMP_FRAME_TIMING=str(trace))
                command = [str(BINARY), '--no-launcher', '--rom', str(ROM),
                           '--config', str(config)]
                game_log = directory / 'game.log'

                def popen(args, **kwargs):
                    if args[0] == str(windows_audio.POWERSHELL):
                        return real_popen([sys.executable, str(helper)], **kwargs)
                    # Capture the real executable separately from helper stderr.
                    kwargs.update(stdout=output, stderr=subprocess.STDOUT)
                    return real_popen(args, **kwargs)

                with game_log.open('w') as output, \
                        mock.patch.object(windows_audio.subprocess, 'check_output', return_value='fake.ps1'), \
                        mock.patch.object(windows_audio.subprocess, 'Popen', side_effect=popen), \
                        contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    started = time.monotonic()
                    self.assertEqual(windows_audio.run(command, directory, ROOT, env), 0)
                    if mode == 'stalled':
                        self.assertLess(time.monotonic() - started, 4,
                                        'stalled completion channel must not block shutdown')
                log = game_log.read_text()
                self.assertIn('audio output: Windows native pipe (44100 Hz)', log)
                self.assertIn('audio queue: native_prefill=3204 high_water=4854', log)
                self.assertIn('frame clock: MONOTONIC_RAW (Windows audio)', log)
                self.assertIn('exit: RUN_FRAMES reached after 90 frames', log)
                if mode == 'exit':
                    self.assertIn('continuing without sound', log)
                else:
                    self.assertIn('complete blocks=', (directory / 'windows-audio.log').read_text())
                # Both a slow consumer and an exited device preserve all guest frames.
                self.assertEqual(len(trace.read_text().splitlines()) - 1, 90)

    def test_failed_handshake_cleans_up_and_allows_sdl_fallback(self):
        real_popen = subprocess.Popen
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            children = []

            def popen(args, **kwargs):
                child = real_popen([sys.executable, '-c', "print('BAD HANDSHAKE', flush=True)"], **kwargs)
                children.append(child)
                return child

            with mock.patch.object(windows_audio.subprocess, 'check_output', return_value='fake.ps1'), \
                    mock.patch.object(windows_audio.subprocess, 'Popen', side_effect=popen), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertIsNone(windows_audio.run(['never-launch'], directory, ROOT))
            self.assertEqual(len(children), 1)
            self.assertIsNotNone(children[0].poll())


if __name__ == '__main__':
    unittest.main()

"""Launcher checks for the demo-1-1 build's Windows-native audio path."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import play_demo_1_1 as play


class Demo11LauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='demo11-launcher-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.build = self.root / 'local/build/demo-1-1'
        self.build.mkdir(parents=True)
        self.rom = self.root / 'local/roms/demo-1-1.sfc'
        self.rom.parent.mkdir(parents=True)
        self.rom.write_bytes(b'test ROM')
        (self.build / 'BrutalMarioDemo11SNESRecomp').write_bytes(b'test executable')
        (self.build / 'm1-build.json').write_text(json.dumps({
            'binary_sha256': hashlib.sha256(b'test executable').hexdigest(),
            'runtime_patches': [],
        }))
        config = self.root / 'config/inputs.json'
        config.parent.mkdir()
        config.write_text(json.dumps({'target': 'test target', 'output': {
            'size': 8, 'sha256': hashlib.sha256(b'test ROM').hexdigest()}}))
        self.config = self.build / 'config.ini'
        self.config.write_text('[Sound]\nEnableAudio = 1\n')
        (self.root / 'recomp').mkdir()
        (self.root / 'recomp/m1-config.ini').write_text('[Sound]\nEnableAudio=1\n')

    def invoke(self, argv=()):
        """Run main() against the fake tree, capturing exec/chdir calls."""
        with patch.object(play, 'ROOT', self.root), \
                patch.object(play, 'patch_plan', return_value=[]), \
                patch.object(play.os, 'chdir') as chdir, \
                patch.object(play.os, 'execv') as execute, \
                patch('sys.argv', ['play_demo_1_1.py', *argv]):
            play.main()
        return chdir, execute

    def test_direct_launch_passes_config_and_rom(self):
        chdir, execute = self.invoke()
        self.assertEqual(chdir.call_args.args[0], self.build)
        command = execute.call_args.args[1]
        self.assertIn('--no-launcher', command)
        self.assertEqual(Path(command[command.index('--config') + 1]), self.config)
        self.assertEqual(Path(command[command.index('--rom') + 1]), self.rom)

    def test_windows_output_launch_and_sdl_fallback(self):
        with patch.object(play.windows_audio, 'available', return_value=True), \
                patch.object(play.windows_audio, 'run', return_value=7) as native:
            with self.assertRaises(SystemExit) as result:
                self.invoke()
            self.assertEqual(result.exception.code, 7)
            command, directory, root = native.call_args.args
            self.assertEqual(root, self.root)
            self.assertEqual(directory, self.build)
            self.assertEqual(Path(command[command.index('--config') + 1]), self.config)

        with patch.object(play.windows_audio, 'available', return_value=True), \
                patch.object(play.windows_audio, 'run', return_value=None) as native:
            _, execute = self.invoke()
            native.assert_called_once()
            execute.assert_called_once()

    def test_forced_sdl_and_disabled_audio_skip_native_output(self):
        with patch.object(play.windows_audio, 'available', return_value=True), \
                patch.object(play.windows_audio, 'run') as native:
            _, execute = self.invoke(['--no-windows-audio'])
            native.assert_not_called()
            execute.assert_called_once()

        self.config.write_text('[Sound]\nEnableAudio = 0\n')
        with patch.object(play.windows_audio, 'available', return_value=True), \
                patch.object(play.windows_audio, 'run') as native:
            _, execute = self.invoke()
            native.assert_not_called()
            execute.assert_called_once()

    def test_unavailable_native_output_falls_back_to_sdl(self):
        with patch.object(play.windows_audio, 'available', return_value=False), \
                patch.object(play.windows_audio, 'run') as native:
            _, execute = self.invoke()
            native.assert_not_called()
            execute.assert_called_once()

    def test_stale_receipt_is_rejected(self):
        (self.build / 'BrutalMarioDemo11SNESRecomp').write_bytes(b'changed executable')
        with patch.object(play, 'ROOT', self.root), \
                patch.object(play, 'patch_plan', return_value=[]), \
                patch('sys.argv', ['play_demo_1_1.py']):
            with self.assertRaises(SystemExit) as result:
                play.main()
        self.assertEqual(result.exception.code, 2)


if __name__ == '__main__':
    unittest.main()

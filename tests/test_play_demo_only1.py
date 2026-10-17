"""Launcher checks for isolated practice saves, menu selection and receipts."""
from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import play_demo_only1 as play


class PracticeLauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='practice-launcher-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.build = self.root / 'local/build/demo-only-1'
        self.build.mkdir(parents=True)
        self.rom = self.root / 'local/roms/demo-only-1.sfc'
        self.rom.parent.mkdir(parents=True)
        self.rom.write_bytes(b'test ROM')
        (self.build / 'BrutalMarioDemoOnly1SNESRecomp').write_bytes(b'test executable')
        (self.build / 'm1-build.json').write_text(json.dumps({
            'binary_sha256': hashlib.sha256(b'test executable').hexdigest(),
            'runtime_patches': [],
        }))
        config = self.root / 'config/demo-only-1.json'
        config.parent.mkdir()
        config.write_text(json.dumps({'target': 'test target', 'output': {
            'size': 8, 'sha256': hashlib.sha256(b'test ROM').hexdigest()}}))
        source = self.root / 'recomp/inputs/demo-only-1-boss-door.script'
        source.parent.mkdir(parents=True)
        source.write_bytes((ROOT / 'recomp/inputs/demo-only-1-boss-door.script').read_bytes())
        (self.root / 'recomp/m1-config.ini').write_text('[Sound]\nEnableAudio=1\n')
        self.config = self.build / 'config.ini'
        self.config.write_text('[Sound]\nEnableAudio=1\nAudioFreq=32000\n')
        self.save = self.build / 'ordinary.srm'
        self.save.write_bytes(b'ordinary progress')
        self.state = self.build / 'ordinary.state'
        self.state.write_bytes(b'ordinary state')

    def invoke(self, args, answers=()):
        with ExitStack() as stack:
            stack.enter_context(patch.object(play, 'ROOT', self.root))
            stack.enter_context(patch.object(play, 'patch_plan', return_value=[]))
            stack.enter_context(patch.object(sys, 'argv', ['play_demo_only1.py'] + args))
            stack.enter_context(patch('builtins.input', side_effect=answers))
            stack.enter_context(patch.dict(play.os.environ, {}, clear=False))
            chdir = stack.enter_context(patch.object(play.os, 'chdir'))
            execute = stack.enter_context(patch.object(play.os, 'execv'))
            output = stack.enter_context(redirect_stdout(io.StringIO()))
            play.main()
            self.assertEqual(self.save.read_bytes(), b'ordinary progress')
            self.assertEqual(self.state.read_bytes(), b'ordinary state')
            return chdir, execute, output.getvalue()

    def test_level_and_air_swim_use_fresh_sessions_with_explicit_config(self):
        directories = []
        for args in (['--level', 'baby-yoshi-hill'],
                     ['--level', 'baby-yoshi-hill', '--air-swim']):
            chdir, execute, output = self.invoke(args)
            directory = Path(chdir.call_args.args[0])
            directories.append(directory)
            self.assertEqual(directory.parent, self.root / 'local/play/demo-only-1/practice')
            command = execute.call_args.args[1]
            config = Path(command[command.index('--config')+1])
            self.assertEqual(config.parent, directory)
            self.assertEqual(config.read_bytes(), self.config.read_bytes())
            script = Path(command[command.index('--script')+1])
            self.assertEqual(script.parent, directory)
            content = script.read_text()
            self.assertEqual('forcepoke 85 01' in content, '--air-swim' in args)
            self.assertFalse(any(line.startswith('poke ') for line in content.splitlines()))
            self.assertTrue(content.endswith('turbo off\n'))
            self.assertIn('Baby Yoshi Hill', output)
            self.assertFalse((directory / 'ordinary.srm').exists())
        self.assertNotEqual(*directories)

    def test_ordinary_launch_preserves_executable_relative_save_paths(self):
        chdir, execute, _ = self.invoke([])
        self.assertEqual(chdir.call_args.args[0], self.build)
        command = execute.call_args.args[1]
        self.assertNotIn('--script', command)
        self.assertNotIn('--config', command)
        self.assertFalse((self.root / 'local/play').exists())

    def test_menu_retries_and_selects_a_level(self):
        chdir, execute, output = self.invoke(['--select-level'], ['99', '2'])
        command = execute.call_args.args[1]
        content = Path(command[command.index('--script')+1]).read_text()
        self.assertIn('Baby Yoshi Hill', content)
        self.assertIn('Enter a number', output)
        self.assertEqual(chdir.call_count, 1)

    def test_menu_keeps_existing_boss_route_and_swimming(self):
        _, execute, _ = self.invoke(['--select-level', '--air-swim'], ['boss-door'])
        command = execute.call_args.args[1]
        content = Path(command[command.index('--script')+1]).read_text()
        self.assertIn('poke 94 78002000', content)
        self.assertIn('forcepoke 85 01', content)

    def test_cancel_and_list_do_not_create_sessions(self):
        for args, answers in ((['--select-level'], ['q']), (['--list-levels'], ())):
            chdir, execute, _ = self.invoke(args, answers)
            chdir.assert_not_called()
            execute.assert_not_called()
            self.assertFalse((self.root / 'local/play').exists())

    def test_custom_teleport_keeps_edits_bounded_and_uses_normal_fade(self):
        _, execute, _ = self.invoke(['--teleport', '6', '0x178', '0x1a8', '--air-swim'])
        command = execute.call_args.args[1]
        content = Path(command[command.index('--script')+1]).read_text()
        pokes = {}
        for line in content.splitlines():
            if line.startswith('poke '):
                _, address, data = line.split()
                pokes[int(address, 16)] = bytes.fromhex(data)
        self.assertEqual(set(pokes), {0x1f11, 0x1f17, 0x1f1f, 0x100})
        self.assertEqual(pokes[0x1f11], bytes([6, 6]))
        self.assertEqual(pokes[0x1f17], bytes.fromhex('7801a8017801a801'))
        self.assertEqual(pokes[0x1f1f], bytes.fromhex('17001a0017001a00'))
        self.assertEqual(pokes[0x100], b'\x0b')
        self.assertIn('forcepoke 85 01', content)

    def test_custom_position_menu_accepts_hex_and_retries_bad_input(self):
        _, execute, output = self.invoke(['--select-level'], ['teleport', 'bad', '1 0x58 0x88'])
        command = execute.call_args.args[1]
        content = Path(command[command.index('--script')+1]).read_text()
        self.assertIn('poke 1f11 0101', content)
        self.assertIn('World 1 castle', output)
        self.assertIn('use decimal', output)

    def test_castle_preset_uses_requested_world1_coordinates(self):
        _, execute, _ = self.invoke(['--level', 'world1-castle'])
        command = execute.call_args.args[1]
        content = Path(command[command.index('--script')+1]).read_text()
        self.assertIn('poke 1f17 1800b8011800b801', content)
        self.assertIn('poke 1f11 0000', content)

    def test_invalid_teleport_does_not_create_session(self):
        for args in (['--teleport', '7', '0', '0'], ['--teleport', '1', '-1', '0'],
                     ['--teleport', '1', '512', '0'],
                     ['--boss-door', '--teleport', '1', '0', '0']):
            with self.subTest(args=args), self.assertRaises(SystemExit) as error:
                self.invoke(args)
            self.assertEqual(error.exception.code, 2)
            self.assertFalse((self.root / 'local/play').exists())

    def test_completion_cheat_uses_safe_level_flags_and_all_dk_bits(self):
        chdir, execute, output = self.invoke(['--complete-all', '--teleport', '6', '0x178', '0x1a8'])
        directory = Path(chdir.call_args.args[0])
        self.assertEqual(directory.parent, self.root / 'local/play/demo-only-1/practice')
        command = execute.call_args.args[1]
        content = Path(command[command.index('--script')+1]).read_text()
        pokes = {int(line.split()[1], 16): bytes.fromhex(line.split()[2])
                 for line in content.splitlines() if line.startswith('poke ')}
        flags = pokes[0x1ea2]
        self.assertEqual(len(flags), 96)
        self.assertTrue(all(flag & 0x80 for flag in flags))
        self.assertTrue(all(flag & 0x0f == 0x0f for flag in flags))
        self.assertFalse(any(flag & 0x60 for flag in flags))
        self.assertEqual(pokes[0x1f2f], bytes([255])*12)
        self.assertEqual(pokes[0x1f02], bytes([255])*15)
        self.assertEqual(pokes[0x1f27], bytes([1])*4)
        self.assertEqual(pokes[0x1182c], bytes(24))
        self.assertIn('All levels + DK coins complete: ON', output)
        self.assertEqual(pokes[0x1f11], bytes([6,6]))

    def test_menu_completion_toggle_is_optional(self):
        for args, answers, enabled in ((['--select-level'], ['c','2'], True),
                                       (['--select-level','--complete-all'], ['c','2'], False)):
            _, execute, _ = self.invoke(args, answers)
            command=execute.call_args.args[1]
            content=Path(command[command.index('--script')+1]).read_text()
            self.assertEqual('poke 1f2f ' in content, enabled)

    def test_completion_is_applied_before_boss_entry(self):
        _, execute, _ = self.invoke(['--boss-door', '--complete-all', '--air-swim'])
        command=execute.call_args.args[1]
        content=Path(command[command.index('--script')+1]).read_text()
        self.assertLess(content.index('poke 1f2f '), content.index('press y 30'))
        self.assertIn('poke 94 78002000', content)
        self.assertIn('forcepoke 85 01', content)

    def test_tampered_binary_is_rejected_before_creating_session(self):
        (self.build / 'BrutalMarioDemoOnly1SNESRecomp').write_bytes(b'changed executable')
        with self.assertRaises(SystemExit) as error:
            self.invoke(['--level', 'athletic-special'])
        self.assertEqual(error.exception.code, 2)
        self.assertFalse((self.root / 'local/play').exists())


if __name__ == '__main__':
    unittest.main()

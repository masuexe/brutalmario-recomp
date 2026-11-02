#!/usr/bin/env python3
"""Review gates for the Windows launcher that mirrors the Linux cheat switches."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import play_windows_target as windows


class WindowsLauncherTests(unittest.TestCase):
    def test_script_reuses_the_linux_cheat_encoding(self):
        text = windows.build_script(map_pos=(6, 0x128, 0x1E8))
        self.assertIn('poke 1f11 0606', text)
        self.assertIn('poke 1f17 2801e8012801e801', text)
        self.assertIn('poke 1f1f 12001e0012001e00', text)
        self.assertIn('poke 0100 0b', text)

    def test_script_room_teleport_encoding(self):
        text = windows.build_script(room=0x151)
        self.assertIn('poke 19b8 51', text)
        self.assertIn('poke 19d8 05', text)
        text = windows.build_script(room=0x0A6)
        self.assertIn('poke 19b8 a6', text)
        self.assertIn('poke 19d8 04', text)

    def test_script_persistent_cheats(self):
        text = windows.build_script(invincible=True, air_swim=True)
        self.assertIn('forcepoke 1490 40', text)
        self.assertIn('forcepoke 85 01', text)

    def test_script_lives_and_stars(self):
        text = windows.build_script(lives=50, stars=99)
        self.assertIn('poke 0dbe 32', text)
        self.assertIn('poke 0f48 63', text)

    def test_music_slot_is_added_by_the_launcher(self):
        text = windows.add_music(windows.build_script(), 0xA5)
        self.assertIn('forcepoke 0dda a5', text)
        self.assertIn('forcepoke 1dfb a5', text)
        self.assertTrue(text.endswith('turbo off\n'))

    def test_script_fast_entry_polls_mode(self):
        text = windows.build_script(room=0x190, fast=True)
        self.assertIn('turbo on', text)
        self.assertIn('until 0100 == 07', text)
        self.assertIn('turbo off', text)

    def test_script_ends_in_turbo_off(self):
        for text in (windows.build_script(), windows.build_script(invincible=True)):
            self.assertTrue(text.endswith('turbo off\n'))

    def test_digest_rewrite_requires_a_known_binary(self):
        unknown = ROOT / 'tmp' / 'not-a-binary.bin'
        unknown.parent.mkdir(parents=True, exist_ok=True)
        unknown.write_bytes(b'not an executable')
        with self.assertRaises(SystemExit):
            windows.rewrite_identity(unknown, windows.SHIPPED_ROM_SHA,
                                     '4ee6d47e0f3a6bfb5395d7531f683ab8aaedf6b29de15ab877341adbd0b71e8b',
                                     ROOT / 'tmp' / 'unused.exe')

    def test_digest_rewrite_replaces_every_site(self):
        source = ROOT / 'local/release/product-r14-event30-v2/bin/BrutalMario.exe'
        if not source.is_file():
            self.skipTest('the shipped Windows bundle is absent')
        target = ROOT / 'tmp' / 'rewrite-check.exe'
        identity = windows.rewrite_identity(
            source, windows.SHIPPED_ROM_SHA,
            '4ee6d47e0f3a6bfb5395d7531f683ab8aaedf6b29de15ab877341adbd0b71e8b', target)
        self.assertEqual(identity['binary_digest_sites'], 2)
        self.assertEqual(identity['ascii_digest_sites'], 1)
        data = target.read_bytes()
        self.assertNotIn(windows.SHIPPED_ROM_SHA.encode('ascii'), data)
        self.assertIn(b'4ee6d47e0f3a6bfb5395d7531f683ab8aaedf6b29de15ab877341adbd0b71e8b', data)


if __name__ == '__main__':
    unittest.main()

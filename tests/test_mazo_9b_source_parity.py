#!/usr/bin/env python3
"""Compare the room 190 preview state between the mazo donor and native product."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = ROOT / 'local/captures'


def state(directory, tag):
    data = (directory / (tag + '.wram.bin')).read_bytes()
    return (data[0x100], data[0x10B] | data[0x10C] << 8,
            data[0x94] | data[0x95] << 8, data[0x96] | data[0x97] << 8,
            data[0x0D85], data[0x0D8F])


@unittest.skipUnless((CAPTURES / 'mazo-9b-entry-v1-donor').exists() and
                     (CAPTURES / 'mazo-9b-entry-v1-native').exists(),
                     'requires the room 190 captures')
class Mazo9bParityTests(unittest.TestCase):
    def test_preview_state_matches(self):
        for version in ('v1', 'v2'):
            donor = CAPTURES / f'mazo-9b-entry-{version}-donor'
            native = CAPTURES / f'mazo-9b-entry-{version}-native'
            for tag in ('castle_idle', 'fight180', 'fight240', 'fight600'):
                if not (donor / f'{tag}.wram.bin').exists():
                    continue
                if not (native / f'{tag}.wram.bin').exists():
                    continue
                self.assertEqual(state(donor, tag), state(native, tag), tag)

    def test_preview_holds_full_health(self):
        donor = CAPTURES / 'mazo-9b-entry-v1-donor'
        mode, room, _x, _y, first, second = state(donor, 'castle_idle')
        self.assertEqual((mode, room, first, second), (0x14, 0x190, 64, 64))


if __name__ == '__main__':
    unittest.main()

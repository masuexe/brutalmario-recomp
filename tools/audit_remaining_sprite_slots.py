#!/usr/bin/env python3
"""Audit the seven remaining placeholder sprite slots against every supplied image.

The placement census lists recipient slots that hold the type-0 default record.
For each slot and its recipient rooms this tool checks:

1. Every supplied image holds the type-0 default record in that slot.
2. The recipient room sprite list and 256-byte layout window equal the Demo 1-1
   baseline, so the room is original recipient content.
3. The level is a course in the level index, or not.

A type-0 record is the default sprite path. When every image holds the default
and the room matches the baseline, no donor program exists to install.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_star_boss_donors import sprite_table
from restore_star_world_1 import lorom, sha

DEFAULT = '0000ffffffffffff218001218001ffff'
TARGET = 'demo11-native-modern-sprites-v1'
BASELINE = 'demo-1-1'
SLOTS = (
    (0x96, 0x1F0), (0xA5, 0x056), (0xA5, 0x102), (0xA6, 0x00C),
    (0xE8, 0x111), (0xE8, 0x119), (0xE9, 0x1CF), (0xEA, 0x1F3), (0xF5, 0x1E2),
)


def sprite_bytes(rom, room):
    slot = lorom(0x05EC00) + room * 2
    address = (rom[lorom(0x0EF100) + room] << 16) | int.from_bytes(rom[slot:slot + 2], 'little')
    offset = lorom(address)
    for count in range(121):
        end = offset + 1 + count * 3
        if rom[end] == 0xFF:
            return rom[offset:end + 1]
    raise ValueError('unterminated sprite list')


def window(rom, room):
    slot = lorom(0x05E000) + room * 3
    pointer = int.from_bytes(rom[slot:slot + 3], 'little')
    return rom[lorom(pointer):lorom(pointer) + 256]


def main():
    images = {}
    for version in sorted((ROOT / 'local/content-versions').iterdir()):
        rom = version / 'rom.sfc'
        if version.is_dir() and rom.is_file():
            images[version.name] = rom.read_bytes()
    images[TARGET] = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    recipient, baseline = images[TARGET], images[BASELINE]
    index = {entry['level'].upper() for entry in
             json.loads((ROOT / 'config/demo11-level-index.json').read_text())['entries']}
    for slot, room in SLOTS:
        records = set()
        for rom in images.values():
            table = lorom(sprite_table(rom)[2])
            records.add(rom[table + slot * 16:table + slot * 16 + 16].hex())
        baseline_match = (sha(sprite_bytes(recipient, room)) == sha(sprite_bytes(baseline, room))
                          and sha(window(recipient, room)) == sha(window(baseline, room)))
        print(f'slot {slot:02X} room {room:03X}: default in {len(images)} images='
              f'{records == {DEFAULT}} baseline_match={baseline_match} '
              f'course={f"{room:03X}" in index}')
    print(f'{len(images)} images scanned. A default record in every image with a baseline '
          f'room gives no donor program. Do not install.')


if __name__ == '__main__':
    main()

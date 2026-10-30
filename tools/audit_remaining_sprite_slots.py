#!/usr/bin/env python3
"""Scan supplied official images for the remaining placeholder sprite slots.

The census reports which recipient slots still hold the type-0 placeholder.
This tool reads the same slot numbers in every supplied image. A placeholder in
every image is only a record-level fact: sprite IDs are version-local, so a
donor program for the same room content can live in a different slot. Match
rooms and layouts before any install.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_star_boss_donors import sprite_table
from restore_star_world_1 import lorom

SLOTS = (0x96, 0xA5, 0xA6, 0xE8, 0xE9, 0xEA, 0xF5)
PLACEHOLDER = '0000ffffffffffff218001218001ffff'


def main():
    versions = sorted(p for p in (ROOT / 'local/content-versions').iterdir() if p.is_dir())
    rows = {}
    for version in versions:
        rom_path = version / 'rom.sfc'
        if not rom_path.is_file():
            continue
        rom = rom_path.read_bytes()
        table = lorom(sprite_table(rom)[2])
        found = []
        for slot in SLOTS:
            raw = rom[table + slot * 16:table + slot * 16 + 16]
            if raw.hex() != PLACEHOLDER:
                found.append({'slot': f'{slot:02X}', 'raw': raw.hex()})
        rows[version.name] = found
        print(version.name, 'non-placeholder:', found)
    missing = [name for name, found in rows.items() if not found]
    print(f'{len(rows)} images scanned, {len(missing)} hold the placeholder in every slot')
    print('Record-level only. Match room layouts before any install.')


if __name__ == '__main__':
    main()

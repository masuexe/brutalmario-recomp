#!/usr/bin/env python3
"""Inventory the custom sprite slots that recipient rooms place but the
recipient record table leaves empty.

Every entry is a slot that at least one recipient room places, whose recipient
record is the type-0 placeholder. The tool also records the newest donor record
for the same slot when a donor has one. The output is a static inventory. It
does not install a record and it does not claim behavior.
"""
import argparse
import json
from pathlib import Path

from audit_star_boss_donors import sprite_table
from prepare_rom import verify
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = '0000ffffffffffff218001218001ffff'
DONORS = ('7hero', 'cheap-demo', 'mazo')
RECIPIENT = 'demo11-native-sprite9e'


def read(path):
    return json.loads(Path(path).read_text())


def slots_of(rom):
    result = {}
    for room in range(0x200):
        pointer = (int.from_bytes(rom[lorom(0x05EC00+room*2):lorom(0x05EC00+room*2)+2], 'little') |
                   rom[lorom(0x0EF100)+room] << 16)
        try:
            offset = lorom(pointer)
            cursor = offset+1
            while rom[cursor] != 0xFF:
                entry = rom[cursor:cursor+3]
                if entry[0] & 8:
                    result.setdefault(entry[2], set()).add(room)
                cursor += 3
        except (ValueError, IndexError):
            continue
    return result


def record(rom, table, slot):
    return rom[lorom(table)+slot*16:lorom(table)+slot*16+16]


def inventory():
    versions = {v['id']: v for v in read(ROOT/'config/content-versions.json')['versions']}
    base = (ROOT/'local/restoration'/RECIPIENT/'rom.sfc').read_bytes()
    pin = read(ROOT/'config/restorations'/(RECIPIENT+'.json'))
    verify(base, pin['output'], 'recipient')
    base_table = sprite_table(base)[2]
    donors = {}
    for name in DONORS:
        body = (ROOT/'local/content-versions'/name/'rom.sfc').read_bytes()
        if name in versions:
            verify(body, versions[name]['output'], name)
        donors[name] = {'rom': body, 'table': sprite_table(body)[2]}
    used = slots_of(base)
    rows, gaps = [], []
    for slot in sorted(used):
        current = record(base, base_table, slot)
        row = {'slot': f'{slot:02X}', 'rooms': [f'{room:03X}' for room in sorted(used[slot])],
               'room_count': len(used[slot]), 'recipient_record': current.hex(),
               'recipient_placeholder': current.hex() == PLACEHOLDER, 'donors': {}}
        if row['recipient_placeholder']:
            for name, donor in donors.items():
                donor_record = record(donor['rom'], donor['table'], slot)
                row['donors'][name] = {'type': donor_record[0], 'record': donor_record.hex(),
                                       'placeholder': donor_record.hex() == PLACEHOLDER}
            gaps.append(f'{slot:02X}')
        rows.append(row)
    return {'scope': __doc__.strip(), 'recipient': RECIPIENT,
            'recipient_rom_sha256': sha(base), 'slot_count': len(rows),
            'gap_slots': gaps, 'gap_room_placements': sum(
                row['room_count'] for row in rows if row['recipient_placeholder']),
            'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-gaps.json')
    args = parser.parse_args()
    report = inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(args.output, sha(args.output.read_bytes()))
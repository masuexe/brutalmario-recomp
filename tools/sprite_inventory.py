#!/usr/bin/env python3
"""Inventory the level sprite lists of a Demo 1-1 family ROM.

The sprite data pointer table is at 05:EC00 (two byte offsets). The bank byte
for each room is in a separate 512-byte table; the inventory finds that table by
searching for a table whose room 105 bank is 0x46. Each sprite list starts with
a one-byte header, continues with three-byte records and ends with FF. The third
record byte is the sprite ID.

Use the tool to find custom sprite IDs that the Demo 1-1 table still marks as
default but an older donor defines. Those IDs are the repair candidates.
"""
import argparse
import json
from pathlib import Path

from restore_star_world_1 import lorom

ROOT = Path(__file__).resolve().parents[1]
PTR_TABLE = 0x05EC00
RECORD_TABLE = {'demo-1-1': 0x188272, 'cheap-demo': 0x8315D}
KNOWN_BANK = {0x105: 0x46}


def find_bank_table(rom):
    pointer_slot = lorom(PTR_TABLE)
    offsets = [int.from_bytes(rom[pointer_slot + room * 2:pointer_slot + room * 2 + 2],
                              'little') for room in range(512)]
    best = None
    for table in range(0, len(rom) - 512):
        if rom[table + 0x105] != 0x46:
            continue
        candidate = rom[table:table + 512]
        if sum(1 for byte in candidate if byte <= 0x7F) < 400:
            continue
        score = 0
        for room in range(512):
            bank = candidate[room]
            if bank > 0x7F:
                continue
            try:
                start = lorom((bank << 16) | 0x8000 | offsets[room])
            except ValueError:
                continue
            data = rom[start:start + 200]
            if data[:4] != b'\xff\xff\xff\xff' and 0 < data.find(b'\xff') < 200:
                score += 1
        if score > 300 and (best is None or score > best[0]):
            best = (score, table)
    return best


def sprite_list(rom, bank_table, room):
    pointer_slot = lorom(PTR_TABLE)
    offset = int.from_bytes(rom[pointer_slot + room * 2:pointer_slot + room * 2 + 2], 'little')
    bank = rom[bank_table + room]
    if bank > 0x7F:
        return None
    try:
        start = lorom((bank << 16) | 0x8000 | offset)
    except ValueError:
        return None
    end = rom.find(b'\xff', start, start + 400)
    if end < 0:
        return None
    data = rom[start:end]
    if len(data) < 1 or (len(data) - 1) % 3:
        return None
    body = data[1:]
    return [body[index + 2] for index in range(0, len(body), 3)]


def record(rom, table, sprite_id):
    if table is None:
        return None
    return rom[table + sprite_id * 16: table + sprite_id * 16 + 16]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path,
                        default=ROOT / 'local/content-versions/demo-1-1/rom.sfc')
    parser.add_argument('--donor', type=Path,
                        default=ROOT / 'local/content-versions/cheap-demo/rom.sfc')
    parser.add_argument('--donor-id', default='cheap-demo')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'local/reports/sprite-inventory.json')
    parser.add_argument('--first', type=lambda text: int(text, 0), default=0x000)
    parser.add_argument('--last', type=lambda text: int(text, 0), default=0x1FF)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    donor = args.donor.read_bytes()
    found = find_bank_table(rom)
    if found is None:
        raise SystemExit('sprite bank table not found')
    score, bank_table = found
    donor_found = find_bank_table(donor)
    donor_table = RECORD_TABLE.get(args.donor_id)
    default = bytes.fromhex('0000ffffffffffff218001218001ffff')

    rooms = {}
    usage = {}
    for room in range(args.first, args.last + 1):
        ids = sprite_list(rom, bank_table, room)
        if ids is None:
            continue
        rooms['%03X' % room] = ids
        for sprite_id in ids:
            usage[sprite_id] = usage.get(sprite_id, 0) + 1

    candidates = []
    for sprite_id in sorted(usage):
        ours = record(rom, RECORD_TABLE['demo-1-1'], sprite_id)
        theirs = record(donor, donor_table, sprite_id) if donor_table else None
        if ours is None or ours != default:
            continue
        if theirs is None or theirs == default:
            continue
        candidates.append({'id': '%02X' % sprite_id, 'rooms': usage[sprite_id],
                           'donor_record': theirs.hex()})

    report = {
        'rom': str(args.rom.relative_to(ROOT)),
        'bank_table': '%06X' % (bank_table if bank_table < 0x8000 else 0),
        'bank_table_file': '%06X' % bank_table,
        'bank_table_score': score,
        'record_table': '%06X' % RECORD_TABLE['demo-1-1'],
        'rooms_with_lists': len(rooms),
        'sprite_usage': {('%02X' % key): value for key, value in sorted(usage.items())},
        'donor': args.donor_id,
        'repair_candidates': candidates,
        'trainer_note': 'Only rooms that load are inspected; sprite lists are static data.',
        'rooms': rooms,
        'limited_by': ['three-byte record decode with a one-byte header',
                       'the bank table search is a heuristic on room 105'],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('sprite lists:', len(rooms), 'rooms; bank table score', score)
    print('used ids:', len(usage), 'repair candidates:', len(candidates))
    for candidate in candidates[:20]:
        print('  id', candidate['id'], 'rooms', candidate['rooms'])


if __name__ == '__main__':
    main()

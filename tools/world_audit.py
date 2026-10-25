#!/usr/bin/env python3
"""Audit one world of the Demo 1-1 line for content gaps.

The audit reports three gap classes from static data:

- empty extended graphics slots that a room header references,
- custom sprite records that are still the default record while a donor defines
  them and a room uses the ID,
- rooms without a level entry in the verified index.

The audit also lists the surveyed entry result for each room. Use it to order
the repairs world by world.
"""
import argparse
import json
from pathlib import Path

from restore_star_world_1 import lorom, pointer_offset
from sprite_inventory import find_bank_table, record, sprite_list

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = bytes.fromhex('0000ffffffffffff218001218001ffff')
RECORD_TABLE = 0x188272
DONORS = [
    ('7hero', 0x8315D),
    ('ra-bowser-castle', 0x8315D),
    ('ra-mario-complete', 0x8315D),
    ('mazo', 0x8315D),
    ('ow', 0x8315D),
    ('cheap-demo', 0x8315D),
    ('demo8', 0x8315D),
    ('demo7', 0x8315D),
    ('demo6', 0x8315D),
]


def load(path):
    return json.loads(Path(path).read_text())


def room_gfx_gaps(rom, room):
    base = lorom(0x14AD08) + room * 32
    header = rom[base:base + 32]
    ids = [int.from_bytes(header[offset:offset + 2], 'little')
           for offset in range(2, 20, 2)]
    missing = []
    for gfx in ids:
        if 0x100 <= gfx <= 0xFFF and rom[pointer_offset(gfx):pointer_offset(gfx) + 3] == b'\xff' * 3:
            missing.append('%03X' % gfx)
    return missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', required=True)
    parser.add_argument('--target', default='demo11-fix-batch-p')
    args = parser.parse_args()

    cfg = load(ROOT / 'config/restorations' / (args.target + '.json'))
    rom = (ROOT / 'local/restoration' / args.target / 'rom.sfc').read_bytes()
    if len(rom) != cfg['output']['size']:
        raise SystemExit('target ROM size differs from the recipe')
    world_map = load(ROOT / 'config/world-map.json')['worlds']
    if args.world not in world_map:
        raise SystemExit('unknown world')
    world = world_map[args.world]
    index = load(ROOT / 'config/demo11-level-index.json')['entries']
    by_level = {}
    for entry in index:
        by_level.setdefault(entry['level'], []).append(entry)

    found = find_bank_table(rom)
    if found is None:
        raise SystemExit('sprite bank table not found')
    bank_table = found[1]

    donor_records = {}
    for version, table in DONORS:
        path = ROOT / 'local/content-versions' / version / 'rom.sfc'
        if path.exists():
            donor_records[version] = (path.read_bytes(), table)

    gaps = {}
    for room_hex in world['rooms']:
        room = int(room_hex, 16)
        entries = by_level.get(room_hex, [])
        room_rows = {
            'translevels': [(entry['translevel'], entry['result']) for entry in entries],
            'gfx_gaps': room_gfx_gaps(rom, room),
            'sprite_gaps': [],
        }
        ids = sprite_list(rom, bank_table, room)
        if ids:
            for sprite_id in sorted(set(ids)):
                ours = record(rom, RECORD_TABLE, sprite_id)
                if ours != DEFAULT_RECORD:
                    continue
                donor = None
                for version, (donor_rom, table) in donor_records.items():
                    donor_row = record(donor_rom, table, sprite_id)
                    if donor_row is not None and donor_row != DEFAULT_RECORD:
                        donor = (version, donor_row.hex())
                        break
                if donor:
                    room_rows['sprite_gaps'].append({'id': '%02X' % sprite_id,
                                                     'rooms_used': ids.count(sprite_id),
                                                     'donor': donor[0],
                                                     'record': donor[1]})
        if room_rows['gfx_gaps'] or room_rows['sprite_gaps'] or not entries:
            gaps[room_hex] = room_rows
        else:
            gaps[room_hex] = room_rows

    report = {
        'world': args.world,
        'name': world['name'],
        'target': args.target,
        'rom_sha256': cfg['output']['sha256'],
        'rules': {
            'gfx_gap': 'empty extended graphics slot in the room header',
            'sprite_gap': 'room uses the ID, the target record is default, a donor record is not',
            'no_entry': 'no translevel in the verified level index',
        },
        'rooms': gaps,
    }
    output = ROOT / 'local/reports' / ('world-audit-%s.json' % args.world)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    gfx_rooms = sum(1 for row in gaps.values() if row['gfx_gaps'])
    sprite_ids = sorted({gap['id'] for row in gaps.values() for gap in row['sprite_gaps']})
    print(args.world, world['name'])
    print('rooms:', len(gaps), 'gfx gap rooms:', gfx_rooms, 'sprite gap IDs:', len(sprite_ids))
    for room_hex, row in gaps.items():
        print(' room', room_hex, 'translevels', row['translevels'],
              'gfx', row['gfx_gaps'], 'sprites', [gap['id'] for gap in row['sprite_gaps']])
    print('report:', output.relative_to(ROOT))


if __name__ == '__main__':
    main()

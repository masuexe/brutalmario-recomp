#!/usr/bin/env python3
"""Review the type-3 SpriteTool records C0, C1 and C2.

The tool reads the newest official demos that carry the records. It pins each
record, its protected code block, the MAIN entry stub, the module body and the
outside calls. It also lists the rooms that place the slots. The output is a
static review. It does not install the records and it does not claim behavior.
"""
import argparse
import json
from pathlib import Path

from audit_star_boss_donors import rats_blocks, sprite_table
from prepare_rom import verify
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
SLOTS = (0xC0, 0xC1, 0xC2)
DONORS = ('7hero',)
BOSS = ROOT/'local/content-versions/boss/rom.sfc'
BOSS_SHA = '337fe036f943dafb0df70bdb556e588b785c58ff019b1b00c08f77743e2b3ccd'
RECIPIENT = 'demo11-native-sprite9e'


def read(path):
    return json.loads(Path(path).read_text())


def owner(blocks, address):
    offset = lorom(address)
    for start, end in blocks:
        if start <= offset < end:
            return start, end
    return None


def record_of(rom, table, slot):
    return rom[lorom(table)+slot*16:lorom(table)+slot*16+16]


def file_address(offset):
    """Convert a file offset into the LoROM address that maps it."""
    bank = offset // 0x8000
    return (bank << 16) | (0x8000 + (offset % 0x8000))


def main_entry(rom, block, magic=b'MAIN'):
    """Find the MAIN label and the stub that follows it."""
    start, end = block
    body = rom[start:end]
    index = body.find(magic)
    if index < 0:
        raise ValueError('no MAIN label in the block')
    label = start+index
    return label, label+len(magic)


def outside_calls(block, pointers):
    start, end = block
    return pointers


def inventory(version, rom):
    constructor, body, table = sprite_table(rom)
    blocks = rats_blocks(rom)
    records = {}
    for slot in SLOTS:
        raw = record_of(rom, table, slot)
        entry = {'raw': raw.hex(), 'type': raw[0], 'pointer': f'{lorom(table)+slot*16:06X}'}
        init = int.from_bytes(raw[8:11], 'little')
        main = int.from_bytes(raw[11:14], 'little')
        init_block = owner(blocks, init)
        main_block = owner(blocks, main)
        if init_block is None or main_block is None:
            entry['status'] = 'code outside a protected block'
            records[f'{slot:02X}'] = entry
            continue
        label, stub = main_entry(rom, init_block)
        entry.update({
            'init_field': f'{init:06X}', 'main_field': f'{main:06X}',
            'block_start': f'{init_block[0]:06X}', 'block_end': f'{init_block[1]:06X}',
            'block_size': init_block[1]-init_block[0],
            'block_sha256': sha(rom[init_block[0]:init_block[1]]),
            'label': f'{label:06X}', 'stub': f'{stub:06X}',
            'label_address': f'{file_address(label):06X}',
            'stub_address': f'{file_address(stub):06X}',
            'same_block': main_block == init_block,
            'parameter_bytes': raw[14:16].hex(),
        })
        records[f'{slot:02X}'] = entry
    return {'id': version, 'rom_sha256': sha(rom),
            'constructor_address': f'{constructor:06X}', 'table_address': f'{table:06X}',
            'records': records}


def placements(rom, slot):
    rooms = []
    for room in range(0x200):
        try:
            pointer = (int.from_bytes(rom[lorom(0x05EC00+room*2):lorom(0x05EC00+room*2)+2], 'little') |
                       rom[lorom(0x0EF100)+room] << 16)
            offset = lorom(pointer)
        except (ValueError, IndexError):
            continue
        cursor = offset+1
        while rom[cursor] != 0xFF:
            entry = rom[cursor:cursor+3]
            if entry[0] & 8 and entry[2] == slot:
                rooms.append({'room': f'{room:03X}', 'raw': entry.hex(),
                              'x': entry[0] >> 4, 'y': entry[1] >> 4})
            cursor += 3
    return rooms


def room_slots(rom, room):
    """Return the custom slots that a room list places."""
    pointer = (int.from_bytes(rom[lorom(0x05EC00+room*2):lorom(0x05EC00+room*2)+2], 'little') |
               rom[lorom(0x0EF100)+room] << 16)
    offset = lorom(pointer)
    cursor, slots = offset+1, []
    while rom[cursor] != 0xFF:
        entry = rom[cursor:cursor+3]
        if entry[0] & 8:
            slots.append(entry[2])
        cursor += 3
    return slots


def dependency_table(donor, recipient, rooms):
    """Compare the custom slot records that each room needs."""
    donor_table = sprite_table(donor)[2]
    recipient_table = sprite_table(recipient)[2]
    result = {}
    for room in rooms:
        rows = []
        for slot in sorted(set(room_slots(donor, room))):
            donor_record = donor[lorom(donor_table)+slot*16:lorom(donor_table)+slot*16+16]
            recipient_record = recipient[lorom(recipient_table)+slot*16:
                                        lorom(recipient_table)+slot*16+16]
            rows.append({'slot': f'{slot:02X}', 'donor_type': donor_record[0],
                         'recipient_type': recipient_record[0],
                         'recipient_placeholder':
                             recipient_record.hex() == '0000ffffffffffff218001218001ffff'})
        result[f'{room:03X}'] = rows
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-type3.json')
    args = parser.parse_args()
    versions = {v['id']: v for v in read(ROOT/'config/content-versions.json')['versions']}
    bodies = {}
    for name in DONORS:
        rom = (ROOT/'local/content-versions'/name/'rom.sfc').read_bytes()
        verify(rom, versions[name]['output'], name)
        bodies[name] = rom
    boss = BOSS.read_bytes()
    verify(boss, {'size': len(boss), 'sha256': BOSS_SHA}, 'boss donor')
    bodies['boss'] = boss
    base = (ROOT/'local/restoration'/RECIPIENT/'rom.sfc').read_bytes()
    report = {'scope': __doc__.strip(), 'recipient': RECIPIENT,
              'donor_rom_sha256': {name: sha(rom) for name, rom in bodies.items()},
              'recipient_rom_sha256': sha(base), 'donors': {}, 'placements': {}}
    for name, rom in bodies.items():
        report['donors'][name] = inventory(name, rom)
    for slot in SLOTS:
        report['placements'][f'{slot:02X}'] = {
            'donor': placements(bodies['7hero'], slot),
            'recipient_slots': [p for p in placements(base, slot)],
            'recipient_record': record_of(base, sprite_table(base)[2], slot).hex()}
    report['room_dependencies'] = dependency_table(bodies['7hero'], base, (0x16B, 0x170))
    identical = all(report['donors']['7hero']['records'][f'{slot:02X}']['raw'] ==
                    report['donors']['boss']['records'][f'{slot:02X}']['raw'] for slot in SLOTS)
    report['donor_block_identical'] = all(
        report['donors']['7hero']['records'][f'{slot:02X}'].get('block_sha256') ==
        report['donors']['boss']['records'][f'{slot:02X}'].get('block_sha256') for slot in SLOTS)
    report['donor_records_identical'] = identical
    mismatched = [f'{slot:02X}' for slot in SLOTS
                  if report['placements'][f'{slot:02X}']['donor'] !=
                  report['placements'][f'{slot:02X}']['recipient_slots']]
    report['placement_differences'] = mismatched
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(args.output, sha(args.output.read_bytes()))
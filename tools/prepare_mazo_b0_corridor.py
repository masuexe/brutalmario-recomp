#!/usr/bin/env python3
"""Prepare the mazo B0 corridor data pack and integration plan.

The recipient has no matching corridor levels. The tool verifies four free
level slots, copies the donor level bytes and sprite lists into one A7 pack,
and writes the level, sprite, metadata and record patches. It does not build a
game target.
"""
import argparse
import json
from pathlib import Path

from audit_star_boss_donors import sprite_table
from prepare_rom import verify
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'config/native-content/mazo-b0-corridor.json'
DONOR_MANIFEST = ROOT / 'config/mazo-donor.json'
MODULE = ROOT / 'config/native-content/mazo-b0-module.json'
BASE = 'demo11-native-sprite9e'
BASE_OUTPUT = {'size': 4194304,
               'sha256': '3077bb3df00a1f26c0728deea091048be792ac1e09af9886cfdb5e36f8d05bb1'}
CUSTOM_SLOT = 0xA9
PACK_BANK = 0xA7
PACK_ADDRESS = 0xA78000
L2_SENTINEL = 0xFFDE54
MAP_ADDRESS = 0x37C008
LEVEL_TABLES = (0x05F000, 0x05F200, 0x05F400, 0x05F600, 0x05DE00, 0x0EF310)
ROOMS = ({'source': 0x00d, 'slot': 0x183}, {'source': 0x10c, 'slot': 0x184},
         {'source': 0x191, 'slot': 0x191}, {'source': 0x192, 'slot': 0x192})


def read(path):
    return json.loads(Path(path).read_text())


def pointer3(rom, offset):
    return int.from_bytes(rom[offset:offset+3], 'little')


def stream_size(rom, room):
    start = lorom(pointer3(rom, lorom(0x05E000+room*3)))
    cursor = start+5
    while cursor-start < 0x8000:
        b0, b1, b2 = rom[cursor:cursor+3]
        if b0 == 0xff:
            return 5+cursor-start+1
        number = ((b0 >> 5) & 3)*16 + (b1 >> 4)
        size = 3
        if number == 0 and b2 in (0, 2):
            size = 4 if b2 == 0 else 5
        elif number in (0x22, 0x23, 0x28):
            size = 4
        elif number == 0x2d:
            size = 5
        elif number in (0x27, 0x29):
            kind = rom[cursor+3] >> 6
            size = (5 if kind < 2 else 6 if kind == 2 else 8 if b2 & 0x80 else 7)
        cursor += size
    raise ValueError('unterminated L1 stream: room '+f'{room:03X}')


def level_bytes(rom, room):
    pointer = pointer3(rom, lorom(0x05E000+room*3))
    data = bytearray(rom[lorom(pointer):lorom(pointer)+stream_size(rom, room)])
    music = None
    if data[2] == 0x31:
        music = {'before': '31', 'after': '02'}
        data[2] = 0x02
    return pointer, bytes(data), music


def sprite_bytes(rom, room, slot):
    pointer = (int.from_bytes(rom[lorom(0x05EC00+room*2):lorom(0x05EC00+room*2)+2], 'little') |
               rom[lorom(0x0EF100)+room] << 16)
    offset = lorom(pointer)
    cursor, data = offset+1, bytearray([rom[offset]])
    while rom[cursor] != 0xff:
        entry = bytearray(rom[cursor:cursor+3])
        if entry[0] & 8 and entry[2] == 0xB0:
            entry[2] = slot
        data.extend(entry)
        cursor += 3
    return pointer, bytes(data)+b'\xff'


def layer2(rom, room):
    pointer = pointer3(rom, lorom(0x05E600+room*3))
    if pointer == L2_SENTINEL:
        return {'mode': 'sentinel', 'value': f'{L2_SENTINEL:06X}'}
    if rom[lorom(pointer)] != 0xff:
        raise ValueError('unreviewed L2 stream: room '+f'{room:03X}')
    return {'mode': 'copy', 'bytes': 'ff'}


def metadata(rom, room):
    offset = lorom(0x14AD08)+room*32
    return rom[offset:offset+32]


def exits(rom, room):
    start = lorom(pointer3(rom, lorom(0x05E000+room*3)))
    cursor, result = start+5, []
    while cursor-start < 0x8000:
        b0, b1, b2 = rom[cursor:cursor+3]
        if b0 == 0xff:
            return result
        number = ((b0 >> 5) & 3)*16 + (b1 >> 4)
        size = 3
        if number == 0 and b2 in (0, 2):
            size = 4 if b2 == 0 else 5
            result.append(int.from_bytes(rom[cursor+3:cursor+size], 'little')
                          if size == 5 else rom[cursor+3] | ((b1 & 1) << 8))
        elif number in (0x22, 0x23, 0x28):
            size = 4
        elif number == 0x2d:
            size = 5
        elif number in (0x27, 0x29):
            kind = rom[cursor+3] >> 6
            size = (5 if kind < 2 else 6 if kind == 2 else 8 if b2 & 0x80 else 7)
        cursor += size
    raise ValueError('unterminated exits: room '+f'{room:03X}')


def used_custom_ids(rom):
    used = {}
    for room in range(0x200):
        try:
            pointer = (int.from_bytes(rom[lorom(0x05EC00+room*2):lorom(0x05EC00+room*2)+2], 'little') |
                       rom[lorom(0x0EF100)+room] << 16)
            offset = lorom(pointer)
            cursor = offset+1
            while rom[cursor] != 0xff:
                entry = rom[cursor:cursor+3]
                if entry[0] & 8:
                    used[entry[2]] = used.get(entry[2], 0)+1
                cursor += 3
        except (ValueError, IndexError):
            continue
    return used


def safety(donor, base):
    used = used_custom_ids(base)
    if CUSTOM_SLOT in used:
        raise ValueError('custom slot is in use')
    constructor, body, table = sprite_table(base)
    offset = lorom(table)+CUSTOM_SLOT*16
    if base[offset:offset+16].hex() != '0000ffffffffffff218001218001ffff':
        raise ValueError('custom slot is not a placeholder')
    destinations = set()
    for room in range(0x200):
        destinations.update(exits(base, room))
    map_bytes = __import__('restore_star_world_1').lz2(base, MAP_ADDRESS, limit=0x4000)[0]
    for entry in ROOMS:
        slot = entry['slot']
        pointer = pointer3(base, lorom(0x05E000+slot*3))
        if pointer != 0x068000:
            raise ValueError('level slot is not empty: '+f'{slot:03X}')
        if slot in destinations:
            raise ValueError('level slot has an incoming exit: '+f'{slot:03X}')
        if bytes([slot & 0xff]) in map_bytes:
            raise ValueError('level slot appears in the map: '+f'{slot:03X}')
    return {'custom_slot': f'{CUSTOM_SLOT:02X}', 'slots': [f"{e['slot']:03X}" for e in ROOMS]}


def build_bytes(donor, slot):
    pack = bytearray()
    rooms = []
    for entry in ROOMS:
        source = entry['source']
        pointer, level, music = level_bytes(donor, source)
        level_offset = len(pack)
        pack.extend(level)
        sprite_pointer, sprites = sprite_bytes(donor, source, slot)
        sprite_offset = len(pack)
        pack.extend(sprites)
        l2 = layer2(donor, source)
        l2_offset = None
        if l2['mode'] == 'copy':
            l2_offset = len(pack)
            pack.extend(bytes.fromhex(l2['bytes']))
        rooms.append({'source_room': f'{source:03X}', 'target_slot': f"{entry['slot']:03X}",
                      'level': {'pointer': f'{pointer:06X}', 'size': len(level), 'sha256': sha(level),
                                'offset': level_offset, 'music': music},
                      'sprites': {'pointer': f'{sprite_pointer:06X}', 'size': len(sprites),
                                  'sha256': sha(sprites), 'offset': sprite_offset},
                      'metadata': {'raw': metadata(donor, source).hex(),
                                   'sha256': sha(metadata(donor, source))},
                      'layer2': l2})
    return bytes(pack), rooms


def donor_byte(base, source, table):
    donor = (ROOT/'local/content-versions/mazo/rom.sfc').read_bytes()
    return f'{donor[lorom(table)+source]:02x}'


def plan(base, offset, after, role):
    before = base[offset:offset+len(bytes.fromhex(after))].hex()
    return {'offset': offset, 'before': before, 'after': after, 'role': role}


def patches(base, rooms, custom_slot):
    result = []
    for room in rooms:
        slot = int(room['target_slot'], 16)
        result.append(plan(base, lorom(0x05E000+slot*3),
                           (PACK_ADDRESS+room['level']['offset']).to_bytes(3, 'little').hex(),
                           'level pointer'))
        if room['layer2']['mode'] == 'sentinel':
            result.append(plan(base, lorom(0x05E600+slot*3),
                               int(room['layer2']['value'], 16).to_bytes(3, 'little').hex(),
                               'retained empty layer 2 sentinel'))
        else:
            offset = room['level']['offset']+room['level']['size']+room['sprites']['size']
            result.append(plan(base, lorom(0x05E600+slot*3),
                               (PACK_ADDRESS+offset).to_bytes(3, 'little').hex(),
                               'layer 2 pointer'))
        sprite_address = PACK_ADDRESS+room['sprites']['offset']
        result.append(plan(base, lorom(0x05EC00+slot*2),
                           (sprite_address & 0xffff).to_bytes(2, 'little').hex(),
                           'sprite pointer low bytes'))
        result.append(plan(base, lorom(0x0EF100)+slot, f'{PACK_BANK:02x}', 'sprite pointer bank'))
        result.append(plan(base, lorom(0x14AD08)+slot*32,
                           room['metadata']['raw'], 'room graphics and palette record'))
        source = int(room['source_room'], 16)
        for table in LEVEL_TABLES:
            result.append(plan(base, lorom(table)+slot, donor_byte(base, source, table),
                               f'level table {table:06X}'))
    constructor, body, table = sprite_table(base)
    module = read(MODULE)
    record = bytearray.fromhex(module['record']['raw'])
    record[10] = 0xa2
    record[13] = 0xa2
    result.append(plan(base, lorom(table)+custom_slot*16, bytes(record).hex(),
                       'B0 record at the free slot'))
    return result


def write_recipe(donor, base):
    facts = safety(donor, base)
    pack, rooms = build_bytes(donor, CUSTOM_SLOT)
    projected = bytearray(base)
    for patch in patches(base, rooms, CUSTOM_SLOT):
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if projected[patch['offset']:patch['offset']+len(before)] != before:
            raise ValueError('patch context differs')
        projected[patch['offset']:patch['offset']+len(after)] = after
    recipe = {'schema': 1, 'id': 'mazo-b0-corridor',
              'scope': 'B0 corridor data pack and integration plan. The target build, runtime data '
                       'pack and gameplay qualification stay separate gates.',
              'donor_manifest': str(DONOR_MANIFEST.relative_to(ROOT)),
              'base_restoration': BASE, 'base_output': BASE_OUTPUT,
              'custom_slot': facts['custom_slot'],
              'data_pack': {'address': f'{PACK_ADDRESS:06X}', 'bank': f'{PACK_BANK:02X}',
                            'pack_file': 'mazo-b0-corridor.bin', 'size': len(pack),
                            'sha256': sha(pack)},
              'rooms': rooms,
              'projected_output': {'size': len(projected), 'sha256': sha(bytes(projected))},
              'open_dependencies': ['target registration and runtime data pack', 'fixture entry',
                                    'actor and room graphics qualification']}
    return recipe, pack


def build(recipe, donor, base):
    verify(base, recipe['base_output'], 'corridor base')
    facts = safety(donor, base)
    pack, rooms = build_bytes(donor, CUSTOM_SLOT)
    if rooms != recipe['rooms']:
        raise ValueError('corridor room facts differ from the review')
    if sha(pack) != recipe['data_pack']['sha256']:
        raise ValueError('corridor pack hash differs from the review')
    patch_list = patches(base, rooms, CUSTOM_SLOT)
    projected = bytearray(base)
    for patch in patch_list:
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if projected[patch['offset']:patch['offset']+len(before)] != before:
            raise ValueError('reviewed patch context differs: '+patch['role'])
        projected[patch['offset']:patch['offset']+len(after)] = after
    if sha(bytes(projected)) != recipe['projected_output']['sha256']:
        raise ValueError('projected corridor ROM differs from the review')
    return pack, patch_list, facts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / 'local/native-modules/mazo-b0-corridor-v1')
    parser.add_argument('--write-recipe', action='store_true')
    args = parser.parse_args()
    donor = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    verify(donor, read(DONOR_MANIFEST)['output'], 'mazo donor')
    if args.write_recipe:
        recipe, pack = write_recipe(donor, base)
        write_verified(RECIPE, (json.dumps(recipe, indent=2)+'\n').encode())
    else:
        recipe = read(RECIPE)
        pack, patch_list, facts = build(recipe, donor, base)
    receipt = {'scope': __doc__.strip(), 'recipe': recipe, 'data_pack_sha256': sha(pack),
               'patch_count': len(recipe.get('rooms', []))*6+1,
               'projected_output': recipe['projected_output']}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_verified(args.output_dir/'mazo-b0-corridor.bin', pack)
    write_verified(args.output_dir/'preparation-receipt.json',
                   (json.dumps(receipt, indent=2)+'\n').encode())
    print(args.output_dir/'preparation-receipt.json',
          sha((args.output_dir/'preparation-receipt.json').read_bytes()))

#!/usr/bin/env python3
"""Reserve the byte-identical vanilla T template for the official Boss ending."""
import json
from pathlib import Path

import native_seven_child as child
from audit_demo11_additions import level_pointers
from prepare_rom import verify
from restore_star_world_1 import lorom, lz2, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-seven-ending-test'
PARENT = 'demo11-native-seven-ending-stop'


def exits(rom, room):
    """Walk L1 object boundaries, including the legacy LM variable-size objects."""
    cursor = lorom(level_pointers(rom, room)['layer1']) + 5
    start = cursor
    result = []
    while cursor-start < 0x8000:
        b0, b1, b2 = rom[cursor:cursor+3]
        if b0 == 0xff:
            return result
        number = ((b0 >> 5) & 3)*16 + (b1 >> 4)
        size = 3
        if number == 0 and b2 in (0, 2):
            size = 4 if b2 == 0 else 5
            destination = rom[cursor+3] | ((b1 & 1) << 8)
            if size == 5:
                destination = int.from_bytes(rom[cursor+3:cursor+5], 'little')
            result.append((destination, bool(b1 & 2)))
        elif number in (0x22, 0x23, 0x28):
            size = 4
        elif number == 0x2d:
            size = 5
        elif number in (0x27, 0x29):
            kind = rom[cursor+3] >> 6
            size = (5 if kind < 2 else 6 if kind == 2 else 8 if b2 & 0x80 else 7)
        cursor += size
    raise ValueError(f'unterminated L1 object stream: {room:03X}')


def adapt(rom, master, donor, recipe):
    verify(rom, recipe['parent_output'], 'T-room parent ROM')
    route = recipe['ending_test']
    verify(master, route['parent_master'], 'T-room parent master')
    source, destination = level_pointers(donor, 0x174), level_pointers(rom, 0x17b)
    for name, kind in (('layout', 'layer1'), ('sprites', 'sprites')):
        pin = route[name]
        if (source[kind] != int(pin['source_address'], 16) or
                destination[kind] != int(pin['native_address'], 16)):
            raise ValueError('T-room source/template pointer differs')
        for image, address in ((donor, source[kind]), (rom, destination[kind])):
            offset = lorom(address)
            verify(image[offset:offset+pin['size']], pin, 'official T-room/template bytes')
    if source['layer2'] != 0xffde54 or destination['layer2'] != 0xffd900:
        raise ValueError('T-room background pointer differs')
    for table, count in ((0x05f000, 1), (0x05f200, 1), (0x05f400, 1),
                         (0x05f600, 1), (0x05de00, 1), (0x0ef310, 1)):
        if donor[lorom(table)+0x174:lorom(table)+0x174+count] != rom[lorom(table)+0x17b:lorom(table)+0x17b+count]:
            raise ValueError('T-room secondary header/background mode differs')
    for table, stride in ((0x14ad08, 32), (0x0ef600, 3)):
        a, b = lorom(table)+0x174*stride, lorom(table)+0x17b*stride
        if donor[a:a+stride] != rom[b:b+stride]:
            raise ValueError('T-room graphics/palette selection differs')
    pin = route['background']
    offset = lorom(int(pin['address'], 16))
    for image in (rom, donor):
        verify(image[offset:offset+pin['size']], pin, 'retained official hills background')
    level_map = route['level_map']
    decoded, _ = lz2(rom, int(level_map['address'], 16), limit=4096)
    verify(decoded, level_map['decoded'], 'current overworld level map')
    if int(level_map['unassigned_translevel'], 16) in decoded:
        raise ValueError('T-room namespace has a map assignment')
    references = [(room, dest) for room in range(512) for dest, _ in exits(rom, room) if dest == 0x17b]
    if references:
        raise ValueError('T-room namespace has an incoming screen exit')
    # These older LM images retain the original 512-entry secondary tables.
    low, flags = lorom(0x05f800), lorom(0x05fe00)
    if any(rom[low+i] == 0x7b and rom[flags+i] & 8 for i in range(512)):
        raise ValueError('T-room namespace has an incoming secondary entrance')
    out = bytearray(rom)
    if [(p['address'], p['before'], p['after']) for p in route['rom_patches']] != [
            ('6AE172', '00050074', '0005007b'), ('05EA71', '00d9ff', '54deff')]:
        raise ValueError('unreviewed T-room ROM patch')
    for patch in route['rom_patches']:
        offset = lorom(int(patch['address'], 16))
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if out[offset:offset+len(before)] != before:
            raise ValueError('T-room patch site differs')
        out[offset:offset+len(before)] = after
    before, after = bytes.fromhex(route['wrapper_before']), bytes.fromhex(route['wrapper_after'])
    if (before.hex() != '0848da5aa571c909d00822d0d81022a0f0a27afa682820ff8060' or
            after.hex() != '0848da5aa571c909f004c906d00822d0d81022a0f0a27afa682820ff8060'):
        raise ValueError('unreviewed ending font adapter')
    offset = 0x7060
    if master[offset:offset+len(after)] != before+bytes(len(after)-len(before)):
        raise ValueError('ending font adapter/padding differs')
    adapted = bytearray(master)
    adapted[offset:offset+len(after)] = after
    verify(adapted, recipe['master_payload'], 'ending font adapter output')
    return bytes(out), bytes(adapted)


def prepare():
    cfg, recipe = child.settings(TARGET)
    if cfg['base_restoration'] != PARENT or recipe['parent_target'] != PARENT:
        raise ValueError('T-room parent differs')
    source = ROOT / 'local/restoration' / PARENT
    receipt_path = source / 'input-manifest.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt['content'] != child.identity(PARENT):
        raise ValueError('T-room parent receipt differs')
    for pack in child.packs(PARENT):
        verify((source / pack['pack_file']).read_bytes(), pack, 'T-room inherited pack')
    donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
    verify(donor, json.loads((ROOT / 'config/boss-donor.json').read_text())['output'], 'official Boss source')
    rom, master = adapt((source / 'rom.sfc').read_bytes(), (source / 'seven-code.bin').read_bytes(), donor, recipe)
    verify(rom, cfg['output'], 'native T-room descendant')
    directory = ROOT / 'local/restoration' / TARGET
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'rom.sfc', rom)
    for pack in child.packs(TARGET):
        data = master if pack['variable'] == 'BM_SEVEN_CODE_PACK' else (source / pack['pack_file']).read_bytes()
        verify(data, pack, 'T-room inherited pack')
        write_verified(directory / pack['pack_file'], data)
    output = {'config': cfg, 'content': child.identity(TARGET),
              'builder_sha256': sha(Path(__file__).read_bytes()),
              'parent_receipt_sha256': sha(receipt_path.read_bytes()),
              'donor_sha256': sha(donor), 'adaptation': recipe['ending_test'],
              'scope': 'User-selected original T-room ending; no earned defeat or saved-clear claim.'}
    write_verified(directory / 'input-manifest.json', (json.dumps(output, indent=2)+'\n').encode())
    print(TARGET, sha(rom), sha(master))


if __name__ == '__main__':
    prepare()

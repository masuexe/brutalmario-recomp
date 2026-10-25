#!/usr/bin/env python3
"""Qualify the full CC lobby custom sprite batch.

The batch ports sprites 0x67, 0x68, 0x6A, 0x71 and 0x5B. It also relocates six
graphics assets that occupied their bank windows. Each relocated asset must
decode to the same pixels as before the move.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, lz2, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-cc-lobby-full'
BASE = 'demo11-sprites-cc-lobby'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
EXPECTED = {
    '67': [0xCD, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xDB, 0xDC, 0xDD, 0xDE, 0xDF, 0xE1, 0xE5, 0xE6, 0xE7],
    '68': [0xD3, 0xD4],
    '6A': [0xD8, 0xE2, 0xE3, 0xE4],
    '71': [0x3A, 0x55, 0x99, 0xC4],
    '5B': [0xC1],
}


def load(path):
    return json.loads(Path(path).read_text())


def frame_diff(old, new, first, last):
    return sum(1 for y in range(first, last) for x in range(256)
               for i in (4 * (y * 256 + x),)
               if old[i:i + 3] != new[i:i + 3])


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    require(cfg['base_restoration'] == BASE, 'base target differs')
    require(cfg['base_output']['sha256'] == base_cfg['output']['sha256'], 'base identity differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'candidate identity differs')

    require(len(cfg['relocations']) == 9, 'relocation count differs')
    placements = []
    for sprite in cfg['custom_sprites']:
        source = lorom(int(sprite['source_address'], 16))
        block = donor[source:source + sprite['block']['size']]
        placements.append((lorom(int(sprite['destination_address'], 16)), block))
    for item in cfg['relocations']:
        source = item['source_offset']
        destination = item['destination_offset']
        size = item['size']
        require(sha(base[source:source + size]) == item['sha256'], 'relocation source differs')
        require(rom[destination:destination + size].hex() == base[source:source + size].hex(),
                'relocation destination differs')
        for offset in range(size):
            value = rom[source + offset]
            if value == 0:
                continue
            inside = [(start, block) for start, block in placements
                      if start <= source + offset < start + len(block)]
            require(inside, 'unexpected byte outside a sprite block: ' + hex(source + offset))
            start, block = inside[0]
            require(block[source + offset - start] == value,
                    'sprite block byte differs: ' + hex(source + offset))
        slot = item['pointer_offset']
        require(base[slot:slot + 3].hex() == item['pointer_before'], 'relocation pointer source differs')
        require(rom[slot:slot + 3].hex() == item['pointer_after'], 'relocation pointer result differs')
        old_pointer = int.from_bytes(bytes.fromhex(item['pointer_before']), 'little')
        new_pointer = int.from_bytes(bytes.fromhex(item['pointer_after']), 'little')
        old_decoded, _ = lz2(base, old_pointer)
        new_decoded, _ = lz2(rom, new_pointer)
        require(old_decoded == new_decoded, 'relocated graphics decode differently')

    require(len(cfg['custom_sprites']) == 5, 'sprite count differs')
    for sprite in cfg['custom_sprites']:
        sprite_id = int(sprite['id'], 16)
        require(sprite['rooms'] == EXPECTED[sprite['id']], 'room set differs for ' + sprite['id'])
        require(sprite_rooms(base, sprite_id) == EXPECTED[sprite['id']], 'base rooms differ for ' + sprite['id'])
        slot = RECORD_TABLE + sprite_id * 16
        require(base[slot:slot + 16] == DEFAULT, 'base record was not default')
        require(rom[slot:slot + 16].hex() == sprite['record_after'], 'installed record differs')
        source = lorom(int(sprite['source_address'], 16))
        block = donor[source:source + sprite['block']['size']]
        require(sha(block) == sprite['block']['sha256'], 'donor block differs')
        destination = lorom(int(sprite['destination_address'], 16))
        require(rom[destination:destination + len(block)] == block, 'installed block differs')

    checks = [
        (0xD3, 'later', '68'),
        (0xD8, 'later', '67/6A'),
        (0xC4, 'later', '71'),
        (0xC1, 'active', '5B'),
    ]
    for room, dump, label in checks:
        old_directory = ROOT / 'local/captures' / ('lobbyfull-%02X-base' % room)
        new_directory = ROOT / 'local/captures' / ('lobbyfull-%02X-full' % room)
        for name, directory in (('base', old_directory), ('full', new_directory)):
            body = (directory / 'active.wram.bin').read_bytes()
            require(body[0x100] in (0x12, 0x14), name + ' capture does not reach gameplay')
            require(int.from_bytes(body[0x10B:0x10D], 'little') == room,
                    name + ' capture is not room ' + hex(room))
        old = (old_directory / (dump + '.fb.bgrx')).read_bytes()
        new = (new_directory / (dump + '.fb.bgrx')).read_bytes()
        require(frame_diff(old, new, 24, 224) > 0,
                'room ' + hex(room) + ' frame did not change for ' + label)
        require(frame_diff(old, new, 0, 24) == 0, 'room ' + hex(room) + ' HUD changed')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Full CC lobby sprite checks passed: 5 sprites, 9 relocations, HUD unchanged')


if __name__ == '__main__':
    main()

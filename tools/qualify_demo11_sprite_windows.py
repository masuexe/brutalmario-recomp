#!/usr/bin/env python3
"""Qualify the sprite window relocation batch.

The batch moves the Star World graphics blocks out of bank 3F and uses the
freed aligned windows for five more custom sprites. The qualifier checks the
chain identity, every relocation and pointer, every sprite record and block,
the transparent Star World rendering, the affected level captures and the
native build identity.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprite-windows'
BASE = 'demo11-sprites-cheap-demo'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
LEVELS = ('041', '039', '01E', '054', '047', '004', '009')
STAR_FRAMES = ('004', '009')


def load(path):
    return json.loads(Path(path).read_text())


def rgb5_different(left, right, width=256, height=224):
    expected = width * height * 4
    return sum(any(left[i + k] >> 3 != right[i + k] >> 3 for k in range(3))
               for i in range(0, expected, 4))


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    require(cfg['base_restoration'] == BASE, 'base target differs')
    require(cfg['base_output']['sha256'] == base_cfg['output']['sha256'],
            'base identity differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'candidate identity differs')
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()

    # The released ranges now hold the new sprite blocks, so only the bytes
    # outside those blocks must stay zero.
    sprite_ranges = []
    for sprite in cfg['custom_sprites']:
        start = lorom(int(sprite['destination_address'], 16))
        sprite_ranges.append((start, start + sprite['block']['size']))
    for item in cfg['relocations']:
        source = item['source_offset']
        destination = item['destination_offset']
        size = item['size']
        block = base[source:source + size]
        require(sha(block) == item['sha256'], 'relocated block source changed')
        require(rom[destination:destination + size] == block,
                'relocated block differs: ' + hex(destination))
        slot = item['pointer_offset']
        require(rom[slot:slot + 3].hex() == item['pointer_after'],
                'relocated pointer differs: ' + hex(slot))
        for index in range(source, source + size):
            if rom[index] == 0:
                continue
            inside = any(start <= index < end for start, end in sprite_ranges)
            require(inside, 'nonzero byte outside a sprite block: ' + hex(index))

    for sprite in cfg['custom_sprites']:
        sprite_id = int(sprite['id'], 16)
        slot = RECORD_TABLE + sprite_id * 16
        require(base[slot:slot + 16] == DEFAULT, 'base record was not default')
        require(rom[slot:slot + 16].hex() == sprite['record_after'],
                'installed record differs: ' + sprite['id'])
        source = lorom(int(sprite['source_address'], 16))
        destination = lorom(int(sprite['destination_address'], 16))
        block = donor[source:source + sprite['block']['size']]
        require(sha(block) == sprite['block']['sha256'],
                'donor block differs: ' + sprite['id'])
        require(rom[destination:destination + sprite['block']['size']] == block,
                'installed block differs: ' + sprite['id'])
        require(sprite_rooms(base, sprite_id) == sprite['rooms'],
                'room dependencies differ: ' + sprite['id'])
        for item in sprite['shared_dependencies']:
            offset = lorom(int(item['address'], 16))
            for data in (rom, donor):
                require(sha(data[offset:offset + item['size']]) == item['sha256'],
                        'shared dependency differs: ' + item['address'])
    require(len(cfg['custom_sprites']) == 5, 'sprite count differs')
    require(len(cfg['relocations']) == 16, 'relocation count differs')

    for translevel in STAR_FRAMES:
        for index in range(8):
            name = 'd%02d.fb.bgrx' % index
            left = (ROOT / 'local/captures' / ('winbase-' + translevel) / name).read_bytes()
            right = (ROOT / 'local/captures' / ('winnew-' + translevel) / name).read_bytes()
            require(rgb5_different(left, right) == 0,
                    'Star World rendering changed: ' + translevel + '/' + name)

    for translevel in LEVELS:
        directory = ROOT / 'local/captures' / ('winprobe-' + translevel)
        if not directory.exists():
            continue
        body = (directory / 'entry600.wram.bin').read_bytes()
        require(body[0x100] == 0x14, 'level does not stay in gameplay: ' + translevel)
        receipt = load(directory / 'receipt.json')
        require(receipt['rom_sha256'] == cfg['output']['sha256'],
                'capture ROM differs: ' + translevel)

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Sprite window batch checks passed: 16 relocations, 5 sprites, Star World unchanged')


if __name__ == '__main__':
    main()

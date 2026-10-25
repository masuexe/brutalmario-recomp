#!/usr/bin/env python3
"""Qualify the first blocked placed custom sprite batch.

The batch ports twelve placed custom sprites whose bank windows held graphics
assets. It moves thirteen graphics assets with reviewed pointer patches. Sampled
rooms must change and keep an identical HUD.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, lz2, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-blocked-one'
BASE = 'demo11-sprites-free-two'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
EXPECTED = ['1E', '1F', '21', '42', '52', '62', '6F', '72', '87', '8C', '8E', '8F']
ROOMS = {0x8F: '68', 0x95: '87', 0xB0: '8C/8E/8F', 0x1D: '62'}


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
    installed = [sprite['id'] for sprite in cfg['custom_sprites']]
    require(installed == EXPECTED, 'sprite list differs: ' + repr(installed))
    require(len(cfg['relocations']) == 13, 'relocation count differs')
    placements = []
    for sprite in cfg['custom_sprites']:
        sprite_id = int(sprite['id'], 16)
        require(sprite_rooms(base, sprite_id) == sprite['rooms'],
                'base room dependencies differ: ' + sprite['id'])
        slot = RECORD_TABLE + sprite_id * 16
        require(base[slot:slot + 16] == DEFAULT, 'base record was not default: ' + sprite['id'])
        require(rom[slot:slot + 16].hex() == sprite['record_after'],
                'installed record differs: ' + sprite['id'])
        source = lorom(int(sprite['source_address'], 16))
        block = donor[source:source + sprite['block']['size']]
        require(sha(block) == sprite['block']['sha256'], 'donor block differs: ' + sprite['id'])
        destination = lorom(int(sprite['destination_address'], 16))
        require(rom[destination:destination + len(block)] == block,
                'installed block differs: ' + sprite['id'])
        placements.append((destination, block))
    for item in cfg['relocations']:
        source_offset = item['source_offset']
        size = item['size']
        require(sha(base[source_offset:source_offset + size]) == item['sha256'],
                'relocation source differs')
        require(rom[item['destination_offset']:item['destination_offset'] + size].hex() ==
                base[source_offset:source_offset + size].hex(), 'relocation destination differs')
        for offset in range(size):
            value = rom[source_offset + offset]
            if value == 0:
                continue
            inside = [(start, data) for start, data in placements
                      if start <= source_offset + offset < start + len(data)]
            require(inside, 'unexpected byte outside a sprite block: ' + hex(source_offset + offset))
            start, data = inside[0]
            require(data[source_offset + offset - start] == value,
                    'sprite block byte differs: ' + hex(source_offset + offset))
        pointer_slot = item['pointer_offset']
        require(base[pointer_slot:pointer_slot + 3].hex() == item['pointer_before'],
                'relocation pointer source differs')
        require(rom[pointer_slot:pointer_slot + 3].hex() == item['pointer_after'],
                'relocation pointer result differs')
        old_pointer = int.from_bytes(bytes.fromhex(item['pointer_before']), 'little')
        new_pointer = int.from_bytes(bytes.fromhex(item['pointer_after']), 'little')
        require(lz2(base, old_pointer)[0] == lz2(rom, new_pointer)[0],
                'relocated graphics decode differently')

    for room in ROOMS:
        old = ROOT / 'local/captures' / ('blk1-%02X-base' % room)
        new = ROOT / 'local/captures' / ('blk1-%02X-fixed' % room)
        for name, directory in (('base', old), ('fixed', new)):
            body = (directory / 'active.wram.bin').read_bytes()
            require(body[0x100] == 0x14, name + ' capture does not reach gameplay')
            require(int.from_bytes(body[0x10B:0x10D], 'little') == room,
                    name + ' capture is not room ' + hex(room))
        old_fb = (old / 'active.fb.bgrx').read_bytes()
        new_fb = (new / 'active.fb.bgrx').read_bytes()
        require(frame_diff(old_fb, new_fb, 24, 224) > 0,
                'room ' + hex(room) + ' frame did not change')
        require(frame_diff(old_fb, new_fb, 0, 24) == 0,
                'room ' + hex(room) + ' HUD changed')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Blocked sprite batch one passed: 12 sprites, 13 relocations, 4 sampled rooms change')


if __name__ == '__main__':
    main()

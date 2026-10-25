#!/usr/bin/env python3
"""Qualify the custom fire projectile sprite 0x56.

Room 0xCC spawns custom sprite 0x56 at run time. The recipient record was the
default, so the fire breath had sound only. The batch ports the cheap-demo
record with two graphics relocations. The projectile must move on screen and
follow the cheap-demo path.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, lz2, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-fireball'
BASE = 'demo11-hp-roomcf'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')


def load(path):
    return json.loads(Path(path).read_text())


def sprite_positions(directory, count):
    positions = []
    for step in range(count):
        body = (directory / ('d%03d.wram.bin' % step)).read_bytes()
        for slot in range(12):
            if body[0x1AB9E + slot] == 0x56:
                x = body[0xE4 + slot] | (body[0x14E0 + slot] << 8)
                y = body[0xD8 + slot] | (body[0x14D4 + slot] << 8)
                positions.append((step, x, y, body[0x14C8 + slot]))
    return positions


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
    require(len(cfg['relocations']) == 2, 'relocation count differs')
    sprite = cfg['custom_sprites'][0]
    require(sprite['id'] == '56', 'sprite id differs')
    sprite_id = 0x56
    require(sprite['rooms'] == [0xB7], 'room set differs: ' + repr(sprite['rooms']))
    require(sprite_rooms(base, sprite_id) == [0xB7], 'base room dependencies differ')
    slot = RECORD_TABLE + sprite_id * 16
    require(base[slot:slot + 16] == DEFAULT, 'base record was not default')
    require(rom[slot:slot + 16].hex() == sprite['record_after'], 'installed record differs')
    source = lorom(int(sprite['source_address'], 16))
    block = donor[source:source + sprite['block']['size']]
    require(sha(block) == sprite['block']['sha256'], 'donor block differs')
    destination = lorom(int(sprite['destination_address'], 16))
    require(rom[destination:destination + len(block)] == block, 'installed block differs')
    placements = [(destination, block)]
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
            require(inside, 'unexpected byte outside the sprite block: ' + hex(source_offset + offset))
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

    old = ROOT / 'local/captures' / 'cc-fight-base'
    new = ROOT / 'local/captures' / 'cc-fight-fixed'
    for name, directory in (('base', old), ('fixed', new)):
        body = (directory / 'd000.wram.bin').read_bytes()
        require(body[0x100] == 0x14, name + ' capture does not reach gameplay')
        require(int.from_bytes(body[0x10B:0x10D], 'little') == 0x0CC, name + ' capture is not room 0xCC')
    base_positions = sprite_positions(old, 8)
    fixed_positions = sprite_positions(new, 13)
    require(base_positions, 'base did not spawn sprite 0x56')
    require(len({position[1] for position in base_positions}) == 1,
            'base sprite 0x56 moved; the control changed')
    moves = {position[1] for position in fixed_positions}
    require(len(moves) >= 4, 'fixed sprite 0x56 does not move on screen')
    old_fb = (old / 'd012.fb.bgrx').read_bytes()
    new_fb = (new / 'd012.fb.bgrx').read_bytes()
    require(frame_diff(old_fb, new_fb, 24, 224) > 0, 'gameplay frame did not change')
    require(frame_diff(old_fb, new_fb, 0, 24) == 0, 'HUD changed')
    cheap = ROOT / 'local/captures' / 'cheap-cc-fight'
    cheap_positions = sprite_positions(cheap, 13)
    require(cheap_positions, 'cheap-demo did not spawn sprite 0x56')
    for step, x, y, _ in fixed_positions[:5]:
        matches = [(cx, cy) for cstep, cx, cy, _ in cheap_positions if cstep == step]
        require(matches, 'cheap-demo has no sample at frame ' + str(step))
        cx, cy = matches[0]
        require(abs(cx - x) <= 12 and abs(cy - y) <= 12,
                'fire projectile path differs at frame ' + str(step))

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Fire projectile checks passed: sprite 0x56 moves and matches cheap-demo')


if __name__ == '__main__':
    main()

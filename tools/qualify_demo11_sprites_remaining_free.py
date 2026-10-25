#!/usr/bin/env python3
"""Qualify the remaining free-window custom sprite batch.

The batch ports fifteen sprites whose donor code fits a reviewed free window.
Some sampled rooms stay unchanged because the sprite is idle or off screen.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-remaining-free'
BASE = 'demo11-sprites-cc-lobby-full'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
EXPECTED_SPRITES = ['1A', '27', '3D', '4F', '51', '53', '5C', '6B', '6D', '70',
                    '73', '77', '7B', '7D', '8B']


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
    require(installed == EXPECTED_SPRITES, 'sprite list differs: ' + repr(installed))
    for sprite in cfg['custom_sprites']:
        sprite_id = int(sprite['id'], 16)
        require(sprite['rooms'], 'sprite has no rooms: ' + sprite['id'])
        require(sprite_rooms(base, sprite_id) == sprite['rooms'], 'room set differs: ' + sprite['id'])
        slot = RECORD_TABLE + sprite_id * 16
        require(base[slot:slot + 16] == DEFAULT, 'base record was not default: ' + sprite['id'])
        require(rom[slot:slot + 16].hex() == sprite['record_after'], 'installed record differs: ' + sprite['id'])
        source = lorom(int(sprite['source_address'], 16))
        block = donor[source:source + sprite['block']['size']]
        require(sha(block) == sprite['block']['sha256'], 'donor block differs: ' + sprite['id'])
        destination = lorom(int(sprite['destination_address'], 16))
        require(rom[destination:destination + len(block)] == block, 'installed block differs: ' + sprite['id'])

    checks = [
        (0x89, 'later', True),
        (0x62, 'later', True),
        (0x96, 'active', True),
        (0x7C, 'later', False),
    ]
    for room, dump, hud_must_match in checks:
        old_directory = ROOT / 'local/captures' / ('remfree-%02X-base' % room)
        new_directory = ROOT / 'local/captures' / ('remfree-%02X-free' % room)
        for name, directory in (('base', old_directory), ('free', new_directory)):
            body = (directory / 'active.wram.bin').read_bytes()
            require(body[0x100] == 0x14, name + ' capture does not reach gameplay')
            require(int.from_bytes(body[0x10B:0x10D], 'little') == room,
                    name + ' capture is not room ' + hex(room))
        old = (old_directory / (dump + '.fb.bgrx')).read_bytes()
        new = (new_directory / (dump + '.fb.bgrx')).read_bytes()
        require(frame_diff(old, new, 24, 224) > 0, 'room ' + hex(room) + ' frame did not change')
        if hud_must_match:
            require(frame_diff(old, new, 0, 24) == 0, 'room ' + hex(room) + ' HUD changed')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Remaining free sprite checks passed: 15 sprites, 4 sampled rooms change')


if __name__ == '__main__':
    main()

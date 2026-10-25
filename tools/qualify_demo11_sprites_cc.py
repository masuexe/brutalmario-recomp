#!/usr/bin/env python3
"""Qualify the CC boss-room custom sprite batch.

Rooms 0xCC, 0xCF, 0xD0, 0xD1, 0xD2 and 0xD5 place custom sprites 0x63 and 0x65
with the default record. The batch ports the cheap-demo records and code blocks.
The HP bar display belongs to the parent HP-bar recipe and must not change.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-cc'
BASE = 'demo11-hp-bars'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
EXPECTED_ROOMS = {'63': [0xCC, 0xCF, 0xD0, 0xD1],
                 '65': [0xCC, 0xCF, 0xD0, 0xD1, 0xD2, 0xD5, 0xD6, 0xDB]}


def load(path):
    return json.loads(Path(path).read_text())


def sprite_ids(body):
    out = {}
    for slot in range(12):
        custom = body[0x1AB9E + slot]
        if custom:
            out['%02X' % custom] = body[0x14C8 + slot]
    return out


def hud_equal(left, right):
    return all(left[i:i + 3] == right[i:i + 3]
               for pixel in range(256 * 24) for i in (pixel * 4,))


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    require(cfg['base_restoration'] == BASE, 'base target differs')
    require(cfg['base_output']['sha256'] == base_cfg['output']['sha256'], 'base identity differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'candidate identity differs')
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    require(len(cfg['custom_sprites']) == 2, 'sprite count differs')
    for sprite in cfg['custom_sprites']:
        sprite_id = int(sprite['id'], 16)
        slot = RECORD_TABLE + sprite_id * 16
        require(base[slot:slot + 16] == DEFAULT, 'base record was not default')
        require(rom[slot:slot + 16].hex() == sprite['record_after'], 'installed record differs')
        source = lorom(int(sprite['source_address'], 16))
        block = donor[source:source + sprite['block']['size']]
        require(sha(block) == sprite['block']['sha256'], 'donor block differs')
        destination = lorom(int(sprite['destination_address'], 16))
        require(rom[destination:destination + len(block)] == block, 'installed block differs')
        require(sprite_rooms(base, sprite_id) == sprite['rooms'], 'room dependencies differ')
        require(sprite['rooms'] == EXPECTED_ROOMS[sprite['id']], 'room set differs')
        for item in sprite['shared_dependencies']:
            offset = lorom(int(item['address'], 16))
            for data in (rom, donor):
                require(sha(data[offset:offset + item['size']]) == item['sha256'],
                        'shared dependency differs: ' + item['address'])

    old = ROOT / 'local/captures' / 'cc2-base'
    new = ROOT / 'local/captures' / 'cc2-final'
    for name, directory in (('base', old), ('final', new)):
        body = (directory / 'active.wram.bin').read_bytes()
        require(body[0x100] == 0x14, name + ' capture does not reach gameplay')
        require(int.from_bytes(body[0x10B:0x10D], 'little') == 0x0CC, name + ' capture is not room CC')
    old_later = (old / 'later.wram.bin').read_bytes()
    new_later = (new / 'later.wram.bin').read_bytes()
    old_sprites = sprite_ids(old_later)
    new_sprites = sprite_ids(new_later)
    require(old_sprites.get('63', 0) == 0 and old_sprites.get('65', 0) == 0,
            'base still runs sprites 63 and 65')
    require(new_sprites.get('63', 0) != 0 and new_sprites.get('65', 0) != 0,
            'final does not keep sprites 63 and 65 active')
    old_fb = (old / 'active.fb.bgrx').read_bytes()
    new_fb = (new / 'active.fb.bgrx').read_bytes()
    require(hud_equal(old_fb, new_fb), 'HP HUD region changed')
    differ = sum(1 for pixel in range(256 * 224)
                 for i in (pixel * 4,)
                 if old_fb[i:i + 3] != new_fb[i:i + 3])
    require(differ > 0, 'second room frame is identical; sprite has no visible effect')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('CC custom sprite checks passed: sprites 63 and 65 active, HUD unchanged')


if __name__ == '__main__':
    main()

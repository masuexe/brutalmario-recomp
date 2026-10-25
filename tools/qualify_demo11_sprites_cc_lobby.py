#!/usr/bin/env python3
"""Qualify the CC lobby custom sprite 0x69 port.

Rooms 0xD6, 0xDA, 0xDB, 0xE0, 0xE2 and 0x155 place custom sprite 0x69 with the
default record. The batch ports the cheap-demo block. The room frame must change
and the HUD must stay identical.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-cc-lobby'
BASE = 'demo11-hp-room146'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
EXPECTED_ROOMS = [0xD6, 0xDA, 0xDB, 0xE0, 0xE2, 0x155]


def load(path):
    return json.loads(Path(path).read_text())


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    require(cfg['base_restoration'] == BASE, 'base target differs')
    require(cfg['base_output']['sha256'] == base_cfg['output']['sha256'], 'base identity differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'candidate identity differs')
    require(len(cfg['custom_sprites']) == 1, 'sprite count differs')
    sprite = cfg['custom_sprites'][0]
    sprite_id = int(sprite['id'], 16)
    require(sprite['rooms'] == EXPECTED_ROOMS, 'room set differs: ' + repr(sprite['rooms']))
    require(sprite_rooms(base, sprite_id) == EXPECTED_ROOMS, 'base room dependencies differ')
    slot = RECORD_TABLE + sprite_id * 16
    require(base[slot:slot + 16] == DEFAULT, 'base record was not default')
    require(rom[slot:slot + 16].hex() == sprite['record_after'], 'installed record differs')
    source = lorom(int(sprite['source_address'], 16))
    block = donor[source:source + sprite['block']['size']]
    require(sha(block) == sprite['block']['sha256'], 'donor block differs')
    destination = lorom(int(sprite['destination_address'], 16))
    require(rom[destination:destination + len(block)] == block, 'installed block differs')
    for item in sprite['shared_dependencies']:
        offset = lorom(int(item['address'], 16))
        for data in (rom, donor):
            require(sha(data[offset:offset + item['size']]) == item['sha256'],
                    'shared dependency differs: ' + item['address'])

    old = ROOT / 'local/captures' / 'lobby-DA-base'
    new = ROOT / 'local/captures' / 'lobby-DA-fixed'
    for name, directory in (('base', old), ('fixed', new)):
        body = (directory / 'active.wram.bin').read_bytes()
        require(body[0x100] == 0x14, name + ' capture does not reach gameplay')
        require(int.from_bytes(body[0x10B:0x10D], 'little') == 0x0DA, name + ' capture is not room 0xDA')
        found = {'%02X' % body[0x1AB9E + slot_] for slot_ in range(12)}
        require('69' in found, name + ' did not spawn sprite 0x69')
    old_fb = (old / 'later.fb.bgrx').read_bytes()
    new_fb = (new / 'later.fb.bgrx').read_bytes()
    field_diff = sum(1 for y in range(24, 224) for x in range(256)
                     for i in (4 * (y * 256 + x),)
                     if old_fb[i:i + 3] != new_fb[i:i + 3])
    hud_diff = sum(1 for y in range(24) for x in range(256)
                   for i in (4 * (y * 256 + x),)
                   if old_fb[i:i + 3] != new_fb[i:i + 3])
    require(field_diff > 0, 'room frame did not change')
    require(hud_diff == 0, 'HUD changed')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('CC lobby sprite checks passed: sprite 0x69 active, HUD unchanged')


if __name__ == '__main__':
    main()

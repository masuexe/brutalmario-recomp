#!/usr/bin/env python3
"""Qualify the room 049 custom sprite port.

The big door of level 0x109 leads to room 049. That room places custom sprite
0x48, and the target record was still the default record. The batch ports the
cheap-demo record.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprite-room49'
BASE = 'demo11-boss-music-retarget'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')


def load(path):
    return json.loads(Path(path).read_text())


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
    require(len(cfg['custom_sprites']) == 1, 'sprite count differs')
    sprite = cfg['custom_sprites'][0]
    require(sprite['id'] == '48', 'sprite id differs')
    slot = RECORD_TABLE + 0x48 * 16
    require(base[slot:slot + 16] == DEFAULT, 'base record was not default')
    require(rom[slot:slot + 16].hex() == sprite['record_after'],
            'installed record differs')
    source = lorom(int(sprite['source_address'], 16))
    destination = lorom(int(sprite['destination_address'], 16))
    block = donor[source:source + sprite['block']['size']]
    require(sha(block) == sprite['block']['sha256'], 'donor block differs')
    require(rom[destination:destination + sprite['block']['size']] == block,
            'installed block differs')
    require(sprite_rooms(base, 0x48) == sprite['rooms'], 'room dependencies differ')
    require(sprite['rooms'] == [0x49], 'sprite is not placed in room 049')
    header = lorom(0x14AD08) + 0x49 * 32
    require(int.from_bytes(rom[header:header + 2], 'little') & 0x8000,
            'room 049 header is not valid')
    for item in sprite['shared_dependencies']:
        offset = lorom(int(item['address'], 16))
        for data in (rom, donor):
            require(sha(data[offset:offset + item['size']]) == item['sha256'],
                    'shared dependency differs: ' + item['address'])
    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Room 049 custom sprite checks passed: record 48 installed')


if __name__ == '__main__':
    main()

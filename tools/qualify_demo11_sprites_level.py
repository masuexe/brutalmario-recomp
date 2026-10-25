#!/usr/bin/env python3
"""Qualify the level-room custom sprite batch.

The batch ports six cheap-demo sprite records that level rooms still missed. A
seventh record from 7hero was dropped because it crashes level 094.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-level1'
BASE = 'demo11-gfx-global13'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
LEVELS = ('012', '097', '062', '05E')


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
    require(len(cfg['custom_sprites']) == 6, 'sprite count differs')
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
    for translevel in LEVELS:
        directory = ROOT / 'local/captures' / ('ls-' + translevel)
        if not directory.exists():
            continue
        body = (directory / 'entry240.wram.bin').read_bytes()
        require(body[0x100] == 0x14, 'level does not stay in gameplay: ' + translevel)
    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Level custom sprite batch checks passed: 6 sprites')


if __name__ == '__main__':
    main()

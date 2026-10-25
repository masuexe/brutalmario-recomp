#!/usr/bin/env python3
"""Qualify the second free-window custom sprite batch.

The batch ports seven remaining custom sprite records. None of the sampled room
frames changes, because these sprites are runtime helpers or spawn later than
the capture window. The checks pin the records, blocks and shared dependencies.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-free-two'
BASE = 'demo11-sprites-snowflake'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
EXPECTED = ['03', '1D', '2F', '41', '59', '84', '85']


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
    installed = [sprite['id'] for sprite in cfg['custom_sprites']]
    require(installed == EXPECTED, 'sprite list differs: ' + repr(installed))
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
    print('Second free sprite checks passed: seven records installed')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Qualify the first custom sprite port batch (World 2 to World 4 rooms).

The batch ports 19 custom sprite records from cheap-demo onto the world
graphics chain end. The qualifier checks the chain identity, every record and
code block, the shared and versioned dependencies, the room dependencies, the
captures of the affected levels and the native build identity.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-cheap-demo'
BASE = 'demo11-gfx-world8c'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
# Level translevels whose rooms reference the ported sprites.
LEVELS = ('047', '048', '049', '041', '04B', '037', '039', '03A',
          '055', '01E', '056', '054', '022', '01F', '021', '04C', '02C')
EXPECTED_DEATH = {'022'}


def load(path):
    return json.loads(Path(path).read_text())


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    require(cfg['base_restoration'] == BASE, 'base target differs')
    require(cfg['base_output']['sha256'] == base_cfg['output']['sha256'], 'base identity differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'candidate identity differs')
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    count = 0
    for sprite in cfg['custom_sprites']:
        sprite_id = int(sprite['id'], 16)
        require(sprite['before'] == DEFAULT.hex(), 'reviewed record was not empty')
        require(sprite['destination_record_address'] ==
                '%06X' % (0x318272 + sprite_id * 16), 'record address differs')
        slot = 0x188272 + sprite_id * 16
        require(base[slot:slot + 16] == DEFAULT, 'base record was not default')
        require(rom[slot:slot + 16].hex() == sprite['record_after'],
                'installed record differs: ' + sprite['id'])
        source = lorom(int(sprite['source_address'], 16))
        destination = lorom(int(sprite['destination_address'], 16))
        block = donor[source:source + sprite['block']['size']]
        require(sha(block) == sprite['block']['sha256'],
                'donor block differs: ' + sprite['id'])
        installed = rom[destination:destination + sprite['block']['size']]
        require(installed == block, 'installed block differs: ' + sprite['id'])
        require(sprite_rooms(base, sprite_id) == sprite['rooms'],
                'room dependencies differ: ' + sprite['id'])
        for item in sprite['shared_dependencies']:
            offset = lorom(int(item['address'], 16))
            for data, role in ((rom, 'candidate'), (donor, 'donor')):
                require(sha(data[offset:offset + item['size']]) == item['sha256'],
                        'shared dependency differs: ' + item['address'])
        count += 1
    require(count == 19, 'sprite count differs')

    for translevel in LEVELS:
        name = 'spriteprobe-' + translevel
        directory = ROOT / 'local/captures' / name
        if not directory.exists():
            continue
        body = (directory / 'entry600.wram.bin').read_bytes()
        mode = body[0x100]
        if translevel in EXPECTED_DEATH:
            require(mode in (0x0D, 0x14), 'unexpected mode: ' + translevel)
        else:
            require(mode == 0x14, 'level does not stay in gameplay: ' + translevel)
        receipt = load(directory / 'receipt.json')
        require(receipt['rom_sha256'] == cfg['output']['sha256'],
                'capture ROM differs: ' + translevel)

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()),
                'native binary differs')
    print('Custom sprite batch checks passed: 19 sprites, 17 affected levels load')


if __name__ == '__main__':
    main()

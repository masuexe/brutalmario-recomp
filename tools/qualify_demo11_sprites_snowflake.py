#!/usr/bin/env python3
"""Qualify the custom snow projectile sprite 0x5A.

The dragon spawn code in sprite 0x63 can spawn custom sprite 0x5A. The chain
record was the default, so that attack had no projectile. The batch ports the
cheap-demo record. A reviewed fixture places 0x5A in room 0xCC and the capture
must show it move on screen.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, lz2, sprite_rooms

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-snowflake'
BASE = 'demo11-sprites-fireball'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')


def load(path):
    return json.loads(Path(path).read_text())


def room_list(fixture):
    word = lorom(0x05EC00) + 0xCC * 2
    address = int.from_bytes(fixture[word:word + 2], 'little') | fixture[lorom(0x0EF100) + 0xCC] << 16
    return lorom(address) + 1


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    require(cfg['base_restoration'] == BASE, 'base target differs')
    require(cfg['base_output']['sha256'] == base_cfg['output']['sha256'], 'base identity differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'candidate identity differs')
    require(len(cfg['relocations']) == 1, 'relocation count differs')
    sprite = cfg['custom_sprites'][0]
    require(sprite['id'] == '5A', 'sprite id differs')
    sprite_id = 0x5A
    require(sprite['rooms'] == [0x1C], 'room set differs: ' + repr(sprite['rooms']))
    require(sprite_rooms(base, sprite_id) == [0x1C], 'base room dependencies differ')
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

    # Reviewed fixture: replace the first dragon 0x65 entry in room 0xCC with
    # sprite 0x5A, so the capture shows the ported sprite without a fight.
    fixture = bytearray(rom)
    cursor = room_list(fixture)
    patched = False
    while fixture[cursor] != 0xFF:
        if fixture[cursor + 2] == 0x65:
            fixture[cursor + 2] = 0x5A
            patched = True
            break
        cursor += 3
    require(patched, 'fixture did not find a dragon entry')
    fixture_sha = hashlib.sha256(bytes(fixture)).hexdigest()
    capture = ROOT / 'local/captures' / 'cc-5A-test'
    receipt = load(capture / 'receipt.json')
    require(receipt['rom_sha256'] == fixture_sha, 'fixture capture ROM differs')
    require(receipt['target_manifest']['output']['sha256'] == fixture_sha,
            'fixture capture manifest differs')
    positions = []
    for step in range(7):
        body = (capture / ('d%03d.wram.bin' % step)).read_bytes()
        for slot_index in range(12):
            if body[0x1AB9E + slot_index] == 0x5A:
                x = body[0xE4 + slot_index] | (body[0x14E0 + slot_index] << 8)
                y = body[0xD8 + slot_index] | (body[0x14D4 + slot_index] << 8)
                positions.append((step, slot_index, x, y, body[0x14C8 + slot_index]))
    require(len({position[2] for position in positions}) >= 4,
            'sprite 0x5A does not move on screen')
    require(all(position[4] == 8 for position in positions), 'sprite 0x5A status differs')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Snow projectile checks passed: sprite 0x5A installed and moves')


if __name__ == '__main__':
    main()

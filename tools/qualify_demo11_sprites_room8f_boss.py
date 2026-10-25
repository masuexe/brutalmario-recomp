#!/usr/bin/env python3
"""Qualify the demoOnly1 room 0x8F boss port.

DemoOnly1 keeps the boss record at its own table (0x8308A) and the code in a
RATS block. The block has internal long references that need the new bank. The
capture must match the demoOnly1 room 0x8F frame closely.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, lz2

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-room8f-boss'
BASE = 'demo11-sprites-native-records'
RECORD_TABLE = 0x318272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')


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
    require(len(cfg['relocations']) == 2, 'relocation count differs')
    for item in cfg['relocations']:
        source = item['source_offset']
        size = item['size']
        require(sha(base[source:source + size]) == item['sha256'], 'relocation source differs')
        require(rom[item['destination_offset']:item['destination_offset'] + size].hex() ==
                base[source:source + size].hex(), 'relocation destination differs')
        slot = item['pointer_offset']
        require(base[slot:slot + 3].hex() == item['pointer_before'], 'pointer source differs')
        require(rom[slot:slot + 3].hex() == item['pointer_after'], 'pointer result differs')
        old_pointer = int.from_bytes(bytes.fromhex(item['pointer_before']), 'little')
        new_pointer = int.from_bytes(bytes.fromhex(item['pointer_after']), 'little')
        require(lz2(base, old_pointer)[0] == lz2(rom, new_pointer)[0],
                'relocated graphics decode differently')
    block = cfg['raw_blocks'][0]
    data = bytes.fromhex(block['bytes'])
    require(sha(data) == block['data']['sha256'], 'raw block hash differs')
    destination = lorom(int(block['destination_address'], 16))
    require(rom[destination:destination + len(data)] == data, 'installed block differs')
    header = lorom(int(block['rats_address'], 16))
    require(rom[header:header + 4] == b'STAR', 'RATS header missing')
    patch = cfg['code_patches'][0]
    slot = lorom(int(patch['address'], 16))
    require(base[slot:slot + 16].hex() == patch['before'], 'record patch source differs')
    require(rom[slot:slot + 16].hex() == patch['after'], 'record patch result differs')
    source_record = donor[0x8308A + 0x42 * 16:0x8308A + 0x42 * 16 + 16]
    installed = bytes.fromhex(patch['after'])
    require(installed[:8] == source_record[:8], 'record header differs')
    require(installed[8:10] == source_record[8:10], 'record pointer low bytes differ')
    require(installed[11:13] == source_record[11:13], 'record second pointer low bytes differ')
    require(installed[10] == 0x23 and installed[13] == 0x23, 'record bank bytes differ')
    require(installed[14:16] == source_record[14:16], 'record tail differs')

    fixed = ROOT / 'local/captures' / 'room8F-boss-fixed'
    demo = ROOT / 'local/captures' / 'room8F-demoonly1'
    native = ROOT / 'local/captures' / 'room8F-base'
    fixed_body = (fixed / 'later.wram.bin').read_bytes()
    require(fixed_body[0x100] == 0x14, 'fixed capture does not reach gameplay')
    require(int.from_bytes(fixed_body[0x10B:0x10D], 'little') == 0x8F,
            'fixed capture is not room 0x8F')
    counts = [slot for slot in range(12) if fixed_body[0x1AB9E + slot] == 0x42]
    require(len(counts) >= 2, 'the boss children do not spawn')
    demo_body = (demo / 'later.wram.bin').read_bytes()
    demo_counts = [slot for slot in range(12) if demo_body[0x1AB9E + slot] == 0x42]
    require(len(demo_counts) >= 2, 'demoOnly1 capture lost the boss children')
    for dump in ('active', 'later'):
        a = (fixed / (dump + '.fb.bgrx')).read_bytes()
        b = (demo / (dump + '.fb.bgrx')).read_bytes()
        require(frame_diff(a, b, 24, 224) < 2000,
                dump + ' frame differs too much from demoOnly1')
        c = (native / (dump + '.fb.bgrx')).read_bytes()
        require(frame_diff(a, c, 24, 224) > 10000,
                dump + ' frame still matches the native record chain')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Room 8F boss checks passed: demoOnly1 boss runs and matches its frame')


if __name__ == '__main__':
    main()

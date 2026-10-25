#!/usr/bin/env python3
"""Qualify the room 0BC boss music retarget to slot A9.

The user specified slot A9 as the correct music for room 0BC. The recipe changes
one byte of the room music object from the placeholder parameter 1F to AA, so
the loader requests slot A9.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha

ROOT = Path(ROOT)
TARGET = 'demo11-boss-room-music-a9'
BASE = 'demo11-gfx-boss76'


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
    require(len(cfg['code_patches']) == 1, 'patch count differs')
    patch = cfg['code_patches'][0]
    offset = ((int(patch['address'], 16) & 0x7F0000) >> 1) | (int(patch['address'], 16) & 0x7FFF)
    require(base[offset:offset + 1].hex() == patch['before'], 'patch source differs')
    require(rom[offset:offset + 1].hex() == patch['after'], 'patch result differs')
    changed = sum(1 for left, right in zip(base, rom) if left != right)
    require(changed == 1, 'patch footprint differs: ' + str(changed))
    directory = ROOT / 'local/captures' / 'bossmusic-a9'
    if directory.exists():
        stall = (directory / 's33.wram.bin').read_bytes()
        require(stall[0x100] == 0x12, 'entry frame was not Mario Start')
        require(int.from_bytes(stall[0x10B:0x10D], 'little') == 0x0BC,
                'entry frame is not room 0BC')
        require(stall[0x0DDA] == 0xA9, 'room does not request slot A9')
        loaded = (directory / 's42.wram.bin').read_bytes()
        require(loaded[0x100] == 0x14, 'boss room does not reach gameplay')
        require(loaded[0x0DDA] == 0xA9, 'gameplay does not request slot A9')
    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Boss room music checks passed: room 0BC requests slot A9')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Qualify the boss room music retarget.

Room 0BC requested the null legacy music slot 2D when entered through the middle
boss door of level 0BC's parent, so Mario Start waited forever and the screen
stayed black. The patch retargets the one-byte music object parameter to the
working slot 1E.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha

ROOT = Path(ROOT)
TARGET = 'demo11-boss-music-retarget'
BASE = 'demo11-sprites-level1'


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
    require(len(cfg['code_patches']) == 1, 'patch count differs')
    patch = cfg['code_patches'][0]
    offset = ((int(patch['address'], 16) & 0x7F0000) >> 1) | (int(patch['address'], 16) & 0x7FFF)
    require(base[offset:offset + 1].hex() == patch['before'], 'patch source differs')
    require(rom[offset:offset + 1].hex() == patch['after'], 'patch result differs')
    changed = sum(1 for left, right in zip(base, rom) if left != right)
    require(changed == 1, 'patch footprint differs: ' + str(changed))

    old = ROOT / 'local/captures' / 'sweepold-083'
    new = ROOT / 'local/captures' / 'sweepfinal-083'
    if old.exists() and new.exists():
        stall = (old / 's33.wram.bin').read_bytes()
        require(stall[0x100] == 0x12, 'old run did not sample the stall')
        require(stall[0x0DDA] == 0x2D, 'old run did not request slot 2D')
        require(int.from_bytes(stall[0x10B:0x10D], 'little') == 0x0BC,
                'old run did not reach room 0BC')
        loaded = (new / 's42.wram.bin').read_bytes()
        require(loaded[0x100] == 0x14, 'new run does not reach gameplay')
        require(int.from_bytes(loaded[0x10B:0x10D], 'little') == 0x0BC,
                'new run does not reach room 0BC')
        require(loaded[0x0DDA] == 0x1E, 'new run does not use slot 1E')
    level094 = ROOT / 'local/captures' / 'ls2-094' / 'entry600.wram.bin'
    if level094.exists():
        body = level094.read_bytes()
        require(body[0x100] == 0x14, 'level 094 does not stay in gameplay')
        require(int.from_bytes(body[0x10B:0x10D], 'little') == 0x170,
                'level 094 loaded the wrong room')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Boss room music retarget checks passed: the middle boss door loads room 0BC')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Qualify the orphan block cleanup.

The records for sprites 0x42 and 0x3D are native again. The old installed code
blocks have no record. This target zeroes both blocks. Two room frames must stay
identical to the demoOnly1 boss chain.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-orphan-cleanup'
BASE = 'demo11-sprites-room8f-boss'
BLOCKS = ((0x107BF9, 772), (0x1EFC1B, 756))


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
    require(len(cfg['code_patches']) == len(BLOCKS), 'patch count differs')
    allowed = set()
    for patch, (header, size) in zip(cfg['code_patches'], BLOCKS):
        slot = lorom(int(patch['address'], 16))
        require(slot == header, 'patch offset differs')
        require(base[slot:slot + size].hex() == patch['before'], 'block source differs')
        require(rom[slot:slot + size] == bytes(size), 'block was not zeroed')
        allowed.update(range(slot, slot + size))
    changed = [index for index, (left, right) in enumerate(zip(base, rom)) if left != right]
    require(changed, 'candidate is identical to the base')
    for index in changed:
        require(index in allowed, 'unexpected changed byte: ' + hex(index))

    for room, base_name, dump in (('8F', 'room8F-boss-fixed', 'later'),
                                  ('13C', 'room13C-fixed', 'entry600')):
        cleanup = ROOT / 'local/captures' / ('room%s-cleanup' % room)
        body = (cleanup / (dump + '.wram.bin')).read_bytes()
        require(body[0x100] == 0x14, 'room ' + room + ' does not reach gameplay')
        reference = (ROOT / 'local/captures' / base_name / (dump + '.fb.bgrx')).read_bytes()
        current = (cleanup / (dump + '.fb.bgrx')).read_bytes()
        require(reference == current, 'room ' + room + ' frame changed')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Orphan cleanup passed: two blocks removed, two room frames unchanged')


if __name__ == '__main__':
    main()

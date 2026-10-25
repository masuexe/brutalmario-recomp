#!/usr/bin/env python3
"""Qualify the native record restores.

The cheap-demo ports for sprite 0x42 (coin boss in room 0x8F) and sprite 0x3D
(the sprite that kills Mario in room 0x13C) do not belong to demo 1-1. Demo 1-1
and demoOnly1 have no custom record for these IDs. This target restores the
native default records.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom

ROOT = Path(ROOT)
TARGET = 'demo11-sprites-native-records'
BASE = 'demo11-sprites-blocked-four'
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
RECORD_TABLE = 0x318272
RESTORED = (0x42, 0x3D)


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
    require(sha(rom) == cfg['output']['sha256'], 'candidate identity differs')
    require(len(cfg['code_patches']) == len(RESTORED), 'patch count differs')
    changed = [index for index, (left, right) in enumerate(zip(base, rom)) if left != right]
    require(changed, 'candidate is identical to the base')
    allowed = set()
    for sprite_id in RESTORED:
        slot = lorom(RECORD_TABLE + sprite_id * 16)
        require(base[slot:slot + 16] != DEFAULT, 'base record was already default: ' + hex(sprite_id))
        require(rom[slot:slot + 16] == DEFAULT, 'candidate record is not default: ' + hex(sprite_id))
        allowed.update(range(slot, slot + 16))
    for index in changed:
        require(index in allowed, 'unexpected changed byte: ' + hex(index))

    fixed = ROOT / 'local/captures' / 'room8F-fixed'
    pristine = ROOT / 'local/captures' / 'room8F-base'
    chain = ROOT / 'local/captures' / 'room8F-chain'
    for name, directory in (('fixed', fixed), ('pristine', pristine), ('chain', chain)):
        body = (directory / 'later.wram.bin').read_bytes()
        require(body[0x100] == 0x14, name + ' capture does not reach gameplay')
        require(int.from_bytes(body[0x10B:0x10D], 'little') == 0x8F,
                name + ' capture is not room 0x8F')
    fixed_body = (fixed / 'later.wram.bin').read_bytes()
    ids = {'%02X' % fixed_body[0x1AB9E + slot] for slot in range(12)}
    require('43' not in ids, 'the coin children still spawn in room 0x8F')
    for dump in ('active', 'later'):
        old = (pristine / (dump + '.fb.bgrx')).read_bytes()
        new = (fixed / (dump + '.fb.bgrx')).read_bytes()
        require(frame_diff(old, new, 24, 224) == 0,
                dump + ' room 0x8F field differs from pristine demo 1-1')
        require(frame_diff(old, new, 0, 24) == 0,
                dump + ' room 0x8F HUD differs from pristine demo 1-1')

    fixed13 = ROOT / 'local/captures' / 'room13C-fixed'
    chain13 = ROOT / 'local/captures' / 'room13C-chain'
    fixed_body = (fixed13 / 'entry600.wram.bin').read_bytes()
    require(fixed_body[0x100] == 0x14, 'room 0x13C still leaves gameplay')
    require(fixed_body[0x0DBE] == 4, 'room 0x13C lost a life')
    custom = {'%02X' % fixed_body[0x1AB9E + slot] for slot in range(12)}
    require('3D' in custom, 'room 0x13C did not spawn sprite 0x3D')
    status = {slot: fixed_body[0x14C8 + slot] for slot in range(12)
              if fixed_body[0x1AB9E + slot] == 0x3D}
    require(all(value == 0 for value in status.values()), 'sprite 0x3D is still active')
    chain_body = (chain13 / 'entry600.wram.bin').read_bytes()
    require(chain_body[0x100] != 0x14, 'the coin-boss chain did not fail as recorded')
    old = (chain13 / 'entry600.fb.bgrx').read_bytes()
    new = (fixed13 / 'entry600.fb.bgrx').read_bytes()
    require(frame_diff(old, new, 24, 224) > 0, 'room 0x13C frame did not change')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Native record checks passed: room 0x8F and room 0x13C match demo 1-1 behavior')


if __name__ == '__main__':
    main()

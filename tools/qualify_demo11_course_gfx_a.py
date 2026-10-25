#!/usr/bin/env python3
"""Qualify the Demo 1-1 course graphics candidate A.

The candidate descends from `demo11-star-bgm` and installs seven extended
graphics IDs from the 7hero donor. Room 0x173 selects these IDs but the base
leaves every pointer null.

This check verifies the candidate identity, the installed graphics and the
reviewed capture. The room still stalls at Mario Start on the candidate because
song 0x1A has no upload. The graphics install is a building block, not a
playability claim.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
TARGET = 'demo11-course-gfx-a'
CAPTURE = 'd11-gfxa-survey-097'
ROOM = 0x173


def main():
    head = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    candidate = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    require(sha(head) == cfg['base_output']['sha256'], 'base ROM identity differs')
    require(sha(candidate) == cfg['output']['sha256'], 'candidate ROM identity differs')

    record = lorom(int(cfg['gfx_record']['address'], 16))
    require(head[record:record + 32].hex() == cfg['gfx_record']['before'],
            'room record differs')
    require(candidate[record:record + 32] == head[record:record + 32],
            'candidate changed the room record')

    allowed = set(range(cfg['allocation']['offset'],
                        cfg['allocation']['offset'] + cfg['allocation']['size']))
    for asset in cfg['assets']:
        source = graphics_pointer(donor, int(asset['source_id'], 16))
        require(f'{source:06X}' == asset['source_address'], 'donor pointer differs')
        decoded, compressed = lz2(donor, source)
        require(sha(decoded) == asset['decoded']['sha256'], 'decoded donor data differs')
        require(sha(compressed) == asset['compressed']['sha256'], 'compressed donor data differs')
        slot = pointer_offset(int(asset['target_id'], 16))
        require(head[slot:slot + 3] == b'\xff' * 3, 'base slot is not empty')
        address = int.from_bytes(candidate[slot:slot + 3], 'little')
        data = lorom(address)
        header = candidate[data - 8:data]
        require(header[:4] == b'STAR', 'candidate slot has no RATS block')
        count = int.from_bytes(header[4:6], 'little')
        require(count == asset['compressed']['size'] - 1, 'graphics count differs')
        check, installed = lz2(candidate, address)
        require(check == decoded, 'installed graphics decode differs')
        require(installed == compressed, 'installed graphics stream differs')
        require(data - 8 >= cfg['allocation']['offset'] and
                data + count + 1 <= cfg['allocation']['offset'] + cfg['allocation']['size'],
                'graphics block is outside the allocation')
        allowed |= set(range(slot, slot + 3))
    changed = {index for index, (a, b) in enumerate(zip(head, candidate)) if a != b}
    require(not (changed - allowed), 'candidate changed an unexpected byte')

    receipt = json.loads((ROOT / 'local/captures' / CAPTURE / 'receipt.json').read_text())
    require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs')
    state = (ROOT / 'local/captures' / CAPTURE / 'entry600.wram.bin').read_bytes()
    require(state[0x100] == 0x12, 'reviewed capture no longer stalls as recorded')
    build = json.loads((ROOT / 'local/build' / TARGET / 'm1-build.json').read_text()) if (
        ROOT / 'local/build' / TARGET / 'm1-build.json').exists() else None
    if build is not None:
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(build['rom_sha256'] == sha(candidate) and
                build['binary_sha256'] == sha(binary.read_bytes()),
                'native build identity differs')
    print('Course graphics candidate checks passed: ' + TARGET)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Qualify Demo 1-1 graphics batch P.

Batch P ports the last two extended graphics IDs that the restored rooms
reference: 226 for room 129 and 1AC for room 130. After batch P, every room
that stalled on the head has no empty extended graphics slot.

The remaining 53 rooms with empty slots are original Demo 1-1 content. Their
empty slots are normal in this game, and the engine uses fallback graphics.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset

ROOT = Path(ROOT)
BASE = 'demo11-fix-batch-o2'
P = 'demo11-fix-batch-p'
LEVELS = ('04D', '054')


def state(capture, tag):
    body = (ROOT / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
    return {'mode': body[0x100], 'room': int.from_bytes(body[0x10B:0x10D], 'little'),
            'lives': body[0x0DBE], 'translevel': body[0x13BF]}


def load(path):
    return json.loads(Path(path).read_text())


def null_slots(rom, room):
    header = rom[lorom(0x14AD08) + room * 32: lorom(0x14AD08) + room * 32 + 32]
    ids = [int.from_bytes(header[offset:offset + 2], 'little')
           for offset in range(2, 20, 2)]
    return [gfx for gfx in ids
            if 0x100 <= gfx <= 0xFFF and
            rom[pointer_offset(gfx):pointer_offset(gfx) + 3] == b'\xff' * 3]


def main():
    cfg = load(ROOT / 'config/restorations' / (P + '.json'))
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    candidate = (ROOT / 'local/restoration' / P / 'rom.sfc').read_bytes()
    require(sha(base) == cfg['base_output']['sha256'], 'base differs')
    require(sha(candidate) == cfg['output']['sha256'], 'candidate identity differs')

    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    for asset in cfg['assets']:
        gfx = int(asset['source_id'], 16)
        decoded, compressed = lz2(donor, graphics_pointer(donor, gfx))
        require(sha(decoded) == asset['decoded']['sha256'], 'decoded data differs')
        require(sha(compressed) == asset['compressed']['sha256'], 'compressed data differs')
        slot = pointer_offset(gfx)
        require(base[slot:slot + 3] == b'\xff' * 3, 'base slot is not empty')
        address = int.from_bytes(candidate[slot:slot + 3], 'little')
        data = lorom(address)
        require(candidate[data - 8:data][:4] == b'STAR', 'RATS block missing')
        check, installed = lz2(candidate, address)
        require(check == decoded and installed == compressed, 'graphics data differs')
        for room in asset['rooms']:
            require(gfx not in null_slots(candidate, room),
                    'asset room still has the empty slot: ' + hex(room))

    for translevel in LEVELS:
        capture = 'd11-fixp-survey-' + translevel
        early = state(capture, 'entry240')
        late = state(capture, 'entry600')
        require(early['mode'] == 0x14, 'no gameplay at entry 240: ' + translevel)
        if translevel == '054':
            require(late['mode'] == 0x14, 'should stay playable: ' + translevel)
        else:
            require(late['lives'] < early['lives'], 'expected a no-input death: ' + translevel)
        receipt = load(ROOT / 'local/captures' / capture / 'receipt.json')
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs')
        native = capture.replace('-survey-', '-native-')
        if (ROOT / 'local/captures' / native).exists():
            for tag in ('entry240', 'entry600'):
                left = state(capture, tag)
                right = state(native, tag)
                for key in ('mode', 'room', 'lives', 'translevel'):
                    require(left[key] == right[key],
                            'native differs: ' + translevel + '/' + tag + '/' + key)
            native_receipt = load(ROOT / 'local/captures' / native / 'receipt.json')
            require(native_receipt['rom_sha256'] == sha(candidate),
                    'native capture ROM differs')

    head = load(ROOT / 'local/reports/demo11-course-survey.json')
    stalled_rooms = {}
    for entry in head['entries']:
        if entry['result'] == 'mario-start-stall':
            stalled_rooms[int(entry['samples']['entry600']['room'], 16)] = entry['translevel']
    remaining = {}
    reports = [load(ROOT / 'local/reports/demo11-course-survey-chain-o.json'),
               load(ROOT / 'local/reports/demo11-course-survey-tail.json')]
    for report in reports:
        for entry in report['entries']:
            room = int(entry['samples']['entry600']['room'], 16)
            found = null_slots(candidate, room)
            if found:
                remaining[room] = found
    still_bad = [translevel for room, translevel in stalled_rooms.items()
                 if room in remaining]
    require(not still_bad, 'restored rooms still have empty slots: ' + str(still_bad))
    require(len(remaining) == 53, 'remaining room count differs: ' + str(len(remaining)))
    require(len({g for values in remaining.values() for g in values}) == 88,
            'remaining unique ID count differs')

    build = load(ROOT / 'local/build' / P / 'm1-build.json')
    from restoration_targets import RESTORATIONS
    binary = ROOT / 'local/build' / P / RESTORATIONS[P]['binary']
    require(build['rom_sha256'] == sha(candidate) and
            build['binary_sha256'] == sha(binary.read_bytes()),
            'native build identity differs')
    print('Graphics batch P checks passed: restored rooms have no empty graphics slots')


if __name__ == '__main__':
    main()

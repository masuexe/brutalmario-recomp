#!/usr/bin/env python3
"""Qualify the Demo 1-1 music batch J and graphics fix batches K1, K2, L, M.

Music batch J installs legacy songs 0x36, 0x3B, 0x3E, 0x42 and 0x43 as raw
group slices. The graphics batches add 21 extended graphics IDs from 7hero.

The reviewed captures fix twelve more translevels:
`00D`, `01A`, `02C`, `034`, `03C`, `048`, `04E`, `055`, `056`,
`062`, `06F` and `070`. All stay in gameplay at entry 240 and 600.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset, raw_group_song

ROOT = Path(ROOT)
BASE = 'demo11-fix-batch-i'
J = 'demo11-music-batch-j'
K1 = 'demo11-fix-batch-k1'
K2 = 'demo11-fix-batch-k2'
L = 'demo11-fix-batch-l'
M = 'demo11-fix-batch-m'
LEVELS = ('00D', '01A', '02C', '034', '03C', '048', '04E', '055', '056', '062',
          '06F', '070')
CAPTURE_PREFIX = 'd11-fixm-survey-'


def capture_state(root, capture, tag):
    body = (root / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
    return {'mode': body[0x100], 'room': int.from_bytes(body[0x10B:0x10D], 'little'),
            'lives': body[0x0DBE], 'translevel': body[0x13BF]}


def load_json(path):
    return json.loads(Path(path).read_text())


def check_music(base_rom, candidate, cfg):
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    for track in cfg['music_tracks']:
        require(track.get('raw') is True, 'track is not raw')
        source = lorom(int(track['source_address'], 16))
        group = donor[source:source + track['source_group']['size']]
        require(sha(group) == track['source_group']['sha256'], 'donor group differs')
        payload = raw_group_song(group, track['sequence_offset'] // 8)
        require(sha(payload) == track['adapted']['sha256'], 'raw payload differs')
        pointer = lorom(int(track['pointer_address'], 16))
        require(base_rom[pointer:pointer + 3] == bytes(3), 'music base slot not empty')
        address = int.from_bytes(candidate[pointer:pointer + 3], 'big')
        start = lorom(address)
        header = candidate[start - 8:start]
        require(header[:4] == b'STAR', 'music RATS block missing')
        require(int.from_bytes(header[4:6], 'little') == len(payload) - 1,
                'music count differs')
        require(candidate[start:start + len(payload)] == payload, 'music payload differs')
        allocation = track['allocation']
        require(start - 8 >= allocation['offset'] and
                start + len(payload) + 4 <= allocation['offset'] + allocation['size'],
                'music block outside allocation')


def check_graphics(base_rom, candidate, cfg):
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    for asset in cfg['assets']:
        gfx = int(asset['source_id'], 16)
        source = graphics_pointer(donor, gfx)
        decoded, compressed = lz2(donor, source)
        require(sha(decoded) == asset['decoded']['sha256'], 'decoded data differs')
        require(sha(compressed) == asset['compressed']['sha256'], 'compressed data differs')
        slot = pointer_offset(gfx)
        require(base_rom[slot:slot + 3] == b'\xff' * 3, 'graphics base slot not empty')
        address = int.from_bytes(candidate[slot:slot + 3], 'little')
        data = lorom(address)
        header = candidate[data - 8:data]
        require(header[:4] == b'STAR', 'graphics RATS block missing')
        check, installed = lz2(candidate, address)
        require(check == decoded and installed == compressed, 'graphics data differs')
        allocation = cfg['allocation']
        require(data - 8 >= allocation['offset'] and
                data + len(compressed) <= allocation['offset'] + allocation['size'],
                'graphics block outside allocation')


def main():
    roms = {name: (ROOT / 'local/restoration' / name / 'rom.sfc').read_bytes()
            for name in (BASE, J, K1, K2, L, M)}
    cfgs = {name: load_json(ROOT / 'config/restorations' / (name + '.json'))
            for name in (J, K1, K2, L, M)}
    require(sha(roms[BASE]) == cfgs[J]['base_output']['sha256'], 'J base differs')
    require(sha(roms[J]) == cfgs[J]['output']['sha256'], 'J identity differs')
    require(sha(roms[J]) == cfgs[K1]['base_output']['sha256'], 'K1 base differs')
    require(sha(roms[K1]) == cfgs[K1]['output']['sha256'], 'K1 identity differs')
    require(sha(roms[K1]) == cfgs[K2]['base_output']['sha256'], 'K2 base differs')
    require(sha(roms[K2]) == cfgs[K2]['output']['sha256'], 'K2 identity differs')
    require(sha(roms[K2]) == cfgs[L]['base_output']['sha256'], 'L base differs')
    require(sha(roms[L]) == cfgs[L]['output']['sha256'], 'L identity differs')
    require(sha(roms[L]) == cfgs[M]['base_output']['sha256'], 'M base differs')
    require(sha(roms[M]) == cfgs[M]['output']['sha256'], 'M identity differs')

    check_music(roms[BASE], roms[J], cfgs[J])
    check_graphics(roms[J], roms[K1], cfgs[K1])
    check_graphics(roms[K1], roms[K2], cfgs[K2])
    check_graphics(roms[K2], roms[L], cfgs[L])
    check_graphics(roms[L], roms[M], cfgs[M])

    before = load_json(ROOT / 'local/reports/demo11-course-survey-chain-i.json')
    before_modes = {}
    for entry in before['entries']:
        if entry['samples'] and entry['samples']['entry600']:
            before_modes[entry['translevel']] = entry['samples']['entry600']['mode']
    for translevel in LEVELS:
        require(before_modes.get(translevel) != '14',
                'base already playable: ' + translevel)
        capture = CAPTURE_PREFIX + translevel
        reference = capture_state(ROOT, capture, 'entry600')
        require(reference['mode'] == 0x14, 'candidate does not stay in gameplay: ' + translevel)
        require(capture_state(ROOT, capture, 'entry240')['mode'] == 0x14,
                'candidate does not reach gameplay: ' + translevel)
        receipt = load_json(ROOT / 'local/captures' / capture / 'receipt.json')
        require(receipt['rom_sha256'] == sha(roms[M]), 'capture ROM differs: ' + translevel)
        native = capture.replace('-survey-', '-native-')
        if (ROOT / 'local/captures' / native).exists():
            for tag in ('entry240', 'entry600'):
                a = capture_state(ROOT, capture, tag)
                b = capture_state(ROOT, native, tag)
                for key in ('mode', 'room', 'lives', 'translevel'):
                    require(a[key] == b[key], 'native differs: ' + translevel + '/' + tag + '/' + key)
            native_receipt = load_json(ROOT / 'local/captures' / native / 'receipt.json')
            require(native_receipt['rom_sha256'] == sha(roms[M]), 'native capture ROM differs')

    build = load_json(ROOT / 'local/build' / M / 'm1-build.json')
    binary = ROOT / 'local/build' / M / RESTORATIONS[M]['binary']
    require(build['rom_sha256'] == sha(roms[M]) and
            build['binary_sha256'] == sha(binary.read_bytes()),
            'native build identity differs')
    print('Music batch J and graphics batches K1-M checks passed')


if __name__ == '__main__':
    main()

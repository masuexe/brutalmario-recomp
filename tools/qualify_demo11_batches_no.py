#!/usr/bin/env python3
"""Qualify the Demo 1-1 music batch N and graphics fix batches O1 and O2.

Music batch N fills the last low-id slots. Audio comparison showed that the
engine plays its built-in track for these ids and ignores the payload content:
two different payloads gave byte-identical audio. The payload only satisfies the
upload handshake.

The graphics batches add 13 extended graphics IDs from 7hero.

All 39 remaining chain stalls now reach gameplay. Four of them (`024`,
`097`, `0AD`, `0BE`) then die because the scripts have no controller
input. Entry and short gameplay are the claims.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset, raw_group_song

ROOT = Path(ROOT)
BASE = 'demo11-fix-batch-m'
N = 'demo11-music-batch-n'
O1 = 'demo11-fix-batch-o1'
O2 = 'demo11-fix-batch-o2'
NO_INPUT_DEATH = {'024', '097', '0AD', '0BE'}
NATIVE_SUBSET = ('024', '046', '05D', '078', '097', '09E', '0A6', '0BE')


def state(capture, tag):
    body = (ROOT / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
    return {'mode': body[0x100], 'room': int.from_bytes(body[0x10B:0x10D], 'little'),
            'lives': body[0x0DBE], 'translevel': body[0x13BF]}


def load(path):
    return json.loads(Path(path).read_text())


def check_music(base_rom, candidate, cfg, donor):
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


def check_graphics(base_rom, candidate, cfg, donor):
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
    names = (BASE, N, O1, O2)
    roms = {name: (ROOT / 'local/restoration' / name / 'rom.sfc').read_bytes() for name in names}
    cfgs = {name: load(ROOT / 'config/restorations' / (name + '.json')) for name in (N, O1, O2)}
    require(sha(roms[BASE]) == cfgs[N]['base_output']['sha256'], 'N base differs')
    require(sha(roms[N]) == cfgs[N]['output']['sha256'], 'N identity differs')
    require(sha(roms[N]) == cfgs[O1]['base_output']['sha256'], 'O1 base differs')
    require(sha(roms[O1]) == cfgs[O1]['output']['sha256'], 'O1 identity differs')
    require(sha(roms[O1]) == cfgs[O2]['base_output']['sha256'], 'O2 base differs')
    require(sha(roms[O2]) == cfgs[O2]['output']['sha256'], 'O2 identity differs')

    music_donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    gfx_donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    check_music(roms[BASE], roms[N], cfgs[N], music_donor)
    check_graphics(roms[N], roms[O1], cfgs[O1], gfx_donor)
    check_graphics(roms[O1], roms[O2], cfgs[O2], gfx_donor)

    chain = load(ROOT / 'local/reports/demo11-course-survey-chain-i.json')
    fixed_jm = set('00D 01A 02C 034 03C 048 04E 055 056 062 06F 070'.split())
    levels = [entry['translevel'] for entry in chain['entries']
              if entry['result'] == 'mario-start-stall' and entry['translevel'] not in fixed_jm]
    require(len(levels) == 39, 'remaining level set differs: ' + str(len(levels)))
    for translevel in levels:
        capture = 'd11-fixo-survey-' + translevel
        early = state(capture, 'entry240')
        late = state(capture, 'entry600')
        require(early['mode'] == 0x14, 'no gameplay at entry 240: ' + translevel)
        expected = (0x0E, 0x0B) if translevel in NO_INPUT_DEATH else (0x14,)
        require(late['mode'] in expected, 'unexpected entry 600 mode: ' + translevel)
        receipt = load(ROOT / 'local/captures' / capture / 'receipt.json')
        require(receipt['rom_sha256'] == sha(roms[O2]), 'capture ROM differs: ' + translevel)

    for translevel in NATIVE_SUBSET:
        native = 'd11-fixo-native-' + translevel
        if not (ROOT / 'local/captures' / native).exists():
            continue
        capture = 'd11-fixo-survey-' + translevel
        for tag in ('entry240', 'entry600'):
            a = state(capture, tag)
            b = state(native, tag)
            for key in ('mode', 'room', 'lives', 'translevel'):
                require(a[key] == b[key], 'native differs: ' + translevel + '/' + tag + '/' + key)
        native_receipt = load(ROOT / 'local/captures' / native / 'receipt.json')
        require(native_receipt['rom_sha256'] == sha(roms[O2]), 'native capture ROM differs')

    build = load(ROOT / 'local/build' / O2 / 'm1-build.json')
    binary = ROOT / 'local/build' / O2 / RESTORATIONS[O2]['binary']
    require(build['rom_sha256'] == sha(roms[O2]) and
            build['binary_sha256'] == sha(binary.read_bytes()),
            'native build identity differs')
    print('Music batch N and graphics batches O1/O2 checks passed')


if __name__ == '__main__':
    main()

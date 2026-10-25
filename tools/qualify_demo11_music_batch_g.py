#!/usr/bin/env python3
"""Qualify the Demo 1-1 music batch G candidate.

The candidate installs six legacy songs as raw group slices. Each payload keeps
the donor source base, so the sequence pointers need no relocation. This
installs songs with commands outside the reviewed adapt_music subset.

The reviewed captures fix three stalled translevels: `02B`, `02F` and
`06C`. Entry and short gameplay are the claims.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import lorom, raw_group_song

ROOT = Path(ROOT)
BASE = 'demo11-fix-batch-f'
TARGET = 'demo11-music-batch-g'
FIXED = ('02B', '02F', '06C')


def capture_state(root, capture, tag):
    body = (root / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
    return {'mode': body[0x100], 'room': int.from_bytes(body[0x10B:0x10D], 'little'),
            'lives': body[0x0DBE], 'translevel': body[0x13BF]}


def main():
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    candidate = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base_cfg = json.loads((ROOT / 'config/restorations' / (BASE + '.json')).read_text())
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    require(sha(base) == cfg['base_output']['sha256'], 'base identity differs')
    require(sha(base) == base_cfg['output']['sha256'], 'base recipe identity differs')
    require(sha(candidate) == cfg['output']['sha256'], 'candidate identity differs')

    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    for track in cfg['music_tracks']:
        require(track.get('raw') is True, 'track is not raw')
        source = lorom(int(track['source_address'], 16))
        group = donor[source:source + track['source_group']['size']]
        require(sha(group) == track['source_group']['sha256'], 'donor group differs')
        payload = raw_group_song(group, track['sequence_offset'] // 8)
        require(sha(payload) == track['adapted']['sha256'], 'raw payload differs: ' + track['id'])
        pointer = lorom(int(track['pointer_address'], 16))
        require(base[pointer:pointer + 3] == bytes(3), 'base slot not empty: ' + track['id'])
        address = int.from_bytes(candidate[pointer:pointer + 3], 'big')
        start = lorom(address)
        header = candidate[start - 8:start]
        require(header[:4] == b'STAR', 'missing RATS block: ' + track['id'])
        count = int.from_bytes(header[4:6], 'little')
        require(count == len(payload) - 1, 'music count differs: ' + track['id'])
        require(candidate[start:start + len(payload)] == payload, 'music payload differs')
        allocation = track['allocation']
        require(start - 8 >= allocation['offset'] and
                start + len(payload) + 4 <= allocation['offset'] + allocation['size'],
                'music block outside allocation: ' + track['id'])

    for translevel in FIXED:
        head = capture_state(ROOT, 'd11-retarget-survey2-' + translevel, 'entry600')
        reference = capture_state(ROOT, 'd11-musicg-survey-' + translevel, 'entry600')
        require(head['mode'] == 0x12, 'head no longer stalls: ' + translevel)
        require(reference['mode'] == 0x14, 'candidate does not reach gameplay: ' + translevel)
        receipt = json.loads((ROOT / 'local/captures' / ('d11-musicg-survey-' + translevel) /
                              'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + translevel)
        native = 'd11-musicg-native-' + translevel
        for tag in ('entry240', 'entry600'):
            reference_state = capture_state(ROOT, 'd11-musicg-survey-' + translevel, tag)
            native_state = capture_state(ROOT, native, tag)
            for key in ('mode', 'room', 'lives', 'translevel'):
                require(reference_state[key] == native_state[key],
                        'native and reference differ: ' + translevel + '/' + tag + '/' + key)
        native_receipt = json.loads((ROOT / 'local/captures' / native / 'receipt.json').read_text())
        require(native_receipt['rom_sha256'] == sha(candidate), 'native capture ROM differs')

    build = json.loads((ROOT / 'local/build' / TARGET / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
    require(build['rom_sha256'] == sha(candidate) and
            build['binary_sha256'] == sha(binary.read_bytes()),
            'native build identity differs')
    print('Music batch G checks passed')


if __name__ == '__main__':
    main()

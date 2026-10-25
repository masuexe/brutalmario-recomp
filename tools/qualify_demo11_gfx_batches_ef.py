#!/usr/bin/env python3
"""Qualify the Demo 1-1 graphics fix batches E and F.

`demo11-fix-batch-e` ports ten extended graphics IDs from 7hero for rooms
0x15C and 0x15D. `demo11-fix-batch-f` adds six graphics IDs for room 0x144.

The reviewed captures fix three more stalled translevels: `080`, `081` and
`068`. Entry and short gameplay are the claims.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset

ROOT = Path(ROOT)
BASE = 'demo11-fix-batch-d'
E = 'demo11-fix-batch-e'
F = 'demo11-fix-batch-f'
FIXED = {'080': ('d11-fixe-survey-080',), '081': ('d11-fixe-survey-081',)}


def capture_state(root, capture, tag):
    body = (root / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
    return {'mode': body[0x100], 'room': int.from_bytes(body[0x10B:0x10D], 'little'),
            'lives': body[0x0DBE], 'translevel': body[0x13BF]}


def main():
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    e_rom = (ROOT / 'local/restoration' / E / 'rom.sfc').read_bytes()
    f_rom = (ROOT / 'local/restoration' / F / 'rom.sfc').read_bytes()
    base_cfg = json.loads((ROOT / 'config/restorations' / 'demo11-fix-batch-d.json').read_text())
    e_cfg = json.loads((ROOT / 'config/restorations' / (E + '.json')).read_text())
    f_cfg = json.loads((ROOT / 'config/restorations' / (F + '.json')).read_text())
    require(sha(base) == base_cfg['output']['sha256'], 'base identity differs')
    require(sha(base) == e_cfg['base_output']['sha256'], 'E base differs')
    require(sha(e_rom) == e_cfg['output']['sha256'], 'E candidate differs')
    require(sha(e_rom) == f_cfg['base_output']['sha256'], 'F base differs')
    require(sha(f_rom) == f_cfg['output']['sha256'], 'F candidate differs')

    donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    for recipe, base_rom, candidate in ((e_cfg, base, e_rom), (f_cfg, e_rom, f_rom)):
        for asset in recipe['assets']:
            gfx = int(asset['source_id'], 16)
            source = graphics_pointer(donor, gfx)
            decoded, compressed = lz2(donor, source)
            require(sha(decoded) == asset['decoded']['sha256'], 'decoded data differs')
            require(sha(compressed) == asset['compressed']['sha256'], 'compressed data differs')
            slot = pointer_offset(gfx)
            require(base_rom[slot:slot + 3] == b'\xff' * 3, 'base slot not empty')
            address = int.from_bytes(candidate[slot:slot + 3], 'little')
            data = lorom(address)
            header = candidate[data - 8:data]
            require(header[:4] == b'STAR', 'RATS block missing')
            check, installed = lz2(candidate, address)
            require(check == decoded and installed == compressed, 'installed data differs')
            allocation = recipe['allocation']
            require(data - 8 >= allocation['offset'] and
                    data + len(compressed) <= allocation['offset'] + allocation['size'],
                    'graphics block outside allocation')

    head_captures = {'080': 'd11-retarget-survey2-080', '081': 'd11-retarget-survey2-081',
                     '068': 'd11-retarget-survey2-068'}
    for translevel, capture in head_captures.items():
        require(capture_state(ROOT, capture, 'entry600')['mode'] == 0x12,
                'head no longer stalls: ' + translevel)
    captures = {'080': 'd11-fixe-survey-080', '081': 'd11-fixe-survey-081',
                '068': 'd11-fixf-survey-068'}
    bodies = {'080': e_rom, '081': e_rom, '068': f_rom}
    for translevel, capture in captures.items():
        state = capture_state(ROOT, capture, 'entry600')
        require(state['mode'] == 0x14, 'candidate does not fix: ' + translevel)
        receipt = json.loads((ROOT / 'local/captures' / capture / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(bodies[translevel]), 'capture ROM differs: ' + translevel)
        native = 'd11-fixf-native-' + translevel
        native_path = ROOT / 'local/captures' / native / ('entry600.wram.bin')
        if native_path.exists():
            for tag in ('entry240', 'entry600'):
                reference_state = capture_state(ROOT, capture, tag)
                native_state = capture_state(ROOT, native, tag)
                for key in ('mode', 'room', 'lives', 'translevel'):
                    require(reference_state[key] == native_state[key],
                            'native and reference differ: ' + translevel + '/' + tag + '/' + key)

    build_path = ROOT / 'local/build' / F / 'm1-build.json'
    if build_path.exists():
        build = json.loads(build_path.read_text())
        binary = ROOT / 'local/build' / F / RESTORATIONS[F]['binary']
        require(build['rom_sha256'] == sha(f_rom) and
                build['binary_sha256'] == sha(binary.read_bytes()),
                'native build identity differs')
    print('Graphics fix batches E and F checks passed')


if __name__ == '__main__':
    main()

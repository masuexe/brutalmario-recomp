#!/usr/bin/env python3
"""Qualify the Demo 1-1 graphics fix batches H and I.

`demo11-fix-batch-h` ports ten extended graphics IDs from 7hero for six
stalled rooms. `demo11-fix-batch-i` adds six IDs for room 0x142.

The reviewed captures fix seven more stalled translevels. `027`, `03A`,
`040`, `051` and `066` stay in gameplay. `018` and `01B` reach gameplay
and then die because the scripts have no controller input. Entry and short
gameplay are the claims.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset

ROOT = Path(ROOT)
BASE = 'demo11-music-batch-g'
H = 'demo11-fix-batch-h'
I = 'demo11-fix-batch-i'
H_LEVELS = {'018': 'd11-fixh-survey-018', '01B': 'd11-fixh-survey-01B',
            '027': 'd11-fixh-survey-027', '03A': 'd11-fixh-survey-03A',
            '040': 'd11-fixh-survey-040', '051': 'd11-fixh-survey-051'}
I_LEVELS = {'066': 'd11-fixi-survey-066'}
STAY = ('027', '03A', '040', '051')
DEATH = ('018', '01B')
DEATH_MODE = {'018': 0x0D, '01B': 0x0C}


def state(root, capture, tag):
    body = (root / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
    return {'mode': body[0x100], 'room': int.from_bytes(body[0x10B:0x10D], 'little'),
            'lives': body[0x0DBE], 'translevel': body[0x13BF]}


def main():
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    h_rom = (ROOT / 'local/restoration' / H / 'rom.sfc').read_bytes()
    i_rom = (ROOT / 'local/restoration' / I / 'rom.sfc').read_bytes()
    base_cfg = json.loads((ROOT / 'config/restorations' / (BASE + '.json')).read_text())
    h_cfg = json.loads((ROOT / 'config/restorations' / (H + '.json')).read_text())
    i_cfg = json.loads((ROOT / 'config/restorations' / (I + '.json')).read_text())
    require(sha(base) == base_cfg['output']['sha256'], 'base identity differs')
    require(sha(base) == h_cfg['base_output']['sha256'], 'H base differs')
    require(sha(h_rom) == h_cfg['output']['sha256'], 'H candidate differs')
    require(sha(h_rom) == i_cfg['base_output']['sha256'], 'I base differs')
    require(sha(i_rom) == i_cfg['output']['sha256'], 'I candidate differs')

    donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    for recipe, base_rom, candidate in ((h_cfg, base, h_rom), (i_cfg, h_rom, i_rom)):
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

    for translevel, capture in list(H_LEVELS.items()) + list(I_LEVELS.items()):
        head = state(ROOT, 'd11-retarget-survey2-' + translevel, 'entry600')
        require(head['mode'] == 0x12, 'head no longer stalls: ' + translevel)
        reference = state(ROOT, capture, 'entry600')
        require(reference['mode'] == (0x14 if translevel in STAY + ('066',) else DEATH_MODE[translevel]),
                'reference result differs: ' + translevel)
        receipt = json.loads((ROOT / 'local/captures' / capture / 'receipt.json').read_text())
        expected = sha(i_rom) if translevel == '066' else sha(h_rom)
        require(receipt['rom_sha256'] == expected, 'capture ROM differs: ' + translevel)
        native = capture.replace('-survey', '-native')
        if (ROOT / 'local/captures' / native).exists():
            for tag in ('entry240', 'entry600'):
                reference_state = state(ROOT, capture, tag)
                native_state = state(ROOT, native, tag)
                for key in ('mode', 'room', 'lives', 'translevel'):
                    require(reference_state[key] == native_state[key],
                            'native and reference differ: ' + translevel + '/' + tag + '/' + key)

    build = json.loads((ROOT / 'local/build' / I / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / I / RESTORATIONS[I]['binary']
    require(build['rom_sha256'] == sha(i_rom) and
            build['binary_sha256'] == sha(binary.read_bytes()),
            'native build identity differs')
    print('Graphics fix batches H and I checks passed')


if __name__ == '__main__':
    main()

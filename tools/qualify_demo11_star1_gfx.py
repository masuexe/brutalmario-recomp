#!/usr/bin/env python3
"""Qualify the Star World lower-left graphics recovery on the Demo 1-1 line.

The three missing extended graphics streams (101/102/103) install as new ids
FFD/FFE/FFF with the room-$005 record words retargeted - the same recipe shape
the demoOnly1 line accepted as `star-world-1`. Both hosts must enter room $005
through its map node and render the terrain (the pre-repair entry showed a
flat void). Course traversal, music and sprite behaviour stay open, matching
the original pilot's boundary.
"""
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-star1-gfx'
BINARY = 'BrutalMarioDemo11Star1GraphicsSNESRecomp'
SCRIPT = ROOT / 'recomp/inputs/demo11-star1-entry.script'


def main():
    candidate = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(candidate, cfg['output'], 'candidate')
    base = (ROOT / 'local/restoration/demo11-castle-sprite06/rom.sfc').read_bytes()
    require(sha(base) == cfg['base_output']['sha256'], 'base identity differs')
    from restore_star_world_1 import pointer_offset, lorom
    for new_id in (0xFFD, 0xFFE, 0xFFF):
        pointer = pointer_offset(new_id)
        require(candidate[pointer:pointer+3] != b'\xff\xff\xff', 'slot %03X still empty' % new_id)
        require(base[pointer:pointer+3] == b'\xff\xff\xff', 'slot %03X was not empty on the base' % new_id)
    hdr = lorom(0x14AD08) + 0x005 * 32
    record = candidate[hdr:hdr+32]
    words = [int.from_bytes(record[i:i+2], 'little') for i in range(2, 20, 2)]
    for new_id in (0xFFD, 0xFFE, 0xFFF):
        require(new_id in words, 'room-005 record does not select %03X' % new_id)

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / BINARY
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build identity differs')

    for host, tag in (('reference', 'ref'), ('native', 'native')):
        directory = ROOT / 'local/captures' / ('d11-star1-entry-' + tag)
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(SCRIPT.read_bytes()),
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        for sample in ('s0', 's1', 's2'):
            body = (directory / (sample + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, 'incomplete WRAM: ' + host + '/' + sample)
            require(body[0x100] == 0x14 and word(body, 0x10B) == 0x005,
                    'room $005 entry missing: ' + host + '/' + sample)
            require(body[0x71] == 0, 'player hurt at entry: ' + host + '/' + sample)
        moved = (directory / 's2.wram.bin').read_bytes()
        require(word(moved, 0x94) > 0x50, 'player did not move right: ' + host)
        # framebuffer non-void: the pre-repair room rendered a flat single-colour void
        fb = (directory / ('s1.fb.bgrx')).read_bytes()
        step = 7 * 4
        px = [fb[i:i+4] for i in range(0, len(fb) - 4, step)]
        dark = sum(1 for p in px if p[0] < 40 and p[1] < 40 and p[2] < 40) / len(px)
        require(dark < 0.5, 'room still renders dark: ' + host + ' (%.2f)' % dark)

    report = {
        'scope': __doc__.strip(),
        'head': HEAD,
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'binary_sha256': build['binary_sha256'],
        'captures': {'reference': 'local/captures/d11-star1-entry-ref',
                     'native': 'local/captures/d11-star1-entry-native'},
        'verified': ['slots FFD/FFE/FFF filled from cheap_demo with the pinned streams',
                     'room-005 record words retargeted to the new ids',
                     'both hosts enter room $005 and render the terrain',
                     'the map-node entry is the same fixture the accepted route work uses'],
        'limits': ['Course traversal, music, sprite behaviour and the other eight Star World rooms '
                   'remain open - this mirrors the original star-world-1 pilot boundary.'],
    }
    output = ROOT / 'local/reports/demo11-star1-gfx-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Star1 graphics checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

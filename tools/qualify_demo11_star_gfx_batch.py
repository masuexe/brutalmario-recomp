#!/usr/bin/env python3
"""Qualify the Star World batch graphics recovery on the Demo 1-1 line.

Sixteen shared extended graphics streams (upper-left 144, snow 225/224/1B2,
sky 190/193, center 10F, upper-inner 127/208/207/126/16C, lower-inner
1AF/1AE/1B0/163) install as global pointers into their existing empty slots -
the shared-graphics pattern. Both hosts must enter upper-left (room $004)
through its map node and render the cave terrain. The other five rooms keep
their music-request stalls at Mario Start (their songs 54/2E family are
separate recoveries, recorded as open), which this checkpoint does not mask.
"""
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-star-gfx-batch'
BINARY = 'BrutalMarioDemo11StarGraphicsBatchSNESRecomp'
S004_SCRIPT = ROOT / 'recomp/inputs/demo11-s004-entry.script'
STUCK_SCRIPT = ROOT / 'recomp/inputs/demo11-star-batch.script'
IDS = (0x144, 0x225, 0x224, 0x1B2, 0x190, 0x193, 0x10F, 0x127,
       0x208, 0x207, 0x126, 0x16C, 0x1AF, 0x1AE, 0x1B0, 0x163)


def main():
    candidate = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(candidate, cfg['output'], 'candidate')
    base = (ROOT / 'local/restoration/demo11-star1-gfx/rom.sfc').read_bytes()
    require(sha(base) == cfg['base_output']['sha256'], 'base identity differs')
    from restore_star_world_1 import pointer_offset
    for gid in IDS:
        pointer = pointer_offset(gid)
        require(base[pointer:pointer+3] == b'\xff\xff\xff', 'slot %03X was not empty on the base' % gid)
        require(candidate[pointer:pointer+3] != b'\xff\xff\xff', 'slot %03X still empty' % gid)

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / BINARY
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build identity differs')

    for host, tag in (('reference', 'ref'), ('native', 'native')):
        directory = ROOT / 'local/captures' / ('d11-star-batch-s004-' + tag)
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(S004_SCRIPT.read_bytes()),
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        body = (directory / 's004.wram.bin').read_bytes()
        require(len(body) == 0x20000 and body[0x100] == 0x14 and word(body, 0x10B) == 0x004,
                'room $004 entry missing: ' + host)
        require(body[0x71] == 0, 'player hurt at entry: ' + host)
        fb = (directory / 's004.fb.bgrx').read_bytes()
        px = [fb[i:i+4] for i in range(0, len(fb) - 4, 28)]
        dark = sum(1 for p in px if p[0] < 40 and p[1] < 40 and p[2] < 40) / len(px)
        require(dark < 0.5, 'room $004 still renders dark: ' + host)

    stuck = json.loads((ROOT / 'local/captures/d11-snow-stuck/stuck1.info.json').read_text())
    require(stuck['frame'] > 0, 'stuck-state capture missing')
    stuck_wram = (ROOT / 'local/captures/d11-snow-stuck/stuck1.wram.bin').read_bytes()
    require(stuck_wram[0x100] == 0x12 and stuck_wram[0x0DDA] == 0x54,
            'snow room stall state changed unexpectedly')

    report = {
        'scope': __doc__.strip(),
        'head': HEAD,
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'binary_sha256': build['binary_sha256'],
        'captures': {'s004': {'reference': 'local/captures/d11-star-batch-s004-ref',
                              'native': 'local/captures/d11-star-batch-s004-native'},
                     'snow_stall_state': 'local/captures/d11-snow-stuck'},
        'verified': ['sixteen shared graphics slots filled from cheap_demo, pins audited',
                     'both hosts enter room $004 and render the cave terrain',
                     'the snow room still stalls at Mario Start requesting song 54 (open item, not masked)'],
        'limits': ['Music recoveries (songs 54/2E family), course traversal, sprites and clear '
                   'behaviour for the six rooms remain open, matching the demoOnly1-line order.'],
    }
    output = ROOT / 'local/reports/demo11-star-gfx-batch-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Star batch graphics checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

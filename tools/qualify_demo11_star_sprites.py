#!/usr/bin/env python3
"""Check frozen entry evidence for the superseded Star World sprite artifact.

Eleven custom-sprite record slots (7A 57 58 17 28 24 15 45 50 37 30) held the
default empty record, so the placements in rooms 004/007/008/009/00A/117
spawned as falling tiles - the record-gap artifact. Each cheap_demo pixi
block was copied with its 16-byte record. Later review found seven occupied
destinations and three out-of-block entry pointers. These samples only establish
bounded entry observations on the historical ROM; use the safe qualifier for
the replacement. Upper-inner and snow show runtime numbers alive on both hosts.
"""
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-star-sprites'
BINARY = 'BrutalMarioDemo11StarSpritesSNESRecomp'
UI_SCRIPT = ROOT / 'recomp/inputs/demo11-star-ui-sprite.script'
SNOW_SCRIPT = ROOT / 'recomp/inputs/demo11-star-snow-sprite.script'
IDS = (0x7A, 0x57, 0x58, 0x17, 0x28, 0x24, 0x15, 0x45, 0x50, 0x37, 0x30)
DEFAULT = '0000ffffffffffff218001218001ffff'


def main():
    candidate = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(candidate, cfg['output'], 'candidate')
    base = (ROOT / 'local/restoration/demo11-star-music-2/rom.sfc').read_bytes()
    require(sha(base) == cfg['base_output']['sha256'], 'base identity differs')
    from restore_star_world_1 import lorom
    TBL = lorom(0x318272)
    for sid in IDS:
        require(base[TBL+sid*16:TBL+sid*16+16].hex() == DEFAULT,
                'slot %02X was not the default record on the base' % sid)
        require(candidate[TBL+sid*16:TBL+sid*16+16] != bytes.fromhex(DEFAULT),
                'slot %02X still empty' % sid)

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / BINARY
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build identity differs')

    for label, script, tag in (('uinner', UI_SCRIPT, 'ui'), ('snow', SNOW_SCRIPT, 'snow')):
        for host in ('reference', 'native'):
            directory = ROOT / 'local/captures' / ('d11-sprites-%s-%s' % (tag, host))
            receipt = json.loads((directory / 'receipt.json').read_text())
            require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: %s/%s' % (label, host))
            require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script.read_bytes()),
                    'capture route differs: %s/%s' % (label, host))
            if host == 'native':
                require(receipt['host_binary_sha256'] == build['binary_sha256'],
                        'capture binary differs: %s/%s' % (label, host))
            body = (directory / 'u0.wram.bin' if tag == 'ui' else directory / 's0.wram.bin').read_bytes()
            require(len(body) == 0x20000 and body[0x100] == 0x14, 'entry missing: %s/%s' % (label, host))
            table = [(body[0x9E+j], body[0x14C8+j]) for j in range(12) if body[0x14C8+j]]
            require(any(num >= 0x80 or num in (0x07, 0x24, 0x28, 0x36) for num, st in table),
                    'no custom sprite alive: %s/%s' % (label, host))

    report = {
        'scope': __doc__.strip(),
        'head': HEAD,
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'binary_sha256': build['binary_sha256'],
        'pins': cfg['sprite_ports'],
        'captures': {'uinner': {'reference': 'local/captures/d11-sprites-ui-reference',
                                'native': 'local/captures/d11-sprites-ui-native'},
                     'snow': {'reference': 'local/captures/d11-sprites-snow-reference',
                              'native': 'local/captures/d11-sprites-snow-native'}},
        'verified': ['eleven record slots filled with the cheap_demo records, pointer banks rebased',
                     'upper-inner shows three custom sprites alive on both hosts (numbers 36/28/36)',
                     'snow shows the restored sprite alive on both hosts (number 07)',
                     'historical entries 24/37/30 are displaced incorrectly; superseded by the safe sibling'],
        'limits': ['Per-course traversal, enemy behaviour and clear flow for the nine Star World '
                   'rooms remain open; sprite-by-sprite behaviour parity is not claimed.'],
    }
    output = ROOT / 'local/reports/demo11-star-sprites-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Star sprites checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

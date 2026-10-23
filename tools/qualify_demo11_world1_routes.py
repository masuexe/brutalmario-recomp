#!/usr/bin/env python3
"""Check World 1 route parity between reference and native on the Demo 1-1 line.

Eight existing demoOnly1-line routes were replayed on the Demo 1-1 head. Assisted
routes drift in player position between hosts because input timing differs, so this
qualifier compares the milestone states that must agree: level mode and room at every
sampled tag, plus the scenario key variables at the final sample.
"""
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-room0cb-gfx'
BINARY = 'BrutalMarioDemo11Room0CbGraphicsSNESRecomp'
ROUTES = [
    ('106-entry', 'world1-room106-entry.script'),
    ('106-clear', 'world1-room106-clear.script'),
    ('106-death', 'world1-room106-death.script'),
    ('010-death', 'world1-next-course-death.script'),
    ('010-subroom', 'world1-next-course-subroom.script'),
    ('120-coins', 'world1-room120-coins-save.script'),
    ('138-death', 'world1-room138-death.script'),
    ('138-natural', 'world1-room138-natural-entry.script'),
]
KEY_BYTES = {'goal_tape': 0x1493, 'map_state': 0x1ECB, 'events': 0x13CE, 'submap': 0x1F11}


def main():
    candidate = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(candidate, cfg['output'], 'candidate')
    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / BINARY
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build identity differs')

    report = {'scope': __doc__.strip(), 'head': HEAD, 'candidate_rom_sha256': sha(candidate),
              'binary_sha256': build['binary_sha256'], 'routes': {}}
    for label, script_name in ROUTES:
        ref_dir = ROOT / 'local/captures' / ('d11-w1-' + label)
        nat_dir = ROOT / 'local/captures' / ('d11-w1n-' + label)
        script = (ROOT / 'recomp/inputs' / script_name).read_bytes()
        tags = sorted(p.name[:-len('.wram.bin')] for p in ref_dir.glob('*.wram.bin'))
        require(tags, 'no samples in ' + label)
        entry = {'reference': {}, 'native': {}, 'tags': tags}
        modes = {}
        for host, directory in (('reference', ref_dir), ('native', nat_dir)):
            receipt = json.loads((directory / 'receipt.json').read_text())
            require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + label + '/' + host)
            require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script),
                    'capture route differs: ' + label + '/' + host)
            if host == 'native':
                require(receipt['host_binary_sha256'] == build['binary_sha256'],
                        'capture binary differs: ' + label)
            entry[host]['receipt'] = receipt
            modes[host] = []
            for tag in tags:
                body = (directory / (tag + '.wram.bin')).read_bytes()
                require(len(body) == 0x20000, 'incomplete WRAM: ' + label + '/' + host + '/' + tag)
                modes[host].append((tag, body[0x100], word(body, 0x10b)))
        mismatched = [(a[0], a[1], b[1], a[2], b[2]) for a, b in zip(modes['reference'], modes['native'])
                      if (a[1], a[2]) != (b[1], b[2])]
        require(not mismatched, 'level mode/room sequence differs: ' + label + ' ' + str(mismatched[:2]))
        entry['samples'] = len(tags)
        entry['final'] = {}
        last = tags[-1]
        for host, directory in (('reference', ref_dir), ('native', nat_dir)):
            body = (directory / (last + '.wram.bin')).read_bytes()
            entry['final'][host] = {'tag': last, 'mode': body[0x100], 'room': word(body, 0x10b),
                                    **{name: body[address] for name, address in KEY_BYTES.items()}}
        for name in KEY_BYTES:
            require(entry['final']['reference'][name] == entry['final']['native'][name],
                    'final key variable differs: ' + label + '/' + name)
        report['routes'][label] = entry

    report['verified'] = ['every capture is pinned to the head ROM, route and binary',
                          'the level mode and room sequences match at every sampled tag',
                          'the final goal-tape, map-state, event and submap bytes match',
                          'all eight routes complete on both hosts']
    report['not_verified'] = ['Exact player position parity between hosts: assisted routes drift',
                              'because input timing differs, so positions are excluded.',
                              'The room 010 full two-pipes route and the two obsolete 1-1 routes',
                              'are not part of this set (recorded separately).']
    output = ROOT / 'local/reports/demo11-world1-route-parity.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('World 1 route parity checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Qualify the repaired World 1 overworld route on the Demo 1-1 line.

The route-enable cells around the 1-1 node are restored in ROM, so the real
1-1 clear event walks the player to the 1-2 node and the course can be entered
with the normal button. No map, route or completion fixture exists after the
goal: the walk, node selection and entry are performed by the game on both
hosts. The 1-1 goal approach itself remains the accepted assisted flight.
"""
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-world1-route'
BINARY = 'BrutalMarioDemo11World1RouteSNESRecomp'
SCRIPT = ROOT / 'recomp/inputs/demo11-world1-route-walk.script'

# Every write in the route-walk script, for review: intro/menu dismissal, the
# practice map transfer to the 1-1 node, and the assisted flight fixtures.
ALLOWED_FIXTURES = {0x109: 1, 0x100: 1, 0x1f11: 2, 0x1f17: 8, 0x1f1f: 8,
                    0x85: 1, 0x1490: 1, 0x1497: 1}


def main():
    candidate = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(candidate, cfg['output'], 'candidate')
    base = (ROOT / 'local/restoration/demo11-sprite0b/rom.sfc').read_bytes()
    require(sha(base) == cfg['base_output']['sha256'], 'base identity differs')
    diffs = [i for i in range(len(base)) if base[i] != candidate[i]]
    require(diffs == [0x67A63, 0x67A72, 0x67A74], 'candidate changed more than the three route cells')

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / BINARY
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build identity differs')

    for line in SCRIPT.read_text().splitlines():
        parts = line.split()
        if parts and parts[0] in ('poke', 'forcepoke', 'pokefor'):
            address = int(parts[1], 16)
            require(address in ALLOWED_FIXTURES and len(bytes.fromhex(parts[-1])) <= ALLOWED_FIXTURES[address],
                    'review new fixture write: ' + line)

    states = {}
    for host, directory in (('reference', ROOT / 'local/captures/d11-route-walk-ref'),
                            ('native', ROOT / 'local/captures/d11-route-walk-native')):
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(SCRIPT.read_bytes()),
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        require(b'quit' in (directory / 'run.log').read_bytes(), 'route incomplete: ' + host)
        samples = {}
        for tag in ('on_map', 'route_left', 'route_settled', 'entered', 'entered_settled'):
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, 'incomplete WRAM: ' + host + '/' + tag)
            samples[tag] = body
        states[host] = samples

    for host, samples in states.items():
        cleared = samples['on_map']
        require(cleared[0x100] == 0x0E and cleared[0x1ECB] == 0x8A and cleared[0x13CE] == 0x01,
                'clear state missing on the map: ' + host)
        for tag in ('on_map', 'route_left', 'route_settled'):
            body = samples[tag]
            require(word(body, 0x1F17) == 0x0018 and word(body, 0x1F19) == 0x01B8,
                    'player did not stand on the 1-2 node: ' + host + '/' + tag)
            require((body[0xCA84], body[0xCA93], body[0xCA95]) == (0x20, 0x04, 0x04),
                    'repaired route cells not loaded: ' + host + '/' + tag)
        for tag in ('entered', 'entered_settled'):
            body = samples[tag]
            require(body[0x100] == 0x14 and word(body, 0x10B) == 0x0010,
                    '1-2 entry missing: ' + host + '/' + tag)

    for tag in ('on_map', 'route_left', 'route_settled', 'entered', 'entered_settled'):
        for address in (0x100, 0x1ECB, 0x13CE, 0x10B, 0x1F17, 0x1F19, 0x10C):
            require(states['reference'][tag][address] == states['native'][tag][address],
                    f'host divergence at {tag}/{address:#x}')

    report = {
        'scope': __doc__.strip(),
        'head': HEAD,
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'binary_sha256': build['binary_sha256'],
        'changed_bytes': ['0x67A63: 00->20', '0x67A72: 00->04', '0x67A74: 00->04'],
        'captures': {'reference': 'local/captures/d11-route-walk-ref',
                     'native': 'local/captures/d11-route-walk-native'},
        'verified': ['real 1-1 clear event walks the player to the 1-2 node (0x18,0x1B8)',
                     'route cells 20/04/04 load from ROM on both hosts',
                     'normal level-entry button opens room 010 on both hosts',
                     'clear state 1ECB=8A, 13CE=01 survives to the map',
                     'exactly three bytes differ from the accepted sprite0b base'],
        'limits': ['The 1-1 goal approach is the accepted assisted flight; the map walk '
                   'and course entry after the goal use no fixtures.',
                   'Onward 1-2 -> later World 1 map travel was not re-qualified here.'],
    }
    output = ROOT / 'local/reports/demo11-world1-route-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('World 1 route repair checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

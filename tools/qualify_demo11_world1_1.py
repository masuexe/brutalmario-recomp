#!/usr/bin/env python3
"""Qualify World 1-1's goal and course-clear event on the Demo 1-1 base.

The newer 1-1 places its goal tape on the end platform at the level's far right
(x~0x16DC, y=0x140), not mid-course. This route flies there with labelled fixtures,
disables them, walks left into the tape, and lets the game perform the clear.
"""
import hashlib, json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-sprite0b'
BINARY = 'BrutalMarioDemo11Sprite0BSNESRecomp'
SCRIPT = 'recomp/inputs/demo11-world1-1-goal.script'


def main():
    candidate = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(candidate, cfg['output'], 'candidate')
    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    require(sha((ROOT / 'local/build' / HEAD / BINARY).read_bytes()) == build['binary_sha256'],
            'native build identity differs')
    script_sha = hashlib.sha256((ROOT / SCRIPT).read_bytes()).hexdigest()

    report = {'scope': __doc__.strip(), 'head': HEAD, 'candidate_rom_sha256': sha(candidate),
              'binary_sha256': build['binary_sha256'], 'hosts': {}, 'captures': {}}
    states = {}
    for host, name in (('reference', 'd11s0b-11-goal-ref'), ('native', 'd11s0b-11-goal-native')):
        directory = ROOT / 'local/captures' / name
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == script_sha,
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        log = (directory / 'run.log').read_bytes()
        require(b'quit' in log and b'timed out' not in log, 'route incomplete: ' + host)
        report['captures'][name] = receipt
        host_states = {}
        for tag in ('at_end', 'at_goal', 'completed_map', 'on_map', 'settled'):
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, 'incomplete WRAM: ' + host + '/' + tag)
            host_states[tag] = {'mode': body[0x100], 'room': word(body, 0x10b),
                                'x': word(body, 0x94), 'y': word(body, 0x96),
                                'goal_tape': body[0x1493], 'map_state': body[0x1ECB],
                                'events': body[0x13CE]}
        require(host_states['at_end']['room'] == 0x105 and host_states['at_end']['x'] >= 0x17E0,
                'route did not reach the far end platform: ' + host)
        require(host_states['at_goal']['goal_tape'] != 0,
                'goal tape was never touched: ' + host)
        completed = host_states['completed_map']
        require(completed['mode'] == 0x0E, 'no map return after the clear: ' + host)
        require(completed['map_state'] == 0x8A and completed['events'] == 0x01,
                'course-clear event writes differ: ' + host)
        states[host] = host_states
        report['hosts'][host] = host_states

    require(states['reference'] == states['native'],
            'reference and native disagree on the course-clear states')
    report['verified'] = ['every capture is pinned to the head ROM, route and native binary',
                          'the route reaches the level far end in room 0x105',
                          'the goal tape variable becomes non-zero on contact',
                          'the clear returns to the map with map state 0x8A and event 0x01',
                          'reference and native agree at every sampled state']
    report['not_verified'] = ['Unassisted traversal: the route uses labelled air-swim and',
                              'invulnerability fixtures to reach the far end.',
                              'Next-course selection after the clear (the map cursor step is not',
                              'part of this route).']
    output = ROOT / 'local/reports/demo11-world1-1-goal.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 World 1-1 goal checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
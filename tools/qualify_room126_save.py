#!/usr/bin/env python3
"""Check room126 clear/save ownership, including the old node-override control."""
import argparse
import json
from pathlib import Path

from qualify_mazo_cumulative import regression_capture
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-product-r14'


def samples(name, script):
    directory, tags = regression_capture(name, TARGET, script)
    result = {}
    for tag in tags:
        w = (directory / (tag + '.wram.bin')).read_bytes()
        s = (directory / (tag + '.sram.bin')).read_bytes()
        require(len(w) == 0x20000 and len(s) == 0x8000, 'incomplete memory: ' + tag)
        info = json.loads((directory / (tag + '.info.json')).read_text())
        result[tag] = (w, s, dict(frame=info['frame'], mode=w[0x100],
                                room=word(w, 0x10b), translevel=w[0x13bf],
                                lives=w[0xdbe], goal=w[0x1493], exits=w[0x1f2e],
                                flags=w[0x1ea2:0x1f02].hex(),
                                wram_sha256=sha(w), sram_sha256=sha(s)))
    return directory, result


def check_route(states, flag_index):
    entry = states['e1'][0]
    require(entry[0x100] == 0x14 and word(entry, 0x10b) == 0x126 and
            entry[0x13bf] == 0x4a and entry[0xdbe] == 4, 'wrong room126 entry')
    touched = states['j10'][0]
    later = states['j15'][0]
    require(0 < later[0x1493] < touched[0x1493] and touched[0xdbe] == 5 and
            entry[0x1493] == 0 and states['j20'][0][0x1493] == 0,
            'real goal/life award absent')
    address = 0x1ea2 + flag_index
    require(not entry[address] & 0x80, 'control is already cleared')
    for tag in ('j20', 'saved_map', 'file_reload'):
        w, s, _ = states[tag]
        # File reload restores the baseline life count; lives are not this
        # completion-persistence assertion.
        require(w[0x100] == 0x0e and w[0xdbe] == (4 if tag == 'file_reload' else 5),
                'wrong map/reload: ' + tag)
        require(w[address] == entry[address] | 0x80 and
                s[flag_index] == w[address] == s[0x1ad + flag_index],
                'flag or either save copy absent: ' + tag)
        require(w[0x1f2e] == entry[0x1f2e] + 1, 'exit count did not persist')
    changed = [i for i in range(0x60)
               if entry[0x1ea2 + i] != states['saved_map'][0][0x1ea2 + i]]
    require(changed == [flag_index], 'unexpected completion ownership')
    return dict(flag_index=flag_index, flag_address=f'{address:04X}',
                saved_offsets=[flag_index, 0x1ad + flag_index],
                samples={tag: row[2] for tag, row in states.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', default='room126-clear-save-reload-v1')
    parser.add_argument('--candidate', default='room126-node-clear-save-reload-v1')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    cp, control = samples(args.control, 'room126-clear-save-reload.script')
    np, candidate = samples(args.candidate, 'room126-node-clear-save-reload.script')
    old = check_route(control, 5)
    node = candidate['node'][0]
    require(node[0x100] == 0x0e and node[0xd727] == 0x4a and
            node[0x1f11] == 6 and word(node, 0x1f17) == 0x178 and
            word(node, 0x1f19) == 0x128,
            'actual node translevel differs')
    new = check_route(candidate, 0x4a)
    report = dict(target=TARGET, control=dict(capture=args.control, **old),
                  candidate=dict(capture=args.candidate, **new),
                  receipts=[sha((p / 'receipt.json').read_bytes()) for p in (cp, np)],
                  limits=['Map coordinates are fixtures; no ordinary map-travel acceptance.',
                          'Room126 is outside the verified Forest World2 course list.',
                          'The old override control saves node05, not room126 completion.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: real goal, actual-node completion, both SRAM copies and File A reload')


if __name__ == '__main__':
    main()

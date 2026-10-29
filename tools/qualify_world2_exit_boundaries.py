#!/usr/bin/env python3
"""Check assisted screen-exit boundaries; no traversal, clear or save claim."""
import argparse
import json
from pathlib import Path

from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-product-r13'
CASES = ((0x121, 4, 0xD7, 5, 0x1D7),
         (0x124, 2, 0x27, 4, 0x027),
         (0x124, 3, 0x27, 4, 0x027),
         (0x124, 11, 0x29, 4, 0x029),
         (0x124, 13, 0x30, 4, 0x030),
         (0x123, 0, 0x23, 5, 0x123),
         (0x123, 4, 0x42, 4, 0x042))


def state(directory, tag):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    require(len(body) == 0x20000, 'incomplete WRAM: ' + tag)
    info = json.loads((directory / (tag + '.info.json')).read_text())
    return body, dict(frame=info['frame'], wram_sha256=sha(body),
                      mode=body[0x100], room=word(body, 0x10B),
                      lives=body[0xDBE], sublevels=body[0x141A])


def checked_capture(name, script):
    directory, receipt = capture(name, TARGET, script, native=True)
    build = json.loads((ROOT / 'local/build' / TARGET / 'm1-build.json').read_text())
    for key in ('native_content', 'runtime_patches', 'analysis'):
        require(receipt[key] == build[key], 'capture/build identity differs: ' + key)
    require('BRK' not in (directory / 'run.log').read_text(), 'BRK: ' + name)
    require((directory / 'input.script').read_bytes() == b'turbo on\n' +
            (ROOT / 'recomp/inputs' / script).read_bytes(), 'copied script differs')
    return directory, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='w2-r13')
    parser.add_argument('--control', default='w2-star-control-v1')
    parser.add_argument('--output', default='local/reports/world2-exit-boundaries-v1.json')
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    require(sha(rom) == cfg['output']['sha256'], 'ROM differs')
    # Recipient routine: explicit-exit bit 2, secondary bit 1, water bit 3,
    # and destination high bit 0. Pin the actual instructions used for this claim.
    address = 0x05DC50
    code = bytes.fromhex('bdd8192904f018bdd819484829024a8d931b6829080a0a0a8d2a196829016b')
    require(rom[lorom(address):lorom(address) + len(code)] == code,
            'exit flag decoder changed')
    results = []
    for room, screen, low, flags, destination in CASES:
        stem = f'room{room:03x}-screen{screen:02x}'
        name = f'{args.prefix}-{room:03x}-{screen:02x}-v1'
        directory, receipt = checked_capture(name, 'world2-' + stem + '.script')
        active, before = state(directory, 'active')
        require(before['mode'] == 0x14 and before['room'] == room, 'wrong entry: ' + name)
        require(active[0x19B8 + screen] == low and active[0x19D8 + screen] == flags,
                'live exit table differs: ' + name)
        require(flags & 4 and not flags & 2, 'case is not an explicit primary exit')
        require(low | ((flags & 1) << 8) == destination, 'wrong primary destination')
        samples = {}
        counters = []
        for tag in ('next', 'later'):
            body, sample = state(directory, tag)
            require(sample['room'] == destination and sample['mode'] in (0x13, 0x14),
                    'wrong destination: ' + name + '/' + tag)
            require(sample['lives'] == before['lives'] == 4, 'life lost: ' + name)
            require(sample['sublevels'] == before['sublevels'] + 1,
                    'transition did not execute: ' + name)
            samples[tag] = sample
            counters.append(body[0x14])
        require(samples['later']['mode'] == 0x14, 'destination never became playable')
        require(samples['later']['frame'] > samples['next']['frame'], 'invalid sample order')
        require(counters[0] != counters[1], 'destination guest frame counter stopped')
        results.append(dict(capture=name, receipt=receipt, room=room, screen=screen,
                            exit_low=low, exit_flags=flags, destination=destination,
                            active=before, samples=samples))
    directory, receipt = checked_capture(args.control, 'world2-star-exit-control.script')
    control = {}
    for tag, room, mode in (('active', 5, 0x14), ('next', 0x48, 0x14),
                            ('room51', 0x51, 0x14), ('side_exit', 0x51, 0x0E)):
        _, sample = state(directory, tag)
        require(sample['room'] == room and sample['mode'] == mode and sample['lives'] == 4,
                'Star control differs: ' + tag)
        control[tag] = sample
    report = dict(target=TARGET, rom_sha256=sha(rom), decoder_address=address,
                  decoder_sha256=sha(code), cases=results,
                  control=dict(capture=args.control, receipt=receipt, samples=control),
                  limits=['Map-node override, position and pipe-action fixtures.',
                          'No ordinary traversal, real pipe activation, clear, map route or save claim.',
                          'Secondary and water exits are decoded statically, not qualified here.',
                          'Course names and world membership require version-specific verification.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: {len(results)} primary exit boundaries and Star control; {output.relative_to(ROOT)}')


if __name__ == '__main__':
    main()

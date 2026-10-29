#!/usr/bin/env python3
"""Qualify the assisted hollow normal save and reproduce its missing A2 branch."""
import argparse
import json
import re
from pathlib import Path

from audit_star_boss_donors import sprite_table
from prepare_rom import verify
from qualify_forest_course_identity import native_capture, sprite_list
from qualify_forest_shack import protected_stream, reference_capture, state as base_state, PLANES
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-product-r13'
NORMAL = ('node', 'active', 'next', 'destination', 'before_goal', 'touched',
          'clear_map', 'file_reload', 'onward')
BRANCH = ('node', 'active', 'before_branch', 'branch')
FIELDS = ('mode', 'room', 'lives', 'player_x', 'player_y', 'goal', 'map', 'map_x', 'map_y',
          'actors', 'wram_sha256', 'sram_sha256', 'vram_sha256')
PLACEHOLDER = '0000ffffffffffff218001218001ffff'


def load(path):
    return json.loads(path.read_text())


def state(directory, tag):
    body, base = base_state(directory, tag)
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    sample = {key: base[key] for key in FIELDS}
    sample.update(flag=body[0x1EE5], save=[saved[0x43], saved[0x1F0]])
    for actor in sample['actors']:
        i = actor['slot']
        actor.update(custom=body[0x1AB9E + i], extra=body[0x1AB10 + i])
    return body, sample


def assert_route(states, route):
    for tag, (_, s) in states.items():
        cleared = tag in ('clear_map', 'file_reload', 'onward')
        flag = 0x8F if cleared else 0x0F
        require(s['lives'] == 4 and s['flag'] == flag and s['save'] == [flag, flag],
                'life/clear/save mismatch: ' + tag)
        if tag in ('node', 'clear_map', 'file_reload'):
            xy = (0x1E8, 0x188) if cleared else (0x1B8, 0x158)
            require(s['mode'] == 0x0E and s['map'] == 0 and
                    (s['map_x'], s['map_y']) == xy, 'wrong actual map node: ' + tag)
        else:
            rooms = dict(active=0x11F, next=0x39, destination=0x43, before_goal=0x43,
                         touched=0x43, onward=0x114, before_branch=0x11F,
                         branch=0x182 if route == 'up' else 0x11F)
            require(s['mode'] == 0x14 and s['room'] == rooms[tag], 'wrong active room: ' + tag)
    require(states['node'][0][0xD35B] == 0x43 and states['active'][0][0x13BF] == 0x43,
            'not the actual hollow-course node/translevel')
    active = states['active'][0]
    require((active[0x19BA], active[0x19DA]) == (0x39, 4) and
            (active[0x19BB], active[0x19DB]) == (0x82, 5), 'existing entrance exits differ')
    if route == 'normal':
        require(states['onward'][0][0x13BF] == 0x38, 'wrong onward translevel')
        room39 = states['next'][0]
        require((room39[0x19D0], room39[0x19F0]) == (0x43, 4), 'existing screen18 exit differs')
        before, touched = states['before_goal'][1], states['touched'][1]
        require(before['goal'] == 0 and any(a['sprite'] == 0x7B and a['status'] == 8
                                           for a in before['actors']), 'goal tape absent')
        require(touched['goal'] == 0xE0 and any(a['sprite'] == 0x7B and a['status'] == 6
                                          for a in touched['actors']), 'real goal touch absent')
    else:
        before, after = states['before_branch'][1], states['branch'][1]
        require((before['player_x'], before['player_y']) == (800, 352), 'branch fixture moved')
        require(after['goal'] == 0 and not after['actors'], 'branch diagnostic changed')


def source_review(rom):
    versions = {v['id']: v for v in load(ROOT / 'config/content-versions.json')['versions']}
    sources, bodies = {}, {}
    # Explicit official sources only; numeric slots from older families are not
    # asserted to represent the newer room182 program.
    for version in ('demo-1-1', 'demo-only-1', 'boss', '7hero', 'mazo', 'cheap-demo'):
        donor = (ROOT / 'local/content-versions' / version / 'rom.sfc').read_bytes()
        pin = load(ROOT / 'config/boss-donor.json')['output'] if version == 'boss' else versions[version]['output']
        verify(donor, pin, version)
        bodies[version] = donor
        table = sprite_table(donor)[2]
        record = donor[lorom(table) + 0xA20:lorom(table) + 0xA30]
        require(record.hex() == ('012200b735839944bfd730ecd7300000' if version == 'demo-only-1'
                                 else PLACEHOLDER), 'official A2 source selection changed')
        rooms = {}
        for room in (0x11F, 0x39, 0x43):
            rows = {}
            for tab, label in ((0x05E000, 'layer1'), (0x05E600, 'layer2')):
                raw, info = protected_stream(donor, tab, room)
                current = protected_stream(rom, tab, room)[0]
                equal = raw == current
                # Newer room039 agrees with boss/7hero; older mazo/cheap streams
                # and placements differ. Record those differences; do not port them.
                expected = not (label == 'layer1' and
                                ((room == 0x11F and version in ('boss', '7hero', 'mazo', 'cheap-demo')) or
                                 (room == 0x39 and version in ('mazo', 'cheap-demo'))))
                require(equal == expected, 'official room allocation comparison changed')
                rows[label] = dict(info, matches_recipient_allocation=equal)
            sprites = sprite_list(donor, room)
            equal = sprites == sprite_list(rom, room)
            require(equal == (room != 0x39 or version not in ('mazo', 'cheap-demo')),
                    'official sprite list comparison changed')
            rows['sprites'] = dict(size=len(sprites), sha256=sha(sprites), matches_recipient=equal)
            rooms[f'{room:03X}'] = rows
        sources[version] = dict(rom_sha256=sha(donor), spriteA2_record=record.hex(), rooms=rooms)
    table = sprite_table(rom)[2]
    require(rom[lorom(table) + 0xA20:lorom(table) + 0xA30].hex() == PLACEHOLDER,
            'A2 is no longer missing; revise diagnostic acceptance')
    require(sprite_list(rom, 0x182).hex() == '0069d0a2ff', 'room182 placement changed')
    donor = bodies['demo-only-1']
    require(sprite_list(donor, 0x182) == sprite_list(rom, 0x182), 'source branch placement differs')
    # The protected program begins with MDK; the init entry is three bytes in.
    offset = lorom(0x30D7BC)
    header = donor[offset - 8:offset]
    require(header == bytes.fromhex('53544152df1c20e3'), 'candidate program allocation changed')
    payload = donor[offset:offset + 7392]
    require(sha(payload) == '22d5da0dceaf8d32a0a8ce1f56af7d75f6ba542ec3f55596fe871b5723723ea3',
            'candidate program differs')
    require(sprite_rooms(donor, 0xA2) == [0x104, 0x182], 'candidate placement scope differs')
    branch = {}
    for tab, label in ((0x05E000, 'layer1'), (0x05E600, 'layer2')):
        a, pin = protected_stream(rom, tab, 0x182)
        b, source_pin = protected_stream(donor, tab, 0x182)
        branch[label] = dict(recipient=pin, source=source_pin,
                             byte_differences=[dict(offset=i, recipient=x, source=y)
                                               for i, (x, y) in enumerate(zip(a, b)) if x != y])
        require(len(a) == len(b), 'branch allocation sizes differ')
    return dict(official_sources=sources, room182=branch,
                candidate_A2=dict(source='demo-only-1', address='30D7BC', size=7392,
                                  sha256=sha(payload), init='30D7BF', main='30D7EC',
                                  source_rooms=['104', '182'], installed=False,
                                  status='Protected candidate only; dependency and behavior review pending.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='forest-r13-hollow')
    parser.add_argument('--output', default='local/reports/forest-hollow-acceptance-v1.json')
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(rom, load(ROOT / 'config/restorations' / (TARGET + '.json'))['output'], TARGET)
    sources = source_review(rom)
    results = {}
    for route, tags, script in (('normal', NORMAL, 'forest-hollow-normal-save.script'),
                                 ('up', BRANCH, 'forest-hollow-branch-up.script'),
                                 ('down', BRANCH, 'forest-hollow-branch-down.script')):
        version = 'v2' if route == 'normal' else 'v1'
        native, nr = native_capture(args.prefix + '-' + route + '-' + version, TARGET, script)
        ref, rr = reference_capture(args.prefix + '-' + route + '-ref-' + version, script, rom)
        mounts = re.findall(r'\[native-seven\] bank=([0-9A-F]+) resolutions=(\d+) executed_page_instructions=(\d+)',
                            (native / 'run.log').read_text())
        require(mounts and all(int(reads) == int(executed) == 0 for _, reads, executed in mounts),
                'external pack used; same-image subset requires review')
        states = {host: {tag: state(directory, tag) for tag in tags}
                  for host, directory in (('native', native), ('reference', ref))}
        for host in states:
            assert_route(states[host], route)
        comparisons = {}
        for tag in tags:
            a, x = states['native'][tag]
            b, y = states['reference'][tag]
            moving = route == 'normal' and tag in ('destination', 'before_goal', 'touched')
            differences = {}
            for key in x.keys() - {'wram_sha256', 'sram_sha256', 'vram_sha256'}:
                if moving and key == 'player_y':
                    require(abs(x[key] - y[key]) <= 1, 'player Y differs by more than one pixel')
                elif moving and key == 'actors':
                    require(len(x[key]) == len(y[key]) == 1, 'expected one tape actor')
                    u, v = x[key][0], y[key][0]
                    require(u['sprite'] == v['sprite'] == 0x7B and abs(u['y'] - v['y']) <= 1 and
                            {k: w for k, w in u.items() if k != 'y'} ==
                            {k: w for k, w in v.items() if k != 'y'}, 'tape actor mismatch')
                else:
                    require(x[key] == y[key], 'semantic/actor mismatch: ' + route + '/' + tag + '/' + key)
                if x[key] != y[key]:
                    differences[key] = dict(native=x[key], reference=y[key])
            require(all(a[start:start + 0x1B00] == b[start:start + 0x1B00] for start in PLANES),
                    'Map16 buffer mismatch: ' + route + '/' + tag)
            comparisons[tag] = dict(native=x, reference=y, observed_differences=differences,
                                    exact_map16_bytes=4 * 0x1B00)
        results[route] = dict(native_receipt=nr, reference_receipt=rr,
                              unused_external_mounts=len(mounts), samples=comparisons)
    report = dict(target=TARGET, rom_sha256=sha(rom), checker_sha256=sha(Path(__file__).read_bytes()),
                  **sources, routes=results,
                  limits=['Position, pipe-action and immunity fixtures bypass full traversal.',
                          'Room043 moving player/tape Y positions permit one pixel; observed differences are recorded.',
                          'A2 branch remains missing; source code candidate is not restored or behavior-qualified.',
                          'Same-image reference applies only to these unused-pack routes.',
                          'No full WRAM/framebuffer/audio, Dragon Coins or full-course acceptance.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(output, sha(output.read_bytes()))


if __name__ == '__main__':
    main()

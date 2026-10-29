#!/usr/bin/env python3
"""Check eight real color choices, wrong-color reset and Lost Forest normal save."""
import argparse
import json
import re
from pathlib import Path

from audit_star_boss_donors import sprite_table
from prepare_rom import verify
from qualify_forest_course_identity import native_capture, sprite_list
from qualify_forest_shack import protected_stream, reference_capture, state as base_state, PLANES
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-product-r13'
NORMAL = ('node', 'active', *(f'maze{i}' for i in range(9)), 'before_goal', 'touched',
          'clear_map', 'file_reload', 'onward')
WRONG = ('node', 'active', 'maze0', 'maze1', 'wrong_color')
CHOICES = (2, 3, 0, 3, 0, 0, 1, 3)  # left, right, up, down
FIELDS = ('mode', 'room', 'lives', 'player_x', 'player_y', 'goal', 'map', 'map_x', 'map_y',
          'actors', 'wram_sha256', 'sram_sha256', 'vram_sha256')


def load(path):
    return json.loads(path.read_text())


def state(directory, tag):
    body, base = base_state(directory, tag)
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    sample = {key: base[key] for key in FIELDS}
    sample.update(flag=body[0x1EE9], save=[saved[0x47], saved[0x1F4]],
                  progress=body[0x14AF], palettes=list(body[0x1FCCC:0x1FCD0]),
                  flower_seed=body[0x1FDDD], target=body[0x1FDDE], flower_pattern=body[0x1C004])
    for actor in sample['actors']:
        i = actor['slot']
        actor.update(custom=body[0x1AB9E + i], extra=body[0x1AB10 + i], quadrant=body[0x1528 + i])
    return body, sample


def assert_route(states, route):
    for tag, (_, s) in states.items():
        cleared = tag in ('clear_map', 'file_reload', 'onward')
        flag = 0x88 if cleared else 8
        require(s['lives'] == 4 and s['flag'] == flag and s['save'] == [flag, flag],
                'life/clear/save mismatch: ' + tag)
        if tag == 'node':
            require(s['mode'] == 0x0E and s['map'] == 0 and
                    (s['map_x'], s['map_y']) == (0x188, 0x178), 'wrong actual map node')
        elif tag in ('clear_map', 'file_reload'):
            require(s['mode'] == 0x0E and s['map'] == 0 and
                    (s['map_x'], s['map_y']) == (0x1B8, 0x158), 'wrong onward node')
        else:
            room = 0x123 if tag == 'active' else 0x11F if tag == 'onward' else 0x50 if (
                tag in ('maze8', 'before_goal', 'touched')) else 0x42
            require(s['mode'] == 0x14 and s['room'] == room, 'wrong active room: ' + tag)
    node = states['node'][0]
    require(node[0xD378] == 0x47, 'node assignment was not the real Forest node')
    require(states['maze0'][1]['progress'] == 0, 'maze started with progress')
    rounds = range(8) if route == 'normal' else range(1)
    for i in rounds:
        before = states[f'maze{i}'][1]
        after = states[f'maze{i + 1}'][1]
        require(before['progress'] == i and after['progress'] == i + 1, 'round did not advance')
        require(sorted(before['palettes']) == [3, 7, 13, 15] and
                before['palettes'][CHOICES[i]] == before['target'], 'chosen exit does not match flower color')
        require(any(a['custom'] == 8 and a['status'] == 8 and a['extra'] & 4
                    for a in before['actors']), 'maze controller absent')
    if route == 'wrong':
        require(states['maze1'][1]['palettes'][0] != states['maze1'][1]['target'],
                'negative control selected the correct color')
        require(states['wrong_color'][1]['progress'] == 0 and
                states['wrong_color'][1]['goal'] == 0, 'wrong color did not reset without clearing')
    else:
        require(states['maze8'][1]['progress'] == 8, 'eight-round boundary absent')
        before = states['before_goal'][1]
        require(before['goal'] == 0 and any(a['sprite'] == 0x7B and a['status'] == 8
                                           for a in before['actors']), 'goal tape absent')
        touched = states['touched'][1]
        require(touched['goal'] > 0 and any(a['sprite'] == 0x7B and a['status'] == 6
                                           for a in touched['actors']), 'real goal touch absent')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='forest-r13-lost')
    parser.add_argument('--output', default='local/reports/forest-lost-acceptance-v1.json')
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(rom, load(ROOT / 'config/restorations' / (TARGET + '.json'))['output'], TARGET)
    versions = {v['id']: v for v in load(ROOT / 'config/content-versions.json')['versions']}
    bodies, sources = {}, {}
    for version in ('demo-1-1', 'demo-only-1', 'boss', '7hero', 'mazo', 'cheap-demo'):
        donor = (ROOT / 'local/content-versions' / version / 'rom.sfc').read_bytes()
        pin = load(ROOT / 'config/boss-donor.json')['output'] if version == 'boss' else versions[version]['output']
        verify(donor, pin, version)
        bodies[version] = donor
        table = sprite_table(donor)[2]
        record = donor[lorom(table) + 8 * 16:lorom(table) + 9 * 16]
        if version != 'cheap-demo':
            require(record[0] == 0, 'a newer official sprite08 needs source-selection review')
        rows = {}
        for room in (0x123, 0x42, 0x50):
            rows[f'{room:03X}'] = {}
            for table, label in ((0x05E000, 'layer1'), (0x05E600, 'layer2')):
                raw, info = protected_stream(donor, table, room)
                require(raw == protected_stream(rom, table, room)[0], 'official room stream differs')
                rows[f'{room:03X}'][label] = info
            sprites = sprite_list(donor, room)
            require(sprites == sprite_list(rom, room), 'official sprite list differs')
            rows[f'{room:03X}']['sprites_sha256'] = sha(sprites)
        sources[version] = dict(rom_sha256=sha(donor), sprite08_record=record.hex(), rooms=rows)
    recipe_path = ROOT / 'config/restorations/demo11-sprites-cheap-demo.json'
    recipe = next(s for s in load(recipe_path)['custom_sprites'] if s['id'] == '08')
    size = recipe['block']['size']
    source = bodies['cheap-demo']
    original = source[lorom(int(recipe['source_address'], 16)):][:size]
    installed = rom[lorom(int(recipe['destination_address'], 16)):][:size]
    verify(original, recipe['block'], 'official sprite08 block')
    require(installed == original, 'installed sprite08 differs from official program')
    table = sprite_table(rom)[2]
    require(rom[lorom(table) + 128:lorom(table) + 144].hex() == recipe['record_after'],
            'installed sprite08 record differs')
    results = {}
    for route, tags, script in (('normal', NORMAL, 'forest-lost-normal-save.script'),
                                 ('wrong', WRONG, 'forest-lost-wrong-color.script')):
        native, native_receipt = native_capture(args.prefix + '-' + route + '-v1', TARGET, script)
        ref, ref_receipt = reference_capture(args.prefix + '-' + route + '-ref-v2', script, rom)
        mounts = re.findall(r'\[native-seven\] bank=([0-9A-F]+) resolutions=(\d+) executed_page_instructions=(\d+)',
                            (native / 'run.log').read_text())
        require(mounts and all(int(reads) == int(executed) == 0 for _, reads, executed in mounts),
                'external pack used; same-image subset needs review')
        states = {host: {tag: state(directory, tag) for tag in tags}
                  for host, directory in (('native', native), ('reference', ref))}
        for host in states:
            assert_route(states[host], route)
        comparisons = {}
        for tag in tags:
            a, x = states['native'][tag]
            b, y = states['reference'][tag]
            for key in x.keys() - {'wram_sha256', 'sram_sha256', 'vram_sha256'}:
                require(x[key] == y[key], 'semantic/actor mismatch: ' + route + '/' + tag + '/' + key)
            require(all(a[start:start + 0x1B00] == b[start:start + 0x1B00] for start in PLANES),
                    'Map16 buffer mismatch: ' + tag)
            comparisons[tag] = dict(native=x, reference=y, exact_map16_bytes=4 * 0x1B00)
        results[route] = dict(native_receipt=native_receipt, reference_receipt=ref_receipt,
                              captures=dict(native=str(native.relative_to(ROOT)), reference=str(ref.relative_to(ROOT))),
                              unused_external_mounts=len(mounts), samples=comparisons)
    report = dict(target=TARGET, rom_sha256=sha(rom), checker_sha256=sha(Path(__file__).read_bytes()),
                  recipe_sha256=sha(recipe_path.read_bytes()), installed_program_sha256=sha(installed),
                  official_sources=sources, directions=['left', 'right', 'up', 'down'], choices=CHOICES,
                  routes=results, limits=['Position/initial pipe/immunity fixtures bypass the first log and P-switch puzzle.',
                                         'Color selections use actual palette state; no puzzle or completion writes.',
                                         'Same-image reference result covers only these unused-pack routes.',
                                         'No full WRAM/framebuffer, full puzzle traversal, Dragon Coin or audio claim.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: eight correct choices, wrong-color reset, real tape, save/reload and onward entry; {output}')


if __name__ == '__main__':
    main()

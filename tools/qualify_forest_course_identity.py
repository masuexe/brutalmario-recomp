#!/usr/bin/env python3
"""Verify version-local Forest identities and assisted Fishing Spree save flow."""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'config/forest-course-identity.json'


def read_json(path):
    return json.loads(path.read_text())


def sprite_list(rom, room):
    slot = lorom(0x05EC00) + room * 2
    address = (rom[lorom(0x0EF100) + room] << 16) | word(rom, slot)
    require(address & 0x8000, 'sprite pointer is outside LoROM')
    offset = lorom(address)
    for count in range(121):
        end = offset + 1 + count * 3
        require(end < len(rom) and end // 0x8000 == offset // 0x8000,
                'sprite list leaves its bank')
        if rom[end] == 0xFF:
            return rom[offset:end + 1]
    raise ValueError('sprite list has no bounded terminator')


def fingerprint(rom, room, translevel):
    # The installed name routine multiplies translevel by 19 and reads a
    # version-local table. Check the multiplier and LDA.l before using it.
    routine = lorom(0x03BB20)
    require(rom[lorom(0x048E81):lorom(0x048E81) + 4] == bytes.fromhex('2220bb03'),
            'name routine entry changed')
    require(rom[routine:routine + 17] == bytes.fromhex('85020a0a0a0a8500a5020a1865026500aa'),
            'name stride changed')
    require(rom[routine + 0x36] == 0xBF, 'name table load changed')
    table = int.from_bytes(rom[routine + 0x37:routine + 0x3A], 'little')
    name_offset = lorom(table) + translevel * 19
    slot = lorom(0x05E000) + room * 3
    pointer = int.from_bytes(rom[slot:slot + 3], 'little')
    require(pointer & 0x8000, 'layout pointer is outside LoROM')
    window = rom[lorom(pointer):lorom(pointer) + 256]
    require(len(window) == 256, 'incomplete layout window')
    sprites = sprite_list(rom, room)
    return dict(name_table=f'{table:06X}',
                name_tiles=rom[name_offset:name_offset + 19].hex(),
                layout_window=dict(size=256, sha256=sha(window)),
                sprite_list=dict(size=len(sprites), sha256=sha(sprites)))


def state(directory, tag):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    require(len(body) == 0x20000 and len(saved) == 0x8000, 'incomplete native dumps')
    require(len((directory / (tag + '.fb.bgrx')).read_bytes()) == 256 * 224 * 4,
            'incomplete framebuffer')
    return body, saved, dict(mode=body[0x100], room=word(body, 0x10B),
                            lives=body[0xDBE], guest_frame=body[0x14],
                            flag=body[0x1ED9], map=body[0x1F11],
                            x=word(body, 0x1F17), y=word(body, 0x1F19),
                            goal_timer=body[0x1493],
                            wram_sha256=sha(body), sram_sha256=sha(saved),
                            framebuffer_sha256=sha((directory / (tag + '.fb.bgrx')).read_bytes()))


def native_capture(name, target, script):
    directory, receipt = capture(name, target, script, native=True)
    build = read_json(ROOT / 'local/build' / target / 'm1-build.json')
    for key in ('native_content', 'runtime_patches', 'analysis'):
        require(receipt[key] == build[key], 'capture/build identity differs: ' + key)
    require('BRK' not in (directory / 'run.log').read_text(), 'BRK: ' + name)
    source = (ROOT / 'recomp/inputs' / script).read_bytes()
    require((directory / 'input.script').read_bytes() == b'turbo on\n' + source,
            'executed script differs')
    allowed = {0x1F11: 2, 0x1F17: 8, 0x1F1F: 8, 0x100: 1, 0x94: 4,
               0x1497: 1, 0x88: 2, 0x71: 1}
    for line in source.decode().splitlines():
        fields = line.split()
        if fields and fields[0] in ('poke', 'forcepoke', 'pokefor'):
            require(len(bytes.fromhex(fields[2])) == allowed.get(int(fields[1], 16)),
                    'fixture writes outside its declared position/immunity scope')
    return directory, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='forest-r13')
    parser.add_argument('--output', default='local/reports/forest-course-identity-v1.json')
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    spec = read_json(SPEC)
    catalog = read_json(ROOT / 'config/world-map.json')
    require(catalog['worlds']['world2']['rooms'] == [row['room'] for row in spec['courses']],
            'Forest world catalog differs from verified identities')
    require(len(spec['courses']) == len({row['map_index'] for row in spec['courses']}) == 10,
            'Forest node inventory is incomplete or duplicated')
    target = spec['target']
    rom = (ROOT / 'local/restoration' / target / 'rom.sfc').read_bytes()
    require(sha(rom) == spec['rom_sha256'], 'product ROM differs')
    versions = {v['id']: v for v in read_json(ROOT / 'config/content-versions.json')['versions']}
    donors = {}
    for name in spec['donors']:
        body = (ROOT / 'local/content-versions' / name / 'rom.sfc').read_bytes()
        verify(body, versions[name]['output'], name)
        donors[name] = body
    results = []
    for row in spec['courses']:
        room, translevel = int(row['room'], 16), int(row['translevel'], 16)
        identity = fingerprint(rom, room, translevel)
        for key in ('name_tiles', 'layout_window', 'sprite_list'):
            require(identity[key] == row[key], 'pinned fingerprint differs: ' + row['room'])
        source_identities = {name: fingerprint(body, room, translevel) for name, body in donors.items()}
        for name, identity in source_identities.items():
            require(identity['name_tiles'] == row['name_tiles'] and
                    identity['sprite_list'] == row['sprite_list'], 'official identity differs: ' + name)
            if name in ('demo-1-1', 'demo-only-1'):
                require(identity['layout_window'] == row['layout_window'], 'modern layout window differs')
        name = f'{args.prefix}-{room:03x}-node-v1'
        directory, receipt = native_capture(name, target, f'forest-room{room:03x}-node-entry.script')
        node, _, node_state = state(directory, 'node')
        index = int(row['map_index'], 16)
        require(node_state['mode'] == 0x0E and node_state['map'] == 0 and
                node_state['x'] == int(row['x'], 16) and node_state['y'] == int(row['y'], 16),
                'wrong map node: ' + name)
        require(node[0xD000 + index] == translevel, 'actual node assignment differs')
        samples = {}
        for tag in ('active', 'later'):
            body, _, sample = state(directory, tag)
            require(sample['mode'] == 0x14 and sample['room'] == room and sample['lives'] == 4,
                    'wrong playable entry: ' + name)
            require(body[0x13BF] == translevel, 'entry translevel differs')
            samples[tag] = sample
        require(samples['active']['guest_frame'] != samples['later']['guest_frame'], 'guest froze')
        results.append(dict(course=row, capture=name, receipt=receipt, node=node_state,
                            samples=samples, official_fingerprints=source_identities))
    directory, receipt = native_capture(args.prefix + '-fishing-normal-save-v1', target,
                                        'forest-fishing-normal-save.script')
    flow = {}
    for tag in ('node', 'active', 'before_goal', 'touched', 'clear_map',
                'file_reload', 'reload_node', 'reentry'):
        body, saved, sample = state(directory, tag)
        require(sample['lives'] == 4, 'life lost: ' + tag)
        expected_flag = 0x05 if tag in ('node', 'active', 'before_goal', 'touched') else 0x85
        require(sample['flag'] == expected_flag and saved[0x37] == saved[0x1E4] == expected_flag,
                'clear/save state differs: ' + tag)
        if tag in ('active', 'before_goal', 'touched', 'reentry'):
            require(sample['mode'] == 0x14 and sample['room'] == 0x113, 'wrong course: ' + tag)
        elif tag in ('node', 'clear_map', 'file_reload', 'reload_node'):
            require(sample['mode'] == 0x0E and sample['map'] == 0, 'wrong overworld: ' + tag)
        if tag == 'before_goal':
            require(any(body[0x9E + i] == 0x7B and body[0x14C8 + i] == 8 for i in range(12)),
                    'no active goal tape')
        if tag == 'touched':
            require(sample['goal_timer'] > 0 and
                    any(body[0x9E + i] == 0x7B and body[0x14C8 + i] == 6 for i in range(12)),
                    'real tape touch did not execute')
        if tag in ('clear_map', 'file_reload'):
            require((sample['x'], sample['y']) == (0x128, 0x1A8), 'wrong next-course node')
        flow[tag] = sample
    directory, linked_receipt = native_capture(args.prefix + '-first-two-normal-save-v1', target,
                                               'forest-first-two-normal-save.script')
    linked_script = (ROOT / 'recomp/inputs/forest-first-two-normal-save.script').read_text()
    onward = linked_script.split('dump clear_map\n', 1)[1]
    for line in onward.splitlines():
        fields = line.split()
        if fields and fields[0] in ('poke', 'pokefor', 'forcepoke'):
            require(int(fields[1], 16) not in (0x1F11, 0x1F17, 0x1F1F, 0x100),
                    'linked progression contains an onward map fixture')
    linked = {}
    for tag in ('clear_map', 'bridge_active', 'bridge_goal_room', 'bridge_before_goal',
                'bridge_touched', 'bridge_clear_map', 'bridge_file_reload', 'shack_entry'):
        body, saved, sample = state(directory, tag)
        require(sample['lives'] == 4 and sample['flag'] == 0x85 and
                saved[0x37] == saved[0x1E4] == 0x85, 'first clear did not persist: ' + tag)
        bridge_flag = 0x83 if tag in ('bridge_clear_map', 'bridge_file_reload', 'shack_entry') else 3
        require(body[0x1ED7] == saved[0x35] == saved[0x1E2] == bridge_flag,
                'bridge clear/save state differs: ' + tag)
        sample['bridge_flag'] = body[0x1ED7]
        if tag == 'clear_map':
            require(sample['mode'] == 0x0E and (sample['x'], sample['y']) == (0x128, 0x1A8),
                    'first exit did not reach bridge node')
        elif tag == 'bridge_active':
            require(sample['mode'] == 0x14 and sample['room'] == 0x111 and body[0x13BF] == 0x35,
                    'natural onward entry did not select bridge')
            require(body[0x19B8 + 11] == 0x2E and body[0x19D8 + 11] == 4,
                    'bridge exit table differs')
        elif tag in ('bridge_goal_room', 'bridge_before_goal', 'bridge_touched'):
            require(sample['mode'] == 0x14 and sample['room'] == 0x2E,
                    'bridge goal room differs: ' + tag)
            if tag == 'bridge_before_goal':
                require(any(body[0x9E + i] == 0x7B and body[0x14C8 + i] == 8 for i in range(12)),
                        'bridge tape absent')
            if tag == 'bridge_touched':
                require(sample['goal_timer'] > 0 and
                        any(body[0x9E + i] == 0x7B and body[0x14C8 + i] == 6 for i in range(12)),
                        'bridge tape touch did not execute')
        elif tag in ('bridge_clear_map', 'bridge_file_reload'):
            require(sample['mode'] == 0x0E and sample['map'] == 0 and
                    (sample['x'], sample['y']) == (0x168, 0x1A8), 'wrong shack node: ' + tag)
        elif tag == 'shack_entry':
            require(sample['mode'] == 0x14 and sample['room'] == 0x15 and body[0x13BF] == 0x15,
                    'natural entry after reload did not select shack')
        linked[tag] = sample
    report = dict(target=target, rom_sha256=sha(rom), spec_sha256=sha(SPEC.read_bytes()),
                  checker_sha256=sha(Path(__file__).read_bytes()),
                  donors={name: sha(body) for name, body in donors.items()}, courses=results,
                  fishing_normal_save=dict(receipt=receipt, samples=flow),
                  linked_normal_saves=dict(receipt=linked_receipt, samples=linked),
                  limits=['Map-coordinate fixtures qualify existing nodes, not walking to each node.',
                          '256-byte layout windows are fingerprints, not complete level comparisons.',
                          'Normal clears use held position, pipe action and immunity; not full traversals.',
                          'No secret exit, five Dragon Coins, audio or new manual acceptance claim.',
                          'Official-source fingerprints do not qualify all actor behavior.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f'PASS: {len(results)} Forest identities, node entries and two linked normal saves/reload; {output}')


if __name__ == '__main__':
    main()

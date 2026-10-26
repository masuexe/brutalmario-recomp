#!/usr/bin/env python3
"""Qualify the mazo B0 corridor entries.

The tool checks the target identities, the imported room graphics records, the
entry mode and room, the custom A9 actor set and the donor reference actor set.
It records the room 183 and room 184 graphics limit. It does not claim corridor
traversal.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-mazo-b0'
CAPTURES = {
    '00D': 'mazo-b0-room183-v5-native',
    '10C': 'mazo-b0-room184-v1-native',
    '191': 'mazo-b0-room191-v2-native',
    '192': 'mazo-b0-room192-v1-native',
}
DONOR = {'191': 'mazo-b0-donor191-v1', '192': 'mazo-b0-donor192-v1'}
DONOR_FINE = {'00D': 'mazo-b0-donor00d-fine-v1', '10C': 'mazo-b0-donor10c-fine-v1'}
SLOTS = {'00D': '183', '10C': '184', '191': '191', '192': '192'}
CUSTOM = 0xA9
DONOR_CUSTOM = 0xB0
SENTINELS = [(272, 48), (32, 64)]
REFERENCE = {
    '191': [('custom', 192, 368), ('standard', 144, 368, 0x77), ('standard', 128, 368, 0x77)],
    '192': [('standard', 128, 368, 0x4A), ('custom', 48, 368)],
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def actors(wram):
    result = []
    for slot in range(12):
        if not wram[0x14C8+slot]:
            continue
        entry = {'slot': slot, 'sprite': wram[0x9E+slot],
                 'x': wram[0xE4+slot] | (wram[0x14E0+slot] << 8),
                 'y': wram[0xD8+slot] | (wram[0x14D4+slot] << 8)}
        if wram[0x1AB10+slot] & 8:
            entry['custom'] = wram[0x1AB9E+slot]
        result.append(entry)
    return result


def frame(directory, tag):
    return (ROOT / 'local/captures' / directory / (tag+'.wram.bin')).read_bytes()


def corridor_record(rom, slot):
    return rom[lorom(0x14AD08)+slot*32:lorom(0x14AD08)+slot*32+32]


def qualify():
    target = read(ROOT / 'config/restorations' / (TARGET + '.json'))
    recipe = read(ROOT / 'config/native-content/mazo-b0.json')
    build = read(ROOT / 'local/build' / TARGET / 'm1-build.json')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(rom, target['output'], 'corridor target ROM')
    require(build['rom_sha256'] == target['output']['sha256'], 'build receipt ROM differs')
    require(recipe['data_packs'][0]['sha256'] ==
            read(ROOT / 'config/native-content/mazo-b0-corridor.json')['data_pack']['sha256'],
            'data pack review differs')
    corridor = read(ROOT / 'config/native-content/mazo-b0-corridor.json')
    report = {'scope': __doc__.strip(), 'target': TARGET,
              'rom_sha256': target['output']['sha256'],
              'binary_sha256': build['binary_sha256'],
              'data_pack_sha256': corridor['data_pack']['sha256'],
              'corridor_receipt_sha256':
                  sha((ROOT/'local/native-modules/mazo-b0-corridor-v1/preparation-receipt.json').read_bytes()),
              'entries': {}, 'donor_parity': {}, 'transition_parity': {},
              'graphics_records': {}, 'limits': []}
    for room, name in CAPTURES.items():
        slot = int(SLOTS[room], 16)
        wram = frame(name, 'entry180')
        entry = {'capture': name, 'target_slot': f'{slot:03X}',
                 'mode': wram[0x100], 'room': int.from_bytes(wram[0x10B:0x10D], 'little'),
                 'mario_x': wram[0x94] | (wram[0x95] << 8), 'mario_y': wram[0x96] | (wram[0x97] << 8),
                 'actors': actors(wram)}
        require(entry['room'] == slot, 'entry room differs: '+room)
        if room in ('00D', '10C'):
            require(entry['mode'] in (0x0F, 0x14), 'entry mode differs: '+room)
            custom = [a for a in entry['actors'] if a.get('custom') == CUSTOM]
            require(len(custom) == 2, 'two custom actors expected: '+room)
            require(sorted((a['x'], a['y']) for a in custom) == sorted(SENTINELS),
                    'custom actor positions differ: '+room)
            later = frame(name, 'entry480')
            later_room = int.from_bytes(later[0x10B:0x10D], 'little')
            entry['later_room'] = later_room
            entry['later_mode'] = later[0x100]
            donor_name = DONOR_FINE[room]
            donor_frame = frame(donor_name, 'f160')
            donor_room = int.from_bytes(donor_frame[0x10B:0x10D], 'little')
            donor_later = frame(donor_name, 'f180')
            donor_later_room = int.from_bytes(donor_later[0x10B:0x10D], 'little')
            require(donor_room == int(room, 16), 'donor fine room differs: '+room)
            require(donor_frame[0x100] == 0x11, 'donor fine mode differs: '+room)
            require(donor_later_room == 0x190, 'donor later room differs: '+room)
            require(later_room == 0x190, 'native later room differs: '+room)
            report['transition_parity'][room] = {
                'donor_capture': donor_name, 'donor_room': donor_room,
                'donor_mode': donor_frame[0x100], 'donor_later_room': donor_later_room,
                'native_capture': name, 'native_room': entry['room'],
                'native_later_room': later_room}
            report['limits'].append(f'room {room}: the native and the donor image both treat '
                                    f'this room as a transition step to 0x{later_room:03X}.')
        else:
            require(entry['mode'] == 0x14, 'entry mode differs: '+room)
            reference = REFERENCE[room]
            require(len(entry['actors']) == len(reference), 'actor count differs: '+room)
            for actor, expected in zip(sorted(entry['actors'], key=lambda a: (a['x'], a['y'])),
                                       sorted(reference, key=lambda e: (e[1], e[2]))):
                if expected[0] == 'custom':
                    require(actor.get('custom') == CUSTOM, 'custom actor differs: '+room)
                else:
                    require(actor.get('custom') is None and actor['sprite'] == expected[3],
                            'standard actor differs: '+room)
                require((actor['x'], actor['y']) == (expected[1], expected[2]),
                        'actor position differs: '+room)
        report['entries'][room] = entry
        report['graphics_records'][room] = {
            'target': corridor_record(rom, slot).hex(),
            'donor': corridor_record((ROOT/'local/content-versions/mazo/rom.sfc').read_bytes(), int(room, 16)).hex()}
        require(report['graphics_records'][room]['target'] == report['graphics_records'][room]['donor'],
                'graphics record differs: '+room)
    for room, name in DONOR.items():
        wram = frame(name, 'room_idle')
        reference = {'room': int.from_bytes(wram[0x10B:0x10D], 'little'),
                     'actors': actors(wram)}
        require(reference['room'] == int(room, 16), 'donor room differs: '+room)
        native = report['entries'][room]['actors']
        require(len(reference['actors']) == len(native), 'donor actor count differs: '+room)
        for actor in reference['actors']:
            if actor.get('custom') == DONOR_CUSTOM:
                actor['custom'] = CUSTOM
        native_sorted = sorted(native, key=lambda a: (a['x'], a['y']))
        donor_sorted = sorted(reference['actors'], key=lambda a: (a['x'], a['y']))
        for got, expected in zip(native_sorted, donor_sorted):
            require((got['x'], got['y'], got.get('custom'), got['sprite']) ==
                    (expected['x'], expected['y'], expected.get('custom'), expected['sprite']),
                    'donor parity differs: '+room)
        report['donor_parity'][room] = {'capture': name, 'actors': len(reference['actors']),
                                        'rooms_match': True}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-mazo-b0-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(args.output, sha(args.output.read_bytes()))
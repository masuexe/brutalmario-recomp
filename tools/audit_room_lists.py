#!/usr/bin/env python3
"""Compare the level sprite list of each gap room with its donor.

A missing actor can come from two causes: the sprite record is absent, or the
level sprite list does not hold the placement. This tool separates the two. It
reads the list from the donor and from the recipient, and reports whether the
bytes are equal. It does not claim behaviour.
"""
import argparse
import json
from pathlib import Path

from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite-full'
RECIPIENT = 'local/restoration/demo11-native-sprite9e/rom.sfc'
DONORS = {
    'cheap-demo': 'local/content-versions/cheap-demo/rom.sfc',
    'mazo': 'local/content-versions/mazo/rom.sfc',
    '7hero': 'local/content-versions/7hero/rom.sfc',
}


def read(path):
    return json.loads(Path(path).read_text())


def list_bytes(rom, room):
    """Return the sprite list bytes of one room, from the header to the end."""
    pointer = lorom(0x05EC00+room*2)
    low = int.from_bytes(rom[pointer:pointer+2], 'little')
    bank = rom[lorom(0x0EF100)+room]
    start = lorom((bank << 16) | low)
    index = start+1
    count = 0
    while rom[index] != 0xFF and count < 120:
        index += 3
        count += 1
    return rom[start:index+1]


def donor_of(recipe):
    name = Path(recipe['donor_manifest']).stem.replace('-donor', '')
    return name, Path(DONORS[name]).read_bytes()


def compare():
    cfg = read(ROOT/'config/restorations'/(TARGET+'.json'))
    recipient = (ROOT/RECIPIENT).read_bytes()
    rooms = {}
    for path in cfg['native_sprite_gap']['manifests']:
        recipe = read(ROOT/path)
        name, donor = donor_of(recipe)
        for text in recipe['record']['rooms']:
            room = int(text, 16)
            donor_list = list_bytes(donor, room)
            host_list = list_bytes(recipient, room)
            rooms[f'{room:03X}'] = {
                'slot': recipe['record']['slot'], 'donor': name,
                'donor_size': len(donor_list), 'host_size': len(host_list),
                'equal': donor_list == host_list,
                'donor_sha256': sha(donor_list), 'host_sha256': sha(host_list)}
    equal = [room for room, entry in rooms.items() if entry['equal']]
    return {'scope': __doc__.strip(), 'target': TARGET,
            'recipient': RECIPIENT, 'rooms': rooms,
            'equal_rooms': sorted(equal),
            'different_rooms': sorted(room for room, entry in rooms.items()
                                      if not entry['equal']),
            'limits': ['A difference shows that the two versions hold different',
                       'placement data. It does not prove a missing record or a',
                       'missing placement in the intended game.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-full-lists.json')
    args = parser.parse_args()
    report = compare()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
    print('equal', len(report['equal_rooms']), 'different', report['different_rooms'])

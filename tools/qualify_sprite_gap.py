#!/usr/bin/env python3
"""Qualify the sprite 95 gap entry against the 7hero donor.

The tool verifies the target identities, the installed record, the module
receipt and the entry actor set. It compares the room 16B actor slots, sprite
ids, custom ids and X positions. It does not claim movement or a course pass.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite95'
DONOR_CAPTURE = 'type3-room16b-7hero-v1'
NATIVE_CAPTURE = 'sprite95-16b-matched-native-v1'
SLOT = 0x95
ROOMS = {
    '16B': ('type3-room16b-7hero-v1', 'sprite95-16b-matched-native-v1'),
    '16C': ('sprite95-16c-donor-v1', 'sprite95-16c-native-v1'),
    '16D': ('sprite95-16d-donor-v1', 'sprite95-16d-native-v1'),
    '16F': ('sprite95-16f-donor-v1', 'sprite95-16f-native-v1'),
    '172': ('sprite95-172-donor-v1', 'sprite95-172-native-v1'),
    '1CC': ('sprite95-1cc-donor-v1', 'sprite95-1cc-native-v1'),
}
WALK = ('sprite95-16b-walk-donor-v1', 'sprite95-16b-walk-native-v1')


def read(path):
    return json.loads(Path(path).read_text())


def actors(wram):
    rows = []
    for slot in range(12):
        if not wram[0x14C8+slot]:
            continue
        row = {'slot': slot, 'sprite': wram[0x9E+slot],
               'x': wram[0xE4+slot] | (wram[0x14E0+slot] << 8),
               'custom': None}
        if wram[0x1AB10+slot] & 8:
            row['custom'] = wram[0x1AB9E+slot]
        rows.append(row)
    return rows


def key(row):
    return (row['slot'], row['sprite'], row['custom'], row['x'])


def qualify():
    cfg = read(ROOT/'config/restorations'/(TARGET+'.json'))
    recipe = read(ROOT/cfg['native_sprite_gap']['manifest'])
    build = read(ROOT/'local/build'/TARGET/'m1-build.json')
    rom = (ROOT/'local/restoration'/TARGET/'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'sprite gap target ROM')
    require(build['rom_sha256'] == cfg['output']['sha256'], 'build receipt ROM differs')
    record = bytes.fromhex(recipe['record']['native_raw'])
    offset = recipe['unapplied_rom_patches'][0]['offset']
    require(rom[offset:offset+len(record)] == record, 'installed record differs')
    require(recipe['record']['raw'][4:8] == recipe['record']['native_raw'][4:8],
            'record property bytes changed')
    module_receipt = read(ROOT/'local/native-modules'/(TARGET+'-final')/'preparation-receipt.json')
    require(module_receipt['adapted_code_sha256'] == recipe['code']['adapted_sha256'],
            'module receipt code differs')
    donor = (ROOT/'local/captures'/DONOR_CAPTURE/'r1.wram.bin').read_bytes()
    native = (ROOT/'local/captures'/NATIVE_CAPTURE/'r1.wram.bin').read_bytes()
    donor_actors, native_actors = actors(donor), actors(native)
    require(sorted(map(key, donor_actors)) == sorted(map(key, native_actors)),
            'entry actor sets differ')
    require(any(row['custom'] == SLOT for row in native_actors),
            'the installed slot does not appear at entry')
    run_log = (ROOT/'local/captures'/NATIVE_CAPTURE/'run.log').read_text()
    require('bank=A3' in run_log, 'the A3 module view did not report')
    rooms = {}
    for room, (donor_name, native_name) in ROOMS.items():
        donor_rows = actors((ROOT/'local/captures'/donor_name/'r1.wram.bin').read_bytes())
        native_rows = actors((ROOT/'local/captures'/native_name/'r1.wram.bin').read_bytes())
        donor_slot = [row for row in donor_rows if row['custom'] == SLOT]
        native_slot = [row for row in native_rows if row['custom'] == SLOT]
        require(len(native_slot) == len(donor_slot),
                'slot 95 actor count differs: '+room)
        rooms[room] = {'donor_capture': donor_name, 'native_capture': native_name,
                       'donor_slot_rows': donor_slot, 'native_slot_rows': native_slot,
                       'slot_rows_equal': donor_slot == native_slot,
                       'whole_row_equal': donor_rows == native_rows}
    walk_core = []
    for index in range(9):
        donor = (ROOT/'local/captures'/WALK[0]/f'w{index}.wram.bin').read_bytes()
        native = (ROOT/'local/captures'/WALK[1]/f'w{index}.wram.bin').read_bytes()
        def state(wram):
            return (wram[0x100], int.from_bytes(wram[0x10B:0x10D], 'little'),
                    wram[0x94] | (wram[0x95] << 8))
        require(state(donor) == state(native), f'walk state differs at sample {index}')
        walk_core.append({'sample': index, 'mode': state(native)[0],
                          'room': state(native)[1], 'player_x': state(native)[2]})
    return {'scope': __doc__.strip(), 'target': TARGET,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'installed_record': recipe['record']['native_raw'],
            'install_offset': offset,
            'module_receipt_sha256': sha(
                (ROOT/'local/native-modules'/(TARGET+'-final')/'preparation-receipt.json').read_bytes()),
            'donor_capture': DONOR_CAPTURE, 'native_capture': NATIVE_CAPTURE,
            'actor_count': len(native_actors),
            'actors': native_actors,
            'rooms': rooms,
            'walk_samples': walk_core,
            'module_view': 'A3',
            'limits': ['Entry parity only. A course pass and a clear are not qualified.',
                       'Room 16C holds a three-pixel offset in one slot 95 actor.',
                       'Rooms 16D and 172 hold differences in other custom slots',
                       '(34 and a standard sprite), which the review does not cover.',
                       'The walk fixture drops both hosts to mode 0x0B and then to',
                       'mode 0x0E at player X 94, so the drop is shared behavior.']}


def require(condition, message):
    if not condition:
        raise ValueError(message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite95-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
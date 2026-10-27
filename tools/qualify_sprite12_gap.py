#!/usr/bin/env python3
"""Qualify the sprite 12 gap record against the cheap-demo donor.

The tool checks the target identities, the installed record, the module view
counters and the room 155 slot-12 actor parity. Rooms 155, 157, 159, 15B and
15C also place other gap slots, so the tool compares slot-12 rows only. It does
not claim movement or a course pass.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite12'
SLOT = 0x12
EXACT_ROOM = '155'
SAMPLES = ('r1', 'r2', 'r3', 'r4')
ROOMS = ('155', '157', '159', '15B', '15C')


def read(path):
    return json.loads(Path(path).read_text())


def actors(wram):
    rows = []
    for slot in range(12):
        if not wram[0x14C8+slot]:
            continue
        rows.append({'slot': slot, 'sprite': wram[0x9E+slot],
                     'custom': wram[0x1AB9E+slot] if wram[0x1AB10+slot] & 8 else None,
                     'x': wram[0xE4+slot] | (wram[0x14E0+slot] << 8),
                     'y': wram[0xD8+slot] | (wram[0x14D4+slot] << 8)})
    return rows


def require(condition, message):
    if not condition:
        raise ValueError(message)


def qualify():
    cfg = read(ROOT/'config/restorations'/(TARGET+'.json'))
    recipe = read(ROOT/cfg['native_sprite_gap']['manifest'])
    build = read(ROOT/'local/build'/TARGET/'m1-build.json')
    rom = (ROOT/'local/restoration'/TARGET/'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'sprite 12 target ROM')
    require(build['rom_sha256'] == cfg['output']['sha256'], 'build receipt ROM differs')
    record = bytes.fromhex(recipe['record']['native_raw'])
    offset = recipe['unapplied_rom_patches'][0]['offset']
    require(rom[offset:offset+len(record)] == record, 'installed record differs')
    require((int(recipe['code']['native_address'], 16) & 0xffff)
            == (int(recipe['code']['source_address'], 16) & 0xffff),
            'module move does not keep the low 16 address bits')
    receipt = ROOT/'local/native-modules'/(TARGET+'-final')/'preparation-receipt.json'
    module = read(receipt)
    require(module['adapted_code_sha256'] == recipe['code']['adapted_sha256'],
            'module receipt code differs')
    samples = {}
    for tag in SAMPLES:
        donor = [row for row in actors((ROOT/'local/captures'/f'sprite12-{EXACT_ROOM}-donor-v1'/(tag+'.wram.bin')).read_bytes())
                 if row['custom'] == SLOT]
        native = [row for row in actors((ROOT/'local/captures'/f'sprite12-{EXACT_ROOM}-native-v1'/(tag+'.wram.bin')).read_bytes())
                  if row['custom'] == SLOT]
        require(donor and native, 'missing a slot 12 sample for '+tag)
        samples[tag] = {'donor': donor, 'native': native,
                        'rows_equal': donor == native}
    require(all(sample['rows_equal'] for sample in samples.values()),
            'room '+EXACT_ROOM+' does not match the donor in every sample')
    rooms = {}
    for room in ROOMS:
        donor_path = ROOT/'local/captures'/f'sprite12-{room}-donor-v1'/'r1.wram.bin'
        native_path = ROOT/'local/captures'/f'sprite12-{room}-native-v1'/'r1.wram.bin'
        donor_rows = actors(donor_path.read_bytes()) if donor_path.is_file() else []
        native_rows = actors(native_path.read_bytes()) if native_path.is_file() else []
        rooms[room] = {'donor_customs': sorted({row['custom'] for row in donor_rows
                                               if row['custom'] is not None}),
                       'native_customs': sorted({row['custom'] for row in native_rows
                                                 if row['custom'] is not None})}
    log = (ROOT/'local/captures'/f'sprite12-{EXACT_ROOM}-native-v1/run.log').read_text()
    require('BRK' not in log, 'the target reached BRK')
    counters = {}
    for line in log.splitlines():
        if line.startswith('[native-seven] bank='):
            parts = line.split()
            counters[parts[1]] = {'resolutions': int(parts[2].split('=')[1]),
                                  'page_instructions': int(parts[3].split('=')[1])}
    require(counters.get('bank=AB', {}).get('page_instructions', 0) > 1000,
            'the AB module view did not run')
    return {'scope': __doc__.strip(), 'target': TARGET,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'installed_record': recipe['record']['native_raw'],
            'install_offset': offset,
            'native_address': recipe['code']['native_address'],
            'module_receipt_sha256': sha(receipt.read_bytes()),
            'module_view': counters.get('bank=AB'),
            'exact_room': EXACT_ROOM, 'samples': samples, 'rooms': rooms,
            'limits': ['Slot 12 rows only. Every room that places slot 12 also',
                       'places other gap slots, so a full actor list cannot match',
                       'until those slots are installed. Movement and a course',
                       'pass are not qualified.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite12-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))

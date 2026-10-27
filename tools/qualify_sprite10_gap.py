#!/usr/bin/env python3
"""Qualify the sprite 10 gap record against the cheap-demo donor.

The tool checks the target identities, the installed record, the module view
counters and the room 12D and 15B actor parity. Rooms 156, 157 and 15C need
slots 11 to 14 as well, so the tool records them as dependent rooms. It does
not claim movement or a course pass.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite10'
SLOT = 0x10
EXACT_ROOMS = ('12d', '15B')
DEPENDENT_ROOMS = ('156', '157', '15C')


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
    verify(rom, cfg['output'], 'sprite 10 target ROM')
    require(build['rom_sha256'] == cfg['output']['sha256'], 'build receipt ROM differs')
    record = bytes.fromhex(recipe['record']['native_raw'])
    offset = recipe['unapplied_rom_patches'][0]['offset']
    require(rom[offset:offset+len(record)] == record, 'installed record differs')
    require((int(recipe['code']['native_address'], 16) & 0xffff)
            == (int(recipe['code']['source_address'], 16) & 0xffff),
            'module move does not keep the low 16 address bits')
    receipt = ROOT/'local/native-modules'/('demo11-native-sprite10-final')/'preparation-receipt.json'
    module = read(receipt)
    require(module['adapted_code_sha256'] == recipe['code']['adapted_sha256'],
            'module receipt code differs')
    rooms = {}
    for room in EXACT_ROOMS:
        samples = {}
        for tag in ('r1', 'r2', 'r3'):
            donor = actors((ROOT/'local/captures'/f'sprite10-{room}-donor-v2'/(tag+'.wram.bin')).read_bytes())
            native = actors((ROOT/'local/captures'/f'sprite10-{room}-native-v2'/(tag+'.wram.bin')).read_bytes())
            require(donor and native, f'missing a sample for room {room} {tag}')
            require(all(row['custom'] in (SLOT, None) for row in native),
                    f'an unexpected custom slot appears in room {room}')
            samples[tag] = {'donor': donor, 'native': native,
                            'rows_equal': donor == native}
        require(samples['r2']['rows_equal'] and samples['r3']['rows_equal'],
                f'room {room} does not match the donor in the later samples')
        rooms[room] = samples
    dependent = {}
    for room in DEPENDENT_ROOMS:
        donor = actors((ROOT/'local/captures'/f'sprite10-{room}-donor-v2'/'r1.wram.bin').read_bytes())
        native = actors((ROOT/'local/captures'/f'sprite10-{room}-native-v2'/'r1.wram.bin').read_bytes())
        missing = sorted({row['custom'] for row in donor
                          if row['custom'] is not None and row['custom'] != SLOT})
        dependent[room] = {'donor_customs': sorted({row['custom'] for row in donor
                                                   if row['custom'] is not None}),
                           'native_customs': sorted({row['custom'] for row in native
                                                     if row['custom'] is not None}),
                           'requires_slots': missing}
        require(missing, f'room {room} shows no dependent slot')
    log = (ROOT/'local/captures/sprite10-12d-native-v2/run.log').read_text()
    require('BRK' not in log, 'the target reached BRK')
    counters = {}
    for line in log.splitlines():
        if line.startswith('[native-seven] bank='):
            parts = line.split()
            counters[parts[1]] = {'resolutions': int(parts[2].split('=')[1]),
                                  'page_instructions': int(parts[3].split('=')[1])}
    require(counters.get('bank=A4', {}).get('page_instructions', 0) > 10000,
            'the A4 module view did not run')
    return {'scope': __doc__.strip(), 'target': TARGET,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'installed_record': recipe['record']['native_raw'],
            'install_offset': offset,
            'native_address': recipe['code']['native_address'],
            'module_receipt_sha256': sha(receipt.read_bytes()),
            'module_view': counters.get('bank=A4'),
            'exact_rooms': rooms,
            'dependent_rooms': dependent,
            'limits': ['Entry parity for rooms 12D and 15B only. Rooms 156, 157',
                       'and 15C also need custom slots 11 to 14, which stay open.',
                       'Movement and a course pass are not qualified.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite10-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
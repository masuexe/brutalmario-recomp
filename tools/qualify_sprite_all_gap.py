#!/usr/bin/env python3
"""Qualify the eleven-record gap target against the cheap-demo donor.

The target carries every cheap-demo gap record that has an install so far.
This tool checks the identities, every installed record, the pack layout and
the room actor parity. It reports a room as exact when every sample matches.
It does not claim movement or a course pass.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha
import qualify_phase_alignment as phase_alignment

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite-all'
ROOMS = {
    '12D': ('sprite10-12d-donor-v2', ('r1', 'r2', 'r3')),
    '155': ('sprite12-155-donor-v1', ('r1', 'r2', 'r3', 'r4')),
    '156': ('sprite11-156-donor-v1', ('r1', 'r2', 'r3')),
    '157': ('sprite12-157-donor-v1', ('r1', 'r2', 'r3')),
    '158': ('sprite11-158-donor-v1', ('r1', 'r2', 'r3')),
    '159': ('sprite12-159-donor-v1', ('r1', 'r2', 'r3')),
    '15B': ('sprite10-15B-donor-v2', ('r1', 'r2', 'r3')),
    '15C': ('sprite10-15C-donor-v2', ('r1', 'r2', 'r3')),
}


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
    paths = cfg['native_sprite_gap']['manifests']
    recipes = [read(ROOT/path) for path in paths]
    build = read(ROOT/'local/build'/TARGET/'m1-build.json')
    rom = (ROOT/'local/restoration'/TARGET/'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'eleven-record gap target ROM')
    require(build['rom_sha256'] == cfg['output']['sha256'], 'build receipt ROM differs')
    require(len(recipes) == 11, 'the target must carry eleven records')
    for recipe in recipes:
        record = bytes.fromhex(recipe['record']['native_raw'])
        offset = recipe['unapplied_rom_patches'][0]['offset']
        require(rom[offset:offset+len(record)] == record,
                'installed record differs for slot '+recipe['record']['slot'])
        require((int(recipe['code']['native_address'], 16) & 0xffff)
                == (int(recipe['code']['source_address'], 16) & 0xffff),
                'a module move does not keep the low 16 address bits')
    banks = sorted(int(recipe['code']['native_address'], 16) >> 16 for recipe in recipes)
    require(len(set(banks)) == 11, 'the recipes share a code bank')
    manifest = read(ROOT/'local/restoration'/TARGET/'input-manifest.json')
    require(len(manifest['module_receipt_sha256']) == 11,
            'the input manifest must hold eleven module receipts')
    rooms = {}
    for room, (donor_dir, tags) in ROOMS.items():
        samples = {}
        for tag in tags:
            donor_path = ROOT/'local/captures'/donor_dir/(tag+'.wram.bin')
            native_path = ROOT/'local/captures'/f'spriteall-{room}-native-v1'/(tag+'.wram.bin')
            if not donor_path.is_file() or not native_path.is_file():
                samples[tag] = {'rows_equal': None, 'note': 'capture absent'}
                continue
            donor = actors(donor_path.read_bytes())
            native = actors(native_path.read_bytes())
            samples[tag] = {'donor': donor, 'native': native,
                            'rows_equal': donor == native}
        checked = [tag for tag, sample in samples.items() if sample['rows_equal'] is not None]
        exact = [tag for tag in checked if samples[tag]['rows_equal']]
        rooms[room] = {'samples': samples, 'checked': len(checked),
                       'exact': len(exact),
                       'rows_equal': len(checked) > 0 and len(checked) == len(exact)}
    log = (ROOT/'local/captures/spriteall-155-native-v1/run.log').read_text()
    require('BRK' not in log, 'the target reached BRK')
    counters = {}
    for line in log.splitlines():
        if line.startswith('[native-seven] bank='):
            parts = line.split()
            counters[parts[1]] = {'resolutions': int(parts[2].split('=')[1]),
                                  'page_instructions': int(parts[3].split('=')[1])}
    require(len(counters) >= 13, 'fewer than thirteen module views ran')
    exact_rooms = sorted(room for room, entry in rooms.items() if entry['rows_equal'])
    return {'scope': __doc__.strip(), 'target': TARGET,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'records': [{'slot': recipe['record']['slot'],
                         'resolved': recipe['record']['native_raw'],
                         'install_offset': recipe['unapplied_rom_patches'][0]['offset'],
                         'native_address': recipe['code']['native_address']}
                        for recipe in recipes],
            'module_views': counters,
            'rooms': rooms, 'exact_rooms': exact_rooms,
            'phase': phase_alignment.measure_all(),
            'limits': ['Entry parity only. A room counts as exact when every',
                       'captured sample matches the donor. Movement and a course',
                       'pass are not qualified.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-all-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
    print('exact rooms', report['exact_rooms'])
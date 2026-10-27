#!/usr/bin/env python3
"""Qualify the full gap target against the donor versions.

The target carries 31 custom sprite records from cheap-demo. This tool checks
the identities, every installed record, the pack layout and the room actor
parity for a sample of rooms. It does not claim movement or a course pass.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite-full'
OPEN_ROOMS = {
    '151': ('room151-donor-v1', 'room151-native-v1'),
    '190': ('room190-donor-v1', 'room190-native-v1'),
}
ROOMS = {
    '155': ('sprite12-155-donor-v1', 'spritefull-155-native-v1',
            ('r1', 'r2', 'r3', 'r4'), True),
    '083': ('room083-donor-v1', 'room083-native-v1', ('r1',), True),
    '087': ('room087-donor-v1', 'room087-native-v1', ('r1',), True),
    '142': ('room142-donor-v1', 'room142-native-v1', ('r1', 'r2'), True),
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
    verify(rom, cfg['output'], 'full gap target ROM')
    require(build['rom_sha256'] == cfg['output']['sha256'], 'build receipt ROM differs')
    require(len(recipes) == 33, 'the target must carry 33 records')
    for recipe in recipes:
        record = bytes.fromhex(recipe['record']['native_raw'])
        offset = recipe['unapplied_rom_patches'][0]['offset']
        require(rom[offset:offset+len(record)] == record,
                'installed record differs for slot '+recipe['record']['slot'])
        require((int(recipe['code']['native_address'], 16) & 0xffff)
                == (int(recipe['code']['source_address'], 16) & 0xffff),
                'a module move does not keep the low 16 address bits')
    banks = sorted(int(recipe['code']['native_address'], 16) >> 16 for recipe in recipes)
    require(len(set(banks)) == 33, 'the recipes share a code bank')
    manifest = read(ROOT/'local/restoration'/TARGET/'input-manifest.json')
    require(len(manifest['module_receipt_sha256']) == 33,
            'the input manifest must hold 33 module receipts')
    rooms = {}
    for room, (donor_dir, native_dir, tags, exact) in ROOMS.items():
        samples = {}
        for tag in tags:
            donor_path = ROOT/'local/captures'/donor_dir/(tag+'.wram.bin')
            native_path = ROOT/'local/captures'/native_dir/(tag+'.wram.bin')
            if not donor_path.is_file() or not native_path.is_file():
                samples[tag] = {'rows_equal': None, 'note': 'capture absent'}
                continue
            donor = actors(donor_path.read_bytes())
            native = actors(native_path.read_bytes())
            samples[tag] = {'donor': donor, 'native': native,
                            'rows_equal': donor == native}
        checked = [tag for tag, sample in samples.items()
                   if sample['rows_equal'] is not None]
        matched = [tag for tag in checked if samples[tag]['rows_equal']]
        rooms[room] = {'samples': samples, 'checked': len(checked),
                       'matched': len(matched), 'required_exact': exact,
                       'rows_equal': len(checked) > 0 and checked == matched}
    require(rooms['155']['rows_equal'], 'room 155 does not match the donor')
    require(rooms['083']['rows_equal'], 'room 083 does not match the donor')
    require(rooms['087']['rows_equal'], 'room 087 does not match the donor')
    require(rooms['142']['rows_equal'], 'room 142 does not match the donor')
    log = (ROOT/'local/captures'/'spritefull-155-native-v1'/'run.log').read_text()
    require('BRK' not in log, 'the target reached BRK')
    counters = {}
    for line in log.splitlines():
        if line.startswith('[native-seven] bank='):
            parts = line.split()
            counters[parts[1]] = {'resolutions': int(parts[2].split('=')[1]),
                                  'page_instructions': int(parts[3].split('=')[1])}
    require(len(counters) >= 35, 'fewer than 35 module views ran')
    return {'scope': __doc__.strip(), 'target': TARGET,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'records': len(recipes),
            'packs': len(manifest['module_receipt_sha256'])+2,
            'slots': [recipe['record']['slot'] for recipe in recipes],
            'module_views': len(counters),
            'rooms': rooms,
            'open_rooms': {room: {
                'donor_actors': len(actors((ROOT/'local/captures'/donor_dir/'r2.wram.bin').read_bytes())),
                'native_actors': len(actors((ROOT/'local/captures'/native_dir/'r2.wram.bin').read_bytes())),
                'rows_equal': actors((ROOT/'local/captures'/donor_dir/'r2.wram.bin').read_bytes())
                               == actors((ROOT/'local/captures'/native_dir/'r2.wram.bin').read_bytes()),
            } for room, (donor_dir, native_dir) in OPEN_ROOMS.items()},
            'exact_rooms': sorted(room for room, entry in rooms.items()
                                  if entry['rows_equal']),
            'limits': ['Entry parity for four sampled rooms only. Movement and a',
                       'course pass are not qualified.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-full-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
    print('exact rooms', report['exact_rooms'])
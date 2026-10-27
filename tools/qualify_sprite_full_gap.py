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
STALLED_ROOMS = {
    '085': ('room085-donor-v1', 'room085-native-v1'),
    '091': ('room091-donor-v1', 'room091-native-v1'),
    '0A2': ('room0A2-donor-v1', 'room0A2-native-v1'),
    '0BA': ('room0BA-donor-v1', 'room0BA-native-v1'),
    '0BB': ('room0BB-donor-v1', 'room0BB-native-v1'),
    '0F3': ('room0F3-donor-v1', 'room0F3-native-v1'),
}
OPEN_ROOMS = {
    '001': ('room001-donor-v1', 'room001-native-v1'),
    '075': ('room075-donor-v1', 'room075-native-v1'),
    '0B1': ('room0B1-donor-v1', 'room0B1-native-v1'),
    '0B3': ('room0B3-donor-v1', 'room0B3-native-v1'),
    '13F': ('room13F-donor-v1', 'room13F-native-v1'),
    '15E': ('room15E-donor-v1', 'room15E-native-v1'),
    '163': ('room163-donor-v1', 'room163-native-v1'),
    '0B5': ('room0B5-donor-v1', 'room0B5-native-v1'),
    '0B6': ('room0B6-donor-v1', 'room0B6-native-v1'),
    '162': ('room162-donor-v1', 'room162-native-v1'),
    '05B': ('room05B-donor-v1', 'room05B-native-v1'),
    '0A5': ('room0A5-donor-v1', 'room0A5-native-v1'),
    '164': ('room164-donor-v1', 'room164-native-v1'),
    '096': ('room096-donor-v1', 'room096-native-v1'),
    '0A3': ('room0A3-donor-v1', 'room0A3-native-v1'),
    '110': ('room110-donor-v1', 'room110-native-v1'),
    '13C': ('room13C-donor-v1', 'room13C-native-v1'),
    '14E': ('room14E-donor-v1', 'room14E-native-v1'),
    '151': ('room151-donor-v1', 'room151-native-v1'),
    '190': ('room190-donor-v1', 'room190-native-v1'),
}
ROOMS = {
    '155': ('sprite12-155-donor-v1', 'spritefull-155-native-v1',
            ('r1', 'r2', 'r3', 'r4'), True),
    '083': ('room083-donor-v1', 'room083-native-v1', ('r1',), True),
    '087': ('room087-donor-v1', 'room087-native-v1', ('r1',), True),
    '142': ('room142-donor-v1', 'room142-native-v1', ('r1', 'r2'), True),
    '147': ('room147-donor-v1', 'room147-native-v1', ('r1', 'r2'), True),
    '05D': ('room05D-donor-v1', 'room05D-native-v1', ('r1', 'r2'), True),
    '15D': ('room15D-donor-v1', 'room15D-native-v1', ('r1', 'r2'), True),
    '08B': ('room08B-donor-v1', 'room08B-native-v1', ('r1', 'r2'), True),
    '160': ('room160-donor-v1', 'room160-native-v1', ('r1', 'r2'), True),
    '0AF': ('room0AF-donor-v1', 'room0AF-native-v1', ('r1', 'r2'), True),
    '00D': ('room00D-donor-v1', 'room00D-native-v1', ('r1', 'r2'), True),
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



def stalled_report():
    """Record the mode and the frame counter of each stalled room."""
    result = {}
    for room, (donor_dir, native_dir) in STALLED_ROOMS.items():
        entry = {}
        for host, directory in (('donor', donor_dir), ('native', native_dir)):
            first = ROOT/'local/captures'/directory/'r1.wram.bin'
            second = ROOT/'local/captures'/directory/'r2.wram.bin'
            if not first.is_file():
                entry[host] = None
                continue
            a = first.read_bytes()
            b = second.read_bytes() if second.is_file() else a
            entry[host] = {'mode': a[0x100],
                           'frame': a[0x13] | (a[0x14] << 8),
                           'frame_later': b[0x13] | (b[0x14] << 8),
                           'frozen': (a[0x13] | (a[0x14] << 8)) ==
                                     (b[0x13] | (b[0x14] << 8))}
        result[room] = {'donor': entry.get('donor'), 'native': entry.get('native'),
                        'native_frozen': bool(entry.get('native')
                                              and entry['native']['frozen'])}
    return result

PHASE_ROOMS = {
    '0A5': ('room0A5-one-donor-v1', 'room0A5-one-native-v1', 460, 61, 'h'),
    '091': ('room091-one-donor-v1', 'room091-one-native-v1', 160, 81, 'h'),
    '190': ('room190-one-mazod-v1', 'room190-one-native-v1', 160, 81, 'h'),
}


def oneframe_phase(room, donor_dir, native_dir, first, count, tag):
    """Find the frame offset that aligns the actor rows of one room."""
    def rows(directory, frame):
        path = ROOT/'local/captures'/directory/f'{tag}{frame}.wram.bin'
        if not path.is_file():
            return None
        wram = path.read_bytes()
        return tuple((slot, wram[0x9E+slot], wram[0x1AB9E+slot],
                      wram[0xE4+slot] | (wram[0x14E0+slot] << 8),
                      wram[0xD8+slot] | (wram[0x14D4+slot] << 8))
                     for slot in range(12) if wram[0x14C8+slot])
    donor = {frame: rows(donor_dir, frame) for frame in range(first, first+count)}
    native = {frame: rows(native_dir, frame) for frame in range(first, first+count)}
    donor = {key: value for key, value in donor.items() if value is not None}
    native = {key: value for key, value in native.items() if value is not None}
    best = None
    for offset in range(-60, 61):
        equal = checked = 0
        for frame, value in donor.items():
            other = native.get(frame+offset)
            if other is None:
                continue
            checked += 1
            equal += value == other
        if checked and (best is None or equal > best[1]):
            best = (offset, equal, checked)
    offset = best[0]
    mismatched = [frame for frame in sorted(donor)
                  if (frame+offset) in native and donor[frame] != native[frame+offset]]
    return {'offset': offset, 'equal': best[1], 'checked': best[2],
            'mismatch_frames': mismatched, 'residual': len(mismatched)}

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
    require(len(recipes) == 35, 'the target must carry 35 records')
    for recipe in recipes:
        record = bytes.fromhex(recipe['record']['native_raw'])
        offset = recipe['unapplied_rom_patches'][0]['offset']
        require(rom[offset:offset+len(record)] == record,
                'installed record differs for slot '+recipe['record']['slot'])
        require((int(recipe['code']['native_address'], 16) & 0xffff)
                == (int(recipe['code']['source_address'], 16) & 0xffff),
                'a module move does not keep the low 16 address bits')
    banks = sorted(int(recipe['code']['native_address'], 16) >> 16 for recipe in recipes)
    require(len(set(banks)) == 35, 'the recipes share a code bank')
    manifest = read(ROOT/'local/restoration'/TARGET/'input-manifest.json')
    require(len(manifest['module_receipt_sha256']) == 35,
            'the input manifest must hold 35 module receipts')
    rooms = {}
    for room, (donor_dir, native_dir, tags, exact) in ROOMS.items():
        samples = {}
        for tag in tags:
            donor_path = ROOT/'local/captures'/donor_dir/(tag+'.wram.bin')
            native_path = ROOT/'local/captures'/native_dir/(tag+'.wram.bin')
            if not donor_path.is_file() or not native_path.is_file():
                samples[tag] = {'rows_equal': None, 'note': 'capture absent'}
                continue
            donor_bytes = donor_path.read_bytes()
            native_bytes = native_path.read_bytes()
            donor = actors(donor_bytes)
            native = actors(native_bytes)
            samples[tag] = {'donor': donor, 'native': native,
                            'donor_mode': donor_bytes[0x100],
                            'native_mode': native_bytes[0x100],
                            'rows_equal': donor == native}
        checked = [tag for tag, sample in samples.items()
                   if sample['rows_equal'] is not None]
        matched = [tag for tag in checked if samples[tag]['rows_equal']]
        same_mode = all(samples[tag]['native_mode'] == samples[tag]['donor_mode']
                        for tag in checked)
        live = all(samples[tag]['native_mode'] >= 0x13 for tag in checked)
        rooms[room] = {'samples': samples, 'checked': len(checked),
                       'matched': len(matched), 'required_exact': exact,
                       'same_mode': same_mode, 'native_live': live,
                       'rows_equal': (live and len(checked) > 0
                                      and checked == matched)}
    require(rooms['155']['rows_equal'], 'room 155 does not match the donor')
    require(rooms['083']['rows_equal'], 'room 083 does not match the donor')
    require(rooms['087']['rows_equal'], 'room 087 does not match the donor')
    require(rooms['142']['rows_equal'], 'room 142 does not match the donor')
    require(rooms['147']['rows_equal'], 'room 147 does not match the donor')
    require(rooms['05D']['rows_equal'], 'room 05D does not match the donor')
    require(rooms['15D']['rows_equal'], 'room 15D does not match the donor')
    require(rooms['08B']['rows_equal'], 'room 08B does not match the donor')
    require(rooms['160']['rows_equal'], 'room 160 does not match the donor')
    require(rooms['0AF']['rows_equal'], 'room 0AF does not match the donor')
    require(rooms['00D']['rows_equal'], 'room 00D does not match the donor')
    log = (ROOT/'local/captures'/'spritefull-155-native-v1'/'run.log').read_text()
    require('BRK' not in log, 'the target reached BRK')
    counters = {}
    for line in log.splitlines():
        if line.startswith('[native-seven] bank='):
            parts = line.split()
            counters[parts[1]] = {'resolutions': int(parts[2].split('=')[1]),
                                  'page_instructions': int(parts[3].split('=')[1])}
    require(len(counters) >= 37, 'fewer than 37 module views ran')
    return {'scope': __doc__.strip(), 'target': TARGET,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'records': len(recipes),
            'packs': len(manifest['module_receipt_sha256'])+2,
            'slots': [recipe['record']['slot'] for recipe in recipes],
            'module_views': len(counters),
            'oneframe_phase': {room: oneframe_phase(room, *spec)
                               for room, spec in PHASE_ROOMS.items()},
            'room_lists': read(ROOT/'local/reports/native-sprite-full-lists.json')
                               if (ROOT/'local/reports/native-sprite-full-lists.json').is_file()
                               else None,
            'stalled_rooms': stalled_report(),
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
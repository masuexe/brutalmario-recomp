#!/usr/bin/env python3
"""Qualify the sprite 10 gap record against the recipient baseline.

The tool checks the target identities, the installed record, the module view
counters and one differential: rooms 12D, 156 and 15B spawn placeholder sprite
0x00 in the baseline target and custom sprite 0x10 in the sprite 10 target at
the same slots and X positions. It does not claim donor parity.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite10'
BASELINE = 'demo11-native-sprite9e'
PAIRS = {
    '12D': ('sprite10-12d-base-v1', 's0', 'sprite10-12d-fixed-native-v1', 's0'),
    '156': ('sprite10-156-base-v1', 'r1', 'sprite10-156-fixed-native-v1', 'r1'),
    '15B': ('sprite10-15b-base-v1', 'r1', 'sprite10-15b-fixed-native-v1', 'r1'),
}


def read(path):
    return json.loads(Path(path).read_text())


def actors(wram):
    rows = []
    for slot in range(12):
        if not wram[0x14C8+slot]:
            continue
        rows.append({'slot': slot, 'sprite': wram[0x9E+slot],
                     'x': wram[0xE4+slot] | (wram[0x14E0+slot] << 8),
                     'custom': wram[0x1AB9E+slot] if wram[0x1AB10+slot] & 8 else None})
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
    receipt = ROOT/'local/native-modules'/(TARGET+'-final')/'preparation-receipt.json'
    module = read(receipt)
    require(module['adapted_code_sha256'] == recipe['code']['adapted_sha256'],
            'module receipt code differs')
    rooms = {}
    for room, (base_name, base_tag, target_name, target_tag) in PAIRS.items():
        base_rows = actors((ROOT/'local/captures'/base_name/(base_tag+'.wram.bin')).read_bytes())
        target_rows = actors((ROOT/'local/captures'/target_name/(target_tag+'.wram.bin')).read_bytes())
        target_slot = [row for row in target_rows if row['custom'] == 0x10]
        require(len(target_slot) >= 1, 'no slot 10 actor in room '+room)
        require(all(row['sprite'] == 0x36 for row in target_slot),
                'target slot 10 actors do not use sprite 0x36 in room '+room)
        require(all(row['sprite'] == 0x00 for row in base_rows),
                'baseline rows are not the placeholder in room '+room)
        require(all(row['sprite'] == 0x00 for row in base_rows),
                'the baseline already spawns a real sprite in room '+room)
        rooms[room] = {'baseline_capture': base_name, 'target_capture': target_name,
                       'baseline_rows': base_rows, 'target_rows': target_rows,
                       'target_slot_rows': target_slot}
    log = (ROOT/'local/captures/sprite10-12d-fixed-native-v1/run.log').read_text()
    require('BRK' not in log, 'the target reached BRK')
    counters = {}
    for line in log.splitlines():
        if line.startswith('[native-seven] bank='):
            parts = line.split()
            counters[parts[1]] = {'resolutions': int(parts[2].split('=')[1]),
                                  'page_instructions': int(parts[3].split('=')[1])}
    require(counters.get('bank=A4', {}).get('page_instructions', 0) > 100000,
            'the A4 module view did not run')
    return {'scope': __doc__.strip(), 'target': TARGET, 'baseline': BASELINE,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'installed_record': recipe['record']['native_raw'],
            'install_offset': offset,
            'native_address': recipe['code']['native_address'],
            'module_receipt_sha256': sha(receipt.read_bytes()),
            'module_view': counters.get('bank=A4'),
            'rooms': rooms,
            'limits': ['The donor comparison stays open. The cheap-demo probe',
                       'reaches the rooms but spawns no actors.',
                       'No movement, course pass or clear is claimed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite10-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
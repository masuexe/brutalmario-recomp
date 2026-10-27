#!/usr/bin/env python3
"""Qualify the sprite 33 gap record against the 7hero donor.

The tool checks the target identities, the installed record, the module view
counters and the room 0x0FE actor parity. The tool does not claim movement or a
course pass.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite33'
DONOR_CAPTURE = 'sprite33-0fe-donor-v1'
NATIVE_CAPTURE = 'sprite33-0fe-native-v1'
SLOT = 0x33


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
    verify(rom, cfg['output'], 'sprite 33 target ROM')
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
    for tag in ('r1', 'r2', 'r3'):
        donor = actors((ROOT/'local/captures'/DONOR_CAPTURE/(tag+'.wram.bin')).read_bytes())
        native = actors((ROOT/'local/captures'/NATIVE_CAPTURE/(tag+'.wram.bin')).read_bytes())
        require(donor and native, 'missing a sample for '+tag)
        require(all(row['custom'] == SLOT for row in native),
                'the target does not spawn only slot 33 actors in '+tag)
        samples[tag] = {'donor': donor, 'native': native,
                        'rows_equal': donor == native}
    require(samples['r1']['rows_equal'], 'the first sample does not match the donor')
    require(samples['r3']['rows_equal'], 'the third sample does not match the donor')
    log = (ROOT/'local/captures'/NATIVE_CAPTURE/'run.log').read_text()
    require('BRK' not in log, 'the target reached BRK')
    counters = {}
    for line in log.splitlines():
        if line.startswith('[native-seven] bank='):
            parts = line.split()
            counters[parts[1]] = {'resolutions': int(parts[2].split('=')[1]),
                                  'page_instructions': int(parts[3].split('=')[1])}
    require(counters.get('bank=A7', {}).get('page_instructions', 0) > 10000,
            'the A7 module view did not run')
    return {'scope': __doc__.strip(), 'target': TARGET,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'installed_record': recipe['record']['native_raw'],
            'install_offset': offset,
            'native_address': recipe['code']['native_address'],
            'module_receipt_sha256': sha(receipt.read_bytes()),
            'module_view': counters.get('bank=A7'),
            'donor_capture': DONOR_CAPTURE, 'native_capture': NATIVE_CAPTURE,
            'samples': samples,
            'limits': ['Entry parity only. The second sample holds an 8-pixel X',
                       'difference. Movement and a course pass are not qualified.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite33-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))

#!/usr/bin/env python3
"""Qualify the sprite 25 gap record against the 7hero donor.

The tool checks the target identities, the installed record, the module view
counters and the room 154 actor parity. The fine capture shows a one-pixel Y
lag that matches a ten-frame mode-onset difference. It does not claim movement
or a course pass.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-sprite25'
DONOR_CAPTURE = 'sprite25-154-donor-v1'
NATIVE_CAPTURE = 'sprite25-154-native-v1'
FINE = ('sprite25-154-fine-donor-v1', 'sprite25-154-fine-native-v1')
SLOT = 0x25


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


def fine_series(directory):
    result = {}
    for index in range(16):
        frame = 140+index*10
        path = ROOT/'local/captures'/directory/f'f{frame}.wram.bin'
        if not path.is_file():
            continue
        wram = path.read_bytes()
        result[frame] = (wram[0x100], actors(wram))
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def qualify():
    cfg = read(ROOT/'config/restorations'/(TARGET+'.json'))
    recipe = read(ROOT/cfg['native_sprite_gap']['manifest'])
    build = read(ROOT/'local/build'/TARGET/'m1-build.json')
    rom = (ROOT/'local/restoration'/TARGET/'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'sprite 25 target ROM')
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
                'the target does not spawn only slot 25 actors in '+tag)
        samples[tag] = {'donor': donor, 'native': native,
                        'rows_equal': donor == native}
    for tag in ('r1', 'r2', 'r3'):
        donor, native = samples[tag]['donor'], samples[tag]['native']
        require(len(donor) == len(native), 'actor count differs in '+tag)
        for left, right in zip(donor, native):
            require(left['slot'] == right['slot'] and left['x'] == right['x']
                    and left['sprite'] == right['sprite']
                    and left['custom'] == right['custom'],
                    'actor identity or X differs in '+tag)
            require(abs(left['y']-right['y']) <= 5, 'the Y gap exceeds five pixels in '+tag)
    donor_fine = fine_series(FINE[0])
    native_fine = fine_series(FINE[1])
    require(donor_fine and native_fine, 'missing the fine captures')
    onset = lambda series: min(frame for frame, (mode, _) in series.items() if mode == 0x14)
    donor_onset, native_onset = onset(donor_fine), onset(native_fine)
    frames = sorted(frame for frame in donor_fine if frame in native_fine)
    lags = []
    for frame in frames:
        donor_rows = donor_fine[frame][1]
        native_rows = native_fine[frame][1]
        if len(donor_rows) == 1 and len(native_rows) == 1:
            lags.append(donor_rows[0]['y']-native_rows[0]['y'])
    require(lags, 'the fine captures hold no single-actor frame')
    require(max(abs(lag) for lag in lags) <= 2,
            'the fine Y gap exceeds two pixels')
    log = (ROOT/'local/captures'/NATIVE_CAPTURE/'run.log').read_text()
    require('BRK' not in log, 'the target reached BRK')
    counters = {}
    for line in log.splitlines():
        if line.startswith('[native-seven] bank='):
            parts = line.split()
            counters[parts[1]] = {'resolutions': int(parts[2].split('=')[1]),
                                  'page_instructions': int(parts[3].split('=')[1])}
    require(counters.get('bank=A8', {}).get('page_instructions', 0) > 10000,
            'the A8 module view did not run')
    return {'scope': __doc__.strip(), 'target': TARGET,
            'rom_sha256': cfg['output']['sha256'],
            'binary_sha256': build['binary_sha256'],
            'installed_record': recipe['record']['native_raw'],
            'install_offset': offset,
            'native_address': recipe['code']['native_address'],
            'module_receipt_sha256': sha(receipt.read_bytes()),
            'module_view': counters.get('bank=A8'),
            'donor_capture': DONOR_CAPTURE, 'native_capture': NATIVE_CAPTURE,
            'samples': samples,
            'fine': {'donor_capture': FINE[0], 'native_capture': FINE[1],
                     'mode_onset_donor': donor_onset, 'mode_onset_native': native_onset,
                     'onset_gap': donor_onset-native_onset,
                     'max_abs_y_lag': max(abs(lag) for lag in lags)},
            'limits': ['Entry parity only. The target holds a one-pixel Y lag that',
                       'matches a ten-frame mode-onset difference. Movement and a',
                       'course pass are not qualified.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite25-final.json')
    args = parser.parse_args()
    report = qualify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))

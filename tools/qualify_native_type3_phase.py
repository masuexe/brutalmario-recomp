#!/usr/bin/env python3
"""Qualify the C0 and C1 shooter child phase in room 16B.

The earlier checkpoints compared fixed-time samples and left the C0 phase and
late-window C1 child motion open. These dense captures sample every frame of
the held window. This tool aligns the C0 sequence by one frame and compares the
child rows and shooter timer, then compares every moving C1 child row.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import sha

TARGET = 'demo11-native-type3-c2-v2'
PAIRS = {
    'C0': ('type3-shooters-native-c0-dense-v1', 'type3-shooters-source-c0-dense-v1', 'c0d', (0xB0, 0x95)),
    'C1': ('type3-shooters-native-c1-dense-v1', 'type3-shooters-source-c1-dense-v1', 'c1d', (0xB1, 0x95)),
}
SCRIPT = {
    'C0': 'native-type3-shooters-c0-dense.script',
    'C1': 'native-type3-shooters-c1-dense.script',
}
SOURCE_SCRIPT = {
    'C0': 'source-type3-shooters-c0-dense.script',
    'C1': 'source-type3-shooters-c1-dense.script',
}
STATIC_X = 1152


def require(value, reason):
    if not value:
        raise ValueError(reason)


def rows(path, ids):
    data = path.read_bytes()
    found = []
    for i in range(12):
        if data[0x14C8 + i] and data[0x1AB10 + i] & 8 and data[0x1AB9E + i] in ids:
            found.append(dict(custom=data[0x1AB9E + i], status=data[0x14C8 + i],
                              x=data[0xE4 + i] | data[0x14E0 + i] << 8,
                              y=data[0xD8 + i] | data[0x14D4 + i] << 8,
                              vx=data[0xB6 + i], vy=data[0xAA + i],
                              s1504=data[0x1504 + i], s151c=data[0x151C + i],
                              s1570=data[0x1570 + i], s157c=data[0x157C + i]))
    return found


def key(row):
    return (row['custom'], row['status'], row['x'], row['y'], row['vx'], row['vy'],
            row['s1504'], row['s151c'], row['s1570'], row['s157c'])


def main():
    directory = ROOT / 'local/captures'
    report = ROOT / 'local/reports/native-type3-phase-v1.json'
    require(not report.exists(), 'use a fresh report path')
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    build = json.loads((ROOT / 'local/build' / TARGET / 'm1-build.json').read_text())
    native_receipt = json.loads((directory / PAIRS['C0'][0] / 'receipt.json').read_text())
    require(native_receipt['target'] == TARGET and native_receipt['stage'] == 'native', 'native role')
    require(native_receipt['rom_sha256'] == cfg['output']['sha256'] == build['rom_sha256'], 'native ROM')
    source_receipt = json.loads((directory / PAIRS['C0'][1] / 'receipt.json').read_text())
    require(source_receipt['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled', 'source options')
    result = {}
    for label, (native_name, source_name, prefix, ids) in PAIRS.items():
        native_dir, source_dir = directory / native_name, directory / source_name
        require((native_dir / 'input.script').read_text() ==
                'turbo on\n' + (ROOT / 'recomp/inputs' / SCRIPT[label]).read_text(), 'native script')
        require((source_dir / 'input.script').read_text() ==
                (ROOT / 'recomp/inputs' / SOURCE_SCRIPT[label]).read_text(), 'source script')
        if label == 'C0':
            exact = total = 0
            for i in range(63):
                a = rows(native_dir / f'{prefix}{i + 1:02d}.wram.bin', ids)
                b = rows(source_dir / f'{prefix}{i:02d}.wram.bin', ids)
                total += 1
                same_timer = ((native_dir / f'{prefix}{i + 1:02d}.wram.bin').read_bytes()[0x17B2]
                              == (source_dir / f'{prefix}{i:02d}.wram.bin').read_bytes()[0x17B2])
                if sorted(key(r) for r in a) == sorted(key(r) for r in b) and same_timer:
                    exact += 1
            require(exact == total and total == 63, f'C0 aligned pairs {exact}/{total}')
            result[label] = dict(shift=1, exact=exact, total=total)
        else:
            moving_exact = total = 0
            static_deltas = set()
            for i in range(64):
                a = rows(native_dir / f'{prefix}{i:02d}.wram.bin', ids)
                b = rows(source_dir / f'{prefix}{i:02d}.wram.bin', ids)
                total += 1
                used = set()
                matched = True
                for row in a:
                    candidates = [(j, other) for j, other in enumerate(b)
                                  if j not in used and other['custom'] == row['custom']]
                    if not candidates:
                        matched = False
                        break
                    j, other = min(candidates, key=lambda item:
                                   abs(item[1]['x'] - row['x']) + abs(item[1]['y'] - row['y']))
                    used.add(j)
                    moving = not (row['s1504'] == 0 and row['vx'] == 0 and row['vy'] == 0)
                    if moving and key(row) != key(other):
                        matched = False
                    if not moving and row['x'] == STATIC_X and row['y'] != other['y']:
                        static_deltas.add(other['y'] - row['y'])
                if matched and len(a) == len(b):
                    moving_exact += 1
            require(moving_exact == total and total == 64, f'C1 moving frames {moving_exact}/{total}')
            require(static_deltas <= {-1, 1}, f'C1 static delta {static_deltas}')
            result[label] = dict(exact=total, static_delta=sorted(static_deltas))
    report.write_text(json.dumps(dict(target=TARGET, rom_sha256=cfg['output']['sha256'],
                                      samples=result, source_rom_sha256=source_receipt['rom_sha256'],
                                      scope=__doc__.strip()), indent=2) + '\n')
    print('C0 aligned pairs exact:', result['C0']['exact'], '/', result['C0']['total'])
    print('C1 moving frames exact:', result['C1']['exact'], '/', result['C1']['exact'],
          'static delta', result['C1']['static_delta'])
    print(report, sha(report.read_bytes()))


if __name__ == '__main__':
    main()

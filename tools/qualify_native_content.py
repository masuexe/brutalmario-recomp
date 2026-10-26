#!/usr/bin/env python3
"""Qualify fresh native external-pack and unchanged Boss-route captures.

Both routes use map/practice fixtures; neither is an unassisted course clear.
Pass --run to collect fresh evidence. Existing captures are never overwritten.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from native_content import ROOT, TARGET, identity, settings, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import graphics_pointer, lorom, lz2

BASE = 'demo11-sprites-orphan-cleanup'
ROUTES = (
    ('star1', 'recomp/inputs/demo11-star1-entry.script', ('s0', 's1', 's2'), 0x005),
    ('boss', 'recomp/inputs/demo11-hp-boss-bc.script', ('active', 'later'), 0x0BC),
)
SIZES = {'wram.bin': 0x20000, 'vram.bin': 0x10000, 'cgram.bin': 512,
         'oam.bin': 544, 'sram.bin': 32768, 'fb.bgrx': 256 * 224 * 4}


def require(value, message):
    if not value:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text())


def capture_path(prefix, role, route):
    return ROOT / 'local/captures' / f'{prefix}-{role}-{route}'


def collect(prefix):
    for route, script, _, _ in ROUTES:
        for role, target in (('control', BASE), ('external', TARGET)):
            subprocess.run([sys.executable, str(ROOT / 'tools/m1.py'), 'native',
                            '--target', target, '--capture', f'{prefix}-{role}-{route}',
                            '--script', script], cwd=ROOT, check=True)
    cfg, spec = settings(TARGET)
    pack = (ROOT / 'local/restoration' / TARGET / spec['pack_file']).read_bytes()
    binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
    for case, data, expected in (
            ('missing', None, 'BM_NATIVE_CONTENT_PACK is required'),
            ('corrupt', bytes([pack[0] ^ 1]) + pack[1:], 'pack SHA-256 differs'),
            ('truncated', pack[:-1], 'pack size differs'),
            ('oversized', pack + b'\0', 'pack size differs')):
        directory = ROOT / 'local/captures' / f'{prefix}-reject-{case}'
        directory.mkdir(parents=True, exist_ok=False)
        env = os.environ.copy()
        env.pop('BM_NATIVE_CONTENT_PACK', None)
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SNESRECOMP_REWIND='0')
        if data is not None:
            path = directory / 'invalid-pack.bin'
            path.write_bytes(data)
            env['BM_NATIVE_CONTENT_PACK'] = str(path)
        command = [str(binary), '--no-launcher', '--config', str(ROOT / 'recomp/m1-config.ini'),
                   '--rom', str(ROOT / 'local/restoration' / TARGET / 'rom.sfc'),
                   '--script', str(ROOT / ROUTES[0][1])]
        with (directory / 'run.log').open('w') as output:
            result = subprocess.run(command, cwd=directory, env=env, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=30)
        receipt = {'binary_sha256': sha(binary.read_bytes()), 'rom': cfg['output'],
                   'content': identity(TARGET), 'pack_sha256': sha(data) if data is not None else None,
                   'returncode': result.returncode, 'expected': expected, 'command': command}
        (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


def qualify(prefix, report_name=None):
    cfg, spec = settings(TARGET)
    folder = ROOT / 'local/restoration' / TARGET
    rom, base = (folder / 'rom.sfc').read_bytes(), (
        ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    payload = (folder / spec['pack_file']).read_bytes()
    require(sha(base) == cfg['base_output']['sha256'], 'base ROM differs')
    require(sha(rom) == cfg['output']['sha256'], 'pilot ROM differs')
    require(len(payload) == spec['payload']['size'] and sha(payload) == spec['payload']['sha256'],
            'pack identity differs')
    start = lorom(int(spec['original_address'], 16))
    slot = spec['pointer_offset']
    require(rom[start:start + len(payload)] == bytes(len(payload)), 'ROM still contains the payload')
    require(base[start:start + len(payload)] == payload, 'pack differs from frozen content')
    expected = bytearray(base)
    expected[start:start + len(payload)] = bytes(len(payload))
    expected[slot:slot + 3] = int(spec['native_address'], 16).to_bytes(3, 'little')
    require(rom == expected, 'unexpected ROM modifications')
    require(graphics_pointer(rom, int(spec['recipient_gfx_id'], 16)) == int(spec['native_address'], 16),
            'native graphics pointer differs')
    decoded, _ = lz2(base, int(spec['original_address'], 16))
    require(len(decoded) == spec['decoded']['size'] and sha(decoded) == spec['decoded']['sha256'],
            'decoded resource differs')

    report = {'target': TARGET, 'base': cfg['base_output'], 'rom': cfg['output'],
              'qualifier_sha256': sha(Path(__file__).read_bytes()),
              'content': identity(TARGET), 'captures': [], 'negative_startup_checks': []}
    for route, script, gameplay_dumps, room in ROUTES:
        control = capture_path(prefix, 'control', route)
        external = capture_path(prefix, 'external', route)
        receipts = []
        for role, directory, target in (('control', control, BASE), ('external', external, TARGET)):
            receipt = read_json(directory / 'receipt.json')
            receipts.append(receipt)
            require(receipt['stage'] == 'native' and receipt['target'] == target, 'wrong capture role')
            require(receipt['rom_sha256'] == (cfg['base_output'] if role == 'control' else cfg['output'])['sha256'],
                    'capture ROM identity differs')
            require(receipt['route_sha256'] == sha((ROOT / script).read_bytes()), 'input identity differs')
            build = read_json(ROOT / 'local/build' / target / 'm1-build.json')
            binary = ROOT / 'local/build' / target / RESTORATIONS[target]['binary']
            require(receipt['host_binary_sha256'] == build['binary_sha256'] == sha(binary.read_bytes()),
                    'capture/build executable identities differ')
            require(receipt.get('native_content') == (identity(TARGET) if role == 'external' else None),
                    'capture content identity differs')
            require(receipt['runtime_patches'] == build['runtime_patches'], 'capture runtime pins differ')
            require(receipt['analysis'] == build['analysis'], 'capture generated code identity differs')
            program = read_json(directory / 'program-manifest.json')
            require(not any(int(key.split(':')[0], 16) >> 16 in (0x36, 0xB6)
                            for key in program['nodes']),
                    'data pilot unexpectedly has generated code in split banks')
            log = (directory / 'run.log').read_text()
            require('exit: script quit after' in log and not re.search(r'script.*(?:timeout|failed)', log, re.I),
                    'route did not finish: ' + str(directory))
            if role == 'external':
                require('[native-content] mounted star1-ffd bank=B6 payload_bytes=3001' in log,
                        'pack not mounted')
                counts = re.findall(r'asset_resolutions=(\d+)', log)
                require(counts, 'missing mapping telemetry')
                if route == 'star1':
                    require(int(counts[-1]) > 0 and 'first_asset_resolution=B68008' in log,
                            'resource was not resolved through the pack')
            for name in gameplay_dumps:
                body = (directory / f'{name}.wram.bin').read_bytes()
                require(len(body) == 0x20000 and body[0x100] == 0x14 and
                        int.from_bytes(body[0x10B:0x10D], 'little') == room,
                        'gameplay state/room differs: ' + str(directory / name))
        require(receipts[0]['upstream_pins'] == receipts[1]['upstream_pins'], 'host source pins differ')
        names = sorted(p.name.removesuffix('.wram.bin') for p in control.glob('*.wram.bin'))
        require(names == sorted(p.name.removesuffix('.wram.bin') for p in external.glob('*.wram.bin')),
                'dump sets differ')
        comparisons = []
        for name in names:
            for suffix, size in SIZES.items():
                filename = f'{name}.{suffix}'
                left, right = (control / filename).read_bytes(), (external / filename).read_bytes()
                require(len(left) == len(right) == size and left == right, 'dump mismatch: ' + filename)
                comparisons.append({'file': filename, 'size': size, 'sha256': sha(left)})
            for suffix in ('apu.tsv', 'ppuw.tsv', 'regs.json', 'dma.tsv'):
                filename = f'{name}.{suffix}'
                left, right = (control / filename).read_bytes(), (external / filename).read_bytes()
                require(left and left == right, 'trace mismatch: ' + filename)
                comparisons.append({'file': filename, 'size': len(left), 'sha256': sha(left)})
        if route == 'star1':
            first = (external / 's1.wram.bin').read_bytes()
            last = (external / 's2.wram.bin').read_bytes()
            require(first[0x94:0x96] != last[0x94:0x96], 'movement fixture did not move Mario')
        report['captures'].append({'route': route, 'control': str(control.relative_to(ROOT)),
                                   'external': str(external.relative_to(ROOT)),
                                   'receipt_sha256': [sha((p / 'receipt.json').read_bytes())
                                                      for p in (control, external)],
                                   'equal_samples': comparisons})

    binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
    for case in ('missing', 'corrupt', 'truncated', 'oversized'):
        directory = ROOT / 'local/captures' / f'{prefix}-reject-{case}'
        receipt = read_json(directory / 'receipt.json')
        log = (directory / 'run.log').read_text()
        require(receipt['binary_sha256'] == sha(binary.read_bytes()) and
                receipt['rom'] == cfg['output'] and receipt['content'] == identity(TARGET),
                'negative capture identity differs')
        require(receipt['returncode'] != 0 and
                '[native-content] rejected: ' + receipt['expected'] in log,
                'bad pack did not fail for the expected reason')
        report['negative_startup_checks'].append({'case': case,
            'receipt_sha256': sha((directory / 'receipt.json').read_bytes())})
    path = ROOT / 'local/reports' / f'{report_name or prefix + "-qualification"}.json'
    require(not path.exists(), 'refusing to overwrite qualification report')
    path.write_text(json.dumps(report, indent=2) + '\n')
    total = sum(len(x['equal_samples']) for x in report['captures'])
    print(f'Native content passed: {total} equal samples; 4 rejected-pack startups; {path.relative_to(ROOT)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-prefix', required=True)
    parser.add_argument('--run', action='store_true', help='collect fresh captures before qualifying')
    parser.add_argument('--report-name', help='fresh report name when rechecking existing evidence')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.capture_prefix):
        parser.error('invalid capture prefix')
    if args.report_name and not re.fullmatch(r'[A-Za-z0-9_-]+', args.report_name):
        parser.error('invalid report name')
    if args.run:
        collect(args.capture_prefix)
    qualify(args.capture_prefix, args.report_name)


if __name__ == '__main__':
    main()

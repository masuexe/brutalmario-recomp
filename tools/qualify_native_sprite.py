#!/usr/bin/env python3
"""Qualify fixed external sprite code, donor behavior and unchanged native routes."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from native_content import identity as graphics_identity
from native_sprite import ROOT, TARGET, identity, settings, sha, environment
from qualify_native_content import ROUTES, SIZES, read_json, require
from restoration_targets import RESTORATIONS
from restore_star_world_1 import lorom
from runtime_patches import patch_plan

BASE = 'demo11-native-pack-pilot'
FLOW = 'recomp/inputs/native-sprite9e-room146.script'
DONOR = 'recomp/inputs/native-sprite9e-donor146.script'
CONTROL = 'recomp/inputs/native-sprite9e-control146.script'
SEMANTIC_DUMPS = ('entry240', 'entry360', 'board', 'ride32', 'ride64', 'ride128',
                  'vertical_board', 'vertical32', 'vertical64', 'other097', 'return146')
FIELDS = (0xaa, 0xb6, 0xc2, 0xd8, 0xe4, 0x14d4, 0x14e0, 0x14c8,
          0x151c, 0x1528, 0x1570, 0x1602, 0x157c)


def folder(prefix, name):
    return ROOT / 'local/captures' / (prefix + '-' + name)


def actors(body):
    return [(i, *[body[a + i] for a in FIELDS]) for i in range(12)
            if body[0x14c8 + i] and body[0x1ab9e + i] == 0x9e]


def collect(prefix):
    runs = [('native-flow', TARGET, FLOW), ('control-entry', BASE, CONTROL)]
    for route, script, _, _ in ROUTES:
        runs += [('control-' + route, BASE, script), ('external-' + route, TARGET, script)]
    for name, target, script in runs:
        subprocess.run([sys.executable, str(ROOT / 'tools/m1.py'), 'native', '--target', target,
                        '--capture', prefix + '-' + name, '--script', script], cwd=ROOT, check=True)
    versions = read_json(ROOT / 'config/content-versions.json')['versions']
    donor = next(v for v in versions if v['id'] == 'cheap-demo')
    manifest = ROOT / 'local/reports' / (prefix + '-donor-manifest.json')
    require(not manifest.exists(), 'donor manifest already exists')
    manifest.write_text(json.dumps({'target': 'Official cheap-demo donor', 'output': donor['output']}, indent=2) + '\n')
    subprocess.run([sys.executable, str(ROOT / 'tools/probe_reference.py'), '--manifest', str(manifest),
                    '--rom', 'local/content-versions/cheap-demo/rom.sfc', '--script', DONOR,
                    '--capture', prefix + '-donor-flow'], cwd=ROOT, check=True)
    cfg, spec = settings(TARGET)
    binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
    code = (ROOT / 'local/restoration' / TARGET / spec['code']['pack_file']).read_bytes()
    for case, variable, payload, reason in (
            ('missing-code', 'BM_NATIVE_SPRITE_PACK', None, 'BM_NATIVE_SPRITE_PACK'),
            ('corrupt-code', 'BM_NATIVE_SPRITE_PACK', bytes(len(code)), 'pack SHA-256 differs'),
            ('short-code', 'BM_NATIVE_SPRITE_PACK', code[:-1], 'pack size differs'),
            ('long-code', 'BM_NATIVE_SPRITE_PACK', code + b'\0', 'pack size differs'),
            ('missing-graphics', 'BM_NATIVE_GRAPHICS_PACK', None, 'BM_NATIVE_GRAPHICS_PACK')):
        directory = folder(prefix, 'reject-' + case)
        directory.mkdir(parents=True, exist_ok=False)
        env = os.environ.copy()
        environment(TARGET, env)
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SNESRECOMP_REWIND='0')
        env.pop(variable)
        if payload is not None:
            path = directory / 'invalid.bin'
            path.write_bytes(payload)
            env[variable] = str(path)
        command = [str(binary), '--no-launcher', '--config', str(ROOT / 'recomp/m1-config.ini'),
                   '--rom', str(ROOT / 'local/restoration' / TARGET / 'rom.sfc'),
                   '--script', str(ROOT / FLOW)]
        with (directory / 'run.log').open('w') as output:
            result = subprocess.run(command, cwd=directory, env=env, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=30)
        receipt = {'rom': cfg['output'], 'binary_sha256': sha(binary.read_bytes()), 'content': identity(TARGET),
                   'invalid_payload_sha256': sha(payload) if payload is not None else None,
                   'returncode': result.returncode, 'expected': reason}
        (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


def check_native(directory, target, script):
    receipt = read_json(directory / 'receipt.json')
    cfg = read_json(ROOT / 'config/restorations' / (target + '.json'))
    build = read_json(ROOT / 'local/build' / target / 'm1-build.json')
    binary = ROOT / 'local/build' / target / RESTORATIONS[target]['binary']
    require(receipt['stage'] == 'native' and receipt['target'] == target, 'capture role differs')
    require(receipt['rom_sha256'] == cfg['output']['sha256'] == build['rom_sha256'], 'ROM identities differ')
    require(receipt['host_binary_sha256'] == build['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    require(receipt['route_sha256'] == sha((ROOT / script).read_bytes()), 'input identity differs')
    require(receipt['native_content'] == (identity(target) or graphics_identity(target)) == build['native_content'],
            'native content identity differs')
    require(receipt['analysis'] == build['analysis'] and receipt['runtime_patches'] == build['runtime_patches'],
            'runtime/generated code identity differs')
    require(receipt['runtime_patches'] == patch_plan(), 'current shared runtime pins differ')
    program = read_json(directory / 'program-manifest.json')
    require(not any(int(k.split(':')[0], 16) >> 16 in (0x25, 0xa5, 0x36, 0xb6) for k in program['nodes']),
            'compiled code overlaps a split bank')
    log = (directory / 'run.log').read_text()
    require('exit: script quit after' in log and 'TIMEOUT' not in log, 'native route did not finish')
    return receipt, log


def qualify(prefix, report_name):
    cfg, spec = settings(TARGET)
    directory = ROOT / 'local/restoration' / TARGET
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    rom = (directory / 'rom.sfc').read_bytes()
    require(sha(base) == cfg['base_output']['sha256'] and sha(rom) == cfg['output']['sha256'], 'ROM pins differ')
    slot = spec['record']['destination_offset']
    expected = bytearray(base)
    expected[slot:slot + 16] = bytes.fromhex(spec['record']['after'])
    require(rom == expected, 'unexpected ROM edits')
    code = spec['code']
    start = lorom(int(code['source_address'], 16))
    require(rom[start:start + code['size']] == base[start:start + code['size']], 'ordinary bank data changed')
    donor_pin = next(v['output'] for v in read_json(ROOT / 'config/content-versions.json')['versions'] if v['id'] == 'cheap-demo')
    donor_rom = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    require(sha(donor_rom) == donor_pin['sha256'], 'official donor identity differs')
    for item, pin, expected_bytes in (
            (code, code, donor_rom[start:start + code['size']]),
            (spec['graphics'], spec['graphics']['payload'],
             (ROOT / 'local/restoration' / BASE / spec['graphics']['pack_file']).read_bytes())):
        data = (directory / item['pack_file']).read_bytes()
        require(len(data) == pin['size'] and sha(data) == pin['sha256'] and data == expected_bytes,
                'external pack differs')
    native = folder(prefix, 'native-flow')
    _, log = check_native(native, TARGET, FLOW)
    counters = re.findall(r'code_resolutions=(\d+) graphics_resolutions=(\d+) executed_page_instructions=(\d+)', log)
    require(counters and int(counters[-1][0]) > 0 and int(counters[-1][2]) > 0, 'external code was not executed')
    coverage = sorted((native / 'coverage').rglob('*.json'))
    require(coverage, 'missing interpreter coverage')
    coverage = read_json(coverage[-1])
    require(coverage['identity']['rom_sha256'] == cfg['output']['sha256'], 'coverage ROM differs')
    require(coverage['identity']['build_digest'] == sha((ROOT / 'local/build' / TARGET /
            RESTORATIONS[TARGET]['binary']).read_bytes()), 'coverage binary differs')
    observed = {v['target_pc24'].upper(): v for v in coverage['discoveries']}
    for key in ('init', 'main'):
        record = observed.get('0X' + code[key])
        require(record and record['observed_hits'] > 0 and record['fallback_reason'] == 'missing_entry',
                'external entry did not use the interpreter: ' + key)

    donor = folder(prefix, 'donor-flow')
    receipt = read_json(donor / 'receipt.json')
    require(receipt['rom_sha256'] == donor_pin['sha256'] and
            receipt['script_sha256'] == sha((ROOT / DONOR).read_bytes()), 'donor capture identities differ')
    require(receipt['frontend_sha256'] == sha((ROOT / 'local/build/snesref/snesref').read_bytes()) and
            receipt['core_sha256'] == sha((ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so').read_bytes()),
            'donor reference binaries differ')
    require('TIMEOUT' not in (donor / 'run.log').read_text() and ' quit' in (donor / 'run.log').read_text(),
            'donor behavior route did not finish')
    shared_prefix = (ROOT / FLOW).read_text().split('# Fall-position fixture.')[0]
    require((ROOT / DONOR).read_text() == shared_prefix + 'quit\n', 'donor/native fixture prefix differs')
    semantics = []
    for name in SEMANTIC_DUMPS:
        a, b = [(p / (name + '.wram.bin')).read_bytes() for p in (native, donor)]
        require(len(a) == len(b) == 0x20000 and a[0x100] == b[0x100] == 0x14, 'bad gameplay dump')
        require(a[0x10b:0x10d] == b[0x10b:0x10d] and a[0x94:0x98] == b[0x94:0x98], 'room/player state differs')
        require(actors(a) == actors(b), 'donor/native sprite states differ: ' + name)
        if name != 'other097':
            require(len(actors(a)) >= 2, 'platforms not active: ' + name)
        semantics.append({'dump': name, 'actors': actors(a), 'player_position': a[0x94:0x98].hex()})
    def body(name):
        data = (native / (name + '.wram.bin')).read_bytes()
        require(len(data) == 0x20000, 'native dump size differs: ' + name)
        return data
    a, b = body('board'), body('ride128')
    dx = b[0xe4 + 7] + 256 * b[0x14e0 + 7] - a[0xe4 + 7] - 256 * a[0x14e0 + 7]
    require(dx > 0 and int.from_bytes(b[0x94:0x96], 'little') - int.from_bytes(a[0x94:0x96], 'little') == dx and
            a[0x1528 + 7] == b[0x1528 + 7] == 1, 'horizontal lift did not carry Mario')
    a, b = body('vertical_board'), body('vertical64')
    dy = b[0xd8 + 6] + 256 * b[0x14d4 + 6] - a[0xd8 + 6] - 256 * a[0x14d4 + 6]
    require(dy < 0 and int.from_bytes(b[0x96:0x98], 'little') - int.from_bytes(a[0x96:0x98], 'little') == dy,
            'vertical lift did not carry Mario')
    require(a[0x1528 + 6] == b[0x1528 + 6] == 1, 'Mario was not carried')
    require(body('other097')[0x10b:0x10d] == bytes.fromhex('9700'), 'other-room transition failed')
    require(body('dying')[0x71] == 9 and body('returned_map')[0x100] == 0x0e, 'real death/map return failed')
    require(body('returned_map')[0xdbe] == body('return146')[0xdbe] - 1, 'life count did not decrease')
    require(body('reentry146')[0x100] == 0x14 and body('reentry146')[0x10b:0x10d] == bytes.fromhex('4601') and
            len(actors(body('reentry146'))) >= 2, 'death re-entry failed')

    control = folder(prefix, 'control-entry')
    check_native(control, BASE, CONTROL)
    for name in ('entry240', 'entry360'):
        old = (control / (name + '.vram.bin')).read_bytes()
        new = (native / (name + '.vram.bin')).read_bytes()
        require(len(old) == len(new) == 0x10000 and old[:0xc000] == new[:0xc000], 'background VRAM changed')
        palette = (native / (name + '.cgram.bin')).read_bytes()
        require(len(palette) == 512 and (control / (name + '.cgram.bin')).read_bytes() == palette,
                'room palette changed')
    unchanged = []
    for route, script, gameplay, room in ROUTES:
        old, new = folder(prefix, 'control-' + route), folder(prefix, 'external-' + route)
        check_native(old, BASE, script)
        check_native(new, TARGET, script)
        for name in gameplay:
            data = (new / (name + '.wram.bin')).read_bytes()
            require(data[0x100] == 0x14 and int.from_bytes(data[0x10b:0x10d], 'little') == room,
                    'unchanged route missed its room')
        files = sorted(p.name for p in old.glob('*.wram.bin'))
        require(files == sorted(p.name for p in new.glob('*.wram.bin')), 'unchanged dump sets differ')
        for filename in files:
            stem = filename.removesuffix('.wram.bin')
            for suffix, size in {**SIZES, 'apu.tsv': None, 'ppuw.tsv': None, 'regs.json': None, 'dma.tsv': None}.items():
                name = stem + '.' + suffix
                a, b = (old / name).read_bytes(), (new / name).read_bytes()
                require(a and a == b and (size is None or len(a) == size), 'unchanged route mismatch: ' + name)
                unchanged.append({'route': route, 'file': name, 'sha256': sha(a)})
    binary_sha = sha((ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']).read_bytes())
    for case in ('missing-code', 'corrupt-code', 'short-code', 'long-code', 'missing-graphics'):
        directory = folder(prefix, 'reject-' + case)
        r = read_json(directory / 'receipt.json')
        require(r['rom'] == cfg['output'] and r['binary_sha256'] == binary_sha and r['content'] == identity(TARGET),
                'negative startup identity differs')
        require(r['returncode'] != 0 and '[native-sprite] rejected: ' + r['expected'] in (directory / 'run.log').read_text(),
                'invalid pack was not rejected correctly')
    path = ROOT / 'local/reports' / (report_name + '.json')
    require(not path.exists(), 'refusing to overwrite qualification report')
    receipts = {str(p.parent.relative_to(ROOT)): sha(p.read_bytes())
                for p in (ROOT / 'local/captures').glob(prefix + '-*/receipt.json')}
    report = {'target': TARGET, 'rom': cfg['output'], 'binary_sha256': binary_sha, 'content': identity(TARGET),
              'qualifier_sha256': sha(Path(__file__).read_bytes()), 'receipt_sha256': receipts,
              'source_behavior': semantics, 'unchanged': unchanged, 'startup_rejections': 5,
              'code_pointer_resolutions': int(counters[-1][0]), 'executed_page_instructions': int(counters[-1][2])}
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Native sprite passed: {len(semantics)} donor-matched samples, {len(unchanged)} unchanged comparisons, 5 rejected startups; {path.relative_to(ROOT)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-prefix', required=True)
    parser.add_argument('--report-name')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    for value in (args.capture_prefix, args.report_name or args.capture_prefix + '-qualification'):
        if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
            parser.error('invalid evidence name')
    if args.run:
        collect(args.capture_prefix)
    qualify(args.capture_prefix, args.report_name or args.capture_prefix + '-qualification')


if __name__ == '__main__':
    main()

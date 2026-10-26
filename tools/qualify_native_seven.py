#!/usr/bin/env python3
"""Qualify Seven Koopalings entry/opening and preserved native routes.

No whole-fight, ending, music, late child-sprite or save acceptance is implied.
Historical controls are reused only after verifying their exact identities.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from native_seven import TARGET, ROOT, identity, settings, environment
from native_sprite import identity as sprite_identity
from prepare_rom import verify
from qualify_native_content import SIZES
from restoration_targets import RESTORATIONS
from restore_star_world_1 import lorom, sha, write_verified
from runtime_patches import patch_plan

BASE = 'demo11-native-sprite9e'
TAGS = ('fight180', 'fight600', 'fight1200', 'fight2400', 'after_b', 'after_a', 'after_x', 'after_y')
SUFFIXES = {**SIZES, 'apu.tsv': None, 'ppuw.tsv': None, 'regs.json': None, 'dma.tsv': None}
FIELDS = (0xc2, 0x1504, 0xe4, 0x14e0, 0xd8, 0x14d4, 0x14c8, 0x15ac,
          0x1602, 0x1528, 0x151c, 0x1570, 0x157c, 0xaa, 0xb6)


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_text())


def native_capture(directory, target, script):
    receipt = read(directory / 'receipt.json')
    cfg = read(ROOT / 'config/restorations' / (target+'.json'))
    build = read(ROOT / 'local/build' / target / 'm1-build.json')
    feature = identity(target) or sprite_identity(target)
    require(receipt['target'] == target and receipt['stage'] == 'native', 'native capture role differs')
    require(receipt['rom_sha256'] == cfg['output']['sha256'] == build['rom_sha256'], 'native ROM differs')
    require(receipt['host_binary_sha256'] == build['binary_sha256'] ==
            sha((ROOT / 'local/build' / target / RESTORATIONS[target]['binary']).read_bytes()), 'binary differs')
    require(receipt['native_content'] == build['native_content'] == feature, 'native module identity differs')
    require(receipt['analysis'] == build['analysis'] and receipt['runtime_patches'] ==
            build['runtime_patches'] == patch_plan(), 'native build/runtime identity differs')
    require(receipt['route_sha256'] == sha((ROOT / script).read_bytes()), 'route differs')
    require((directory / 'input.script').read_text() == 'turbo on\n'+(ROOT / script).read_text(),
            'executed input copy differs')
    log = (directory / 'run.log').read_text()
    require('exit: script quit after' in log and 'TIMEOUT' not in log, 'capture did not complete')
    return receipt, log


def state(directory, tag):
    body = (directory / (tag+'.wram.bin')).read_bytes()
    require(len(body) == 0x20000, 'WRAM size differs')
    require(len((directory / (tag+'.vram.bin')).read_bytes()) == 0x10000, 'VRAM size differs')
    return body


def actors(body, detailed=False):
    fields = FIELDS if detailed else (0xc2, 0x1504)
    return [(slot, *[body[address+slot] for address in fields]) for slot in range(12)
            if body[0x14c8+slot] == 8 and body[0x1ab10+slot] & 8 and body[0x1ab9e+slot] == 0x2a]


def reject_startups(prefix):
    cfg, _ = settings(TARGET)
    rom = ROOT / 'local/restoration' / TARGET / 'rom.sfc'
    binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
    code = (rom.parent / 'seven-code.bin').read_bytes()
    for case, variable, payload, reason in (
        ('missing-code', 'BM_SEVEN_CODE_PACK', None, 'BM_SEVEN_CODE_PACK'),
        ('missing-graphics', 'BM_SEVEN_GRAPHICS_PACK', None, 'BM_SEVEN_GRAPHICS_PACK'),
        ('corrupt-code', 'BM_SEVEN_CODE_PACK', bytes(len(code)), 'pack SHA-256 differs'),
        ('short-code', 'BM_SEVEN_CODE_PACK', code[:-1], 'pack size differs'),
        ('long-code', 'BM_SEVEN_CODE_PACK', code+b'\0', 'pack size differs'),
    ):
        directory = ROOT / 'local/captures' / (prefix+'-reject-'+case)
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
                   '--rom', str(rom), '--script', str(ROOT / 'recomp/inputs/native-seven-native-opening.script')]
        with (directory / 'run.log').open('w') as output:
            result = subprocess.run(command, cwd=directory, env=env,
                                    stdout=output, stderr=subprocess.STDOUT, timeout=30)
        receipt = {'rom': cfg['output'], 'binary_sha256': sha(binary.read_bytes()),
                   'feature': identity(TARGET), 'returncode': result.returncode, 'expected': reason,
                   'invalid_payload_sha256': sha(payload) if payload is not None else None}
        (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


def qualify(opening, regression, output):
    cfg, recipe = settings(TARGET)
    current = ROOT / 'local/restoration' / TARGET
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    verify(base, cfg['base_output'], 'parent')
    expected = bytearray(base)
    for patch in recipe['unapplied_rom_patches']:
        offset, data = patch['offset'], bytes.fromhex(patch['after'])
        expected[offset:offset+len(data)] = data
    rom = (current / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'native target')
    require(rom == expected, 'unexpected recipient edits')
    donor_pin = read(ROOT / 'config/boss-donor.json')['output']
    donor_rom = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
    verify(donor_rom, donor_pin, 'official donor')
    donor = ROOT / 'local/captures' / (opening+'-donor')
    native = ROOT / 'local/captures' / (opening+'-native')
    source_receipt = read(donor / 'receipt.json')
    source_script = ROOT / 'recomp/inputs/native-seven-donor-opening.script'
    require(source_receipt['rom_sha256'] == donor_pin['sha256'] and
            source_receipt['script_sha256'] == sha(source_script.read_bytes()) and
            (donor / 'input.script').read_bytes() == source_script.read_bytes(), 'donor identities differ')
    for key, path in (('frontend_sha256', 'local/build/snesref/snesref'),
                      ('core_sha256', 'local/upstream/snes9x/libretro/snes9x_libretro.so')):
        require(source_receipt[key] == sha((ROOT / path).read_bytes()), 'reference binary differs')
    require(source_receipt['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled', 'reference option differs')
    require(' quit' in (donor / 'run.log').read_text(), 'reference script did not complete')
    receipt, log = native_capture(native, TARGET, 'recomp/inputs/native-seven-native-opening.script')
    counters = re.findall(r'bank=([A-F0-9]+) resolutions=(\d+) executed_page_instructions=(\d+)', log)
    counts = {bank: {'resolutions': int(resolutions), 'instructions': int(instructions)}
              for bank, resolutions, instructions in counters}
    require(counts['A2']['instructions'] > 0 and counts['A6']['resolutions'] > 0, 'new packs were not exercised')
    font = recipe['font_adaptation']['decoded']
    semantics = []
    for tag in TAGS:
        a, b = state(donor, tag), state(native, tag)
        for body in (a, b):
            require(body[0x100] == 0x14 and int.from_bytes(body[0x10b:0x10d], 'little') == 0xff,
                    'opening did not remain in intended room')
        require(actors(a) == actors(b) and actors(b), 'opening actor slot/phase mismatch')
        exact = actors(a, True) == actors(b, True)
        if tag in ('fight1200', 'fight2400'):
            require(exact, 'paused transformation actor state differs')
        for directory in (donor, native):
            graphics = (directory / (tag+'.vram.bin')).read_bytes()[0x9000:0x9800]
            verify(graphics, font, 'fight-local Japanese GFX2A in VRAM')
        semantics.append({'tag': tag, 'actors': actors(b), 'all_sampled_actor_fields_equal': exact,
                          'native_wram_sha256': sha(b), 'donor_wram_sha256': sha(a)})
    unchanged = []
    controls = []
    for route, old_suffix, script in (
        ('star1', 'external-star1', 'recomp/inputs/demo11-star1-entry.script'),
        ('boss', 'external-boss', 'recomp/inputs/demo11-hp-boss-bc.script'),
        ('lifts', 'native-flow', 'recomp/inputs/native-sprite9e-room146.script'),
    ):
        old = ROOT / 'local/captures' / ('native-sprite9e-final-'+old_suffix)
        new = ROOT / 'local/captures' / (regression+'-'+route)
        native_capture(old, BASE, script)
        native_capture(new, TARGET, script)
        old_tags = sorted(path.name.removesuffix('.wram.bin') for path in old.glob('*.wram.bin'))
        require(old_tags == sorted(path.name.removesuffix('.wram.bin') for path in new.glob('*.wram.bin')),
                'regression dump set differs')
        for tag in old_tags:
            for suffix, size in SUFFIXES.items():
                name = tag+'.'+suffix
                a, b = (old / name).read_bytes(), (new / name).read_bytes()
                require(a and a == b and (size is None or len(a) == size), 'regression mismatch: '+route+'/'+name)
                unchanged.append({'route': route, 'file': name, 'sha256': sha(a)})
        controls.extend([old, new])
    rejection_receipts = []
    for case in ('missing-code', 'missing-graphics', 'corrupt-code', 'short-code', 'long-code'):
        directory = ROOT / 'local/captures' / (opening+'-reject-'+case)
        negative = read(directory / 'receipt.json')
        require(negative['rom'] == cfg['output'] and negative['feature'] == identity(TARGET) and
                negative['binary_sha256'] == receipt['host_binary_sha256'], 'negative startup identity differs')
        require(negative['returncode'] != 0 and '[native-seven] rejected: '+negative['expected']
                in (directory / 'run.log').read_text(), 'invalid pack was not rejected')
        rejection_receipts.append(directory)
    late_native, late_donor = state(native, 'attack1200'), state(donor, 'attack1200')
    report = {'scope': __doc__.strip(), 'target': TARGET, 'rom': cfg['output'],
        'binary_sha256': receipt['host_binary_sha256'], 'feature': identity(TARGET),
        'qualifier_sha256': sha(Path(__file__).read_bytes()), 'opening': semantics,
        'execution': counts, 'font_vram_sha256': font['sha256'], 'unchanged': unchanged,
        'startup_rejections': len(rejection_receipts),
        'late_probe_observation': {'native_room': f'{int.from_bytes(late_native[0x10b:0x10d], "little"):03X}',
            'donor_room': f'{int.from_bytes(late_donor[0x10b:0x10d], "little"):03X}',
            'dependency': 'Source at 2284D5 creates custom 6A; recipient 6A is a different restored actor. '
                          'This capture does not establish a complete causal explanation of the divergent transition.'},
        'limitations': ['Phase/actor-slot correspondence at eight samples; full actor fields match only the two paused samples.',
                       'No full motion/pixel/audio equivalence, complete fight, ending, map return or saved-clear qualification.',
                       'Music and the late dynamically spawned 6A dependency remain open.',
                       'Original ROMs, earlier captures, parent A5/B6 assets and recipient global font are preserved.'],
        'receipt_sha256': {str(path.relative_to(ROOT)): sha((path / 'receipt.json').read_bytes())
                           for path in [donor, native, *controls, *rejection_receipts]}}
    write_verified(output, (json.dumps(report, indent=2)+'\n').encode())
    print(f'8 opening samples / {len(unchanged)} unchanged comparisons / 5 rejected startups; {output}')
    print('Report SHA-256:', sha(output.read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--opening-prefix', default='seven-opening-v1')
    parser.add_argument('--regression-prefix', default='seven-regression-v1')
    parser.add_argument('--collect-rejections', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'local/reports/native-seven-entry-final.json')
    args = parser.parse_args()
    if args.collect_rejections:
        reject_startups(args.opening_prefix)
    qualify(args.opening_prefix, args.regression_prefix, args.output)

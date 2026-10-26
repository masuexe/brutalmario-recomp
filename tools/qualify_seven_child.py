#!/usr/bin/env python3
"""Check the bounded Seven child phase, native death/re-entry and regressions.

Event waits align a spawned child, not the entire cross-version fight. Different
dialogue/phase timing outside these samples remains unqualified.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from native_seven_child import ROOT, TARGET, identity, settings, environment, packs
from prepare_rom import verify
from qualify_native_content import SIZES
from qualify_native_seven import native_capture as parent_capture
from restore_star_world_1 import lorom, sha, write_verified
from runtime_patches import patch_plan
from restoration_targets import RESTORATIONS

BASE = 'demo11-native-seven-font-entry'
FIELDS = (0x9e, 0xc2, 0x1504, 0xe4, 0x14e0, 0xd8, 0x14d4, 0x14c8, 0x15ac,
          0x1602, 0x1528, 0x151c, 0x1570, 0x157c, 0xaa, 0xb6, 0x1662, 0x166e, 0x167a)
SUFFIXES = {**SIZES, 'apu.tsv': None, 'ppuw.tsv': None, 'regs.json': None, 'dma.tsv': None}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_text())


def body(directory, tag):
    data = (directory / (tag+'.wram.bin')).read_bytes()
    require(len(data) == 0x20000, 'WRAM size differs')
    require(len((directory / (tag+'.vram.bin')).read_bytes()) == 0x10000, 'VRAM size differs')
    return data


def room(data):
    return int.from_bytes(data[0x10b:0x10d], 'little')


def native_capture(directory, script):
    receipt = read(directory / 'receipt.json')
    cfg, _ = settings(TARGET)
    build = read(ROOT / 'local/build' / TARGET / 'm1-build.json')
    require(receipt['stage'] == 'native' and receipt['target'] == TARGET, 'native role differs')
    require(receipt['rom_sha256'] == build['rom_sha256'] == cfg['output']['sha256'], 'native ROM differs')
    require(receipt['native_content'] == build['native_content'] == identity(TARGET), 'native child feature differs')
    require(receipt['host_binary_sha256'] == build['binary_sha256'] ==
            sha((ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']).read_bytes()), 'binary differs')
    require(receipt['analysis'] == build['analysis'] and receipt['runtime_patches'] ==
            build['runtime_patches'] == patch_plan(), 'build/runtime identity differs')
    route = (ROOT / script).read_bytes()
    require(receipt['route_sha256'] == sha(route) and
            (directory / 'input.script').read_bytes() == b'turbo on\n'+route, 'executed input differs')
    program = read(directory / 'program-manifest.json')
    forbidden = (0x1e, 0x9e, 0x22, 0xa2, 0x25, 0xa5, 0x26, 0xa6, 0x36, 0xb6)
    require(not any(int(key.split(':')[0], 16) >> 16 in forbidden for key in program['nodes']),
            'AOT node overlaps a split bank')
    log = (directory / 'run.log').read_text()
    require('exit: script quit after' in log and 'TIMEOUT' not in log, 'native script did not complete')
    return receipt, log


def collect_rejections(prefix):
    cfg, _ = settings(TARGET)
    directory = ROOT / 'local/restoration' / TARGET
    binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
    code = (directory / 'seven-child6a.bin').read_bytes()
    for case, data, expected in (('missing', None, 'BM_SEVEN_CHILD_PACK'),
                                ('corrupt', bytes(len(code)), 'pack SHA-256 differs'),
                                ('short', code[:-1], 'pack size differs'),
                                ('long', code+b'\0', 'pack size differs')):
        capture = ROOT / 'local/captures' / (prefix+'-'+case)
        capture.mkdir(parents=True, exist_ok=False)
        env = os.environ.copy()
        environment(TARGET, env)
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', SNESRECOMP_REWIND='0')
        env.pop('BM_SEVEN_CHILD_PACK')
        if data is not None:
            invalid = capture / 'invalid.bin'
            invalid.write_bytes(data)
            env['BM_SEVEN_CHILD_PACK'] = str(invalid)
        command = [str(binary), '--no-launcher', '--config', str(ROOT / 'recomp/m1-config.ini'),
                   '--rom', str(directory / 'rom.sfc'),
                   '--script', str(ROOT / 'recomp/inputs/seven-child-native-event.script')]
        with (capture / 'run.log').open('w') as output:
            result = subprocess.run(command, cwd=capture, env=env, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=30)
        receipt = {'rom': cfg['output'], 'binary_sha256': sha(binary.read_bytes()),
                   'feature': identity(TARGET), 'returncode': result.returncode, 'expected': expected,
                   'invalid_sha256': sha(data) if data is not None else None}
        (capture / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


def qualify(args):
    cfg, recipe = settings(TARGET)
    directory = ROOT / 'local/restoration' / TARGET
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    rom = (directory / 'rom.sfc').read_bytes()
    verify(base, cfg['base_output'], 'parent image')
    verify(rom, cfg['output'], 'child image')
    expected = bytearray(base)
    offset = recipe['record']['destination_offset']
    expected[offset:offset+16] = bytes.fromhex(recipe['record']['after'])
    require(rom == expected, 'unexpected ROM edits outside the E0 record')
    for pack in packs(TARGET):
        verify((directory / pack['pack_file']).read_bytes(), pack, 'final pack')
    kept = recipe['preserved_recipient_6a']
    verify(rom[kept['code_offset']:kept['code_offset']+kept['size']], kept, 'retained original 6A')
    require(rom[kept['record_offset']:kept['record_offset']+16].hex() == kept['record'], 'old 6A record changed')
    source = ROOT / 'local/captures' / args.donor
    native = ROOT / 'local/captures' / args.native
    source_receipt = read(source / 'receipt.json')
    donor_pin = read(ROOT / recipe['donor_manifest'])['output']
    verify((ROOT / 'local/content-versions/boss/rom.sfc').read_bytes(), donor_pin, 'official donor')
    route = (ROOT / 'recomp/inputs/seven-child-donor-event.script').read_bytes()
    require(source_receipt['rom_sha256'] == donor_pin['sha256'] and
            source_receipt['script_sha256'] == sha(route) and (source / 'input.script').read_bytes() == route,
            'source capture identity differs')
    for field, path in (('frontend_sha256', 'local/build/snesref/snesref'),
                        ('core_sha256', 'local/upstream/snes9x/libretro/snes9x_libretro.so')):
        require(source_receipt[field] == sha((ROOT / path).read_bytes()), 'reference binary differs')
    require(source_receipt['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled' and
            ' quit' in (source / 'run.log').read_text(), 'reference configuration/completion differs')
    receipt, log = native_capture(native, 'recomp/inputs/seven-child-native-event.script')
    execution = {bank: {'resolutions': int(reads), 'instructions': int(count)} for bank, reads, count in
                 re.findall(r'bank=([A-F0-9]+) resolutions=(\d+) executed_page_instructions=(\d+)', log)}
    require(execution['9E']['instructions'] > 0, 'child bank was not executed')
    samples = []
    font = read(ROOT / 'config/native-content/seven-font-module.json')['font_adaptation']['decoded']
    for tag in ('child_spawn', 'child32', 'child96'):
        old, new = body(source, tag), body(native, tag)
        require(old[0x100] == new[0x100] == 0x14 and room(old) == room(new) == 0xff, 'child sample missed fight')
        for slot in (6, 7):
            require(old[0x14c8+slot] == new[0x14c8+slot] == 8 and
                    old[0x1ab10+slot] & 8 and new[0x1ab10+slot] & 8, 'expected child not active/custom')
            require(old[0x1ab9e+slot] == 0x6a and new[0x1ab9e+slot] == 0xe0, 'wrong child namespace')
            old_state, new_state = [old[field+slot] for field in FIELDS], [new[field+slot] for field in FIELDS]
            require(old_state == new_state and new[0x9e+slot] == 0x6a and new[0xc2+slot] == 0x15,
                    'child state differs or normal ID was changed')
            samples.append({'tag': tag, 'slot': slot, 'fields': old_state})
        for capture in (source, native):
            verify((capture / (tag+'.vram.bin')).read_bytes()[0x9000:0x9800], font, 'local Japanese font')
    before, dying, returned = body(native, 'child96'), body(native, 'child_death'), body(native, 'child_map')
    reentry = body(native, 'child_fight_reentry')
    course = body(native, 'child_course_reentry')
    require(dying[0x71] == 9 and dying[0x100] == 0x14 and room(dying) == 0xff, 'real death not reached')
    require(returned[0x100] == 0x0e and returned[0xdbe]+1 == before[0xdbe], 'map return/life loss differs')
    require(course[0x100] == 0x14 and room(course) == 5, 'ordinary map re-entry differs')
    require(reentry[0x100] == 0x14 and room(reentry) == 0xff and reentry[0xdbe] == returned[0xdbe],
            'explicit fight re-entry failed')
    require(reentry[0x14c8+9] == 8 and reentry[0x1ab9e+9] == 0x2a and reentry[0xc2+9] == 0,
            'fight controller did not reset')
    english = recipe['font_lifecycle']['recipient_font']['decoded']
    verify((native / 'child_course_reentry.vram.bin').read_bytes()[0x9000:0x9800], english,
           'recipient English font after native death/map return')
    verify((native / 'child_fight_reentry.vram.bin').read_bytes()[0x9000:0x9800], font,
           'Japanese font on explicit fight re-entry')
    captures = [source, native]
    comparisons, observations = [], []
    routes = [('star1', 'recomp/inputs/demo11-star1-entry.script'),
              ('boss', 'recomp/inputs/demo11-hp-boss-bc.script'),
              ('lifts', 'recomp/inputs/native-sprite9e-room146.script')]
    cases = [(ROOT / 'local/captures' / ('seven-regression-v1-'+name),
              ROOT / 'local/captures' / (args.regression+'-'+name), script, name) for name, script in routes]
    for name in ('0d8', '0e2', '0e3', '0e4'):
        cases.append((ROOT / 'local/captures' / (args.existing_parent+'-parent-'+name),
                      ROOT / 'local/captures' / (args.existing+'-new-'+name),
                      'recomp/inputs/seven-child-existing-'+name+'.script', name))
    for old, new, script, name in cases:
        parent_capture(old, BASE, script)
        native_capture(new, script)
        tags = sorted(path.name.removesuffix('.wram.bin') for path in old.glob('*.wram.bin'))
        require(tags == sorted(path.name.removesuffix('.wram.bin') for path in new.glob('*.wram.bin')),
                'regression dump set differs')
        for tag in tags:
            for suffix, size in SUFFIXES.items():
                filename = tag+'.'+suffix
                a, b = (old / filename).read_bytes(), (new / filename).read_bytes()
                require(a and a == b and (size is None or len(a) == size), 'regression differs: '+name+'/'+filename)
                comparisons.append({'route': name, 'file': filename, 'sha256': sha(a)})
        if name.startswith('0'):
            sample = body(new, 'existing_later')
            observations.append({'room': name, 'mode': f'{sample[0x100]:02X}',
                'active_6a_slots': [slot for slot in range(12) if sample[0x14c8+slot] == 8
                                    and sample[0x1ab9e+slot] == 0x6a]})
        captures.extend([old, new])
    for case in ('missing', 'corrupt', 'short', 'long'):
        capture = ROOT / 'local/captures' / (args.reject+'-'+case)
        negative = read(capture / 'receipt.json')
        require(negative['rom'] == cfg['output'] and negative['feature'] == identity(TARGET) and
                negative['binary_sha256'] == receipt['host_binary_sha256'], 'negative startup identity differs')
        require(negative['returncode'] != 0 and '[native-seven] rejected: '+negative['expected'] in
                (capture / 'run.log').read_text(), 'invalid child pack was not rejected')
        captures.append(capture)
    report = {'scope': __doc__.strip(), 'target': TARGET, 'rom': cfg['output'],
        'binary_sha256': receipt['host_binary_sha256'], 'feature': identity(TARGET),
        'qualifier_sha256': sha(Path(__file__).read_bytes()),
        'field_addresses': [f'{field:05X}' for field in FIELDS], 'child_samples': samples,
        'execution': execution, 'native_death_reentry': {'before_lives': before[0xdbe],
            'after_lives': returned[0xdbe], 'map_mode': '0E', 'ordinary_course': '005',
            'pipe_fixture_reentry': '0FF', 'ordinary_course_font_sha256': english['sha256'],
            'fight_reentry_font_sha256': font['sha256']}, 'unchanged': comparisons,
        'existing_room_observations': observations, 'rejected_startups': 4,
        'limitations': ['Three event-aligned child samples, not full fight or motion/audio parity.',
            'Fixed-time probes retain different dialogue/phase timing; neither their cause nor whole-flow parity is qualified.',
            'Death/re-entry is native-only and fight re-entry uses an explicit pipe-action fixture.',
            'Room 0E4 remains at baseline mode 12; 0E2/0E3 samples contain no active 6A. Only 0D8 exercises an active old 6A.',
            'Font restoration is qualified on this death/map/re-entry path; other future fight exits remain open.',
            'Music, all later fight phases, ending and saved completion remain open.'],
        'receipt_sha256': {str(capture.relative_to(ROOT)): sha((capture / 'receipt.json').read_bytes())
                           for capture in captures},
        'event_dump_sha256': {str((capture / (tag+'.wram.bin')).relative_to(ROOT)):
            sha((capture / (tag+'.wram.bin')).read_bytes()) for capture in (source, native)
            for tag in ('child_spawn', 'child32', 'child96')}}
    write_verified(args.output, (json.dumps(report, indent=2)+'\n').encode())
    print(f'6 child samples / {len(comparisons)} unchanged comparisons / native death and fixture re-entry / 4 rejected startups')
    print(args.output, sha(args.output.read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', default='seven-child-event-v1-donor')
    parser.add_argument('--native', default='seven-child-cycle-event-v1-native')
    parser.add_argument('--regression', default='seven-child-cycle-regression-v1')
    parser.add_argument('--existing-parent', default='seven-child-existing-v1')
    parser.add_argument('--existing', default='seven-child-cycle-existing-v1')
    parser.add_argument('--reject', default='seven-child-cycle-reject-v1')
    parser.add_argument('--collect-rejections', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'local/reports/native-seven-child-cycle-final.json')
    args = parser.parse_args()
    if args.collect_rejections:
        collect_rejections(args.reject)
    qualify(args)

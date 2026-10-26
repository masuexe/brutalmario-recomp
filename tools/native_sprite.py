#!/usr/bin/env python3
"""Build the fixed-bank external sprite 9E descendant without ROM allocation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from native_content import ROOT, sha
from prepare_rom import verify
from restore_star_world_1 import lorom, sprite_rooms, write_verified

TARGET = 'demo11-native-sprite9e'


def settings(target):
    path = ROOT / 'config/restorations' / (target + '.json')
    if not path.exists():
        return None
    cfg = json.loads(path.read_text())
    if 'native_sprite' not in cfg:
        return None
    spec = json.loads((ROOT / cfg['native_sprite']['manifest']).read_text())
    if cfg['id'] != target or cfg['schema'] != 1 or spec['schema'] != 1:
        raise ValueError('native sprite schema/identity differs')
    return cfg, spec


def header(target):
    cfg, spec = settings(target)
    code, gfx = spec['code'], spec['graphics']
    def digest(name, value):
        return f'static const uint8_t {name}[32] = {{' + ','.join(
            str(v) for v in bytes.fromhex(value)) + '};\n'
    first = int(code['native_address'], 16)
    values = {'ROM_SIZE': cfg['output']['size'], 'CODE_BANK': first >> 16,
              'GFX_BANK': int(gfx['native_address'], 16) >> 16,
              'CODE_OFFSET': lorom(first), 'CODE_SIZE': code['size'],
              'GFX_OFFSET': lorom(int(gfx['original_address'], 16)),
              'GFX_SIZE': gfx['payload']['size'], 'FIRST_PAGE': first >> 8,
              'LAST_PAGE': (first + code['size'] - 1) >> 8}
    return ('/* Generated from reviewed native sprite recipe. */\n#include <stdint.h>\n' +
            ''.join(f'#define BM_SPRITE_{k} {v}u\n' for k, v in values.items()) +
            digest('bm_sprite_rom_sha', cfg['output']['sha256']) +
            digest('bm_sprite_code_sha', code['sha256']) +
            digest('bm_sprite_gfx_sha', gfx['payload']['sha256']))


def identity(target):
    pair = settings(target)
    if pair is None:
        return None
    cfg, spec = pair
    source = ROOT / 'local/upstream/snesrecomp/runner/src/snes/cart.c'
    if sha(source.read_bytes()) != spec['runtime_source_sha256']:
        raise ValueError('native sprite cartridge source differs')
    if sha((ROOT / spec['runtime_patch']).read_bytes()) != spec['runtime_patch_sha256']:
        raise ValueError('native sprite cartridge patch differs')
    files = [ROOT / 'config/restorations' / (target + '.json'),
             ROOT / cfg['native_sprite']['manifest'], ROOT / spec['runtime_patch'],
             ROOT / spec['graphics']['source_manifest'], ROOT / 'tools/native_sprite.py',
             ROOT / 'recomp/native_sprite.c', ROOT / 'recomp/native_content.h']
    return {'kind': 'immutable-external-sprite',
            'files': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in files},
            'code': spec['code'], 'graphics': spec['graphics'],
            'runtime_source_sha256': spec['runtime_source_sha256'],
            'runtime_result_sha256': spec['runtime_result_sha256'],
            'generated_header_sha256': sha(header(target).encode())}


def audit_code(donor, spec):
    """Bound donor control flow and reject unreviewed external/bank references."""
    sys.path.insert(0, str(ROOT / 'local/upstream/snesrecomp/recompiler'))
    from v2.decoder import decode_function
    from snes65816 import ABS, ABS_X, ABS_Y, LONG, LONG_X
    code = spec['code']
    first = int(code['source_address'], 16)
    last = first + code['size']
    bank = first >> 16
    # Record pointers, with the source bank restored; code bytes stay unchanged.
    todo = [(bank << 16) | (int(code[k], 16) & 0xffff) for k in ('init', 'main')]
    entries, insns = set(), {}
    while todo:
        pc = todo.pop()
        if pc in entries:
            continue
        if not first + 8 <= pc < last:
            raise ValueError('local entry escapes the external code block')
        entries.add(pc)
        graph = decode_function(donor, bank, pc & 0xffff, 1, 1, end=last & 0xffff)
        if graph.unresolved_indirects or graph.suppressed_indirect_calls:
            raise ValueError('unreviewed indirect control flow')
        for decoded in graph.insns.values():
            ins = decoded.insn
            if not first + 8 <= ins.addr < last or ins.addr + ins.length > last:
                raise ValueError('instruction escapes the code block')
            insns[(ins.addr, decoded.key.m, decoded.key.x)] = ins
            if ins.mnem == 'JSR' and ins.mode == ABS:
                todo.append((bank << 16) | ins.operand)
            if ins.mode in (ABS, ABS_X, ABS_Y) and ins.operand >= 0x8000:
                if not first <= (bank << 16 | ins.operand) < last:
                    raise ValueError('bank-local reference escapes the code block')
            if ins.mode in (LONG, LONG_X) and ins.operand >> 16 == bank:
                raise ValueError('source-bank long reference needs an explicit adaptation')
    calls = sorted({ins.operand for ins in insns.values() if ins.mnem in ('JSL', 'JML')})
    if calls != [int(v, 16) for v in spec['external_calls']]:
        raise ValueError('external call set differs from the reviewed closure')
    return {'entries': [f'{v:06X}' for v in sorted(entries)],
            'instruction_variants': len(insns),
            'external_calls': [f'{v:06X}' for v in calls],
            'source_code_sha256': code['sha256']}


def prepare(target=TARGET):
    cfg, spec = settings(target)
    identity(target)
    base_dir = ROOT / 'local/restoration' / cfg['base_restoration']
    base = (base_dir / 'rom.sfc').read_bytes()
    verify(base, cfg['base_output'], 'native sprite base')
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    pin = next(v for v in versions if v['id'] == cfg['donor'])
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    verify(donor, pin['output'], 'official sprite donor')
    code, record, gfx = spec['code'], spec['record'], spec['graphics']
    source, destination = int(code['source_address'], 16), int(code['native_address'], 16)
    if destination != source | 0x800000 or source >> 16 >= 0x40:
        raise ValueError('sprite pilot requires a split system-bank mirror')
    start = lorom(source)
    payload = donor[start:start + code['size']]
    verify(payload, code, 'sprite code')
    n, complement = int.from_bytes(payload[4:6], 'little'), int.from_bytes(payload[6:8], 'little')
    if payload[:4] != b'STAR' or n ^ complement != 0xffff or n + 9 != len(payload):
        raise ValueError('sprite RATS bounds differ')
    if (source & 0xffff) + len(payload) > 0x10000:
        raise ValueError('sprite crosses its fixed bank')
    if sprite_rooms(base, 0x9e) != spec['rooms']:
        raise ValueError('sprite placement dependencies differ')
    for dependency in spec['shared_dependencies']:
        off = lorom(int(dependency['address'], 16))
        for image in (base, donor):
            verify(image[off:off + dependency['size']], dependency, 'shared sprite dependency')
    audit = audit_code(donor, spec)
    slot, donor_slot = record['destination_offset'], record['source_offset']
    if donor[donor_slot:donor_slot + 16].hex() != record['source'] or base[slot:slot + 16].hex() != record['before']:
        raise ValueError('sprite record identity differs')
    new_record = bytearray(bytes.fromhex(record['source']))
    for index, key in ((8, 'init'), (11, 'main')):
        entry = int.from_bytes(new_record[index:index + 3], 'little')
        if not source + 8 <= entry < source + len(payload):
            raise ValueError('sprite entry is outside its bounded code')
        new_record[index + 2] = destination >> 16
        if int.from_bytes(new_record[index:index + 3], 'little') != int(code[key], 16):
            raise ValueError('rebased sprite entry differs')
    if new_record.hex() != record['after']:
        raise ValueError('sprite record adaptation differs')
    out = bytearray(base)
    out[slot:slot + 16] = new_record
    verify(out, cfg['output'], 'native sprite descendant')
    graphics = (base_dir / gfx['pack_file']).read_bytes()
    verify(graphics, gfx['payload'], 'cumulative external graphics')
    directory = ROOT / 'local/restoration' / target
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in (('rom.sfc', out), (code['pack_file'], payload), (gfx['pack_file'], graphics)):
        write_verified(directory / name, data)
    receipt = {'config': cfg, 'content': identity(target), 'donor': pin['output'], 'code_audit': audit}
    (directory / 'input-manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'{target}: ROM {sha(out)}, code {len(payload)} external bytes, {len(audit["entries"])} local entries')
    return bytes(out)


def environment(target, env):
    cfg, spec = settings(target)
    directory = ROOT / 'local/restoration' / target
    for variable, item, pin in (
            ('BM_NATIVE_SPRITE_PACK', spec['code'], spec['code']),
            ('BM_NATIVE_GRAPHICS_PACK', spec['graphics'], spec['graphics']['payload'])):
        path = directory / item['pack_file']
        verify(path.read_bytes(), pin, variable)
        env[variable] = str(path)


def configure(experiment, binary, target):
    if identity(target) is None:
        return
    cfg, spec = settings(target)
    program = json.loads((experiment / 'src/gen/program_manifest.json').read_text())
    if any(int(key.split(':')[0], 16) >> 16 in (0x25, 0xA5, 0x36, 0xB6) for key in program['nodes']):
        raise ValueError('external sprite pilot forbids AOT nodes in split banks and their aliases')
    directory = ROOT / 'local/native-content-runtime' / target
    cart = directory / 'runner/src/snes/cart.c'
    cart.parent.mkdir(parents=True, exist_ok=True)
    if not cart.exists():
        cart.write_bytes((ROOT / 'local/upstream/snesrecomp/runner/src/snes/cart.c').read_bytes())
    actual = sha(cart.read_bytes())
    if actual == spec['runtime_source_sha256']:
        subprocess.run(['git', 'apply', '--directory=' + str(directory.relative_to(ROOT)),
                        str(ROOT / spec['runtime_patch'])], cwd=ROOT, check=True)
    if sha(cart.read_bytes()) != spec['runtime_result_sha256']:
        raise ValueError('unknown native sprite runtime override')
    write_verified(directory / 'native_sprite_manifest.h', header(target).encode())
    cmake = experiment / 'CMakeLists.txt'
    text = cmake.read_text()
    begin, end = '# BEGIN native sprite pilot', '# END native sprite pilot'
    block = '\n'.join([begin, f'get_target_property(_sprite_sources {binary} SOURCES)',
        'list(REMOVE_ITEM _sprite_sources "${SNESRECOMP_ROOT}/runner/src/snes/cart.c")',
        f'set_property(TARGET {binary} PROPERTY SOURCES ${{_sprite_sources}})',
        f'target_sources({binary} PRIVATE "{cart}" "{ROOT / "recomp/native_sprite.c"}")',
        f'target_include_directories({binary} PRIVATE "{directory}" "{ROOT / "recomp"}" "{ROOT / "local/upstream/snesrecomp/runner/src/snes"}")', end])
    if begin in text:
        text = text[:text.index(begin)] + block + text[text.index(end) + len(end):]
    else:
        text += '\n' + block + '\n'
    cmake.write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default=TARGET)
    prepare(parser.parse_args().target)

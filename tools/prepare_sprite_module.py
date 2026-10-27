#!/usr/bin/env python3
"""Prepare a reviewed gap sprite module pack without changing a game target.

The tool verifies the pinned donor, the reviewed record and the protected
program, audits inline dispatch tables and the outside call set, and writes an
unapplied code pack with a receipt. Runtime mapping, graphics and gameplay stay
separate gates.
"""
import argparse
import json
from pathlib import Path
import sys

from audit_star_boss_donors import sprite_table
from prepare_rom import prepare_bytes, verify
from restore_star_world_1 import lorom, sha, sprite_rooms, write_verified

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'config/native-content/sprite95-module.json'


def read_recipe(path=RECIPE):
    return json.loads(Path(path).read_text())


def prepare_donor(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text())
    patch = manifest['authoritative_patch']
    rom = prepare_bytes((ROOT / patch['base_path']).read_bytes(),
                        (ROOT / patch['ips_path']).read_bytes(),
                        dict(patch, output=manifest['output']))
    verify(rom, manifest['output'], 'prepared donor')
    return rom


def check_record(donor, recipe):
    record = recipe['record']
    constructor, body, table = sprite_table(donor)
    slot = int(record['slot'], 16)
    raw = donor[lorom(table)+slot*16:lorom(table)+slot*16+16]
    if raw.hex() != record['raw']:
        raise ValueError('module record differs from the review')
    if f'{int.from_bytes(raw[8:11], "little"):06X}' != record['init']:
        raise ValueError('module init address differs from the review')
    if f'{int.from_bytes(raw[11:14], "little"):06X}' != record['main']:
        raise ValueError('module main address differs from the review')
    rooms = [f'{room:03X}' for room in sprite_rooms(donor, slot)]
    if rooms != record['rooms']:
        raise ValueError('module room list differs from the review')
    native = int(recipe['code']['native_address'], 16)
    relative = recipe['record']['relative']
    native_payload = bytearray(raw)
    native_payload[8:11] = (native + int(relative['init'], 16)).to_bytes(3, 'little')
    native_payload[11:14] = (native + int(relative['main'], 16)).to_bytes(3, 'little')
    if native_payload.hex() != record['native_raw']:
        raise ValueError('native record adaptation differs from the review')
    return {'slot': f'{slot:02X}', 'raw': raw.hex(), 'init': record['init'],
            'main': record['main'], 'rooms': rooms,
            'native_raw': native_payload.hex(),
            'constructor': f'{constructor:06X}', 'table': f'{table:06X}'}


def analyze(donor, recipe):
    """Audit the reviewed module recipe."""
    sys.path.insert(0, str(ROOT / 'local/upstream/snesrecomp/recompiler'))
    from v2.decoder import decode_function
    from snes65816 import ABS, ABS_X, ABS_Y, LONG, LONG_X
    code = recipe['code']
    first = int(code['source_address'], 16)
    end = first + code['size']
    bank = first >> 16
    todo = [(int(seed, 16) & 0xffff, 1, 1) for seed in recipe['entry_seeds']]
    reviewed, tables = set(), []
    for table in recipe['dispatch_tables']:
        address, count = int(table['address'], 16), table['count']
        start = lorom(address)
        data = donor[start:start+count*3]
        verify(data, {'size': count*3, 'sha256': table['sha256']}, 'dispatch table')
        targets = []
        for index in range(count):
            entry = data[index*3:index*3+3]
            if entry[0] != 0x20:
                raise ValueError('dispatch entry is not an inline JSR')
            target = int.from_bytes(entry[1:], 'little')
            if not first+8 <= (bank << 16 | target) < end:
                raise ValueError('dispatch target escapes module')
            todo.append((target, 1, 1))
            targets.append(f'{bank << 16 | target:06X}')
        dispatcher = int(table['dispatcher'], 16)
        if donor[lorom(dispatcher):lorom(dispatcher)+3] != bytes.fromhex('6c0000'):
            raise ValueError('reviewed indirect dispatcher differs')
        reviewed.add(dispatcher)
        tables.append(dict(table, targets=targets))
    entries, instructions, observed = set(), {}, set()
    while todo:
        pc, m, x = todo.pop()
        if (pc, m, x) in entries:
            continue
        entries.add((pc, m, x))
        if not first+8 <= (bank << 16 | pc) < end:
            raise ValueError('local entry escapes module')
        graph = decode_function(donor, bank, pc, m, x, end=0x10000)
        if graph.suppressed_indirect_calls:
            raise ValueError('suppressed indirect call remains unreviewed')
        for jump in graph.unresolved_indirects:
            if jump.site_pc24 not in reviewed:
                raise ValueError('unreviewed indirect jump')
            observed.add(jump.site_pc24)
        for decoded in graph.insns.values():
            ins = decoded.insn
            if not first <= (bank << 16 | ins.addr) < end or (bank << 16 | ins.addr)+ins.length > end:
                raise ValueError('decoded instruction escapes module')
            instructions[(ins.addr, decoded.key.m, decoded.key.x)] = ins
            if (ins.mode in (ABS, ABS_X, ABS_Y) and ins.operand >= 0x8000
                    and ins.mnem not in ('PEA', 'PER')):
                if not first <= (bank << 16 | ins.operand) < end:
                    declared = recipe.get('ignored_operands', []) + recipe.get('relocated_operands', [])
                    ignored = {(int(item['address'], 16), int(item['operand'], 16))
                               for item in declared}
                    if (bank << 16 | ins.addr, ins.operand) not in ignored:
                        raise ValueError('bank-local operand escapes module')
            if ins.mnem in ('JMP', 'JSR') and ins.mode in (ABS, LONG):
                target = (bank << 16 | ins.operand) if ins.mode == ABS else ins.operand
                if first <= target < end:
                    if ins.mnem == 'JSR':
                        todo.append((ins.operand, decoded.key.m, decoded.key.x))
                elif (target >> 16) == bank:
                    declared = {(int(item['address'], 16), int(item['operand'], 16))
                                for item in recipe.get('external_entries', [])}
                    if (bank << 16 | ins.addr, ins.operand) not in declared:
                        raise ValueError('bank-local jump leaves module at %04X' % ins.addr)
                target = bank << 16 | ins.operand
                if first <= target < end:
                    todo.append((ins.operand, decoded.key.m, decoded.key.x))
            if ins.mnem in ('JSL', 'JML') and ins.mode in (LONG, LONG_X):
                target = ins.operand
                if (target >> 16) == bank and first <= target < end:
                    todo.append((target & 0xffff, decoded.key.m, decoded.key.x))
    if observed != reviewed:
        raise ValueError('reviewed indirect dispatch coverage differs')
    local = {ins.addr: ins for ins in instructions.values()
             if ins.mode in (LONG, LONG_X) and ins.operand >> 16 == bank}
    expected = {int(patch['address'], 16) for patch in recipe['code_patches']
                if len(bytes.fromhex(patch['before'])) == 4
                and patch['before'].startswith(('22', '5c'))}
    calls_only = all(ins.mnem in ('JSL', 'JML') or
                     (ins.mnem == 'JMP' and ins.mode == LONG) for ins in local.values())
    if set(local) != expected or not calls_only:
        raise ValueError('source-bank call adaptations differ from decoded sites')
    calls = sorted({f'{ins.operand:06X}' for ins in instructions.values()
                    if ins.mnem in ('JSL', 'JML') and ins.operand >> 16 != bank})
    if calls != recipe['external_calls']:
        raise ValueError('outside call set differs from review')
    return {'local_entry_states': len(entries), 'instruction_variants': len(instructions),
            'reviewed_dispatch_tables': tables,
            'source_bank_jsl_sites': [f'{pc:06X}' for pc in sorted(local)],
            'outside_calls': calls,
            'scope': 'Bounded explicit dispatch seeds plus local JSR/self-bank JSL '
                     'traversal; entry M/X states are recorded, not a whole-program proof.'}


def build_code(donor, base, recipe):
    code = recipe['code']
    first, native = int(code['source_address'], 16), int(code['native_address'], 16)
    bank_start = lorom(native & 0xff8000)
    if ((first & 0xffff) < 0x8000 or (native & 0xffff) < 0x8000 or
            lorom(native)+code['size'] > bank_start+0x8000):
        raise ValueError('unreviewed executable mapping')
    if (native & 0xffff) != (first & 0xffff):
        raise ValueError('module move must keep the low 16 address bits')
    payload = donor[lorom(first):lorom(first)+code['size']]
    verify(payload, code, 'source protected program')
    if (payload[:4] != b'STAR' or int.from_bytes(payload[4:6], 'little')+9 != len(payload)
            or int.from_bytes(payload[4:6], 'little') ^ int.from_bytes(payload[6:8], 'little') != 0xffff):
        raise ValueError('protected program bounds differ')
    audit = analyze(donor, recipe)
    adapted = bytearray(payload)
    for patch in recipe['code_patches']:
        start = int(patch['address'], 16)-first
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if (len(before) != len(after) or start < 8 or start+len(before) > len(adapted)
                or adapted[start:start+len(before)] != before):
            raise ValueError('code adaptation bytes/bounds differ')
        adapted[start:start+len(before)] = after
    if sha(bytes(adapted)) != code.get('adapted_sha256'):
        raise ValueError('adapted program hash differs from the review')
    for dependency in recipe.get('shared_dependencies', []):
        offset = lorom(int(dependency['address'], 16))
        for image in (donor, base):
            verify(image[offset:offset+dependency['size']], dependency, 'shared helper pin')
    appendix = recipe.get('code', {}).get('data_appendix')
    payload = bytes(adapted)
    if appendix:
        source = lorom(int(appendix['source_address'], 16))
        data = donor[source:source+appendix['size']]
        verify(data, appendix, 'data appendix')
        payload = payload+data
    payload_pin = recipe.get('code', {}).get('native_payload')
    if payload_pin:
        verify(payload, payload_pin, 'module pack payload')
    return payload, audit


def prepare(directory, recipe_path=RECIPE):
    recipe = read_recipe(recipe_path)
    donor = prepare_donor(ROOT / recipe['donor_manifest'])
    base = (ROOT / 'local/restoration' / recipe['base_restoration'] / 'rom.sfc').read_bytes()
    verify(base, recipe['base_output'], 'native base')
    record = check_record(donor, recipe)
    code, audit = build_code(donor, base, recipe)
    directory.mkdir(parents=True, exist_ok=True)
    paths = [Path(__file__), Path(recipe_path), ROOT / recipe['donor_manifest'],
             ROOT / 'tools/prepare_rom.py', ROOT / 'tools/restore_star_world_1.py',
             ROOT / 'tools/audit_star_boss_donors.py',
             ROOT / 'local/upstream/snesrecomp/recompiler/v2/decoder.py',
             ROOT / 'local/upstream/snesrecomp/recompiler/snes65816.py']
    receipt = {'scope': __doc__.strip(), 'recipe': recipe, 'audit': audit, 'record': record,
               'donor_manifest': recipe['donor_manifest'],
               'donor_sha256': sha(donor), 'base_sha256': sha(base),
               'adapted_code_sha256': sha(code[:int(recipe['code']['size'])]),
               'payload_sha256': sha(code), 'payload_size': len(code),
               'input_files': {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in paths},
               'graphics': 'not prepared; the graphics review stays open'}
    for name, data in ((recipe['code']['pack_file'], code),
                       ('preparation-receipt.json',
                        (json.dumps(receipt, indent=2) + chr(10)).encode())):
        write_verified(directory / name, data)
    print(f'Prepared {len(code)} code bytes; no game ROM written')
    print('Receipt SHA-256:', sha((directory / 'preparation-receipt.json').read_bytes()))
    return code, receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'local/native-modules/sprite95-v1')
    parser.add_argument('--recipe', type=Path, default=RECIPE)
    args = parser.parse_args()
    prepare(args.output_dir, args.recipe)
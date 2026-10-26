#!/usr/bin/env python3
"""Prepare reviewed Seven Koopalings packs without changing a game target.

The output includes an unapplied integration plan. CPU boundary qualification
and bounded static analysis do not qualify complete native Boss gameplay.
"""
import argparse
import json
from pathlib import Path
import sys

from audit_boss_dependencies import prepare_boss
from prepare_rom import verify
from restore_star_world_1 import graphics_pointer, lorom, lz2, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'config/native-content/seven-module.json'


def read_recipe(path=RECIPE):
    overlay = json.loads(path.read_text())
    if 'base_manifest' not in overlay:
        return overlay
    base = json.loads((ROOT / overlay['base_manifest']).read_text())
    base['id'], base['scope'] = overlay['id'], overlay['scope']
    base['base_manifest'] = overlay['base_manifest']
    base['font_adaptation'] = overlay['font_adaptation']
    base['code_patches'].append(overlay['font_adaptation']['init_patch'])
    base['code']['native_payload'] = overlay['native_payload']
    base['code']['adapted_sha256'] = overlay['native_payload']['sha256']
    base['graphics_pack'].update(overlay['graphics_payload'])
    return base


def analyze(donor, recipe):
    sys.path.insert(0, str(ROOT / 'local/upstream/snesrecomp/recompiler'))
    from v2.decoder import decode_function
    from snes65816 import ABS, ABS_X, ABS_Y, LONG, LONG_X
    code = recipe['code']
    first = int(code['source_address'], 16)
    end = first + code['size']
    bank = first >> 16
    todo = [(0x800f, 1, 1), (0x808d, 1, 1)]
    reviewed = set()
    tables = []
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
            if not first+8 <= bank << 16 | target < end:
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
        if not first+8 <= bank << 16 | pc < end:
            raise ValueError('local entry escapes module')
        graph = decode_function(donor, bank, pc, m, x, end=end & 0xffff)
        if graph.suppressed_indirect_calls:
            raise ValueError('suppressed indirect call remains unreviewed')
        for jump in graph.unresolved_indirects:
            if jump.site_pc24 not in reviewed:
                raise ValueError('unreviewed indirect jump')
            observed.add(jump.site_pc24)
        for decoded in graph.insns.values():
            ins = decoded.insn
            if not first+8 <= ins.addr < end or ins.addr+ins.length > end:
                raise ValueError('decoded instruction escapes module')
            instructions[(ins.addr, decoded.key.m, decoded.key.x)] = ins
            if ins.mode in (ABS, ABS_X, ABS_Y) and ins.operand >= 0x8000:
                if not first <= bank << 16 | ins.operand < end:
                    raise ValueError('bank-local operand escapes module')
            if ins.mnem == 'JSR' and ins.mode == ABS:
                todo.append((ins.operand, decoded.key.m, decoded.key.x))
            if ins.mnem in ('JSL', 'JML') and ins.operand >> 16 == bank:
                todo.append((ins.operand & 0xffff, decoded.key.m, decoded.key.x))
    if observed != reviewed:
        raise ValueError('reviewed indirect dispatch coverage differs')
    local = {ins.addr: ins for ins in instructions.values()
             if ins.mode in (LONG, LONG_X) and ins.operand >> 16 == bank}
    expected = {int(patch['address'], 16) for patch in recipe['code_patches']
                if len(bytes.fromhex(patch['before'])) == 4 and patch['before'].startswith('22')}
    if set(local) != expected or any(ins.mnem != 'JSL' for ins in local.values()):
        raise ValueError('source-bank call adaptations differ from decoded sites')
    calls = sorted({f'{ins.operand:06X}' for ins in instructions.values()
                    if ins.mnem in ('JSL', 'JML') and ins.operand >> 16 != bank})
    if calls != recipe['external_calls']:
        raise ValueError('outside call set differs from review')
    scheduler = sorted(ins.addr for ins in instructions.values()
                       if ins.mnem == 'JSL' and ins.operand == 0x10d8d0)
    for address in set(scheduler):
        if address+4 not in local:
            raise ValueError('deferred callback lacks a reviewed inline JSL')
    return {'local_entry_states': len(entries), 'instruction_variants': len(instructions),
            'reviewed_dispatch_tables': tables,
            'source_bank_jsl_sites': [f'{pc:06X}' for pc in sorted(local)],
            'scheduler_sites': [f'{pc:06X}' for pc in sorted(set(scheduler))],
            'outside_calls': calls,
            'scope': 'Bounded explicit dispatch seeds plus local JSR/self-bank JSL traversal; '
                     'entry M/X states are recorded, not a whole-program dataflow proof. '
                     'Outside shared-helper closure and gameplay remain separate gates.'}


def build(donor, base, recipe):
    verify(base, recipe['base_output'], 'unchanged native base')
    code = recipe['code']
    first = int(code['source_address'], 16)
    native = int(code['native_address'], 16)
    if first != 0x228000 or native != 0xa28000 or code['size'] > 0x8000:
        raise ValueError('unreviewed executable mapping')
    payload = donor[lorom(first):lorom(first)+code['size']]
    verify(payload, code, 'source protected program')
    if (payload[:4] != b'STAR' or int.from_bytes(payload[4:6], 'little')+9 != len(payload)
            or int.from_bytes(payload[4:6], 'little') ^ int.from_bytes(payload[6:8], 'little') != 0xffff):
        raise ValueError('protected program bounds differ')
    audit = analyze(donor, recipe)
    adapted = bytearray(payload)
    changed = set()
    for patch in recipe['code_patches']:
        start = int(patch['address'], 16)-first
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if (len(before) != len(after) or start < 8 or start+len(before) > len(adapted)
                or adapted[start:start+len(before)] != before):
            raise ValueError('code adaptation bytes/bounds differ')
        if changed.intersection(range(start, start+len(before))):
            raise ValueError('overlapping code adaptations')
        changed.update(range(start, start+len(before)))
        adapted[start:start+len(before)] = after
    font = recipe.get('font_adaptation')
    if font:
        address = int(font['native_routine'], 16)
        routine = bytes.fromhex(font['routine_bytes'])
        offset = address-native
        if address != 0xa2f000 or offset < len(adapted) or offset+len(routine) > 0x8000:
            raise ValueError('unreviewed local font routine mapping')
        adapted.extend(bytes(offset-len(adapted)))
        adapted.extend(routine)
    verify(adapted, code.get('native_payload', dict(code, sha256=code['adapted_sha256'])), 'adapted program')
    for dependency in recipe['shared_dependencies']:
        offset = lorom(int(dependency['address'], 16))
        for image in (donor, base):
            verify(image[offset:offset+dependency['size']], dependency, 'shared helper pin')
    for adaptation in recipe['recipient_adaptations']:
        offset = lorom(int(adaptation['address'], 16))
        for name, image in (('source', donor), ('recipient', base)):
            if name+'_bytes' in adaptation:
                raw = bytes.fromhex(adaptation[name+'_bytes'])
                if image[offset:offset+len(raw)] != raw:
                    raise ValueError('retained recipient hook differs')
            elif sha(image[offset:offset+128]) != adaptation[name+'_sha256']:
                raise ValueError('retained recipient death behavior differs')
    packed = bytearray(8)
    namespace = set()
    for graphics in recipe['graphics']:
        gid = int(graphics['source_id'], 16)
        pointer = graphics_pointer(donor, gid)
        if pointer != int(graphics['source_address'], 16):
            raise ValueError('donor graphics pointer differs')
        decoded, encoded = lz2(donor, pointer, limit=0x1000)
        verify(decoded, graphics['decoded'], 'decoded graphics')
        verify(encoded, graphics['encoded'], 'encoded graphics')
        if int(graphics['native_address'], 16) != 0xa68000+len(packed):
            raise ValueError('graphics pack has unreviewed layout')
        namespace.add(int(graphics['namespace_id'], 16))
        packed.extend(encoded)
    if font:
        pointer = graphics_pointer(donor, int(font['source_id'], 16))
        if pointer != int(font['source_address'], 16):
            raise ValueError('font source pointer differs')
        decoded, encoded = lz2(donor, pointer, limit=0x800)
        verify(decoded, font['decoded'], 'local donor font')
        verify(encoded, font['encoded'], 'encoded donor font')
        if int(font['native_address'], 16) != 0xa68000+len(packed):
            raise ValueError('local font pack extent differs')
        packed.extend(decoded)
    if namespace != set(range(0xfe0, 0xfec)) or len(packed) > 0x8000:
        raise ValueError('unreviewed graphics namespace or extent')
    for room in range(512):
        offset = lorom(0x14ad08)+room*32
        metadata = base[offset:offset+32]
        if metadata[:2] == b'\x01\x80' and any(int.from_bytes(metadata[i:i+2], 'little')
                in namespace for i in range(2, 20, 2)):
            raise ValueError('native graphics namespace has existing room references')
    verify(packed, recipe['graphics_pack'], 'graphics pack')
    projected = bytearray(base)
    for patch in recipe['unapplied_rom_patches']:
        offset = patch['offset']
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if len(before) != len(after) or projected[offset:offset+len(before)] != before:
            raise ValueError('unapplied recipient integration plan differs')
        projected[offset:offset+len(before)] = after
    audit['unapplied_integration_rom_sha256'] = sha(projected)
    audit['adapted_code_sha256'] = sha(adapted)
    return bytes(adapted), bytes(packed), audit


def prepare(directory, recipe_path=RECIPE):
    donor_manifest = prepare_boss()
    recipe = read_recipe(recipe_path)
    donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
    verify(donor, donor_manifest['output'], 'official IPS-derived donor')
    base = (ROOT / 'local/restoration' / recipe['base_restoration'] / 'rom.sfc').read_bytes()
    code, graphics, audit = build(donor, base, recipe)
    directory.mkdir(parents=True, exist_ok=True)
    paths = [Path(__file__), recipe_path, ROOT / recipe['donor_manifest'],
             ROOT / 'tools/audit_boss_dependencies.py', ROOT / 'tools/prepare_rom.py',
             ROOT / 'tools/restore_star_world_1.py',
             ROOT / 'local/upstream/snesrecomp/recompiler/v2/decoder.py',
             ROOT / 'local/upstream/snesrecomp/recompiler/snes65816.py']
    if 'base_manifest' in recipe:
        paths.append(ROOT / recipe['base_manifest'])
    receipt = {'scope': __doc__.strip(), 'recipe': recipe, 'audit': audit,
               'donor_sha256': sha(donor), 'base_sha256': sha(base),
               'input_files': {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in paths}}
    for name, data in ((recipe['code']['pack_file'], code),
                       (recipe['graphics_pack']['pack_file'], graphics),
                       ('preparation-receipt.json', (json.dumps(receipt, indent=2)+'\n').encode())):
        write_verified(directory / name, data)
    print(f'Prepared {len(code)} code bytes / {len(graphics)} graphics bytes; no game ROM written')
    print('Receipt SHA-256:', sha((directory / 'preparation-receipt.json').read_bytes()))
    return code, graphics, audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'local/native-modules/seven-v1')
    prepare(parser.parse_args().output_dir)

#!/usr/bin/env python3
"""Prepare the bounded official demoOnly1 A2 module without altering a game ROM."""
import argparse
import json
from pathlib import Path
import sys

from audit_star_boss_donors import sprite_table
from prepare_rom import verify
from qualify_forest_course_identity import sprite_list
from qualify_forest_shack import protected_stream
from qualify_world1_next_course import require
from restore_star_world_1 import graphics_pointer, lorom, lz2, sha, sprite_rooms, write_verified

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'config/native-content/spritea2-modern-module.json'


def load(path):
    return json.loads(path.read_text())


def audit_program(source, recipe):
    sys.path.insert(0, str(ROOT / 'local/upstream/snesrecomp/recompiler'))
    from v2.decoder import decode_function
    from snes65816 import ABS, ABS_X, ABS_Y, LONG, LONG_X
    code = recipe['code']
    first = int(code['source_address'], 16)
    end = first + code['size']
    bank = first >> 16
    dispatch = recipe['short_dispatch']
    table, count = int(dispatch['table'], 16), dispatch['count']
    raw = source[lorom(table):lorom(table) + count * 2]
    verify(raw, dict(size=count * 2, sha256=dispatch['sha256']), 'short dispatch table')
    targets = [bank << 16 | int.from_bytes(raw[i:i + 2], 'little') for i in range(0, len(raw), 2)]
    require([f'{pc:06X}' for pc in targets] == dispatch['targets'], 'dispatch target set differs')
    require(all(first + 8 <= pc < end for pc in targets), 'dispatch leaves protected program')
    helper = int(dispatch['helper'], 16)
    todo = [(int(seed, 16) & 0xFFFF, 1, 1) for seed in recipe['entry_seeds']]
    entries, instructions, sites = set(), {}, set()
    while todo:
        pc, m, x = todo.pop()
        if (pc, m, x) in entries:
            continue
        entries.add((pc, m, x))
        require(first + 8 <= bank << 16 | pc < end, 'local entry escapes program')
        graph = decode_function(source, bank, pc, m, x, end=end & 0xFFFF,
                                dispatch_helpers={helper: 'short'},
                                data_regions=[(bank, table & 0xFFFF, (table & 0xFFFF) + count * 2)])
        require(not graph.unresolved_indirects and not graph.suppressed_indirect_calls,
                'unreviewed indirect control flow')
        for decoded in graph.insns.values():
            ins = decoded.insn
            require(first + 8 <= ins.addr and ins.addr + ins.length <= end,
                    'decoded instruction escapes program')
            instructions[(ins.addr, decoded.key.m, decoded.key.x)] = ins
            if ins.dispatch_entries is not None:
                require(ins.addr == int(dispatch['site'], 16) and
                        ins.operand == helper and ins.dispatch_entries == [pc & 0xFFFF for pc in targets],
                        'unexpected dispatch site or targets')
                sites.add(ins.addr)
                todo.extend((pc & 0xFFFF, decoded.key.m, decoded.key.x) for pc in targets)
            if ins.mode in (ABS, ABS_X, ABS_Y) and ins.operand >= 0x8000:
                require(first + 8 <= bank << 16 | ins.operand < end,
                        'absolute code/data reference escapes program')
            if ins.mnem == 'JSR' and ins.mode == ABS:
                todo.append((ins.operand, decoded.key.m, decoded.key.x))
            if ins.mnem in ('JSL', 'JML') and ins.operand >> 16 == bank:
                todo.append((ins.operand & 0xFFFF, decoded.key.m, decoded.key.x))
    require(sites == {int(dispatch['site'], 16)}, 'dispatch coverage differs')
    calls = sorted({f'{ins.operand:06X}' for ins in instructions.values()
                    if ins.mnem in ('JSL', 'JML') and ins.operand >> 16 != bank})
    require(calls == recipe['external_calls'], 'external call set differs')
    local = {ins.addr: ins for ins in instructions.values()
             if ins.mode in (LONG, LONG_X) and ins.operand >> 16 == bank}
    declared = {int(p['address'], 16): p for p in recipe['relocations']}
    require(len(declared) == len(recipe['relocations']) and set(local) == set(declared),
            'source-bank relocation coverage differs')
    for pc, ins in local.items():
        patch = declared[pc]
        require(ins.length == 4 and first + 8 <= ins.operand < end,
                'long source-bank operand escapes program')
        original = source[lorom(pc):lorom(pc) + 4]
        expected = original[:3] + bytes([int(code['native_address'], 16) >> 16])
        require(patch['before'] == original.hex() and patch['after'] == expected.hex() and
                patch['kind'] == ('call' if ins.mnem in ('JSL', 'JML') else 'data'),
                'relocation changes more than its reviewed bank operand')
    return dict(local_entry_states=len(entries), instruction_variants=len(instructions),
                short_dispatch=dispatch, external_calls=calls,
                source_bank_relocations=[f'{pc:06X}' for pc in sorted(local)],
                limits='Explicit entry/dispatch seeds and local calls; dynamic WRAM data pointers and gameplay require execution evidence.')


def build(recipe):
    source_path = ROOT / 'local/content-versions' / recipe['source']['version'] / 'rom.sfc'
    source = source_path.read_bytes()
    verify(source, recipe['source']['output'], 'official source')
    parent = (ROOT / 'local/restoration' / recipe['parent']['target'] / 'rom.sfc').read_bytes()
    verify(parent, recipe['parent']['output'], 'parent')
    record = recipe['record']
    table = sprite_table(source)[2]
    require(source[lorom(table) + 0xA20:lorom(table) + 0xA30].hex() == record['raw'], 'source record differs')
    require([f'{room:03X}' for room in sprite_rooms(source, 0xA2)] == record['source_rooms'],
            'source placements differ')
    require(sprite_list(source, 0x182) == sprite_list(parent, 0x182) == bytes.fromhex('0069d0a2ff'),
            'modern branch placement differs')
    offset = lorom(sprite_table(parent)[2]) + 0xA20
    require(record['recipient_offset'] == offset and parent[offset:offset + 16].hex() == record['before'],
            'parent record differs')
    native_record = bytearray.fromhex(record['raw'])
    native_record[10] = native_record[13] = int(recipe['code']['native_address'], 16) >> 16
    require(native_record.hex() == record['native_raw'], 'native record changes outside the entry banks')
    for dependency in recipe['shared_dependencies']:
        pc = lorom(int(dependency['address'], 16))
        for body in (source, parent):
            verify(body[pc:pc + dependency['size']], dependency, 'shared dependency')
    helper = recipe['recipient_helper']
    pc = lorom(int(helper['address'], 16))
    a, b = source[pc:pc + helper['size']], parent[pc:pc + helper['size']]
    require(sha(a) == helper['source_sha256'] and sha(b) == helper['recipient_sha256'], 'draw helper differs')
    adapted = bytearray(a)
    for patch in helper['changes']:
        pos = lorom(int(patch['address'], 16)) - pc
        require(adapted[pos:pos + 2].hex() == patch['source'], 'draw helper source operand differs')
        adapted[pos:pos + 2] = bytes.fromhex(patch['recipient'])
    require(adapted == b and source[lorom(0x288000):lorom(0x288004)].hex() == helper['source_table'] and
            parent[lorom(0x28FD69):lorom(0x28FD6D)].hex() == helper['recipient_table'], 'draw helper adaptation differs')
    for graphics in recipe['graphics']:
        for body, label in ((source, 'source'), (parent, 'recipient')):
            pointer = graphics_pointer(body, int(graphics['id'], 16))
            require(f'{pointer:06X}' == graphics[label], 'graphics pointer differs')
            decoded, encoded = lz2(body, pointer, limit=0x10000)
            verify(encoded, graphics['encoded'], 'encoded graphics')
            verify(decoded, graphics['decoded'], 'decoded graphics')
    code = recipe['code']
    first, native = int(code['source_address'], 16), int(code['native_address'], 16)
    require((native >> 16 & 0x7F) < 0x40,
            'native program bank lacks the source WRAM/IO mirrors')
    require(first & 0xFFFF == native & 0xFFFF and native & 0xFFFF >= 0x8000 and
            (native & 0xFFFF) + code['size'] <= 0x10000, 'native mapping changes low addresses or leaves its bank')
    data = source[lorom(first):lorom(first) + code['size']]
    verify(data, code, 'protected program')
    require(data[:8] == bytes.fromhex('53544152df1c20e3') and len(data) == 7400,
            'protected program header or bound differs')
    audit = audit_program(source, recipe)
    output = bytearray(data)
    for patch in recipe['relocations']:
        pos = int(patch['address'], 16) - first
        require(output[pos:pos + 4].hex() == patch['before'], 'patch preimage differs')
        output[pos:pos + 4] = bytes.fromhex(patch['after'])
    adaptation = recipe['return_adaptation']
    require(adaptation['secondary_entrance'] == '1FF' and adaptation['destination'] == '11F' and
            (adaptation['player_x'], adaptation['player_y']) == (800, 352), 'return contract differs')
    fields = adaptation['fields']
    require([(p['address'], p['before'], p['after']) for p in fields] ==
            [('05F9FF', '00', '1f'), ('05FBFF', '00', '16'),
             ('05FDFF', '00', '43'), ('05FFFF', '00', '68')], 'secondary return encoding differs')
    for field in fields:
        require(parent[lorom(int(field['address'], 16))] == int(field['before'], 16),
                'return entrance namespace is occupied')
    seen, checked = set(), 0
    for room in range(512):
        try:
            body, pin = protected_stream(parent, 0x05E000, room)
        except ValueError:
            continue
        if pin['address'] in seen:
            continue
        seen.add(pin['address'])
        checked += 1
        # Conservative raw scan: a hit rejects admission even if it might be
        # an object/data byte sequence, so no semantic object parser is needed.
        require(not any(body[i] <= 31 and body[i + 1:i + 4] == b'\x07\x00\xff'
                        for i in range(len(body) - 3)), 'possible incoming secondary1FF reference')
    patch = adaptation['program_patch']
    require(patch == dict(address='30F3C7', before='00', after='ff'), 'unexpected return program patch')
    pos = int(patch['address'], 16) - first
    require(output[pos:pos + 1].hex() == patch['before'], 'return table preimage differs')
    output[pos] = int(patch['after'], 16)
    audit['return_namespace_layer1_allocations_checked'] = checked
    audit['return_adaptation'] = adaptation
    verify(output, dict(size=code['size'], sha256=code['adapted_sha256']), 'adapted program')
    return bytes(output), audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'local/native-modules/forest-a2-v3')
    args = parser.parse_args()
    recipe = load(RECIPE)
    code, audit = build(recipe)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = [RECIPE, Path(__file__), ROOT / 'config/content-versions.json',
             ROOT / 'local/upstream/snesrecomp/recompiler/v2/decoder.py',
             ROOT / 'local/upstream/snesrecomp/recompiler/snes65816.py']
    receipt = dict(recipe=recipe, audit=audit,
                   files={str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths},
                   payload_sha256=sha(code), payload_size=len(code), installed=False)
    write_verified(args.output_dir / recipe['code']['pack_file'], code)
    write_verified(args.output_dir / 'preparation-receipt.json', (json.dumps(receipt, indent=2) + '\n').encode())
    print(json.dumps(dict(output=str(args.output_dir), audit=audit, payload_sha256=sha(code))))


if __name__ == '__main__':
    main()

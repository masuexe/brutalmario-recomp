#!/usr/bin/env python3
"""Recover official demoOnly1 sprites99/A1 with reviewed bank semantics."""
import json
from pathlib import Path
import sys

from audit_star_boss_donors import sprite_table
from native_sprite_gap import packs, prepare
from prepare_rom import verify
from prepare_sprite_module import build_code, check_record
from qualify_world1_next_course import require
from restore_star_world_1 import lorom, sha, sprite_rooms, write_verified

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'config/native-content/modern-sprite-integration.json'
A1 = ROOT / 'config/native-content/spritea1-modern-module.json'
TARGET = 'demo11-native-modern-sprites-v1'


def load(path):
    return json.loads(Path(path).read_text())


def audit_a1(source, recipe):
    sys.path.insert(0, str(ROOT / 'local/upstream/snesrecomp/recompiler'))
    from v2.decoder import decode_function
    from snes65816 import ABS, ABS_X, ABS_Y, LONG, LONG_X
    first = int(recipe['code']['source_address'], 16)
    end = first+recipe['code']['size']
    bank = first >> 16
    tables = recipe['short_dispatches']
    require([(t['site'], t['table'], t['count']) for t in tables] ==
            [('30893F', '308943', 8), ('3089B1', '3089B5', 8)], 'A1 dispatch boundaries differ')
    regions, targets = [], {}
    for table in tables:
        at = int(table['table'], 16)
        raw = source[lorom(at):lorom(at)+table['count']*2]
        verify(raw, dict(size=table['count']*2, sha256=table['sha256']), 'A1 short dispatch')
        rows = [bank << 16 | int.from_bytes(raw[i:i+2], 'little') for i in range(0, len(raw), 2)]
        require([f'{pc:06X}' for pc in rows] == table['targets'] and
                all(first+8 <= pc < end for pc in rows), 'A1 dispatch targets escape program')
        targets[int(table['site'], 16)] = rows
        regions.append((bank, at & 0xFFFF, (at & 0xFFFF)+len(raw)))
    todo = [(int(seed, 16) & 0xFFFF, 1, 1) for seed in recipe['entry_seeds']]
    entries, instructions, sites = set(), {}, set()
    while todo:
        pc, m, x = todo.pop()
        if (pc, m, x) in entries:
            continue
        entries.add((pc, m, x))
        require(first+8 <= bank << 16 | pc < end, 'A1 local entry escapes program')
        graph = decode_function(source, bank, pc, m, x, end=end & 0xFFFF,
                                dispatch_helpers={0x0086DF: 'short'}, data_regions=regions)
        require(not graph.unresolved_indirects and not graph.suppressed_indirect_calls,
                'A1 unreviewed indirect control flow')
        for decoded in graph.insns.values():
            ins = decoded.insn
            require(first+8 <= ins.addr and ins.addr+ins.length <= end, 'A1 instruction escapes program')
            instructions[(ins.addr, decoded.key.m, decoded.key.x)] = ins
            if ins.dispatch_entries is not None:
                require(ins.addr in targets and ins.operand == 0x0086DF and
                        ins.dispatch_entries == [pc & 0xFFFF for pc in targets[ins.addr]],
                        'A1 unexpected dispatcher or table extent')
                sites.add(ins.addr)
                todo.extend((pc & 0xFFFF, decoded.key.m, decoded.key.x) for pc in targets[ins.addr])
            if ins.mode in (ABS, ABS_X, ABS_Y) and ins.operand >= 0x8000 and ins.mnem not in ('PEA', 'PER'):
                require(first+8 <= bank << 16 | ins.operand < end, 'A1 absolute operand escapes program')
            if ins.mnem == 'JSR' and ins.mode == ABS:
                todo.append((ins.operand, decoded.key.m, decoded.key.x))
            if ins.mnem in ('JSL', 'JML') and ins.operand >> 16 == bank:
                todo.append((ins.operand & 0xFFFF, decoded.key.m, decoded.key.x))
    require(sites == set(targets), 'A1 dispatch coverage differs')
    calls = sorted({f'{ins.operand:06X}' for ins in instructions.values()
                    if ins.mnem in ('JSL', 'JML') and ins.operand >> 16 != bank})
    require(calls == recipe['external_calls'], 'A1 external calls differ')
    local = {ins.addr: ins for ins in instructions.values()
             if ins.mode in (LONG, LONG_X) and ins.operand >> 16 == bank}
    declared = {int(p['address'], 16): p for p in recipe['relocations']}
    require(len(declared) == len(recipe['relocations']) == 52 and set(local) == set(declared),
            'A1 source-bank relocation coverage differs')
    for pc, ins in local.items():
        patch = declared[pc]
        original = source[lorom(pc):lorom(pc)+4]
        replacement = original[:3]+bytes([int(recipe['code']['native_address'], 16) >> 16])
        require(ins.length == 4 and first+8 <= ins.operand < end and
                patch['before'] == original.hex() and patch['after'] == replacement.hex() and
                patch['kind'] == ('call' if ins.mnem in ('JSL', 'JML') else 'data'),
                'A1 relocation changes beyond one reviewed bank byte')
    return dict(local_entry_states=len(entries), instruction_variants=len(instructions),
                short_dispatches=tables, external_calls=calls, relocated_sites=sorted(declared))


def build_a1(source, parent, recipe):
    code = recipe['code']
    start, address = int(code['source_address'], 16), int(code['native_address'], 16)
    require(address == 0x8A88EB and start == 0x3088EB and code['size'] == 5724 and
            start & 0xFFFF == address & 0xFFFF and address >> 16 & 0x7F < 0x40,
            'A1 source or native mirror mapping differs')
    data = source[lorom(start):lorom(start)+code['size']]
    verify(data, code, 'official A1 protected program')
    require(data[:4] == b'STAR' and int.from_bytes(data[4:6], 'little')+9 == len(data) and
            int.from_bytes(data[4:6], 'little') ^ int.from_bytes(data[6:8], 'little') == 0xFFFF,
            'A1 protected allocation bounds differ')
    table = lorom(sprite_table(source)[2])
    require(source[table+0xA10:table+0xA20].hex() == recipe['record']['raw'] and
            [f'{room:03X}' for room in sprite_rooms(source, 0xA1)] == recipe['record']['source_rooms'],
            'A1 official record/placements differ')
    for pin in recipe['shared_dependencies']:
        at = lorom(int(pin['address'], 16))
        for image in (source, parent):
            verify(image[at:at+pin['size']], pin, 'A1 shared helper entry')
    # The recipient already relocates GetDrawInfo's shared data table. Keep
    # that qualified engine adaptation; do not install the older helper.
    helper = recipe['recipient_helper']
    require(helper['address'] == '28FD6D' and helper['size'] == 125, 'drawing helper scope differs')
    at = lorom(int(helper['address'], 16))
    a, b = source[at:at+helper['size']], parent[at:at+helper['size']]
    require(sha(a) == helper['source_sha256'] and sha(b) == helper['recipient_sha256'],
            'recipient drawing helper identity differs')
    adapted_helper = bytearray(a)
    for patch in helper['changes']:
        pos = int(patch['address'], 16)-int(helper['address'], 16)
        require(adapted_helper[pos:pos+2].hex() == patch['source'], 'drawing helper preimage differs')
        adapted_helper[pos:pos+2] = bytes.fromhex(patch['recipient'])
    require(adapted_helper == b, 'unreviewed recipient drawing helper change')
    graph = audit_a1(source, recipe)
    output = bytearray(data)
    for patch in recipe['relocations']:
        pos = int(patch['address'], 16)-start
        require(output[pos:pos+4].hex() == patch['before'], 'A1 relocation preimage differs')
        output[pos:pos+4] = bytes.fromhex(patch['after'])
    verify(output, dict(size=code['size'], sha256=code['adapted_sha256']), 'native A1 program')
    return bytes(output), graph


def review(plan=None, a1=None):
    plan = plan if plan is not None else load(PLAN)
    a1 = a1 if a1 is not None else load(A1)
    require((plan['parent'], plan['candidate']) == ('demo11-native-sprite-product-v1', TARGET),
            'modern integration lineage differs')
    cfg = load(ROOT / 'config/restorations' / (TARGET+'.json'))
    old_cfg = load(ROOT / 'config/restorations' / (plan['parent']+'.json'))
    parent = (ROOT / 'local/restoration' / plan['parent'] / 'rom.sfc').read_bytes()
    source = (ROOT / 'local/content-versions/demo-only-1/rom.sfc').read_bytes()
    verify(parent, plan['parent_output'], 'cumulative parent')
    verify(source, load(ROOT / 'config/demo-only-1-donor.json')['output'], 'official demoOnly1')
    require(cfg['parent_restoration'] == plan['parent'] and cfg['parent_output'] == old_cfg['output'] ==
            plan['parent_output'] and cfg['output'] == plan['candidate_output'], 'modern candidate pin differs')
    sprite99 = load(ROOT / plan['sprite99_recipe'])
    require(sprite99['record']['slot'] == '99' and sprite99['code']['native_address'] == '8BA6FC' and
            sprite99['donor_manifest'] == 'config/demo-only-1-donor.json', 'selected99 program differs')
    require(sprite99['ignored_operands'] == plan['sprite99_db07_operands'], '99 bank-context exceptions differ')
    prelude = source[lorom(0x13AA46):lorom(0x13AA58)]
    require(prelude.hex() == '8ba90748abb9f3fb9d1c15b913fc9d2815ab', '99 explicit DB07 reads differ')
    foundation = (ROOT / 'local/restoration' / sprite99['base_restoration'] / 'rom.sfc').read_bytes()
    check_record(source, sprite99)
    code99, graph99 = build_code(source, foundation, sprite99)
    codea1, grapha1 = build_a1(source, parent, a1)
    expected, patches = bytearray(parent), []
    table = lorom(sprite_table(parent)[2])
    for slot, record, bank in ((0x99, sprite99['record'], 0x8B), (0xA1, a1['record'], 0x8A)):
        before = parent[table+slot*16:table+slot*16+16]
        require(before.hex() == '0000ffffffffffff218001218001ffff', 'modern omitted record differs')
        after = bytearray.fromhex(record['raw'])
        after[10] = after[13] = bank
        require(after.hex() == record['native_raw'], 'modern record changes beyond mapping')
        expected[table+slot*16:table+slot*16+16] = after
        patches.append(dict(slot=f'{slot:02X}', offset=table+slot*16, before=before.hex(), after=after.hex()))
    require(patches == plan['patches'], 'modern patch scope differs')
    old, new = old_cfg['native_sprite_gap'], cfg['native_sprite_gap']
    require(new['manifests'] == old['manifests']+[plan['sprite99_recipe']] and
            new['extra_packs'] == old['extra_packs']+[plan['a1_pack']] and
            new['extra_patches'] == old['extra_patches']+[plan['a1_patch']] and
            cfg['native_adaptations'] == old_cfg['native_adaptations'], 'unrelated cumulative content changed')
    prior, fresh = packs(plan['parent']), packs(TARGET)
    require(not any(p['address'][:2] in ('8A', '8B') for p in prior), 'modern code bank is already occupied')
    additions = {0x99: code99, 0xA1: codea1}
    for address, payload in (('8BA6FC', code99), ('8A88EB', codea1)):
        descriptor = next(p for p in fresh if p['address'] == address)
        verify(payload, descriptor, 'modern mapped pack')
    require(len(fresh) == 56 and [p for p in fresh if p['address'] not in ('8BA6FC', '8A88EB')] == prior,
            'inherited54 mappings changed')
    verify(expected, cfg['output'], 'two-record modern descendant')
    return dict(target=TARGET, rom_sha256=sha(expected), source_sha256=sha(source), patches=patches,
                sprite99_audit=graph99, spritea1_audit=grapha1, inherited_packs=prior,
                payloads={f'{slot:02X}': dict(size=len(data), sha256=sha(data)) for slot, data in additions.items()})


def main():
    result = review()
    a1, plan = load(A1), load(PLAN)
    source = (ROOT / 'local/content-versions/demo-only-1/rom.sfc').read_bytes()
    parent = (ROOT / 'local/restoration' / plan['parent'] / 'rom.sfc').read_bytes()
    data, _ = build_a1(source, parent, a1)
    directory = ROOT / plan['a1_pack']['source']
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / a1['code']['pack_file'], data)
    prepare(TARGET)
    result['files'] = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in (Path(__file__), PLAN, A1)}
    path = ROOT / 'local/restoration' / TARGET / 'modern-sprite-review.json'
    write_verified(path, (json.dumps(result, indent=2)+'\n').encode())
    print(path, sha(path.read_bytes()))


if __name__ == '__main__':
    main()

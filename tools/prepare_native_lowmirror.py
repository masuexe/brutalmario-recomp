#!/usr/bin/env python3
"""Prepare reviewed module mappings that retain source low WRAM and IO mirrors."""
import argparse
import json
from pathlib import Path

from audit_star_boss_donors import sprite_table
from native_sprite_gap import packs, prepare
from prepare_rom import verify
from qualify_world1_next_course import require
from restore_star_world_1 import lorom, sha, write_verified
import prepare_sprite_module as modules

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'config/native-content/lowmirror95-boss-r14.json'


def load(path):
    return json.loads(Path(path).read_text())


def review(plan):
    parent = (ROOT / 'local/restoration' / plan['parent'] / 'rom.sfc').read_bytes()
    verify(parent, plan['parent_output'], 'parent product')
    cfg = load(ROOT / 'config/restorations' / (plan['candidate'] + '.json'))
    require(cfg['parent_restoration'] == plan['parent'] and cfg['output'] == plan['candidate_output'],
            'candidate lineage differs')
    old_packs = {p['address']: p for p in packs(plan['parent'])}
    new_packs = {p['address']: p for p in packs(plan['candidate'])}
    require(len(plan['changes']) == len({c['slot'] for c in plan['changes']}) == 10,
            'reviewed mapping set differs')
    source = (ROOT / 'local/content-versions' / plan['official_type3_source']['version'] / 'rom.sfc').read_bytes()
    verify(source, plan['official_type3_source']['output'], 'official type3 source')
    source_table = sprite_table(source)[2]
    parent_table = sprite_table(parent)[2]
    expected = bytearray(parent)
    audit = {}
    for change in plan['changes']:
        old, new = int(change['old_address'], 16), int(change['new_address'], 16)
        require(old & 0xFFFF == new & 0xFFFF and old >> 16 & 0x7F >= 0x40 and
                new >> 16 & 0x7F < 0x40, 'mapping does not correct low-memory mirrors')
        before = bytes.fromhex(change['old_record'])
        after = bytearray(before)
        require(before[10] == before[13] == old >> 16, 'old record banks differ')
        after[10] = after[13] = new >> 16
        require(after.hex() == change['new_record'], 'record changes outside bank pointers')
        offset = lorom(parent_table) + 16 * int(change['slot'], 16)
        require(offset == change['record_offset'] and parent[offset:offset + 16] == before,
                'parent record preimage differs')
        expected[offset:offset + 16] = after
        a, b = old_packs.pop(change['old_address']), new_packs.pop(change['new_address'])
        require(a['size'] == b['size'] == change['size'] and a['executable'] and b['executable'] and
                a['pack_file'] == b['pack_file'] and a['variable'] == b['variable'] and
                a['sha256'] == change['old_pack_sha256'] and b['sha256'] == change['new_pack_sha256'],
                'pack mapping changes beyond declared code/address')
        old_code = (ROOT / 'local/restoration' / plan['parent'] / a['pack_file']).read_bytes()
        verify(old_code, a, 'parent pack')
        main = int.from_bytes(before[11:14], 'little') - old
        require(old_code[main:main + 3] == bytes.fromhex('8b4bab'), 'module lacks reviewed PHB/PHK/PLB main entry')
        if change['kind'] == 'type1':
            old_recipe, new_recipe = load(ROOT / change['parent_recipe']), load(ROOT / change['recipe'])
            donor = modules.prepare_donor(ROOT / new_recipe['donor_manifest'])
            require(old_recipe['donor_manifest'] == new_recipe['donor_manifest'] and
                    old_recipe['record']['raw'] == new_recipe['record']['raw'] and
                    old_recipe['code']['source_address'] == new_recipe['code']['source_address'] and
                    old_recipe['code']['sha256'] == new_recipe['code']['sha256'], 'official source changed')
            source_pc = int(new_recipe['code']['source_address'], 16)
            require((source_pc >> 16 & 0x7F) < 0x40, 'source bank did not have low mirrors')
            base = (ROOT / 'local/restoration' / new_recipe['base_restoration'] / 'rom.sfc').read_bytes()
            modules.check_record(donor, new_recipe)
            code, graph = modules.build_code(donor, base, new_recipe)
            # The old and new packs may differ only at declared four-byte
            # self-bank call operands. No logic, constants or timing changes.
            patched = bytearray(old_code)
            for patch in new_recipe['code_patches']:
                pos = int(patch['address'], 16) - source_pc
                target = bytes.fromhex(patch['after'])
                if patched[pos:pos + len(target)] != target:
                    require(len(target) == 4 and target[0] in (0x22, 0x5C) and
                            patched[pos:pos + 3] == target[:3] and
                            patched[pos + 3] == old >> 16 and target[3] == new >> 16,
                            'code changes beyond self-bank call operand')
                    patched[pos:pos + 4] = target
            require(bytes(patched) == code, 'unexpected adapted code difference')
            audit[change['slot']] = graph
        else:
            slot = int(change['slot'], 16)
            raw = source[lorom(source_table) + slot * 16:lorom(source_table) + slot * 16 + 16]
            require(raw.hex() == change['official_record'] and raw[0] == 3,
                    'official type3 record differs')
            start = lorom(int(change['official_block_address'], 16))
            code = source[start:start + change['size']]
            require(old_code == code and a['sha256'] == b['sha256'], 'type3 code bytes changed')
            audit[change['slot']] = dict(scope='Original protected type3 bytes retained; mapping and record banks only.')
        verify(code, b, 'reviewed native pack')
    for restoration in plan.get('additional_restorations', []):
        require(restoration['slot'] == '95', 'unreviewed additional restoration')
        recipe = load(ROOT / restoration['recipe'])
        require(recipe['record']['rooms'] == restoration['rooms'] and
                recipe['code']['native_address'] == restoration['pack_address'], 'sprite95 scope differs')
        donor = modules.prepare_donor(ROOT / recipe['donor_manifest'])
        base = (ROOT / 'local/restoration' / recipe['base_restoration'] / 'rom.sfc').read_bytes()
        modules.check_record(donor, recipe)
        code, graph = modules.build_code(donor, base, recipe)
        verify(code, dict(size=recipe['code']['size'], sha256=restoration['pack_sha256']), 'sprite95 code')
        if 'behavior_reference' in restoration:
            spec = restoration['behavior_reference']
            reference = (ROOT / 'local/content-versions' / spec['version'] / 'rom.sfc').read_bytes()
            verify(reference, spec['output'], 'official behavior reference')
            modules.check_record(reference, recipe)
            start = lorom(int(recipe['code']['source_address'], 16))
            require(reference[start:start + len(code)] == code, 'older behavior-reference code differs')
        extra = new_packs.pop(restoration['pack_address'])
        require(extra['sha256'] == restoration['pack_sha256'] and extra['executable'] and
                int(extra['address'], 16) >> 16 & 0x7F < 0x40, 'sprite95 mapping differs')
        offset = lorom(parent_table) + 0x95 * 16
        require(offset == restoration['record_offset'] and
                parent[offset:offset + 16].hex() == restoration['old_record'] ==
                '0000ffffffffffff218001218001ffff' and
                restoration['new_record'] == recipe['record']['native_raw'], 'sprite95 record differs')
        expected[offset:offset + 16] = bytes.fromhex(restoration['new_record'])
        audit['95'] = graph
    require(old_packs == new_packs, 'unrelated pack mapping changed')
    verify(expected, plan['candidate_output'], 'record-only descendant')
    return dict(rom_sha256=sha(expected), audit=audit,
                scope='Ten mappings plus explicitly declared official record recoveries; original logic and inherited resources retained. Runtime behavior remains a separate qualification.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=PLAN)
    args = parser.parse_args()
    plan = load(args.plan)
    audit = review(plan)
    prepare(plan['candidate'])
    paths = [args.plan, Path(__file__)] + [ROOT / c['recipe'] for c in plan['changes'] if 'recipe' in c]
    paths += [ROOT / c['recipe'] for c in plan.get('additional_restorations', [])]
    receipt = dict(plan=plan, review=audit,
                   files={str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths})
    path = ROOT / 'local/restoration' / plan['candidate'] / 'lowmirror-review.json'
    write_verified(path, (json.dumps(receipt, indent=2) + '\n').encode())
    print(path, sha(path.read_bytes()))


if __name__ == '__main__':
    main()

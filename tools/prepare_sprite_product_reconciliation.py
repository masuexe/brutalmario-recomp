#!/usr/bin/env python3
"""Recover three omitted official sprite modules in the cumulative native game."""
import json
from pathlib import Path

from audit_star_boss_donors import sprite_table
from native_sprite_gap import packs, prepare
from prepare_rom import verify
from prepare_sprite_module import build_code, check_record
from qualify_world1_next_course import require
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'config/native-content/sprite-product-reconciliation.json'
TARGET = 'demo11-native-sprite-product-v1'


def load(path):
    return json.loads(Path(path).read_text())


def review(plan=None):
    plan = plan if plan is not None else load(PLAN)
    require((plan['parent'], plan['candidate']) == ('demo11-native-seven-product-v1', TARGET),
            'reconciliation lineage differs')
    parent_cfg = load(ROOT / 'config/restorations' / (plan['parent']+'.json'))
    cfg = load(ROOT / 'config/restorations' / (TARGET+'.json'))
    parent = (ROOT / 'local/restoration' / plan['parent'] / 'rom.sfc').read_bytes()
    verify(parent, plan['parent_output'], 'cumulative parent')
    require(parent_cfg['output'] == plan['parent_output'] and
            cfg['parent_restoration'] == plan['parent'] and cfg['parent_output'] == plan['parent_output'] and
            cfg['output'] == plan['candidate_output'], 'candidate/parent identities differ')
    foundation = (ROOT / 'local/restoration' / cfg['base_restoration'] / 'rom.sfc').read_bytes()
    verify(foundation, cfg['base_output'], 'shared foundation')
    require(cfg['base_restoration'] == parent_cfg['base_restoration'] and
            cfg['base_output'] == parent_cfg['base_output'] and
            cfg['native_adaptations'] == parent_cfg['native_adaptations'], 'inherited adaptation changed')
    changes = plan['changes']
    require([(c['slot'], c['native_bank']) for c in changes] == [('25', '8F'), ('33', '8E'), ('94', '8D')],
            'reviewed three-slot/mapping set differs')
    old_spec, new_spec = parent_cfg['native_sprite_gap'], cfg['native_sprite_gap']
    require(new_spec['manifests'] == old_spec['manifests']+[c['recipe'] for c in changes] and
            new_spec['extra_packs'] == old_spec['extra_packs'] and
            new_spec['extra_patches'] == old_spec['extra_patches'], 'unrelated inherited content changed')
    source_versions = {}
    sources = {}
    for version in ('boss', '7hero'):
        body = (ROOT / 'local/content-versions' / version / 'rom.sfc').read_bytes()
        pin = load(ROOT / 'config' / (version+'-donor.json'))['output']
        require(pin == plan['sources'][version], 'official source pin differs')
        verify(body, pin, 'official '+version)
        source_versions[version], sources[version] = sha(body), body
    expected = bytearray(parent)
    offset = lorom(sprite_table(parent)[2])
    programs = {}
    new_addresses = set()
    old_packs, new_packs = packs(plan['parent']), packs(TARGET)
    for change in changes:
        recipe = load(ROOT / change['recipe'])
        prior = load(ROOT / change['qualified_recipe'])
        slot = int(change['slot'], 16)
        require(recipe['donor_manifest'] == 'config/boss-donor.json' and
                recipe['record']['slot'] == change['slot'] and
                recipe['record']['raw'] == prior['record']['raw'] and
                recipe['code']['source_address'] == prior['code']['source_address'] and
                recipe['code']['sha256'] == prior['code']['sha256'] and
                recipe['code']['size'] == prior['code']['size'] and
                recipe['code_patches'] == prior['code_patches'] == [], 'selected official program changed')
        for source in sources.values():
            check_record(source, recipe)
        payload, graph = build_code(sources['boss'], foundation, recipe)
        address = int(recipe['code']['native_address'], 16)
        require(address >> 16 == int(change['native_bank'], 16) and address >> 16 & 0x7F < 0x40 and
                address & 0xFFFF == int(recipe['code']['source_address'], 16) & 0xFFFF,
                'native mapping changes source low16/mirror semantics')
        source_at = lorom(int(recipe['code']['source_address'], 16))
        require(payload == sources['boss'][source_at:source_at+len(payload)] ==
                sources['7hero'][source_at:source_at+len(payload)], 'protected program differs')
        before = parent[offset+slot*16:offset+slot*16+16]
        require(before.hex() == '0000ffffffffffff218001218001ffff', 'omitted record preimage differs')
        after = bytearray.fromhex(recipe['record']['raw'])
        after[10] = after[13] = address >> 16
        require(after.hex() == recipe['record']['native_raw'] and recipe['unapplied_rom_patches'] ==
                [dict(offset=offset+slot*16, before=before.hex(), after=after.hex(),
                      role=change['patch_role'])], 'record changes beyond the selected program mapping')
        expected[offset+slot*16:offset+slot*16+16] = after
        descriptor = next(p for p in new_packs if p['address'] == recipe['code']['native_address'])
        require(not any(p['address'][:2] == change['native_bank'] for p in old_packs) and
                descriptor['executable'] and descriptor['pack_file'] == recipe['code']['pack_file'],
                'new mapping conflicts with inherited packs')
        verify(payload, descriptor, 'new native pack')
        new_addresses.add(descriptor['address'])
        programs[change['slot']] = dict(recipe=change['recipe'], graph=graph, pack=descriptor,
                                       source_sha256=sha(payload), record_offset=offset+slot*16,
                                       before=before.hex(), after=after.hex())
    require(len(new_packs) == 54 and [p for p in new_packs if p['address'] not in new_addresses] == old_packs,
            'inherited 51 pack mappings changed')
    verify(expected, cfg['output'], 'three-record descendant')
    return dict(target=TARGET, parent=plan['parent'], rom_sha256=sha(expected),
                sources=source_versions, programs=programs, inherited_packs=old_packs,
                changed_bytes=sum(x != y for x, y in zip(parent, expected)),
                scope='Only three omitted records and three byte-identical official programs; no layout, timing or engine patches.')


def main():
    result = review()
    prepare(TARGET)
    inputs = [Path(__file__), PLAN]+[ROOT / c['recipe'] for c in load(PLAN)['changes']]
    result['files'] = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in inputs}
    path = ROOT / 'local/restoration' / TARGET / 'sprite-product-review.json'
    write_verified(path, (json.dumps(result, indent=2)+'\n').encode())
    print(path, sha(path.read_bytes()))


if __name__ == '__main__':
    main()

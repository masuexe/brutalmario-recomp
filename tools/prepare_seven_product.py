#!/usr/bin/env python3
"""Reconcile the qualified Boss Seven feature with the cumulative native game."""
import json
from pathlib import Path

from native_seven_child import packs as seven_packs
from native_sprite_gap import packs, prepare
from prepare_rom import verify
from qualify_world1_next_course import require
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'config/native-content/seven-product-integration.json'
CHILD = ROOT / 'config/native-content/seven-product-child.json'


def load(path):
    return json.loads(path.read_text())


def review(plan=None, child=None):
    plan = plan if plan is not None else load(PLAN)
    child = child if child is not None else load(CHILD)
    require((plan['parent'], plan['source'], plan['foundation'], plan['candidate']) ==
            ('demo11-native-type3-c2-v2', 'demo11-native-seven-ending-1up',
             'demo11-native-sprite9e', 'demo11-native-seven-product-v1'), 'integration lineage differs')
    cfg = load(ROOT / 'config/restorations' / (plan['candidate']+'.json'))
    require(cfg['parent_restoration'] == plan['parent'] and cfg['parent_output'] == plan['parent_output'],
            'candidate parent identity differs')
    parent = (ROOT / 'local/restoration' / plan['parent'] / 'rom.sfc').read_bytes()
    source = (ROOT / 'local/restoration' / plan['source'] / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / plan['foundation'] / 'rom.sfc').read_bytes()
    verify(parent, plan['parent_output'], 'cumulative parent')
    source_cfg = load(ROOT / 'config/restorations' / (plan['source']+'.json'))
    require(source_cfg['output'] == plan['source_output'], 'qualified source pin differs')
    verify(source, plan['source_output'], 'qualified Seven image')
    verify(base, load(ROOT / 'config/restorations' / (plan['foundation']+'.json'))['output'], 'shared foundation')
    # Enumerated feature allocations, not arbitrary recipient/donor merging.
    spans = ((0x7294, 5), (0x2EA71, 2), (0xA2CA8, 36), (0xA2CFC, 3),
             (0xA4CEA, 16), (0xA5C69, 17), (0x188512, 16),
             (0x189072, 16), (0x356175, 1), (0x356178, 1))
    allowed = {i for start, size in spans for i in range(start, start+size)}
    indices = [i for i, (x, y) in enumerate(zip(base, source)) if x != y]
    require(len(indices) == 111 and set(indices) <= allowed, 'source feature delta exceeds reviewed ranges')
    runs = []
    for i in indices:
        if runs and i == runs[-1][-1]+1:
            runs[-1].append(i)
        else:
            runs.append([i])
    expected, patches = bytearray(parent), []
    for run in runs:
        start, stop = run[0], run[-1]+1
        require(all(parent[i] in (base[i], source[i]) for i in run), 'conflicting cumulative feature bytes')
        replacement = bytearray(source[start:stop])
        if start == 0x189072:
            replacement[10] = replacement[13] = 0x90
        if parent[start:stop] != replacement:
            patches.append((start, parent[start:stop].hex(), replacement.hex()))
            expected[start:stop] = replacement
    declared = [(p['offset'], p['before'], p['after']) for p in plan['patches']]
    require(declared == patches and declared == [(p['offset'], p['before'], p['after'])
                for p in child['unapplied_rom_patches']], 'integration patches exceed qualified feature delta')
    verify(expected, cfg['output'], 'integrated descendant')
    require(cfg['output'] == plan['candidate_output'], 'plan candidate identity differs')
    native_child = bytes.fromhex(child['code']['raw_payload'])
    source_packs = seven_packs(plan['source'])
    require(source_packs == plan['source_packs'], 'qualified source pack identities differ')
    for pack in source_packs:
        verify((ROOT / 'local/restoration' / plan['source'] / pack['pack_file']).read_bytes(), pack, 'qualified Seven pack')
    donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
    verify(donor, load(ROOT / 'config/boss-donor.json')['output'], 'newest official Boss source')
    require(native_child == donor[lorom(0x1EC20E):lorom(0x1EC20E)+3385] ==
            (ROOT / 'local/restoration' / plan['source'] / 'seven-child6a.bin').read_bytes(),
            'child program differs from qualified official source')
    verify(native_child, child['code'], 'byte-identical child program')
    require(child['code']['native_address'] == '90C20E' and
            expected[0x189072:0x189082].hex() == '013610003bab18401dc29065c2900000',
            'E0 low-mirror mapping differs')
    kept = load(ROOT / 'config/native-content/seven-ending-1up.json')['preserved_recipient_6a']
    verify(expected[kept['code_offset']:kept['code_offset']+kept['size']], kept, 'preserved recipient6A program')
    require(expected[kept['record_offset']:kept['record_offset']+16].hex() == kept['record'], 'recipient6A record changed')
    old_packs, new_packs = packs(plan['parent']), packs(plan['candidate'])
    require(len(new_packs) == 51, 'unexpected integration pack count')
    remaining = []
    for pack in new_packs:
        if pack['pack_file'] == 'seven-child6a.bin':
            require(pack['address'] == '90C20E' and pack['sha256'] == sha(native_child), 'child descriptor differs')
            continue
        if pack['pack_file'] in ('seven-code.bin', 'seven-graphics.bin'):
            qualified = next(p for p in source_packs if p['pack_file'] == pack['pack_file'])
            require(all(pack[k] == qualified[k] for k in ('address', 'size', 'sha256', 'executable')),
                    'master/resource differs from qualified feature')
            pack = next(p for p in old_packs if p['pack_file'] == pack['pack_file'])
        remaining.append(pack)
    require(remaining == old_packs, 'unrelated cumulative mappings changed')
    return dict(target=plan['candidate'], rom_sha256=sha(expected), patches=plan['patches'],
                source_rom_sha256=sha(source), source_packs=source_packs,
                child_source_sha256=sha(native_child),
                scope='Qualified newest Boss Seven controller/resources/ending feature carried forward; child bank90 only; unrelated content retained.')


def main():
    result = review()
    prepare(result['target'])
    paths = [Path(__file__), PLAN, CHILD]
    result['files'] = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}
    path = ROOT / 'local/restoration' / result['target'] / 'seven-product-review.json'
    write_verified(path, (json.dumps(result, indent=2)+'\n').encode())
    print(path, sha(path.read_bytes()))


if __name__ == '__main__':
    main()

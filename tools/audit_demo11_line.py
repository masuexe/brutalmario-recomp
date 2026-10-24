#!/usr/bin/env python3
"""Audit every byte that differs between the Demo 1-1 input and the line head.

Each descendant target in the chain is supposed to touch only reviewed regions:
allocations, graphics slots, room-record words, music slots and code patches. This
tool unions those regions from the recipe configs and asserts that the head differs
from the pinned input nowhere else, across the whole line at once.
"""
import json
import sys
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, pointer_offset

ROOT = Path(__file__).resolve().parents[1]
CHAIN = ['demo11-base', 'demo11-room106', 'demo11-room010-gfx',
         'demo11-room010-music', 'demo11-room138-audio', 'demo11-room0cb-gfx',
         'demo11-sprite8d', 'demo11-sprite0b', 'demo11-world1-route', 'demo11-room106-music',
         'demo11-castle-sprite06', 'demo11-yoshihouse-sprite', 'demo11-star1-gfx', 'demo11-star-gfx-batch']
HEAD = CHAIN[-1]


def allowed_regions(cfg):
    regions = set()
    allocation = cfg.get('allocation')
    if allocation:
        regions |= set(range(allocation['offset'], allocation['offset'] + allocation['size']))
    for asset in cfg.get('assets', []):
        if 'record_offset' in asset or 'record_addresses' in asset:
            regions |= set(range(pointer_offset(int(asset['target_id'], 16)),
                            pointer_offset(int(asset['target_id'], 16)) + 3))
            records = list(asset.get('record_addresses', []))
            if not records and 'record_offset' in asset and cfg.get('gfx_record'):
                records = [cfg['gfx_record']['address']]
            for address in records:
                base = lorom(int(address, 16)) + asset['record_offset']
                regions |= set(range(base, base + 2))
        elif asset.get('global_pointer'):
            regions |= set(range(pointer_offset(int(asset['target_id'], 16)),
                            pointer_offset(int(asset['target_id'], 16)) + 3))
    for patch in cfg.get('code_patches', []):
        offset = lorom(int(patch['address'], 16))
        regions |= set(range(offset, offset + len(bytes.fromhex(patch['before']))))
    music = cfg.get('music')
    if music:
        allocation = music['allocation']
        regions |= set(range(allocation['offset'], allocation['offset'] + allocation['size']))
        offset = lorom(int(music['pointer_address'], 16))
        regions |= set(range(offset, offset + 3))
    sprite = cfg.get('custom_sprite')
    if sprite:
        start = lorom(int(sprite['destination_address'], 16))
        regions |= set(range(start - 8, start + sprite['block']['size']))
        offset = lorom(int(sprite['destination_record_address'], 16))
        regions |= set(range(offset, offset + 16))
    return regions


def main():
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    input_pin = next(v['output'] for v in versions if v['id'] == 'demo-1-1')
    source = (ROOT / 'local/content-versions/demo-1-1/rom.sfc').read_bytes()
    verify(source, input_pin, 'demo 1-1 input')
    head = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    head_cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(head, head_cfg['output'], HEAD)

    regions = set()
    for target in CHAIN:
        cfg = json.loads((ROOT / 'config/restorations' / (target + '.json')).read_text())
        regions |= allowed_regions(cfg)

    changed = {i for i, (a, b) in enumerate(zip(source, head)) if a != b}
    unexpected = sorted(changed - regions)
    print(f'chain: {" -> ".join(CHAIN)}')
    print(f'head:  {head_cfg["output"]["sha256"]}')
    print(f'changed bytes: {len(changed)}')
    print(f'reviewed regions: {len(regions)} bytes')
    print(f'unexpected bytes: {len(unexpected)}')
    if unexpected:
        for start in unexpected[:10]:
            print(f'  file 0x{start:06X}  input 0x{source[start]:02X} -> head 0x{head[start]:02X}')
        return 1
    report = {
        'chain': CHAIN,
        'input_sha256': input_pin['sha256'],
        'head_sha256': head_cfg['output']['sha256'],
        'changed_bytes': len(changed),
        'reviewed_region_bytes': len(regions),
        'unexpected_bytes': 0,
        'verified': ['every byte differing from the pinned Demo 1-1 input lies in a reviewed',
                     'allocation, graphics slot, room-record word, music slot/payload,',
                     'code patch or custom sprite block declared by the chain recipes'],
    }
    output = ROOT / 'local/reports/demo11-line-audit.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'audit passed: {output.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
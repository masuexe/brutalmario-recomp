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
from restore_star_world_1 import lorom, make_candidate, pointer_offset

ROOT = Path(__file__).resolve().parents[1]
HEAD = 'demo11-star-forest'


def recipe_chain(head):
    chain = []
    while head:
        if head in chain:
            raise ValueError('cyclic recipe ancestry')
        chain.append(head)
        cfg = json.loads((ROOT / 'config/restorations' / (head + '.json')).read_text())
        head = cfg.get('base_restoration')
    return list(reversed(chain))


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
    for patch in cfg.get('code_patches', []) + cfg.get('pre_asset_patches', []):
        offset = lorom(int(patch['address'], 16))
        regions |= set(range(offset, offset + len(bytes.fromhex(patch['before']))))
    for music in ([cfg['music']] if cfg.get('music') else []) + cfg.get('music_tracks', []):
        allocation = music['allocation']
        regions |= set(range(allocation['offset'], allocation['offset'] + allocation['size']))
        offset = lorom(int(music['pointer_address'], 16))
        regions |= set(range(offset, offset + 3))
    for sprite in ([cfg['custom_sprite']] if cfg.get('custom_sprite') else []) + cfg.get('custom_sprites', []):
        start = lorom(int(sprite['destination_address'], 16))
        regions |= set(range(start, start + sprite['block']['size']))
        offset = lorom(int(sprite['destination_record_address'], 16))
        regions |= set(range(offset, offset + 16))
    for block in cfg.get('raw_blocks', []):
        start = lorom(int(block['rats_address'], 16))
        regions |= set(range(start, start + 8 + block['data']['size']))
    for item in cfg.get('level_data', []):
        offset = lorom(int(item['table'], 16)) + int(item['room'], 16) * 3
        regions |= set(range(offset, offset + 3))
    return regions


def main():
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    input_pin = next(v['output'] for v in versions if v['id'] == 'demo-1-1')
    source = (ROOT / 'local/content-versions/demo-1-1/rom.sfc').read_bytes()
    verify(source, input_pin, 'demo 1-1 input')
    head = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    head_cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(head, head_cfg['output'], HEAD)

    chain = recipe_chain(HEAD)
    regions = set()
    previous = None
    pins = {v['id']: v['output'] for v in versions}
    for target in chain:
        cfg = json.loads((ROOT / 'config/restorations' / (target + '.json')).read_text())
        recipient = (ROOT / 'local/content-versions' / cfg['recipient'] / 'rom.sfc').read_bytes()
        donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
        verify(recipient, pins[cfg['recipient']], cfg['recipient'])
        verify(donor, pins[cfg['donor']], cfg['donor'])
        if previous is not None:
            verify(previous, cfg['base_output'], 'recipe base')
            recipient = previous
        previous, _ = make_candidate(recipient, donor, cfg)
        stored = (ROOT / 'local/restoration' / target / 'rom.sfc').read_bytes()
        if previous != stored:
            raise ValueError('recipe does not reproduce prepared ROM: ' + target)
        regions |= allowed_regions(cfg)

    changed = {i for i, (a, b) in enumerate(zip(source, head)) if a != b}
    unexpected = sorted(changed - regions)
    print(f'chain: {" -> ".join(chain)}')
    print(f'head:  {head_cfg["output"]["sha256"]}')
    print(f'changed bytes: {len(changed)}')
    print(f'reviewed regions: {len(regions)} bytes')
    print(f'unexpected bytes: {len(unexpected)}')
    if unexpected:
        for start in unexpected[:10]:
            print(f'  file 0x{start:06X}  input 0x{source[start]:02X} -> head 0x{head[start]:02X}')
        return 1
    report = {
        'chain': chain,
        'input_sha256': input_pin['sha256'],
        'head_sha256': head_cfg['output']['sha256'],
        'changed_bytes': len(changed),
        'reviewed_region_bytes': len(regions),
        'unexpected_bytes': 0,
        'recipes_reproduced': len(chain),
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

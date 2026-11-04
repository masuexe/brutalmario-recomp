#!/usr/bin/env python3
"""Lay the reviewed sprite-gap records onto the accepted product line.

The product image r19 carries 14 placeholder sprite records. Seven of them
have a reviewed official program on an isolated experiment line. This tool
writes the descendant config, then builds the ROM and the module packs through
the shared sprite-gap preparation code.

The tool copies the r19 pack list, adds the reviewed recipes and pins the two
record patches whose recipes hold no unapplied patch. It does not rebuild the
music layer: the base image already holds that work.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = 'demo11-native-product-r19'
TARGET = 'demo11-native-product-r20'

# Reviewed recipes from the isolated sprite lines.
NEW_MANIFESTS = [
    'config/native-content/type3-shooters-c2-v2.json',
    'config/native-content/type3-c2-boss-lowmirror.json',
    'config/native-content/sprite25-boss-product-module.json',
    'config/native-content/sprite33-boss-product-module.json',
    'config/native-content/sprite94-boss-product-module.json',
    'config/native-content/sprite99-modern-module.json',
    'config/native-content/sprite97-modern-module.json',
]

# The A1 program is a raw protected block, not a decoded recipe.
NEW_PACK = {
    'variable': 'BM_NATIVE_SPRITE_A1_PACK',
    'pack_file': 'spritea1-modern-code.bin',
    'address': '8A88EB',
    'size': 5724,
    'sha256': 'c90d51865fde2e6bad2a17e06ed92d023d9bffdaff34cb7145981fef40c7571f',
    'executable': True,
    'source': 'local/native-modules/spritea1-modern-v1',
}

# Record patches for slots 97 and A1. Their recipes hold no unapplied patch.
NEW_PATCHES = [
    {'offset': 1608674,
     'before': '0000ffffffffffff218001218001ffff',
     'after': '013600b73503994439a58c4ba58c0000'},
    {'offset': 1608834,
     'before': '0000ffffffffffff218001218001ffff',
     'after': '013600863587b944f6888a34898a0000'},
]


def main():
    sys.path.insert(0, str(ROOT / 'tools'))
    from prepare_rom import verify
    from restore_star_world_1 import sha, write_verified
    import native_sprite_gap

    base_path = ROOT / 'config/restorations' / (BASE + '.json')
    base_cfg = json.loads(base_path.read_text())
    base_rom_path = ROOT / 'local/restoration' / BASE / 'rom.sfc'
    base_rom = base_rom_path.read_bytes()
    verify(base_rom, base_cfg['output'], 'sprite merge base ROM')

    gap = json.loads(json.dumps(base_cfg['native_sprite_gap']))
    # The base image already holds every inherited record. Mark those recipes
    # so the shared preparer mounts their packs without a second record write.
    gap['frozen_manifests'] = list(gap['manifests'])
    for path in NEW_MANIFESTS:
        if path in gap['manifests']:
            raise ValueError('sprite merge recipe already present: ' + path)
        gap['manifests'].append(path)
    if any(pack['variable'] == NEW_PACK['variable'] for pack in gap.get('extra_packs', [])):
        raise ValueError('sprite merge pack already present')
    gap.setdefault('extra_packs', []).append(dict(NEW_PACK))
    gap['extra_patches'] = [dict(patch) for patch in NEW_PATCHES]

    config = {
        'schema': 1,
        'id': TARGET,
        'target': 'Brutal Mario Demo11 Product R20',
        'recipient': base_cfg['recipient'],
        'donor': base_cfg['donor'],
        'base_restoration': BASE,
        'base_output': base_cfg['output'],
        'scope': ('Product r19 plus the seven reviewed custom sprite records: '
                  '25, 33, 94, 97, 99, A1 and C2. The music layer, packs, hooks '
                  'and room layouts stay unchanged. The other seven placeholder '
                  'slots have no official program.'),
        'native_sprite_gap': gap,
        'music_region_pack': base_cfg['music_region_pack'],
        'output': None,
    }

    out = bytearray(base_rom)
    for patch in gap['extra_patches']:
        offset = patch['offset']
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if len(before) != len(after) or out[offset:offset+len(before)] != before:
            raise ValueError('sprite merge record patch differs at %d' % offset)
        out[offset:offset+len(after)] = after
    for path in NEW_MANIFESTS:
        recipe = json.loads((ROOT / path).read_text())
        for patch in recipe.get('unapplied_rom_patches', []):
            offset = patch['offset']
            before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
            if len(before) != len(after) or out[offset:offset+len(before)] != before:
                raise ValueError('sprite merge recipe patch differs at %d' % offset)
            out[offset:offset+len(after)] = after
    config['output'] = {'size': len(out), 'sha256': sha(out)}

    config_path = ROOT / 'config/restorations' / (TARGET + '.json')
    write_verified(config_path, (json.dumps(config, indent=1) + chr(10)).encode())
    result = native_sprite_gap.prepare(TARGET)
    region = config.get('music_region_pack')
    if region:
        source = ROOT / 'local/restoration' / BASE / region['pack_file']
        data = source.read_bytes()
        verify(data, {'size': region['pack_size'], 'sha256': region['pack_sha256']},
               'sprite merge music region pack')
        target_dir = ROOT / 'local/restoration' / TARGET
        write_verified(target_dir / region['pack_file'], data)
    if sha(result) != config['output']['sha256']:
        raise ValueError('prepared sprite merge ROM differs from the plan')
    print(json.dumps({'target': TARGET, 'rom_sha256': config['output']['sha256'],
                      'manifests': len(gap['manifests']),
                      'extra_packs': len(gap['extra_packs'])}, indent=1))


if __name__ == '__main__':
    main()

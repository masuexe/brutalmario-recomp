#!/usr/bin/env python3
"""Add the external sprite graphics provider to the product line.

Product r21 descends from r20. It changes no image byte: the reviewed VRAM
pack lives outside the image and the provider writes it at room entry. The
tool writes the descendant config, then builds the packs through the shared
sprite-gap preparation code.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = 'demo11-native-product-r20'
TARGET = 'demo11-native-product-r21'
GRAPHICS = ['config/native-content/sprite-graphics-99.json']


def main():
    sys.path.insert(0, str(ROOT / 'tools'))
    from prepare_rom import verify
    from restore_star_world_1 import sha, write_verified
    import native_sprite_gap

    base_cfg = json.loads((ROOT / 'config/restorations' / (BASE + '.json')).read_text())
    base_rom = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    verify(base_rom, base_cfg['output'], 'sprite graphics base ROM')

    gap = json.loads(json.dumps(base_cfg['native_sprite_gap']))
    # The base image already holds every record and patch. Freeze the recipes
    # so the shared preparer mounts their packs without a second write.
    gap['frozen_manifests'] = list(gap['manifests'])
    gap['extra_patches'] = []

    config = {
        'schema': 1,
        'id': TARGET,
        'target': 'Brutal Mario Demo11 Product R21',
        'recipient': base_cfg['recipient'],
        'donor': base_cfg['donor'],
        'base_restoration': BASE,
        'base_output': base_cfg['output'],
        'scope': ('Product r20 plus the external sprite graphics provider. '
                  'The provider mounts one reviewed VRAM pack and writes it '
                  'when the game enters a named room. Room 175 slot 99 is the '
                  'pilot. The image bytes do not change.'),
        'native_sprite_gap': gap,
        'native_sprite_graphics': GRAPHICS,
        'music_region_pack': base_cfg['music_region_pack'],
        'output': base_cfg['output'],
    }
    write_verified(ROOT / 'config/restorations' / (TARGET + '.json'),
                   (json.dumps(config, indent=1) + chr(10)).encode())
    result = native_sprite_gap.prepare(TARGET)
    region = config['music_region_pack']
    source = ROOT / 'local/restoration' / BASE / region['pack_file']
    data = source.read_bytes()
    verify(data, {'size': region['pack_size'], 'sha256': region['pack_sha256']},
           'sprite graphics music region pack')
    write_verified(ROOT / 'local/restoration' / TARGET / region['pack_file'], data)
    if sha(result) != config['output']['sha256']:
        raise ValueError('prepared sprite graphics ROM differs from the plan')
    print(json.dumps({'target': TARGET, 'rom_sha256': config['output']['sha256'],
                      'graphics_manifests': len(GRAPHICS)}, indent=1))


if __name__ == '__main__':
    main()

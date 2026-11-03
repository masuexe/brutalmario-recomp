#!/usr/bin/env python3
"""Lay the music work onto a product ROM.

The product line and the music line both descend from demo11-native-sprite9e,
so neither one is an ancestor of the other. This tool rebuilds the music
layer against a product image:

1. Plan the music selection patches and the three ported songs on the product
   image. Every site must hold the reviewed byte before the write.
2. Build, then plan the level-block moves and build again.
3. Move unused song slots and song 4F into a region pack, so the pack supplies
   them at run time.
4. Record one recipe that descends from the product image.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import (apply_code_patches, check_allocation, lorom,
                                  raw_group_song, sha, write_verified)
import prepare_music_objects
import prepare_music_retarget as music

BASE_TARGET = 'demo11-native-product-r16'
TARGET = 'demo11-native-product-r17'
TITLE = 'Brutal Mario Demo11 Product R17'


def build_layer(base, donor, config):
    return music.build(base, donor, config)


def main():
    base_cfg = json.loads((ROOT / 'config/restorations' / (BASE_TARGET + '.json')).read_text())
    base = (ROOT / 'local/restoration' / BASE_TARGET / 'rom.sfc').read_bytes()
    verify(base, base_cfg['output'], BASE_TARGET)
    donor = (ROOT / 'local/content-versions' / music.DONOR / 'rom.sfc').read_bytes()
    verify(donor, music.DONOR_OUTPUT, music.DONOR)

    result = music.plan(base, donor)
    config = {
        'schema': 1, 'id': TARGET, 'target': TITLE, 'recipient': 'demo-1-1',
        'donor': music.DONOR,
        'base_restoration': BASE_TARGET, 'base_output': base_cfg['output'],
        'music_retarget': {'tool': 'prepare_music_retarget.py',
                           'targets': 'config/music-level-targets.json'},
        'scope': ('Product r16 plus the reviewed course music retarget, three '
                  'ported legacy songs and a region pack for the songs that do '
                  'not fit the image.'),
        'assets': [],
        'music_tracks': result['tracks'],
        'code_patches': result['patches'],
    }
    # Inherit the product packs, since they make the game boot.
    config['native_sprite_gap'] = json.loads(json.dumps(base_cfg['native_sprite_gap']))

    level_moves = prepare_music_objects.plan(bytearray(build_layer(base, donor, dict(config, level_music_objects=[]))))
    config['level_music_objects'] = level_moves
    rom = build_layer(base, donor, config)
    print(f'stage 1: {len(config["code_patches"])} patches, {len(level_moves)} level moves, sha {sha(rom)[:16]}')
    (ROOT / 'local/music-audit/product-r17-stage1.json').write_text(json.dumps(
        {'sha': sha(rom), 'patches': len(config['code_patches']),
         'moves': level_moves}, indent=1) + '\n')
    (ROOT / 'local/music-audit/product-r17-stage1.sfc').write_bytes(rom)
    (ROOT / 'local/music-audit/product-r17-recipe.json').write_text(json.dumps(config, indent=1) + '\n')


if __name__ == '__main__':
    main()

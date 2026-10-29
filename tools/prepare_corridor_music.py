#!/usr/bin/env python3
"""Set the room 151 music request to recipient slot 0xA4."""
import json
from pathlib import Path
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
R8_SHA = '4a45955c65c30495940b69fbd4675ed41574e3ae37c4471ecc80c32adf2bd55f'
MUSIC_PARAM_OFFSET = lorom(0x5BBCFF) + 0x3F4  # room 151 level data, '40 60 PP' music object


def prepare():
    cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r8.json').read_text())
    rom = bytearray((ROOT / 'local/restoration/demo11-native-product-r8/rom.sfc').read_bytes())
    assert sha(rom) == cfg['output']['sha256'] == R8_SHA
    assert rom[MUSIC_PARAM_OFFSET - 2:MUSIC_PARAM_OFFSET] == b'\x40\x60'
    assert rom[MUSIC_PARAM_OFFSET] == 0x61
    cfg['native_sprite_gap']['extra_patches'].append(dict(
        offset=MUSIC_PARAM_OFFSET, before='61', after='a5',
        role='Room 151 music: request recipient slot A4 (parameter A5)'))
    rom[MUSIC_PARAM_OFFSET] = 0xA5
    cfg['id'] = 'demo11-native-product-r9'
    cfg['output']['sha256'] = sha(rom)
    (ROOT / 'config/restorations/demo11-native-product-r9.json').write_text(
        json.dumps(cfg, separators=(', ', ': ')) + '\n')
    print(cfg['output'])


if __name__ == '__main__':
    prepare()

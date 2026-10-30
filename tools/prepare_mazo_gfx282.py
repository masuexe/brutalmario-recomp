#!/usr/bin/env python3
"""Restore mazo extended graphics 0x282 requested by the room 151 boss 9C."""
import json
from pathlib import Path
from restore_star_world_1 import graphics_pointer, lz2, pointer_offset, sha

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'demo11-native-product-r14'
TARGET = 'demo11-native-mazo-gfx282-v1'
GFX = 0x282
PACK_ADDRESS = 0xD28000
MAZO_SHA = '94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1'


def prepare():
    parent_cfg = json.loads((ROOT / 'config/restorations' / (PARENT + '.json')).read_text())
    rom = (ROOT / 'local/restoration' / PARENT / 'rom.sfc').read_bytes()
    assert sha(rom) == parent_cfg['output']['sha256']
    mazo = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
    assert sha(mazo) == MAZO_SHA
    data, stream = lz2(mazo, graphics_pointer(mazo, GFX), limit=0x10000)
    assert len(data) == 4096, len(data)
    off = pointer_offset(GFX)
    assert rom[off:off + 3] == b'\xff' * 3, rom[off:off + 3].hex()
    out = bytearray(rom)
    out[off:off + 3] = PACK_ADDRESS.to_bytes(3, 'little')
    cfg = json.loads(json.dumps(parent_cfg))
    cfg['id'] = TARGET
    cfg['output']['sha256'] = sha(out)
    cfg['native_sprite_gap']['extra_patches'].append(dict(
        offset=off, before='ffffff', after=PACK_ADDRESS.to_bytes(3, 'little').hex(),
        role=f'Extended graphics {GFX:03X} requested by the room 151 boss 9C'))
    source = 'local/native-modules/mazo-gfx282-v1'
    directory = ROOT / source
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'gfx282.bin').write_bytes(stream)
    cfg['native_sprite_gap']['extra_packs'].append(dict(
        variable='BM_MAZO_GFX282_PACK', pack_file='gfx282.bin',
        address=f'{PACK_ADDRESS:06X}', size=len(stream), sha256=sha(stream),
        executable=False, source=source))
    (ROOT / 'config/restorations' / (TARGET + '.json')).write_text(
        json.dumps(cfg, separators=(', ', ': ')) + '\n')
    print(TARGET, sha(out), len(stream))


if __name__ == '__main__':
    prepare()

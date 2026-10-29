#!/usr/bin/env python3
"""Restore mazo extended graphics 0x27D for the room 151 tidal-wave background."""
import json
from pathlib import Path
from restore_star_world_1 import graphics_pointer, lz2, pointer_offset, sha

ROOT = Path(__file__).resolve().parents[1]
R7_SHA = 'e18964c5b90e53eba2836f293dbb209ee4118af7649b1e7ecc6882a5892fe8b1'
MAZO_SHA = '94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1'
GFX = 0x27D
PACK_ADDRESS = 0xD18000

def prepare():
    cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r7.json').read_text())
    rom = bytearray((ROOT / 'local/restoration/demo11-native-product-r7/rom.sfc').read_bytes())
    assert sha(rom) == cfg['output']['sha256'] == R7_SHA
    mazo = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
    assert sha(mazo) == MAZO_SHA
    data, stream = lz2(mazo, graphics_pointer(mazo, GFX), limit=0x10000)
    assert len(data) == 4096, len(data)
    off = pointer_offset(GFX)
    assert rom[off:off+3] == b'\xff' * 3, rom[off:off+3].hex()
    ptr = PACK_ADDRESS.to_bytes(3, 'little').hex()
    cfg['native_sprite_gap']['extra_patches'].append(dict(
        offset=off, before='ffffff', after=ptr,
        role=f'Extended graphics {GFX:03X} for the room 151 tidal-wave background'))
    source = 'local/native-modules/corridor-wave-v1'
    directory = ROOT / source
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'corridor-wave.bin').write_bytes(stream)
    cfg['native_sprite_gap']['extra_packs'].append(dict(
        variable='BM_CORRIDOR_WAVE_PACK', pack_file='corridor-wave.bin',
        address=f'{PACK_ADDRESS:06X}', size=len(stream), sha256=sha(stream),
        executable=False, source=source))
    rom[off:off+3] = bytes.fromhex(ptr)
    cfg['id'] = 'demo11-native-product-r8'
    cfg['output']['sha256'] = sha(rom)
    (ROOT / 'config/restorations/demo11-native-product-r8.json').write_text(
        json.dumps(cfg, separators=(', ', ': ')) + '\n')
    print(cfg['output'], sha(stream))

if __name__ == '__main__':
    prepare()

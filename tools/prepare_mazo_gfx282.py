#!/usr/bin/env python3
"""Restore mazo extended graphics 0x282 requested by the room 151 boss 9C."""
import argparse
import json
from pathlib import Path
from native_sprite_gap import packs
from restore_star_world_1 import graphics_pointer, lz2, pointer_offset, sha

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'demo11-native-product-r14'
TARGET = 'demo11-native-mazo-gfx282-v1'
GFX = 0x282
PACK_ADDRESS = 0xD28000
MAZO_SHA = '94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1'
CUMULATIVE_PARENT = 'demo11-native-modern-sprites-v2'
CUMULATIVE_TARGET = 'demo11-native-mazo-cumulative-v1'
CUMULATIVE_SHA = 'e431d5aa168a4a07b63fca7aa4f7ca9fba08333a3b521a8c5f59553c8be2c2c4'
CUMULATIVE_CONFIG_SHA = 'a8c61098098fee3a06c504b133e91097e2a12284d373a5572f3d0e8b17b80603'


def prepare(cumulative=False):
    parent = CUMULATIVE_PARENT if cumulative else PARENT
    target = CUMULATIVE_TARGET if cumulative else TARGET
    parent_cfg = json.loads((ROOT / 'config/restorations' / (parent + '.json')).read_text())
    rom = (ROOT / 'local/restoration' / parent / 'rom.sfc').read_bytes()
    assert sha(rom) == parent_cfg['output']['sha256']
    if cumulative:
        assert sha(rom) == CUMULATIVE_SHA, 'cumulative parent changed'
        assert sha((ROOT / 'config/restorations' / (parent+'.json')).read_bytes()) == CUMULATIVE_CONFIG_SHA, 'parent config changed'
    # The loader owns complete banks, including data-only mappings.
    assert all(int(p['address'], 16) >> 16 != PACK_ADDRESS >> 16 for p in packs(parent)), 'pack bank occupied'
    mazo = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
    assert sha(mazo) == MAZO_SHA
    data, stream = lz2(mazo, graphics_pointer(mazo, GFX), limit=0x10000)
    assert len(data) == 4096, len(data)
    off = pointer_offset(GFX)
    assert rom[off:off + 3] == b'\xff' * 3, rom[off:off + 3].hex()
    out = bytearray(rom)
    out[off:off + 3] = PACK_ADDRESS.to_bytes(3, 'little')
    cfg = json.loads(json.dumps(parent_cfg))
    cfg['id'] = target
    if cumulative:
        cfg['parent_restoration'] = parent
        cfg['parent_output'] = parent_cfg['output']
        cfg['scope'] = 'Retain modern-sprites-v2 and mount official mazo GFX0282; experimental, no earned clear/save acceptance.'
    cfg['output']['sha256'] = sha(out)
    cfg['native_sprite_gap']['extra_patches'].append(dict(
        offset=off, before='ffffff', after=PACK_ADDRESS.to_bytes(3, 'little').hex(),
        role=f'Extended graphics {GFX:03X} requested by the room 151 boss 9C'))
    source = 'local/native-modules/mazo-gfx282-v1'
    directory = ROOT / source
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'gfx282.bin'
    if path.exists():
        assert path.read_bytes() == stream, 'existing source pack differs'
    else:
        path.write_bytes(stream)
    cfg['native_sprite_gap']['extra_packs'].append(dict(
        variable='BM_MAZO_GFX282_PACK', pack_file='gfx282.bin',
        address=f'{PACK_ADDRESS:06X}', size=len(stream), sha256=sha(stream),
        executable=False, source=source))
    path = ROOT / 'config/restorations' / (target + '.json')
    text = json.dumps(cfg, separators=(', ', ': ')) + '\n'
    if path.exists():
        assert path.read_text() == text, 'existing target config differs'
    else:
        path.write_text(text)
    print(target, sha(out), len(stream))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cumulative', action='store_true', help='derive an isolated modern-sprites-v2 descendant')
    prepare(parser.parse_args().cumulative)

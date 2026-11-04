#!/usr/bin/env python3
"""Add the external sprite graphics provider to a cartridge.

The provider mounts one pack per manifest and writes the reviewed VRAM ranges
when the game enters a named room. The patch is idempotent: a cartridge that
already carries the calls is left unchanged.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import sha

NL = chr(10)
DECLS = ('extern void bm_sprite_graphics_mount(void);' + NL +
         'extern void bm_sprite_graphics_tick(void);' + NL)
INCLUDE_ANCHOR = '#include "native_content.h"' + NL
MOUNT_ANCHOR = '  bm_content_load(cart->rom, cart->romSize);' + NL
MOUNT_ADDED = MOUNT_ANCHOR + '  bm_sprite_graphics_mount();' + NL
TICK_ANCHOR = '  if (bank == 0x7e || bank == 0x7f) return NULL;' + NL
TICK_ADDED = TICK_ANCHOR + '  bm_sprite_graphics_tick();' + NL


def patch(text):
    changed = False
    if 'bm_sprite_graphics_mount(void);' not in text:
        if INCLUDE_ANCHOR not in text:
            raise ValueError('cartridge does not carry the native content include')
        text = text.replace(INCLUDE_ANCHOR, INCLUDE_ANCHOR + DECLS, 1)
        changed = True
    if 'bm_sprite_graphics_mount();' not in text:
        if MOUNT_ANCHOR not in text:
            raise ValueError('cartridge does not mount the sprite packs')
        text = text.replace(MOUNT_ANCHOR, MOUNT_ADDED, 1)
        changed = True
    if 'bm_sprite_graphics_tick();' not in text:
        if TICK_ANCHOR not in text:
            raise ValueError('cartridge resolver block differs')
        text = text.replace(TICK_ANCHOR, TICK_ADDED, 1)
        changed = True
    return text, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cart', required=True)
    args = parser.parse_args()
    path = Path(args.cart)
    text = path.read_text()
    updated, changed = patch(text)
    if changed:
        path.write_text(updated)
    print(f'{"patched" if changed else "already patched"} {path} sha {sha(updated.encode())}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Add the native region pack to a cartridge that already maps sprite packs.

The sprite-gap runtime owns bm_content_resolve. This tool appends a second
resolver call, so a music region in a bank that the sprite packs do not map
still reads from its payload file.

The patch is idempotent: a cartridge that already carries the call is left
unchanged.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import sha

ANCHOR = '  uint8_t *native = bm_content_resolve(cart->rom, bank, adr);\n  if (native) return native;\n'
ADDED = (ANCHOR +
         '  uint8_t *region = bm_region_resolve(cart->rom, bank, adr);\n'
         '  if (region) return region;\n')
INCLUDE = '#include "native_content.h"\n'
INCLUDE_ANCHOR = '#include "cart.h"\n'
MOUNT = '  bm_content_load(cart->rom, cart->romSize);\n'
MOUNT_ADDED = MOUNT + '  bm_region_load(cart->rom, cart->romSize);\n'


def patch(text):
    changed = False
    if INCLUDE not in text:
        if INCLUDE_ANCHOR not in text:
            raise ValueError('cartridge include block differs')
        text = text.replace(INCLUDE_ANCHOR, INCLUDE_ANCHOR + INCLUDE, 1)
        changed = True
    if 'bm_region_resolve' not in text:
        if ANCHOR not in text:
            raise ValueError('cartridge does not carry the sprite pack resolver')
        text = text.replace(ANCHOR, ADDED, 1)
        changed = True
    if 'bm_region_load' not in text:
        if MOUNT not in text:
            raise ValueError('cartridge does not mount the sprite packs')
        text = text.replace(MOUNT, MOUNT_ADDED, 1)
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

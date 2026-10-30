#!/usr/bin/env python3
"""Report extended graphics pointers and code requests for a native target.

For each id the tool prints the 3-byte pointer, the decoded size when the
pointer is valid, and the pack files that hold an immediate request
(`LDA #$id`). A missing pointer with a request marks a gap. A missing pointer
without a request stays unexplained, not proven unused.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import graphics_pointer, lz2, pointer_offset, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default='demo11-native-product-r14')
    parser.add_argument('--first', type=lambda v: int(v, 0), default=0x27D)
    parser.add_argument('--last', type=lambda v: int(v, 0), default=0x283)
    args = parser.parse_args()
    cfg = json.loads((ROOT / 'config/restorations' / (args.target + '.json')).read_text())
    rom = (ROOT / 'local/restoration' / args.target / 'rom.sfc').read_bytes()
    if sha(rom) != cfg['output']['sha256']:
        raise ValueError('target ROM differs from its config')
    packs = sorted((ROOT / 'local/restoration' / args.target).glob('*.bin'))
    for gid in range(args.first, args.last + 1):
        pointer = rom[pointer_offset(gid):pointer_offset(gid) + 3]
        size = None
        if pointer != b'\xff' * 3:
            try:
                data, _ = lz2(rom, graphics_pointer(rom, gid), limit=0x20000)
                size = len(data)
            except Exception:
                size = 'invalid'
        pattern = bytes([0xA9, gid & 0xFF, (gid >> 8) & 0xFF])
        requested = [p.name for p in packs if pattern in p.read_bytes()]
        print(f'{gid:03X} pointer={pointer.hex()} size={size} requested={requested}')


if __name__ == '__main__':
    main()

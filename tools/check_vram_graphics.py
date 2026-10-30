#!/usr/bin/env python3
"""Find decoded donor graphics inside captured VRAM dumps.

The first 64 bytes of unrelated 4bpp sheets can be equal, so the tool compares a
distinctive slice near byte 2048. Use it to confirm that a specific extended
graphics id reached VRAM.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import graphics_pointer, lz2

SLICE = (2048, 2112)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--version', default='mazo')
    parser.add_argument('--ids', nargs='+', required=True)
    args = parser.parse_args()
    donor = (ROOT / 'local/content-versions' / args.version / 'rom.sfc').read_bytes()
    start, end = SLICE
    for text in args.ids:
        gid = int(text, 16)
        data, _ = lz2(donor, graphics_pointer(donor, gid), limit=0x10000)
        needle = data[start:end]
        hits = []
        for path in sorted(args.capture.glob('*.vram.bin')):
            offset = path.read_bytes().find(needle)
            if offset >= 0:
                hits.append((path.stem, offset))
        print(f'{gid:03X} hits={len(hits)}', [(name, hex(offset)) for name, offset in hits[:4]])


if __name__ == '__main__':
    main()

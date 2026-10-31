#!/usr/bin/env python3
"""Read the assigned translevel table from a map-mode WRAM dump.

Super Mario World writes one translevel byte for each Layer 1 overworld tile at
7ED000. The six submaps use 0x400 bytes each. This tool reports the nonzero
entries with their submap and local tile index.
"""
import argparse
from pathlib import Path

BASE = 0xD000
SUBMAP = 0x400
SIZE = 7 * SUBMAP


def entries(data, base=BASE, size=SIZE):
    result = {}
    for index in range(size):
        value = data[base + index]
        if value:
            result[index] = value
    return result


def lookup(data, x, y, submaps=7):
    index = (y << 5) | x
    return [data[BASE + sub * SUBMAP + index] for sub in range(submaps)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('tag', nargs='?', default='map1')
    parser.add_argument('--x', type=lambda value: int(value, 0))
    parser.add_argument('--y', type=lambda value: int(value, 0))
    args = parser.parse_args()
    data = (args.capture / (args.tag + '.wram.bin')).read_bytes()
    if args.x is not None and args.y is not None:
        print([hex(v) for v in lookup(data, args.x, args.y)])
        return
    for index, value in entries(data).items():
        print(hex(index), 'submap', index // SUBMAP,
              'local', hex(index % SUBMAP), 'value', hex(value))


if __name__ == '__main__':
    main()

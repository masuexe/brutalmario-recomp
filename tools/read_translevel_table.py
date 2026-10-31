#!/usr/bin/env python3
"""Read the assigned translevel table from a map-mode WRAM dump.

Super Mario World writes one translevel byte for each Layer 1 overworld tile at
7ED000. This tool reports the nonzero entries, so a map node can be matched to
its tile index.
"""
import argparse
from pathlib import Path

BASE = 0xD000
SIZE = 0x800


def entries(data, base=BASE, size=SIZE):
    result = {}
    for index in range(size):
        value = data[base + index]
        if value:
            result[index] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('tag', nargs='?', default='map1')
    args = parser.parse_args()
    data = (args.capture / (args.tag + '.wram.bin')).read_bytes()
    for index, value in entries(data).items():
        print(hex(index), hex(value))


if __name__ == '__main__':
    main()

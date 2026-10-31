#!/usr/bin/env python3
"""Report custom sprite 2A part positions in a Seven fight capture."""
import argparse
from pathlib import Path

CUSTOM = 0x1AB9E
STATUS = 0x14C8
Y_LOW = 0xD8
Y_HIGH = 0x14D4


def parts(data):
    result = []
    for slot in range(12):
        if data[STATUS + slot] == 0 and data[CUSTOM + slot] != 0x2A:
            continue
        if data[CUSTOM + slot] != 0x2A:
            continue
        y = data[Y_LOW + slot] | (data[Y_HIGH + slot] << 8)
        result.append((slot, y, data[0x1528 + slot]))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--floor', type=lambda x: int(x, 0), default=0xE0)
    args = parser.parse_args()
    for path in sorted(args.capture.glob('*.wram.bin')):
        data = path.read_bytes()
        below = [p for p in parts(data) if p[1] > args.floor]
        if below:
            print(path.stem, below)


if __name__ == '__main__':
    main()

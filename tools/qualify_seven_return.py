#!/usr/bin/env python3
"""Qualify the Seven post-room return capture.

The check requires the final map dump to show map mode, map id 0, pixel
(256,240) and tile (16,15).
"""
import argparse
from pathlib import Path

EXPECTED = (0x0E, 0x00, 256, 240, 16, 15)


def check(data):
    room = data[0x10B] | (data[0x10C] << 8)
    px = data[0x1F17] | (data[0x1F18] << 8)
    py = data[0x1F19] | (data[0x1F1A] << 8)
    tx = data[0x1F1F] | (data[0x1F20] << 8)
    ty = data[0x1F21] | (data[0x1F22] << 8)
    return (data[0x100], data[0x1F11], px, py, tx, ty, room)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--dump', default='e2')
    args = parser.parse_args()
    data = (args.capture / (args.dump + '.wram.bin')).read_bytes()
    got = check(data)
    if got[:6] != EXPECTED:
        raise SystemExit(f'FAIL: {got[:6]}')
    print('PASS:', got[:6], 'room', hex(got[6]))


if __name__ == '__main__':
    main()

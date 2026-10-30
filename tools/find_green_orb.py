#!/usr/bin/env python3
"""Find the green orb in captured frames.

The room 151 damage window needs contact with the green orb. This tool reads the
captured BMP frames and reports the bright green pixel bounds in the upper part
of the screen.
"""
import argparse
import struct
from pathlib import Path


def read_bmp(path):
    data = path.read_bytes()
    offset = struct.unpack_from('<I', data, 10)[0]
    width = struct.unpack_from('<i', data, 18)[0]
    height = struct.unpack_from('<i', data, 22)[0]
    bits = struct.unpack_from('<H', data, 28)[0]
    row = ((width * bits + 31) // 32) * 4
    rows = []
    for y in range(abs(height)):
        base = offset + (abs(height) - 1 - y if height > 0 else y) * row
        line = []
        for x in range(width):
            b, g, r = data[base + x * 3:base + x * 3 + 3]
            line.append((r, g, b))
        rows.append(line)
    return rows


def green_bounds(rows, max_y=160):
    points = []
    for y, line in enumerate(rows[:max_y]):
        for x, (r, g, b) in enumerate(line):
            if g > 150 and r < 100 and b < 130:
                points.append((x, y))
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys), len(points)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    for path in sorted(args.capture.glob('*.fb.bmp')):
        bounds = green_bounds(read_bmp(path))
        print(path.stem, bounds)


if __name__ == '__main__':
    main()

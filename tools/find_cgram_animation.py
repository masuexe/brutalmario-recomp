#!/usr/bin/env python3
"""Report animated CGRAM palette entries in a capture directory.

The room 151 green orb pulses one palette entry. This tool lists every entry
that changes between the captured CGRAM dumps, so the orb glow is separate from
a player palette flash.
"""
import argparse
from pathlib import Path


def animated_entries(base, frames):
    result = {}
    for name, data in frames:
        for index in range(min(len(base), len(data)) // 2):
            a = base[index * 2] | base[index * 2 + 1] << 8
            b = data[index * 2] | data[index * 2 + 1] << 8
            if a != b:
                result.setdefault(index, {})[name] = b
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    paths = sorted(args.capture.glob('*.cgram.bin'))
    if not paths:
        raise SystemExit('no CGRAM dumps')
    base = paths[0].read_bytes()
    frames = [(path.stem, path.read_bytes()) for path in paths[1:]]
    for index, values in sorted(animated_entries(base, frames).items()):
        print(index, values)


if __name__ == '__main__':
    main()

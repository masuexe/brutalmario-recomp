#!/usr/bin/env python3
"""Move a song upload block from the legacy ARAM base to the recipient base.

The product engine starts a song only when the upload block targets ARAM 5400.
The legacy donor family stores most group songs at 6800. The block has this
layout:

    +0  payload length, little-endian word
    +2  ARAM destination, little-endian word
    +4  payload bytes

The payload keeps one sequence header and one shared data area. Both areas
hold absolute ARAM addresses in the source range. This tool subtracts the
base difference from every word in that range and repairs the sequence
self-pointer.

Usage: adapt_song_base.py <in.bin> <out.bin> [--to 5400]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

RECIPIENT_BASE = 0x5400


def adapt(block, destination=RECIPIENT_BASE):
    """Return a block that targets the recipient base."""
    if len(block) < 12:
        raise ValueError('block is too short')
    count = block[0] | block[1] << 8
    source = block[2] | block[3] << 8
    if len(block) != count + 8:
        raise ValueError('block length does not match its header')
    if source == destination:
        return bytes(block)
    if source > destination:
        delta = source - destination
    else:
        delta = -destination + source
    song = bytearray(block[4:4 + count])
    lo, hi = source, source + count
    moved = 0
    for i in range(len(song) - 1):
        word = song[i] | song[i + 1] << 8
        if lo <= word < hi:
            new = word - delta
            if new < destination or new >= destination + count:
                raise ValueError('relocated pointer leaves the upload area')
            song[i] = new & 0xFF
            song[i + 1] = new >> 8
            moved += 1
    if song[4:6] != b'\xff\x00':
        raise ValueError('sequence marker not found')
    song[6] = (destination + 2) & 0xFF
    song[7] = (destination + 2) >> 8
    out = count.to_bytes(2, 'little') + destination.to_bytes(2, 'little') + bytes(song)
    out += block[4 + count:]
    return out, moved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--to', default='5400')
    args = parser.parse_args()
    block = Path(args.source).read_bytes()
    out, moved = adapt(block, int(args.to, 16))
    Path(args.output).write_bytes(out)
    print('%s: %d bytes, base %04X to %s, %d words relocated' % (
        args.source, len(out), block[2] | block[3] << 8, args.to, moved))


if __name__ == '__main__':
    main()

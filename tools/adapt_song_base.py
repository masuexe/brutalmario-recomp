#!/usr/bin/env python3
"""Move a song upload block from the legacy ARAM base to the recipient base.

The product engine starts a song only when the upload block targets ARAM 5400.
The legacy donor family stores most group songs at 6800. The block has this
layout:

    +0  payload length, little-endian word
    +2  ARAM destination, little-endian word
    +4  payload bytes

The payload holds a sequence header, a pattern table and channel tracks. Only
these fields hold ARAM addresses:

- the two pattern pointers in the sequence header;
- the eight channel pointers of each pattern;
- the target of command e9;
- the sequence self-pointer.

Do not relocate every word in the source range. Note parameters can hold a
value in that range. A blanket pass corrupted 115 words of the room 0F5 song.

Usage: adapt_song_base.py <in.bin> <out.bin> [--to 5400] [--report]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

RECIPIENT_BASE = 0x5400

# Parameter byte count for each command at or above da. Commands below 80 are
# a duration. Commands 80 to d9 are a note value. The walk needs every other
# command to consume the correct number of bytes.
LENGTHS = {0xda: 1, 0xdb: 1, 0xdc: 1, 0xdd: 1, 0xde: 1, 0xdf: 1, 0xe0: 1, 0xe2: 1,
           0xe7: 1, 0xe8: 2, 0xe9: 3, 0xef: 3, 0xf0: 0, 0xf1: 3, 0xf2: 3}


class SongError(ValueError):
    """The block is not a song that this tool can move."""


def _walk(song, base):
    """Return the offsets of the pointer fields and the count of track bytes."""
    count = len(song)

    def relative(value):
        return value - base

    def check(cursor):
        if cursor < 64 or cursor >= count:
            raise SongError('track cursor leaves the song: %d' % cursor)

    fields = {0, 2, 6}
    pending = []
    visited = set()
    for i in (0, 2):
        pattern = relative(song[i] | song[i + 1] << 8)
        if pattern < 0 or pattern + 16 > count:
            raise SongError('pattern table leaves the song')
        for k in range(pattern, pattern + 16, 2):
            address = song[k] | song[k + 1] << 8
            if address:
                pending.append(relative(address))
                fields.add(k)
    while pending:
        cursor = pending.pop()
        while cursor not in visited:
            check(cursor)
            visited.add(cursor)
            command = song[cursor]
            cursor += 1
            if command == 0:
                break
            if command < 0x80:
                check(cursor)
                if song[cursor] < 0x80:
                    cursor += 1
            elif command >= 0xda:
                if command not in LENGTHS:
                    raise SongError('unsupported command %02X' % command)
                size = LENGTHS[command]
                if cursor + size > count:
                    raise SongError('command parameter leaves the song')
                if command == 0xe9:
                    pending.append(relative(song[cursor] | song[cursor + 1] << 8))
                    fields.add(cursor)
                cursor += size
    return fields, len(visited)


def adapt(block, destination=RECIPIENT_BASE, report=None):
    """Return a block that targets the destination base."""
    if len(block) < 12:
        raise SongError('block is too short')
    count = block[0] | block[1] << 8
    source = block[2] | block[3] << 8
    if len(block) != count + 8:
        raise SongError('block length does not match its header')
    if source == destination:
        if report is not None:
            report.update({'moved': 0, 'fields': 0, 'track_bytes': 0, 'unchanged': True})
        return bytes(block)
    song = bytearray(block[4:4 + count])
    if song[4:6] != b'\xff\x00':
        raise SongError('sequence marker not found')
    fields, walked = _walk(song, source)
    delta = source - destination
    lo, hi = destination, destination + count
    moved = 0
    for i in sorted(fields):
        word = song[i] | song[i + 1] << 8
        if not source <= word < source + count:
            raise SongError('pointer %04X outside the source range at %d' % (word, i))
        new = word - delta
        if not lo <= new < hi:
            raise SongError('relocated pointer %04X leaves the destination' % new)
        song[i] = new & 0xFF
        song[i + 1] = new >> 8
        moved += 1
    song[6] = (destination + 2) & 0xFF
    song[7] = (destination + 2) >> 8
    if report is not None:
        report.update({'moved': moved, 'fields': len(fields), 'track_bytes': walked,
                       'unchanged': False})
    out = count.to_bytes(2, 'little') + destination.to_bytes(2, 'little') + bytes(song)
    out += block[4 + count:]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--to', default='5400')
    parser.add_argument('--report', action='store_true')
    args = parser.parse_args()
    block = Path(args.source).read_bytes()
    report = {}
    out = adapt(block, int(args.to, 16), report)
    Path(args.output).write_bytes(out)
    if args.report:
        print('%s: %d bytes, base %04X to %s, %d pointer fields moved of %d walked bytes' % (
            args.source, len(out), block[2] | block[3] << 8, args.to,
            report['moved'], report['track_bytes']))
    else:
        print('%s: base %04X to %s, %d pointers relocated' % (
            args.source, block[2] | block[3] << 8, args.to, report['moved']))


if __name__ == '__main__':
    main()

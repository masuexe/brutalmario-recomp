"""Parse a Demo 1-1 song payload into its tracks and commands.

The payload is the bytes that follow the 4-byte upload header. Its layout is:

  +0   word  first pattern table address
  +2   word  second pattern table address
  +4   word  0x00FF
  +6   word  loop entry point (base + 2)
  +8..63     zero
  +64..      track data and pattern tables

A pattern table holds up to eight track pointers. A track is a byte stream of
commands. This module reads the structure only; it does not synthesise audio.
"""
from pathlib import Path

BASE = 0x5400


def words(data, offset, count):
    return [int.from_bytes(data[offset + 2 * i:offset + 2 * i + 2], 'little')
            for i in range(count)]


def parse(payload):
    """Return the patterns of one payload as lists of track addresses."""
    first, second = words(payload, 0, 2)
    if first == 0 and second == 0:
        raise ValueError('payload has no pattern pointer')
    patterns = []
    for address in (first, second):
        if address == 0:
            continue
        offset = address - BASE
        if not 0 <= offset < len(payload) - 15:
            raise ValueError(f'pattern pointer {address:04X} leaves the payload')
        tracks = [value for value in words(payload, offset, 8) if value]
        patterns.append((address, tracks))
    return patterns


def command_length(data, index):
    """Return the byte length of the command at the given index."""
    command = data[index]
    if command < 0x80:
        length = 1
        if index + 1 < len(data) and data[index + 1] < 0x80:
            length = 2
        return length
    if command in (0xDA, 0xDB, 0xDE, 0xDF, 0xE0, 0xE2, 0xE7):
        return 2
    if command in (0xE9, 0xEF, 0xF1, 0xF2):
        return 4
    if command == 0xF0:
        return 1
    return 1


def walk(payload, address, limit=4096):
    """Return the command stream of one track as (address, bytes) pairs."""
    steps, cursor = [], address
    while len(steps) < limit:
        offset = cursor - BASE
        if not 0 <= offset < len(payload):
            raise ValueError(f'track cursor {cursor:04X} leaves the payload')
        command = payload[offset]
        length = command_length(payload, offset)
        steps.append((cursor, bytes(payload[offset:offset + length])))
        if command == 0:
            return steps
        cursor += length
    return steps


def load(path):
    return Path(path).read_bytes()


if __name__ == '__main__':
    import sys
    data = load(sys.argv[1])
    for address, tracks in parse(data):
        print(f'pattern {address:04X}: {len(tracks)} tracks')
        for track in tracks:
            steps = walk(data, track)
            print(f'  track {track:04X}: {len(steps)} commands')
            for cursor, chunk in steps[:8]:
                print(f'    {cursor:04X}: {chunk.hex(" ")}')

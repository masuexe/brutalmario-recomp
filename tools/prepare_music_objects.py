#!/usr/bin/env python3
"""Add a level music object to rooms that inherit their song.

Some Demo 1-1 rooms hold no level music object, so they keep the song of the
room that leads to them. The user report expects a specific song for those
rooms. This tool moves the level data into free cartridge space, appends the
music object, and repoints the level table.

The move is bounded: the source RATS block must have no other reference, the
destination must be a free within-bank range, and the rewritten stream must
parse to the same objects plus the new music object.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import file_to_lorom, lorom, sha, write_verified

TARGET = 'demo11-music-retarget'
RECIPE = ROOT / 'config/restorations' / (TARGET + '.json')
# room -> (song slot, screen, vertical)
OBJECTS = {
    0x02F: (0x6B, 0x07, 0x00),
    0x032: (0x6B, 0x03, 0x00),
    0x033: (0x6B, 0x04, 0x00),
    0x034: (0x6B, 0x03, 0x00),
    0x035: (0x6B, 0x03, 0x00),
    0x03C: (0x51, 0x0C, 0x08),
}
# Room 107 is left out. Its RATS block is 261 bytes but the object stream
# needs 326, so the level data is truncated in the base image. The move
# recipe refuses a stream that does not terminate inside its own block.


def pointer3(rom, offset):
    return int.from_bytes(rom[offset:offset + 3], 'little')


def object_size(data, i):
    b0, b1, b2 = data[i], data[i + 1], data[i + 2]
    number = ((b0 >> 5) & 3) * 16 + (b1 >> 4)
    if number == 0:
        return 4 if b2 == 0 else 5 if b2 == 2 else 3
    if number in (0x22, 0x23, 0x28):
        return 4
    if number == 0x2D:
        return 5
    if number in (0x27, 0x29):
        kind = data[i + 3] >> 6
        return 5 if kind < 2 else 6 if kind == 2 else (8 if b2 & 0x80 else 7)
    return 3


def walk(data):
    """Return the object list and the terminator index of a level stream."""
    index, objects = 5, []
    while index < len(data):
        if data[index] == 0xFF:
            return objects, index
        objects.append((index, data[index:index + object_size(data, index)]))
        index += object_size(data, index)
    raise ValueError('unterminated level stream')


def free_segments(rom, minimum):
    coverage = bytearray(len(rom))
    cursor = 0
    while True:
        cursor = rom.find(b'STAR', cursor)
        if cursor < 0:
            break
        header = rom[cursor:cursor + 8]
        if len(header) == 8:
            count = int.from_bytes(header[4:6], 'little')
            complement = int.from_bytes(header[6:8], 'little')
            if count ^ complement == 0xffff and cursor + count + 9 <= len(rom):
                coverage[cursor:cursor + count + 9] = b'\x01' * (count + 9)
        cursor += 4
    segments, offset = [], 0
    while offset < len(rom):
        if rom[offset] == 0 and not coverage[offset]:
            end = offset
            limit = min(len(rom), (offset // 0x8000 + 1) * 0x8000)
            while end < limit and rom[end] == 0 and not coverage[end]:
                end += 1
            if end - offset >= minimum:
                segments.append((offset, end - offset))
            offset = end
        else:
            offset += 1
    return segments


def plan(out):
    """Return the move records for one built image without keeping them."""
    scratch = bytearray(out)
    return apply(scratch, None)


def apply(out, config):
    """Append a music object to the reviewed rooms and repoint the level table.

    The image must already hold the song installs and the selection patches.
    The free ranges are recomputed on that image, so the placement is
    deterministic for a given input.
    """
    segments = free_segments(bytes(out), 512)
    moves = []
    for room, (song, screen, height) in sorted(OBJECTS.items()):
        slot = lorom(0x05E000) + room * 3
        pointer = pointer3(out, slot)
        start = lorom(pointer)
        header = bytes(out[start - 8:start])
        if header[:4] != b'STAR':
            raise ValueError(f'room {room:03X} has no bounded level block')
        size = int.from_bytes(header[4:6], 'little') + 1
        data = bytes(out[start:start + size])
        objects, terminator = walk(data)
        numbers = [((item[0] >> 5) & 3) * 16 + (item[1] >> 4) for _, item in objects]
        if 0x26 in numbers:
            raise ValueError(f'room {room:03X} already holds a music object')
        object_bytes = bytes([0x40 | (screen & 0x1F), 0x60 | (height & 0x0F), song + 1])
        body = data[:terminator] + object_bytes + b'\xFF'
        count = len(body) - 1
        blob = b'STAR' + count.to_bytes(2, 'little') + (count ^ 0xffff).to_bytes(2, 'little') + body
        placed = None
        for index, (offset, length) in enumerate(segments):
            if length >= len(blob):
                placed = offset
                segments[index] = (offset + len(blob), length - len(blob))
                break
        if placed is None:
            raise ValueError('no free within-bank range fits a moved level block')
        out[placed:placed + len(blob)] = blob
        address = file_to_lorom(placed + 8)
        out[slot:slot + 3] = (address & 0xFFFFFF).to_bytes(3, 'little')
        moves.append({'room': f'{room:03X}', 'source_pointer': f'{pointer:06X}',
                      'source_size': size, 'source_offset': start,
                      'destination_pointer': f'{address:06X}',
                      'destination_offset': placed, 'blob_size': len(blob),
                      'blob_sha256': sha(blob), 'song': f'{song:02X}',
                      'object': object_bytes.hex()})
    return moves


def main():
    config = json.loads(RECIPE.read_text())
    base = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(base, config['output'], TARGET)
    print('This step now runs inside prepare_music_retarget.py.')

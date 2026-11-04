"""Rewrite the song of a room that already holds a music object.

`prepare_music_objects` appends a music object to a room that has none, and it
rejects a room that already holds one. Some rooms hold a music object that
selects the wrong song. This tool changes the song of such a room.

The level block keeps its size, so the patch writes the block in place and the
level table keeps its pointer. No free range is needed.

Object encoding, calibrated on three rooms whose song is known:

    40 60 <song + 1>

Room 0AA holds 40 60 31 and plays 0x30. Room 018 holds 40 60 54 and plays 0x53.
Room 01B holds 40 60 40 and plays 0x3F.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_music_objects import object_size
from restore_star_world_1 import lorom

LEVEL_TABLE = 0x05E000
MUSIC_OBJECT = 0x26   # ((0x40 >> 5) & 3) * 16 + (0x60 >> 4)


def object_number(item):
    """Return the number that the level editor shows for one object."""
    return ((item[0] >> 5) & 3) * 16 + (item[1] >> 4)


def walk(data):
    """Return (offset, bytes) for each object, stopping at the terminator."""
    objects, i = [], 5
    while i + 2 < len(data):
        if data[i] == 0:
            break
        size = object_size(data, i)
        if size <= 0 or i + size > len(data):
            raise ValueError(f'object at {i} leaves the level block')
        objects.append((i, data[i:i + size]))
        i += size
    return objects


def plan(rom, room, song):
    """Return the patch for one room, or raise when the room does not fit."""
    slot = lorom(LEVEL_TABLE) + room * 3
    pointer = int.from_bytes(rom[slot:slot + 3], 'little')
    if pointer == 0:
        raise ValueError(f'room {room:03X} has no level pointer')
    start = lorom(pointer)
    header = bytes(rom[start - 8:start])
    if header[:4] != b'STAR':
        raise ValueError(f'room {room:03X} has no bounded level block')
    size = int.from_bytes(header[4:6], 'little') + 1
    data = bytes(rom[start:start + size])
    found = [(offset, item) for offset, item in walk(data)
             if object_number(item) == MUSIC_OBJECT]
    if len(found) != 1:
        raise ValueError(f'room {room:03X} holds {len(found)} music objects')
    offset, item = found[0]
    if len(item) < 3:
        raise ValueError(f'room {room:03X} music object is too short')
    before = int(item[2]) - 1
    replacement = bytes([item[0], item[1], (song + 1) & 0xFF])
    return {'room': f'{room:03X}', 'offset': start + offset,
            'before': f'{before:02X}', 'after': f'{song:02X}',
            'object_before': item.hex(), 'object_after': replacement.hex(),
            'replacement': replacement}


def apply(rom, patches):
    """Write every planned patch into the image and return the records."""
    records = []
    for patch in patches:
        rom[patch['offset']:patch['offset'] + 3] = patch['replacement']
        records.append({key: value for key, value in patch.items()
                        if key != 'replacement'})
    return records


def prepare(rom, overrides):
    """Plan and apply every override. Each entry is (room, song)."""
    patches = [plan(rom, room, song) for room, song in overrides]
    return apply(rom, patches)


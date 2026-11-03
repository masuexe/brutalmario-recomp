#!/usr/bin/env python3
"""Qualify the Demo 1-1 level music retarget checkpoint.

The checks are static and bounded.  They prove the selection bytes, the
installed song payloads and the ROM delta.  They do not prove an audible
match; that needs the user listening check.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_music_retarget import (BASE, BASE_OUTPUT, DONOR, DONOR_OUTPUT,
                                    TARGET, TARGETS, level_block, music_objects,
                                    song_pointer)
import prepare_music_objects
from prepare_rom import verify
from restore_star_world_1 import lorom, sha


def require(value, reason):
    if not value:
        raise ValueError(reason)


def main():
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    require(cfg['id'] == TARGET, 'recipe identity differs')
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    verify(base, BASE_OUTPUT, 'base restoration')
    candidate = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(candidate, cfg['output'], TARGET)
    donor = (ROOT / 'local/content-versions' / DONOR / 'rom.sfc').read_bytes()
    verify(donor, DONOR_OUTPUT, DONOR)

    expected = set()
    for patch in cfg['code_patches']:
        offset = lorom(int(patch['address'], 16))
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        require(len(before) == len(after) == 1, 'music patch width differs')
        require(before != after, 'music patch changes nothing: ' + patch['address'])
        require(base[offset:offset + 1] == before, 'music patch site differs: ' + patch['address'])
        require(candidate[offset:offset + 1] == after, 'music patch result differs: ' + patch['address'])
        # The patched byte is the parameter of a music object.
        require((base[offset - 2] & 0xE0) == 0x40 and (base[offset - 1] & 0xF0) == 0x60,
                'patch site is not a music object: ' + patch['address'])
        expected.add(offset)

    table = lorom(0x0FE000)
    present = {slot for slot in range(256)
               if int.from_bytes(candidate[table + slot * 3:table + slot * 3 + 3], 'big')}
    for track in cfg['music_tracks']:
        slot = int(track['id'], 16)
        pointer = lorom(int(track['pointer_address'], 16))
        start = track['allocation']['offset']
        size = track['allocation']['size']
        require(base[pointer:pointer + 3] == bytes(3), 'song slot was not null')
        require(candidate[pointer:pointer + 3] != bytes(3), 'song slot stays null')
        entry = candidate[pointer:pointer + 3]
        require(int.from_bytes(entry, 'big') != 0, 'song pointer is zero')
        # The cartridge reaches banks 0x7E/0x7F only through the mirror, so a
        # plain 0x7E/0x7F pointer names WRAM and the upload never completes.
        require(entry[0] not in (0x7E, 0x7F), 'song pointer names a WRAM bank')
        require(entry == song_pointer(track), 'song pointer differs from the allocation')
        require(lorom(int.from_bytes(entry, 'big')) == start + 8,
                'song pointer does not address the installed payload')
        require(size >= track['adapted']['size'] + 8, 'song allocation is too small')
        require(base[start:start + size] == bytes(size), 'song allocation was occupied')
        header = candidate[start:start + 8]
        require(header[:4] == b'STAR', 'song RATS header differs')
        count = int.from_bytes(header[4:6], 'little')
        require(count ^ int.from_bytes(header[6:8], 'little') == 0xffff, 'song RATS checksum differs')
        payload = candidate[start + 8:start + 8 + count + 1]
        require(len(payload) == track['adapted']['size'], 'song payload length differs')
        require(sha(payload) == track['adapted']['sha256'], 'song payload differs')
        require(payload[:2] == (len(payload) - 8).to_bytes(2, 'little'), 'song length word differs')
        expected.update(range(start, start + 8 + len(payload)))
        expected.update(range(pointer, pointer + 3))
    for slot in present:
        require(candidate[table + slot * 3:table + slot * 3 + 3] != bytes(3), 'null entry is present')

    # Every reviewed target slot must hold a song in the candidate.
    targets = json.loads(TARGETS.read_text())
    for entry in targets['entries']:
        if entry['target'] is None:
            continue
        slot = int(entry['target'], 16)
        if entry.get('silent'):
            # Slot 0x1E is the legacy convention for "play no music", so a null
            # slot is correct for a silent entry.
            require(slot == 0x1E, f"room {entry['room']} silent entry is not slot 1E")
            continue
        require(slot in present, f"room {entry['room']} target slot {entry['target']} is null")

    for move in cfg.get('level_music_objects', []):
        start = move['destination_offset']
        size = move['blob_size']
        require(base[start:start + size] == bytes(size),
                'level block destination was occupied: ' + move['room'])
        require(sha(candidate[start:start + size]) == move['blob_sha256'],
                'moved level block differs: ' + move['room'])
        slot = lorom(0x05E000) + int(move['room'], 16) * 3
        require(base[slot:slot + 3] == bytes.fromhex(move['source_pointer'])[:3] or
                int.from_bytes(base[slot:slot + 3], 'little') == int(move['source_pointer'], 16),
                'level pointer was not the reviewed source: ' + move['room'])
        require(int.from_bytes(candidate[slot:slot + 3], 'little') ==
                int(move['destination_pointer'], 16),
                'level pointer does not name the moved block: ' + move['room'])
        # The moved stream must parse to the original objects plus one music object.
        objects, terminator = prepare_music_objects.walk(
            candidate[start + 8:start + 8 + size - 8])
        numbers = [((item[0] >> 5) & 3) * 16 + (item[1] >> 4) for _, item in objects]
        require(numbers.count(0x26) == 1, 'moved block does not hold one music object')
        music = [item for index, item in objects
                 if ((item[0] >> 5) & 3) * 16 + (item[1] >> 4) == 0x26][0]
        require(music == bytes.fromhex(move['object']), 'music object bytes differ')
        require(terminator == len(candidate[start + 8:start + 8 + size - 8]) - 1,
                'moved block terminator differs')
        expected.update(range(start, start + size))
        expected.update(range(slot, slot + 3))

    changed = {index for index, (a, b) in enumerate(zip(base, candidate)) if a != b}
    require(changed <= expected, 'unreviewed ROM difference: '
            + str(sorted(changed - expected)[:8]))
    require(len(changed) >= len(cfg['code_patches']), 'music patches did not land')
    print(f'Music retarget checks passed: {len(cfg["code_patches"])} selection bytes, '
          f'{len(cfg["music_tracks"])} installed songs, {len(changed)} changed bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())

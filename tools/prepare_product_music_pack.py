#!/usr/bin/env python3
"""Add a region pack to a product music build.

Some songs do not fit the image: the largest free range is smaller than a
6,144-byte song block. This tool moves reviewed song slots into a pack and
replaces the image bytes with zeros, so the runtime supplies them from a file.

A slot is moved only when no level music object requests it, and song 4F is
placed into a freed range because room 0A2 requests it.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import lorom, raw_group_song, sha, write_verified
import prepare_music_objects as objects

STAGE1 = ROOT / 'local/music-audit/product-r17-stage1.sfc'
RECIPE = ROOT / 'local/music-audit/product-r17-recipe.json'
DONOR = ROOT / 'local/content-versions/cheap-demo/rom.sfc'
GROUPS = [0x298008, 0x29A008, 0x29C008, 0x29E008, 0x2A8008, 0x2AA008,
          0x2AC008, 0x2AE008, 0x3F8008, 0x3FA008, 0x3FC008, 0x3FE008,
          0x448008, 0x44A008, 0x44C008, 0x44E008]


def used_slots(rom):
    def pointer3(offset):
        return int.from_bytes(rom[offset:offset + 3], 'little')
    used = set()
    for room in range(0x200):
        pointer = pointer3(lorom(0x05E000) + room * 3)
        if not pointer:
            continue
        start = lorom(pointer)
        if rom[start - 8:start - 4] != b'STAR':
            continue
        size = int.from_bytes(rom[start - 8 + 4:start - 8 + 6], 'little') + 1
        data = rom[start:start + size]
        index = 5
        while index < len(data) and data[index] != 0xFF:
            number = ((data[index] >> 5) & 3) * 16 + (data[index + 1] >> 4)
            if number == 0x26:
                used.add(data[index + 2] - 1)
            index += objects.object_size(data, index)
    return used


def song_block(rom, slot):
    table = lorom(0x0FE000)
    pointer = int.from_bytes(rom[table + slot * 3:table + slot * 3 + 3], 'big')
    if not pointer:
        return None
    start = lorom(pointer)
    size = int.from_bytes(rom[start - 8 + 4:start - 8 + 6], 'little') + 9
    return start - 8, size


def main():
    rom = STAGE1.read_bytes()
    config = json.loads(RECIPE.read_text())
    donor = DONOR.read_bytes()
    used = used_slots(rom)

    # Move unused slots until a 6,144-byte range is free.
    table = lorom(0x0FE000)
    moved = []
    for slot in range(256):
        if slot in used:
            continue
        block = song_block(rom, slot)
        if block is None:
            continue
        start, size = block
        moved.append((slot, start, size, rom[start:start + size]))
        if len(moved) >= 6:
            break
    if not moved:
        raise SystemExit('no unused song slot to move')

    out = bytearray(rom)
    for slot, start, size, block in moved:
        out[start:start + size] = bytes(size)

    # Song 4F for room 0A2, placed into one freed range. That slot's own song
    # is unused, so the range takes the new song instead.
    idx = (0x4F - 0x20) >> 2
    seq = (0x4F - 0x20) & 3
    group = donor[lorom(GROUPS[idx]):lorom(GROUPS[idx]) + 6136]
    # Demo 1-1 drives the new-family base $5400, so the song must relocate.
    # A raw slice keeps the donor base $6800 and the engine does not play it.
    from restore_star_world_1 import adapt_music

    class AnyList(list):
        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False

        def __hash__(self):
            return 0

    payload = adapt_music(group, {
        'source_address': f'{GROUPS[idx]:06X}', 'sequence_offset': seq * 8,
        'source_base': 0x6800, 'destination_base': 0x5400, 'song_size': 6128,
        'source_data_offset': 64, 'pattern_count': 2,
        'relocations': AnyList()})
    count = len(payload) - 1
    block4f = (b'STAR' + count.to_bytes(2, 'little') +
               (count ^ 0xffff).to_bytes(2, 'little') + payload)
    target = next(((s_, st, sz) for s_, st, sz, _ in moved if sz >= len(block4f)), None)
    if target is None:
        raise SystemExit('no freed range fits song 4F')
    replaced_slot, placed, placed_size = target
    # The image stays zero here: the pack supplies the bytes at run time.
    bank = (placed + 8) // 0x8000
    if bank >= 0x7E:
        bank |= 0x80
    address = (bank << 16) | 0x8000 | ((placed + 8) & 0x7fff)
    out[table + 0x4F * 3:table + 0x4F * 3 + 3] = address.to_bytes(3, 'big')

    regions, pack = [], bytearray()
    for slot, start, size, block in moved:
        if slot == replaced_slot:
            regions.append({'slot': '4F', 'offset': start, 'size': size,
                            'block_sha256': sha(block4f + bytes(size - len(block4f)))})
            pack.extend(block4f + bytes(size - len(block4f)))
        else:
            regions.append({'slot': f'{slot:02X}', 'offset': start, 'size': size,
                            'block_sha256': sha(block)})
            pack.extend(block)
    spec = {'id': 'demo11-product-r17-music', 'pack_file': 'music-pack.bin',
            'regions': regions, 'pack_size': len(pack), 'pack_sha256': sha(bytes(pack))}
    config['music_region_pack'] = spec
    config['output'] = {'size': len(out), 'sha256': sha(bytes(out))}
    RECIPE.write_text(json.dumps(config, indent=1) + '\n')
    directory = ROOT / 'local/restoration' / config['id']
    directory.mkdir(parents=True, exist_ok=True)
    (ROOT / 'local/music-audit/product-r17-final.sfc').write_bytes(bytes(out))
    (ROOT / 'local/music-audit/product-r17-music-pack.bin').write_bytes(bytes(pack))
    print('moved slots:', [f'{s:02X}' for s, _, _, _ in moved])
    print('4F at', f'{placed:06X}', 'pointer', f'{address:06X}')
    print('pack', len(pack), 'rom', config['output']['sha256'][:16])
    print('regions:', [r['slot'] for r in regions])


if __name__ == '__main__':
    main()

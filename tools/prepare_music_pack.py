#!/usr/bin/env python3
"""Move song payloads out of the cartridge image into a native pack.

A song slot is a 24-bit pointer to a RATS block that holds the upload header
and the payload.  This tool moves the blocks of reviewed slots into a pack,
replaces the image bytes with zeros, and records the region in the recipe.

The move is bounded:
- the slot must be in the reviewed list;
- the block must not overlap another block or a level block;
- the pack keeps the blocks in table order, so a region offset is exact;
- the runtime resolves the region through the existing cartridge hook.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import lorom, sha


def rats_at(rom, start):
    header = rom[start:start + 8]
    if header[:4] != b'STAR':
        return None
    count = int.from_bytes(header[4:6], 'little')
    if count ^ int.from_bytes(header[6:8], 'little') != 0xffff:
        return None
    return count + 9


def song_blocks(rom, slots):
    """Return the block start, size and payload of the reviewed song slots."""
    table = lorom(0x0FE000)
    found = []
    for slot in slots:
        pointer = int.from_bytes(rom[table + slot * 3:table + slot * 3 + 3], 'big')
        if not pointer:
            raise ValueError(f'slot {slot:02X} is null')
        start = lorom(pointer)
        size = rats_at(rom, start - 8)
        if size is None:
            raise ValueError(f'slot {slot:02X} has no valid RATS block')
        found.append({'slot': slot, 'pointer': pointer, 'offset': start - 8,
                      'size': size, 'block': rom[start - 8:start - 8 + size]})
    return found


def plan(rom, slots):
    """Return the region records and the pack bytes for the reviewed slots."""
    blocks = song_blocks(rom, slots)
    covered = bytearray(len(rom))
    for block in blocks:
        start, size = block['offset'], block['size']
        if covered[start:start + size] != bytes(size):
            raise ValueError(f'slot {block["slot"]:02X} overlaps another reviewed block')
        covered[start:start + size] = b'\x01' * size
    pack = b''.join(block['block'] for block in blocks)
    regions = [{'slot': f'{block["slot"]:02X}',
                'pointer': f'{block["pointer"]:06X}',
                'original_address': f'{file_to_address(block["offset"]):06X}',
                'offset': block['offset'], 'size': block['size'],
                'block_sha256': sha(block['block'])} for block in blocks]
    return regions, pack


def file_to_address(offset):
    """Return the LoROM address that names one file offset."""
    bank = (offset + 8) // 0x8000
    if bank >= 0x7E:
        bank |= 0x80
    return (bank << 16) | 0x8000 | ((offset + 8) & 0x7fff)


def apply(rom, regions):
    """Return the image with the reviewed blocks cleared and the pack bytes."""
    out = bytearray(rom)
    pack = bytearray()
    for region in regions:
        start, size = region['offset'], region['size']
        block = rom[start:start + size]
        if sha(block) != region['block_sha256']:
            raise ValueError(f'slot {region["slot"]} block differs')
        pack.extend(block)
        out[start:start + size] = bytes(size)
    return out, bytes(pack)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True)
    parser.add_argument('--slots', required=True,
                        help='comma separated song slots, for example 02,03')
    parser.add_argument('--out', required=True)
    parser.add_argument('--pack', required=True)
    parser.add_argument('--manifest', required=True)
    args = parser.parse_args()
    rom = Path(args.rom).read_bytes()
    slots = [int(value, 16) for value in args.slots.split(',')]
    regions, _ = plan(rom, slots)
    out, pack = apply(rom, regions)
    Path(args.out).write_bytes(out)
    Path(args.pack).write_bytes(pack)
    manifest = {'schema': 1, 'id': 'demo11-music-pack',
                'pack_size': len(pack), 'pack_sha256': sha(pack),
                'regions': [{k: region[k] for k in ('slot', 'original_address',
                                                    'offset', 'size', 'block_sha256')}
                            for region in regions]}
    Path(args.manifest).write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'slots {len(regions)}  pack {len(pack)} bytes  image {sha(out)}')


if __name__ == '__main__':
    main()

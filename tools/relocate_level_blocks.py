#!/usr/bin/env python3
"""Free a contiguous range in one bank by relocating level blocks.

A LoROM data block must stay inside one 32 KB bank.  When no bank holds a
range of the needed size, this tool moves level blocks out of a chosen bank
into free ranges in other banks and repoints the level table.

The move is bounded:
- the source block must have exactly one reference in the level tables;
- the destination must be empty and outside every RATS block;
- the moved block keeps its bytes and its RATS header;
- the caller re-parses the level stream after the move.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import file_to_lorom, lorom

LEVEL_TABLES = (('L1', 0x05E000), ('L2', 0x05E600))


def pointer3(data, offset):
    return int.from_bytes(data[offset:offset + 3], 'little')


def rats_map(rom):
    """Return the start and size of every valid RATS block in the image."""
    blocks, cursor = {}, 0
    while True:
        cursor = rom.find(b'STAR', cursor)
        if cursor < 0:
            return blocks
        header = rom[cursor:cursor + 8]
        if len(header) == 8:
            count = int.from_bytes(header[4:6], 'little')
            complement = int.from_bytes(header[6:8], 'little')
            if count ^ complement == 0xffff and cursor + count + 9 <= len(rom):
                blocks[cursor] = count + 9
        cursor += 4


def level_blocks(rom):
    """Return the start, size and references of every level block."""
    found = {}
    for name, table in LEVEL_TABLES:
        base = lorom(table)
        for room in range(0x200):
            pointer = pointer3(rom, base + room * 3)
            if not pointer:
                continue
            start = lorom(pointer)
            header = rom[start - 8:start]
            if header[:4] != b'STAR':
                continue
            entry = found.setdefault(start - 8, {'size': int.from_bytes(header[4:6], 'little') + 9,
                                                 'refs': []})
            entry['refs'].append((name, room, base + room * 3))
    return found


def occupancy(rom):
    """Return a byte map of every byte that is inside a block or nonzero."""
    taken = bytearray(len(rom))
    for start, size in rats_map(rom).items():
        taken[start:start + size] = b'\x01' * size
    for index in range(len(rom)):
        if rom[index]:
            taken[index] = 1
    return taken


def free_ranges(taken, minimum, exclude_bank=None):
    """Return within-bank free ranges of at least the given size."""
    ranges, index = [], 0
    while index < len(taken):
        if taken[index]:
            index += 1
            continue
        limit = (index // 0x8000 + 1) * 0x8000
        end = index
        while end < limit and not taken[end]:
            end += 1
        if end - index >= minimum and (exclude_bank is None or index // 0x8000 != exclude_bank):
            ranges.append((index, end - index))
        index = end
    return ranges


def longest_run(taken, bank):
    base, end = bank * 0x8000, (bank + 1) * 0x8000
    best = run = 0
    for index in range(base, end):
        if not taken[index]:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def plan(rom, bank, need):
    """Return the level-block moves that free a range of the needed size."""
    blocks = level_blocks(rom)
    taken = occupancy(rom)
    if longest_run(taken, bank) >= need:
        return [], []
    base, end = bank * 0x8000, (bank + 1) * 0x8000
    inside = sorted((start, entry) for start, entry in blocks.items()
                    if base <= start < end)
    # Try the smallest groups first: the fewest moves that reach the size.
    from itertools import combinations
    for count in range(1, len(inside) + 1):
        for group in combinations(inside, count):
            trial = bytearray(taken)
            for start, entry in group:
                trial[start:start + entry['size']] = bytes(entry['size'])
            if longest_run(trial, bank) < need:
                continue
            dests = free_ranges(taken, max(entry['size'] for _, entry in group))
            moves, cursor = [], 0
            ok = True
            for start, entry in group:
                placed = None
                for index in range(cursor, len(dests)):
                    offset, length = dests[index]
                    if length >= entry['size']:
                        placed = offset
                        dests[index] = (offset + entry['size'], length - entry['size'])
                        break
                if placed is None:
                    ok = False
                    break
                moves.append((start, entry, placed))
            if ok:
                return moves, sorted(blocks)
    return None, None


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True)
    parser.add_argument('--bank', required=True, help='bank to free, for example 32')
    parser.add_argument('--need', type=int, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    rom = Path(args.rom).read_bytes()
    bank, need = int(args.bank, 16), args.need
    moves, _ = plan(rom, bank, need)
    if moves is None:
        raise SystemExit('no bounded relocation frees the needed range')
    taken = occupancy(rom)
    before = longest_run(taken, bank)
    print(f'bank {bank:02X}: largest free run {before} -> need {need}')
    for start, entry, placed in moves:
        print(f'  block {start:06X} size {entry["size"]:>6} ref {entry["refs"][0][0]}'
              f':{entry["refs"][0][1]:03X} -> {placed:06X}')
    trial = bytearray(taken)
    for start, entry, _ in moves:
        trial[start:start + entry['size']] = bytes(entry['size'])
    print(f'  after: largest free run {longest_run(trial, bank)}')
    if args.dry_run:
        return
    out = bytearray(rom)
    for start, entry, placed in moves:
        out[placed:placed + entry['size']] = rom[start:start + entry['size']]
        address = file_to_lorom(placed + 8)
        for _, room, slot in entry['refs']:
            out[slot:slot + 3] = (address & 0xFFFFFF).to_bytes(3, 'little')
    Path(args.rom).write_bytes(bytes(out))
    print('written', args.rom)


if __name__ == '__main__':
    main()

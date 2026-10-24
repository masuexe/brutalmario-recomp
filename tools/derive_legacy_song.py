#!/usr/bin/env python3
"""Derive one legacy donor song from its four-song upload group.

The legacy donor family stores four songs in each upload group. A group starts
with a two-byte count and a two-byte source base. Then four eight-byte sequence
headers follow at offsets 4, 12, 20 and 28. The song data area starts at
source base + 64.

This tool walks the reachable command graph with the same rules as
tools/restore_star_world_1.py adapt_music. It prints the reviewed config fields
and the adapted payload identity. It can also write the payload file.

Example:
  python3 tools/derive_legacy_song.py --version cheap-demo \
      --source-address 44A008 --slot 3
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import adapt_music, lorom

LEN = {0xDA: 1, 0xDB: 1, 0xDE: 1, 0xDF: 1, 0xE0: 1, 0xE2: 1, 0xE7: 1,
       0xE9: 3, 0xEF: 3, 0xF0: 0, 0xF1: 3, 0xF2: 3}


def walk(group, slot, source_base, data_offset=64):
    count = int.from_bytes(group[:2], 'little')
    base = int.from_bytes(group[2:4], 'little')
    if base != source_base or len(group) != count + 8:
        raise ValueError('not a legacy four-song group')
    sequence_offset = 8 * slot
    sequence_source = source_base + sequence_offset
    data_source = source_base + data_offset
    data_size = count - data_offset
    song = bytearray(group[4 + sequence_offset:12 + sequence_offset] + bytes(56) +
                     group[4 + data_offset:4 + data_offset + data_size])
    patterns = sorted({int.from_bytes(song[i:i + 2], 'little') for i in (0, 2)})
    if not 1 <= len(patterns) <= 2:
        raise ValueError('unexpected pattern count')
    if song[4:8] != b'\xff\x00' + (sequence_source + 2).to_bytes(2, 'little'):
        raise ValueError('sequence header differs')
    relocations = [0, 2, 6]

    def offset(address, size=1):
        if sequence_source <= address and address + size <= sequence_source + 8:
            return address - sequence_source
        if data_source <= address and address + size <= data_source + data_size:
            return 64 + address - data_source
        raise ValueError(f'pointer {address:04X} escapes the selected song')

    def check(cursor, size=1):
        if cursor < 64 or cursor + size > len(song):
            raise ValueError(f'cursor {cursor} escapes')

    visited = set()
    pending = []
    for address in patterns:
        pattern = offset(address, 16)
        for index in range(pattern, pattern + 16, 2):
            address = int.from_bytes(song[index:index + 2], 'little')
            if address:
                pending.append(offset(address))
                relocations.append(index)
    highest = 64
    while pending:
        cursor = pending.pop()
        while cursor not in visited:
            check(cursor)
            visited.add(cursor)
            command = song[cursor]
            cursor += 1
            if command == 0:
                highest = max(highest, cursor)
                break
            if command < 0x80:
                check(cursor)
                if song[cursor] < 0x80:
                    cursor += 1
            elif command >= 0xDA:
                if command not in LEN:
                    raise ValueError(f'unsupported command {command:02X}')
                check(cursor, LEN[command])
                if command == 0xE9:
                    pending.append(offset(int.from_bytes(song[cursor:cursor + 2], 'little')))
                    relocations.append(cursor)
                cursor += LEN[command]
            highest = max(highest, cursor)
    relocations = sorted(relocations)
    needed = max(highest, max(relocations) + 2)
    for song_size in range(needed, 4096):
        config = {'id': f'{slot:02X}', 'source_base': source_base,
                  'destination_base': 0x5400, 'sequence_offset': sequence_offset,
                  'source_data_offset': data_offset, 'song_size': song_size,
                  'pattern_count': len(patterns), 'relocations': relocations}
        try:
            payload = adapt_music(group, config)
        except ValueError:
            continue
        return config, payload
    raise ValueError('no reviewed song size fits')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', default='cheap-demo')
    parser.add_argument('--source-address', required=True,
                        help='LoROM address of the group, for example 44A008')
    parser.add_argument('--slot', type=int, required=True, choices=(0, 1, 2, 3))
    parser.add_argument('--size', type=lambda text: int(text, 0), default=6136)
    parser.add_argument('--payload-out', type=Path)
    args = parser.parse_args()
    rom = (ROOT / 'local/content-versions' / args.version / 'rom.sfc').read_bytes()
    start = lorom(int(args.source_address, 16))
    group = rom[start:start + args.size]
    config, payload = walk(group, args.slot, int.from_bytes(group[2:4], 'little'))
    result = {'version': args.version, 'source_address': args.source_address,
              'slot': args.slot, 'group_size': len(group),
              'group_sha256': hashlib.sha256(group).hexdigest(),
              'song_size': config['song_size'],
              'pattern_count': config['pattern_count'],
              'relocations': config['relocations'],
              'source_base': config['source_base'],
              'destination_base': config['destination_base'],
              'sequence_offset': config['sequence_offset'],
              'source_data_offset': config['source_data_offset'],
              'payload_size': len(payload),
              'payload_sha256': hashlib.sha256(payload).hexdigest()}
    print(json.dumps(result, indent=2))
    if args.payload_out:
        args.payload_out.write_bytes(payload)
        print(f'wrote {args.payload_out}')


if __name__ == '__main__':
    main()

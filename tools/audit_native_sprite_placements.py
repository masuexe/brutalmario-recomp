#!/usr/bin/env python3
"""Inventory native room sprite lists through verified external packs and LoROM.

This is a static slot/placement census, not room playability, source equivalence
or proof that an absent record was intended to exist.
"""
import argparse
import json
from pathlib import Path

from audit_star_boss_donors import sprite_table
from native_sprite_gap import packs
from prepare_rom import verify
from qualify_world1_next_course import require
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = '0000ffffffffffff218001218001ffff'


def decode_list(stream):
    require(bool(stream), 'empty/unmapped sprite stream')
    placed = []
    for count in range(121):
        cursor = 1+count*3
        require(cursor < len(stream), 'sprite list leaves its mapped allocation/bank')
        if stream[cursor] == 0xFF:
            return stream[:cursor+1], placed
        require(cursor+3 <= len(stream), 'incomplete sprite record')
        entry = stream[cursor:cursor+3]
        if entry[0] & 8:
            placed.append(entry[2])
    raise ValueError('sprite list lacks a bounded terminator')


def audit(target):
    directory = ROOT / 'local/restoration' / target
    cfg = json.loads((ROOT / 'config/restorations' / (target+'.json')).read_text())
    rom = (directory / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'native census ROM')
    mapped = []
    for descriptor in packs(target):
        data = (directory / descriptor['pack_file']).read_bytes()
        verify(data, descriptor, 'native census pack')
        mapped.append((int(descriptor['address'], 16), data, descriptor))
    table = lorom(sprite_table(rom)[2])
    used, rooms = {}, {}
    for room in range(512):
        at = lorom(0x05EC00)+room*2
        pointer = int.from_bytes(rom[at:at+2], 'little') | rom[lorom(0x0EF100)+room] << 16
        require(pointer & 0x8000, 'sprite list pointer is outside LoROM/native data window')
        owners = [(start, data, pin) for start, data, pin in mapped if start <= pointer < start+len(data)]
        require(len(owners) <= 1, 'overlapping native list mappings')
        if owners:
            start, data, pin = owners[0]
            stream = data[pointer-start:]
            origin = dict(kind='external-pack', pack_file=pin['pack_file'], sha256=pin['sha256'])
        else:
            offset = lorom(pointer)
            stream = rom[offset:min((offset//0x8000+1)*0x8000, len(rom))]
            origin = dict(kind='rom')
        raw, placed = decode_list(stream)
        for slot in placed:
            used.setdefault(slot, set()).add(room)
        rooms[f'{room:03X}'] = dict(address=f'{pointer:06X}', origin=origin, size=len(raw),
                                    sha256=sha(raw), custom_slots=[f'{slot:02X}' for slot in placed])
    missing = {}
    for slot, placements in sorted(used.items()):
        record = rom[table+slot*16:table+slot*16+16]
        if record.hex() == PLACEHOLDER:
            missing[f'{slot:02X}'] = [f'{room:03X}' for room in sorted(placements)]
    return dict(target=target, rom_sha256=sha(rom), packs=[p for _, _, p in mapped], rooms=rooms,
                custom_slot_count=len(used), placeholder_slots=missing,
                checker_sha256=sha(Path(__file__).read_bytes()),
                scope=__doc__.strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default='demo11-native-sprite-product-v1')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'use a fresh report path')
    result = audit(args.target)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(args.output, sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()

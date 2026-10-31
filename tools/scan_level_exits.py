#!/usr/bin/env python3
"""Scan every level exit for a target destination room.

Use this to find a neighbor entry before a fixture. The tool reads the product
level data directly and reports the source room, screen and destination.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from inspect_level_exits import exits


def filter_exits(table, dest):
    found = []
    for room, items in table.items():
        for item in items:
            if item.get('dest') == dest:
                found.append((room, item))
    return found


def scan(rom, dest):
    table = {}
    for room in range(0x200):
        try:
            table[room] = exits(rom, room).get('exits', [])
        except Exception:
            continue
    return filter_exits(table, dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'local/restoration/demo11-native-product-r14/rom.sfc')
    parser.add_argument('--dest', type=lambda x: int(x, 0), required=True)
    args = parser.parse_args()
    for room, item in scan(args.rom.read_bytes(), args.dest):
        print(hex(room), item)


if __name__ == '__main__':
    main()

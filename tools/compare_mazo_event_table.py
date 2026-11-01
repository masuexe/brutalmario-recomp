#!/usr/bin/env python3
"""Compare the Mazo event assignment table between product and donor."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import lorom

BASE = 0x05D608
INDEX = 0x30


def collisions(table, value=0x30):
    return [index for index, item in enumerate(table) if item == value]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product', type=Path, default=ROOT / 'local/restoration/demo11-native-product-r14/rom.sfc')
    parser.add_argument('--mazo', type=Path, default=ROOT / 'local/content-versions/mazo/rom.sfc')
    args = parser.parse_args()
    for name, path in (('product', args.product), ('mazo', args.mazo)):
        rom = path.read_bytes()
        table = rom[lorom(BASE):lorom(BASE) + 0x200]
        print(name, 'event30', hex(table[INDEX]), 'collisions',
              [hex(i) for i in collisions(table)])


if __name__ == '__main__':
    main()

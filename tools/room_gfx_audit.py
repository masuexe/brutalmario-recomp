#!/usr/bin/env python3
"""Find the base GFX files that a room shows and that differ from a donor.

The tool decompresses the base GFX files of the recipient and the donor. It
then searches the decoded bytes in a room VRAM dump. A file that the room loads
and that differs is a port target.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from restore_star_world_1 import graphics_pointer, lz2

ROOT = Path(__file__).resolve().parents[1]


def load_gfx(rom, gfx, limit=0x4000):
    return lz2(rom, graphics_pointer(rom, gfx), limit=limit)[0]


def audit(recipient, donor, vram, gfx_range=range(0x32), limit=0x4000):
    rows = []
    for gfx in gfx_range:
        rec = load_gfx(recipient, gfx, limit)
        don = load_gfx(donor, gfx, limit)
        differs = rec != don
        address = vram.find(rec)
        if address >= 0 and differs:
            rows.append({'gfx': gfx, 'vram': address, 'size': len(rec)})
    return rows


def main():
    args = sys.argv[1:]
    if len(args) < 3:
        raise SystemExit('usage: room_gfx_audit.py RECIPIENT_ROM DONOR_ROM VRAM.bin')
    recipient = Path(args[0]).read_bytes()
    donor = Path(args[1]).read_bytes()
    vram = Path(args[2]).read_bytes()
    rows = audit(recipient, donor, vram)
    for row in rows:
        print('gfx %02X  vram 0x%04X  size %d' % (row['gfx'], row['vram'], row['size']))
    print('targets:', ' '.join('%02X' % row['gfx'] for row in rows) or 'none')


if __name__ == '__main__':
    main()

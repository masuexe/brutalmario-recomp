#!/usr/bin/env python3
"""Build one external sprite graphics pack from a reviewed VRAM capture.

The pack holds reviewed VRAM ranges. The manifest pins the pack size, the
SHA-256, the slot and the rooms. The runtime writes the ranges when the game
enters a named room.
"""
import argparse
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def build_pack(vram, ranges):
    """Return the pack bytes for (vram word address, words) pairs."""
    out = bytearray(struct.pack('<I', len(ranges)))
    for address, words in ranges:
        if address < 0 or words <= 0 or address + words > 0x8000:
            raise ValueError('range is out of VRAM')
        if len(vram) != 0x10000:
            raise ValueError('VRAM sample size differs')
        out += struct.pack('<HH', address, words)
        out += vram[address*2:(address+words)*2]
    return bytes(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--slot', required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--donor', required=True)
    parser.add_argument('--capture', required=True)
    parser.add_argument('--frame', default='f512')
    parser.add_argument('--ranges', nargs='+', required=True,
                        help='VRAM word address and word count, for example 3000:1000')
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--rooms', nargs='+', required=True)
    parser.add_argument('--scope', required=True)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    output_directory = args.output_directory.resolve()
    if manifest_path.exists() or output_directory.exists():
        raise ValueError('refuse to replace an existing manifest or directory')
    ranges = []
    for text in args.ranges:
        address, words = text.split(':')
        ranges.append((int(address, 16), int(words, 16)))
    source = ROOT / 'local/captures' / args.capture / (args.frame + '.vram.bin')
    vram = source.read_bytes()
    pack = build_pack(vram, ranges)
    output_directory.mkdir(parents=True)
    pack_file = 'sprite' + args.slot.lower() + '-vram.bin'
    (output_directory / pack_file).write_bytes(pack)
    import hashlib
    manifest = {
        'schema': 1,
        'id': args.id,
        'slot': args.slot,
        'scope': args.scope,
        'donor': args.donor,
        'source': {'kind': 'decoded-vram', 'capture': args.capture, 'frame': args.frame},
        'rooms': [text.upper() for text in args.rooms],
        'ranges': [{'vram': '%04X' % address, 'words': words} for address, words in ranges],
        'pack_file': pack_file,
        'size': len(pack),
        'sha256': hashlib.sha256(pack).hexdigest(),
        'source_directory': str(output_directory.relative_to(ROOT)),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=1) + chr(10))
    print(json.dumps({'manifest': str(manifest_path), 'pack': str(output_directory / pack_file),
                      'size': len(pack), 'sha256': manifest['sha256']}, indent=1))


if __name__ == '__main__':
    main()

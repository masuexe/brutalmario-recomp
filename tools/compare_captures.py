#!/usr/bin/env python3
"""Compare matched scene dumps, without claiming full emulator equivalence."""
import argparse
import json
from pathlib import Path


def scene(directory, tag):
    wram = (directory / (tag + '.wram.bin')).read_bytes()
    info = json.loads((directory / (tag + '.info.json')).read_text())
    if len(wram) != 0x20000:
        raise ValueError('expected 128 KiB WRAM')
    return {'frame': info['frame'], 'width': info['fb_width'], 'height': info['fb_height'],
            'game_mode': wram[0x100], 'level': int.from_bytes(wram[0x10b:0x10d], 'little'),
            'player_x': int.from_bytes(wram[0x94:0x96], 'little'),
            'player_y': int.from_bytes(wram[0x96:0x98], 'little'),
            'lives_minus_one': wram[0xdbe]}, wram, (directory / (tag + '.fb.bgrx')).read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('native', type=Path)
    args = parser.parse_args()
    tags_a = {p.name.removesuffix('.info.json') for p in args.reference.glob('*.info.json')}
    tags_b = {p.name.removesuffix('.info.json') for p in args.native.glob('*.info.json')}
    if not tags_a or tags_a != tags_b:
        parser.error('capture scene sets are empty or differ')
    results = []
    for tag in tags_a:
        ref, rw, rf = scene(args.reference, tag)
        native, nw, nf = scene(args.native, tag)
        if (ref['frame'], ref['width'], ref['height']) != (native['frame'], native['width'], native['height']):
            parser.error(f'{tag}: frame numbers or dimensions differ')
        expected = ref['width'] * ref['height'] * 4
        if len(rf) != expected or len(nf) != expected:
            parser.error(f'{tag}: framebuffer size mismatch')
        results.append({'tag': tag, 'reference': ref, 'native': native,
                        'wram_different_bytes': sum(a != b for a, b in zip(rw, nw)),
                        'rgb_different_pixels': sum(rf[i:i+3] != nf[i:i+3] for i in range(0, expected, 4)),
                        # Compare on a common 5-bit grid to account for RGB565
                        # expansion differences. This does not hide geometry shifts.
                        'rgb5_different_pixels': sum(any(rf[i+k] >> 3 != nf[i+k] >> 3 for k in range(3))
                                                     for i in range(0, expected, 4))})
    print(json.dumps({'reference_path': str(args.reference), 'native_path': str(args.native),
                      'scope': 'Matched scene samples; not full frame-by-frame or audio qualification',
                      'scenes': sorted(results, key=lambda r: r['reference']['frame'])}, indent=2))


if __name__ == '__main__':
    main()

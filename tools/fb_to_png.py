#!/usr/bin/env python3
"""Convert a host framebuffer BMP dump to a PNG image."""
import struct
import sys
import zlib
from pathlib import Path


def read_bmp(path):
    data = Path(path).read_bytes()
    if data[:2] != b'BM':
        raise ValueError('not a BMP file')
    offset = int.from_bytes(data[10:14], 'little')
    width = int.from_bytes(data[18:22], 'little', signed=True)
    height = int.from_bytes(data[22:26], 'little', signed=True)
    bpp = int.from_bytes(data[28:30], 'little')
    if bpp != 24:
        raise ValueError('only 24-bit BMP is supported')
    stride = (width * 3 + 3) & ~3
    pixels = []
    for row in range(abs(height)):
        start = offset + row * stride
        line = data[start:start + width * 3]
        rgb = bytearray()
        for x in range(width):
            b, g, r = line[x * 3:x * 3 + 3]
            rgb += bytes((r, g, b))
        pixels.append(bytes(rgb))
    if height > 0:
        pixels.reverse()
    return width, abs(height), pixels


def write_png(path, width, height, rows, scale=1):
    def chunk(tag, payload):
        return (struct.pack('>I', len(payload)) + tag + payload +
                struct.pack('>I', zlib.crc32(tag + payload) & 0xFFFFFFFF))
    raw = bytearray()
    for row in rows:
        if scale == 1:
            raw += b'\x00' + row
        else:
            wide = b''.join(row[i:i + 3] * scale for i in range(0, len(row), 3))
            for _ in range(scale):
                raw += b'\x00' + wide
    png = (b'\x89PNG\r\n\x1a\n' +
           chunk(b'IHDR', struct.pack('>IIBBBBB', width * scale,
                                      height * scale, 8, 2, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))
    Path(path).write_bytes(png)


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit('usage: fb_to_png.py IN.bmp [OUT.png] [scale]')
    source = Path(args[0])
    target = Path(args[1]) if len(args) > 1 else source.with_suffix('.png')
    scale = int(args[2]) if len(args) > 2 else 1
    width, height, rows = read_bmp(source)
    write_png(target, width, height, rows, scale)
    print(target)


if __name__ == '__main__':
    main()

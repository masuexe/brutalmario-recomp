#!/usr/bin/env python3
"""Extract the donor Japanese GFX2A font and build a room-scoped VRAM run pack.

The Seven fight adapter uploads this font to VRAM 9000. The corridor message
rooms 191 and 192 need the same glyphs because the Demo 1-1 recipient replaces
them with the English font. The VRAM pack follows the diagnostic run format:
u32 run count, then u16 start word, u16 length, u16 value per run.
"""
import hashlib
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPHICS = ROOT / 'local/native-modules/demo11-native-seven-font-entry-final/seven-graphics.bin'
FONT_OFFSET = 0x5A7D
FONT_SIZE = 2048
FONT_SHA = '2f0619a305c515d72c4707dd7f18a792dcc376d3a5ac65adab35e68e75e15e1f'
OUT = ROOT / 'local/native-modules/corridor-font-v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    data = GRAPHICS.read_bytes()
    font = data[FONT_OFFSET:FONT_OFFSET + FONT_SIZE]
    assert len(font) == FONT_SIZE and sha(font) == FONT_SHA, sha(font)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'gfx2a.bin').write_bytes(font)
    runs = bytearray(struct.pack('<I', FONT_SIZE // 2))
    for index in range(FONT_SIZE // 2):
        word = int.from_bytes(font[index * 2:index * 2 + 2], 'little')
        runs += struct.pack('<HHH', 0x4800 + index, 1, word)
    pack = OUT / 'vram-font-191.bin'
    pack.write_bytes(runs)
    print('gfx2a', len(font), sha(font))
    print('vram pack', len(runs), sha(runs))


if __name__ == '__main__':
    main()

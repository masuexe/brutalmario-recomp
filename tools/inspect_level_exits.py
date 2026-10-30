#!/usr/bin/env python3
"""List bounded level screen exits for a native product ROM.

The parser uses the RATS header bounds and the object sizes from the level
format. It reports screen exits, five-byte exits and screen jumps. A screen
exit destination uses the low byte and the high bit at flag bit 0. A later
review can compare the list with live probes.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import lorom, sha


def require(value, reason):
    if not value:
        raise ValueError(reason)


def obj27_size(b2, b3):
    hi = b3 >> 6
    if hi in (0, 1):
        return 5
    if hi == 2:
        return 6
    return 8 if b2 & 0x80 else 7


def stream(rom, room):
    slot = lorom(0x05E000) + room * 3
    pointer = int.from_bytes(rom[slot:slot + 3], 'little')
    offset = lorom(pointer)
    header = rom[offset - 8:offset]
    require(header[:4] == b'STAR' and
            int.from_bytes(header[4:6], 'little') ^ int.from_bytes(header[6:8], 'little') == 0xFFFF,
            f'room {room:03X} has no bounded RATS header')
    size = int.from_bytes(header[4:6], 'little') + 1
    require(0 < size <= 0x8000 and offset + size <= len(rom), 'room stream bounds invalid')
    return rom[offset:offset + size], pointer, size


def exits(rom, room):
    data, pointer, size = stream(rom, room)
    i = 5
    found = []
    while i < len(data):
        b0 = data[i]
        if b0 == 0xFF:
            break
        require(i + 1 < len(data), 'truncated object header')
        objnum = ((b0 >> 5) & 0x03) * 16 + ((data[i + 1] >> 4) & 0x0f)
        if objnum == 0:
            require(i + 2 < len(data), 'truncated extended object')
            ext = data[i + 2]
            if ext == 0x00:
                require(i + 3 < len(data), 'truncated screen exit')
                flag = data[i + 1]
                dest = data[i + 3] | ((flag & 1) << 8)
                found.append(dict(kind='screen_exit', screen=b0 & 0x1F, dest=dest,
                                  secondary=(flag >> 1) & 1))
                i += 4
                continue
            if ext == 0x01:
                require(i + 2 < len(data), 'truncated screen jump')
                found.append(dict(kind='screen_jump', screen=b0 & 0x1F, dest=None,
                                  secondary=None))
                i += 3
                continue
            if ext == 0x02:
                require(i + 4 < len(data), 'truncated five-byte exit')
                flag = data[i + 1]
                dest = data[i + 3] | ((flag & 1) << 8)
                found.append(dict(kind='screen_exit15', screen=b0 & 0x1F, dest=dest,
                                  secondary=(flag >> 1) & 1))
                i += 5
                continue
            i += 3
            continue
        require(i + 2 < len(data), 'truncated standard object')
        if objnum in (0x22, 0x23):
            i += 4
        elif objnum in (0x27, 0x29):
            require(i + 3 < len(data), 'truncated object 27/29')
            i += obj27_size(data[i + 2], data[i + 3])
        elif objnum == 0x28:
            i += 4
        elif objnum == 0x2D:
            i += 5
        else:
            i += 3
    return dict(pointer=f'{pointer:06X}', size=size, exits=found)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default='demo11-native-product-r14')
    parser.add_argument('--rooms', nargs='+', required=True)
    args = parser.parse_args()
    cfg = json.loads((ROOT / 'config/restorations' / (args.target + '.json')).read_text())
    rom = (ROOT / 'local/restoration' / args.target / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'target ROM differs')
    for name in args.rooms:
        info = exits(rom, int(name, 16))
        print(name.upper(), info['pointer'], info['size'],
              [(e['kind'], e['screen'], e['dest'] if e['dest'] is None else f"{e['dest']:03X}",
                e['secondary']) for e in info['exits']])


if __name__ == '__main__':
    main()

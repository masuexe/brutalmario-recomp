#!/usr/bin/env python3
"""Qualify the boss HP row for rooms 08A, 08B and 091 in product r26."""
import json
from pathlib import Path

from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'local/restoration/demo11-native-product-r25'
CANDIDATE = ROOT / 'local/restoration/demo11-native-product-r26'
CAPTURES = ROOT / 'local/captures'
REPORT = ROOT / 'local/reports/product-r26-boss-hp-row.json'

HUD_HOOK = 0x008DE1
SHIM = 0x40A570
OLD_HOOK = bytes([0x22, 0x08, 0xA5, 0x40])
NEW_HOOK = bytes([0x22, 0x70, 0xA5, 0x40])
SHIM_BYTES = bytes([
    0x22, 0x08, 0xA0, 0x3E, 0x08, 0xC2, 0x20, 0x48, 0xAD, 0x0B, 0x01,
    0xC9, 0x8A, 0x00, 0xF0, 0x0E, 0xC9, 0x8B, 0x00, 0xF0, 0x09,
    0xC9, 0x91, 0x00, 0xF0, 0x04, 0x5C, 0x10, 0xA5, 0x40,
    0x5C, 0x2C, 0xA5, 0x40])
LABEL = [0x0B, 0x18, 0x1C, 0x1C]
BAR = [0x44, 0x44, 0x44, 0x44]


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def wram(capture, tag):
    return (CAPTURES / capture / (tag + '.wram.bin')).read_bytes()


def vram(capture, tag):
    return (CAPTURES / capture / (tag + '.vram.bin')).read_bytes()


def row1(data):
    base = 0xA000
    return [int.from_bytes(data[base + i * 2:base + i * 2 + 2], 'little') & 0x3FF
            for i in range(32, 64)]


def check_image():
    parent = (PARENT / 'rom.sfc').read_bytes()
    candidate = (CANDIDATE / 'rom.sfc').read_bytes()
    require(len(parent) == len(candidate), 'image size changed')
    offset = lorom(HUD_HOOK)
    require(parent[offset:offset + 4] == OLD_HOOK, 'parent hook differs')
    require(candidate[offset:offset + 4] == NEW_HOOK, 'candidate hook differs')
    shim_offset = lorom(SHIM)
    require(parent[shim_offset:shim_offset + len(SHIM_BYTES)] == bytes(len(SHIM_BYTES)),
            'shim area was not free in the parent')
    require(candidate[shim_offset:shim_offset + len(SHIM_BYTES)] == SHIM_BYTES,
            'candidate shim differs')
    changed = [i for i in range(len(parent)) if parent[i] != candidate[i]]
    allowed = set([offset + 1])
    allowed.update(range(shim_offset, shim_offset + len(SHIM_BYTES)))
    require(set(changed) <= allowed, 'candidate changed other bytes')
    require(offset + 1 in changed, 'candidate hook byte did not change')
    return changed


def check_room(capture, room, tag, label_tiles):
    data = vram(capture, tag)
    first = row1(data)
    require(first[8:8 + len(label_tiles)] == label_tiles,
            f'{capture}: label tiles differ')
    state = wram(capture, tag)
    require(state[0x10B] | state[0x10C] << 8 == room, f'{capture}: room differs')
    return first


def main():
    changed = check_image()
    rooms = {}
    for capture, room, tag, label in (
            ('r26-room08a-v1', 0x008A, 'f1020', [0x1E, 0x15, 0x1D, 0x12, 0x16, 0x0A]),
            ('r26-room08b-v1', 0x008B, 'f060', LABEL),
            ('r26-room0091-v1', 0x0091, 'f060', [0x21, 0x0A, 0x17])):
        rooms['%03X' % room] = check_room(capture, room, tag, label)
    reference = vram('low-bank-cheap-08b-v1', 'motion')
    expected = row1(reference)[8:18]
    require(rooms['08B'][8:18] == expected, 'room 08B row differs from the reference')
    report = {
        'candidate': 'demo11-native-product-r26',
        'candidate_output': sha((CANDIDATE / 'rom.sfc').read_bytes()),
        'changed_bytes': len(changed),
        'shim_address': '%06X' % SHIM,
        'hook_address': '%06X' % HUD_HOOK,
        'rooms': {key: value[8:18] for key, value in rooms.items()},
        'reference_row': expected,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print('passed: %d changed bytes, rooms %s' % (len(changed), sorted(rooms)))
    print('report:', REPORT)


if __name__ == '__main__':
    main()

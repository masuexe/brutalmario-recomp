#!/usr/bin/env python3
"""Compare the modern sprite source entries with the native pilot samples.

Each sample pairs the native actors with the nearest source actors of the same
slot, status and velocity signs. The report separates an exact field match, a
near position match and a real difference. The tool reads retained captures
only. It runs no emulator and writes no file.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from qualify_seven_child import FIELDS

CAPTURES = ROOT / 'local/captures'
TAGS = ('entered', 'f001', 'f016', 'f032', 'f064', 'f128', 'f256', 'f512')
CASES = (
    ('174/99', 'modern-pilot-174-native-v1', 'modern-source-174-v1', 0x99),
    ('175/99', 'modern-pilot-175-native-v1', 'modern-source-175-v1', 0x99),
    ('175/A1', 'modern-pilot-175-native-v1', 'modern-source-175-v1', 0xA1),
    ('176/A1', 'modern-pilot-176-native-v1', 'modern-source-176-v1', 0xA1),
    ('178/A1', 'modern-pilot-178-native-v1', 'modern-source-178-v1', 0xA1),
)
TOLERANCE = 16


def rows(directory, slot):
    out = {}
    for tag in TAGS:
        path = directory / (tag + '.wram.bin')
        if not path.is_file():
            out[tag] = None
            continue
        data = path.read_bytes()
        found = []
        for i in range(12):
            if data[0x14C8 + i] and data[0x1AB10 + i] & 8 and data[0x1AB9E + i] == slot:
                found.append(dict(
                    status=data[0x14C8 + i],
                    x=data[0xE4 + i] | data[0x14E0 + i] << 8,
                    y=data[0xD8 + i] | data[0x14D4 + i] << 8,
                    vx=data[0xB6 + i], vy=data[0xAA + i],
                    fields=tuple(data[field + i] for field in FIELDS)))
        out[tag] = found
    return out


def pair(native, source):
    pairs, left = [], list(source)
    for row in native:
        if not left:
            return None
        best = min(left, key=lambda other: abs(other['x'] - row['x']) + abs(other['y'] - row['y']))
        left.remove(best)
        pairs.append((row, best))
    return pairs if not left else None


def classify(pairs):
    exact = all(a['fields'] == b['fields'] and a['status'] == b['status'] and
                a['x'] == b['x'] and a['y'] == b['y'] for a, b in pairs)
    if exact:
        return 'exact', 0, 0
    near = all(a['status'] == b['status'] and a['vx'] == b['vx'] and a['vy'] == b['vy'] and
               abs(a['x'] - b['x']) <= TOLERANCE and abs(a['y'] - b['y']) <= TOLERANCE
               for a, b in pairs)
    dx = max(abs(a['x'] - b['x']) for a, b in pairs)
    dy = max(abs(a['y'] - b['y']) for a, b in pairs)
    return ('near' if near else 'diff'), dx, dy


def trajectory(rows_by_tag, tag):
    row = rows_by_tag.get(tag)
    if not row:
        return None
    return [(r['x'], r['y']) for r in sorted(row, key=lambda r: (r['x'], r['y']))]


def main():
    summary = {}
    for name, native_name, source_name, slot in CASES:
        native = rows(CAPTURES / native_name, slot)
        source = rows(CAPTURES / source_name, slot)
        print('==', name)
        counts = {'exact': 0, 'near': 0, 'diff': 0, 'missing': 0}
        for tag in TAGS:
            a, b = native[tag], source[tag]
            if a is None or b is None:
                counts['missing'] += 1
                print(f'  {tag:8s} missing')
                continue
            if not a and not b:
                print(f'  {tag:8s} both empty')
                continue
            pairs = pair(a, b)
            if pairs is None:
                counts['missing'] += 1
                print(f'  {tag:8s} count native={len(a)} source={len(b)}')
                continue
            kind, dx, dy = classify(pairs)
            counts[kind] += 1
            print(f'  {tag:8s} {kind:5s} rows={len(pairs)} max offset=({dx},{dy}) '
                  f'native={[(hex(r["status"]), r["x"], r["y"]) for r in a]} '
                  f'source={[(hex(r["status"]), r["x"], r["y"]) for r in b]}')
        moving = (trajectory(native, 'entered') != trajectory(native, 'f128'))
        print('  summary', counts, 'native moves', moving)
        summary[name] = dict(counts=counts, native_moves=moving)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()

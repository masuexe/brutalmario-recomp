#!/usr/bin/env python3
"""Check that the cartridge still has the reviewed free space budget.

The thresholds are lower bounds. Update them only with a reviewed decision,
because later boss content needs the space. The floor was reviewed on
2026-10-26 after the boss room graphics chain, which installed 143 graphics
assets of the remaining subrooms.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ['demo11-gfx-boss76']
THRESHOLDS = {
    'total_free': 300000,
    'aligned_free': 80000,
    'largest_run': 16384,
}


def load(path):
    return json.loads(Path(path).read_text())


def zero_runs(data, minimum=256):
    runs = []
    cursor = 0
    while cursor < len(data):
        if data[cursor] != 0:
            cursor += 1
            continue
        start = cursor
        while cursor < len(data) and data[cursor] == 0:
            cursor += 1
        if cursor - start >= minimum:
            runs.append((start, cursor - start))
    return runs


def report(rom):
    runs = zero_runs(rom)
    total = sum(size for _, size in runs)
    aligned = 0
    for start, size in runs:
        if start // 0x8000 >= 0x40:
            continue
        bank_end = ((start // 0x8000) + 1) * 0x8000
        aligned += min(start + size, bank_end) - start
    largest = max(size for _, size in runs)
    return {'total_free': total, 'aligned_free': aligned, 'largest_run': largest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default=TARGETS[-1])
    args = parser.parse_args()
    cfg = load(ROOT / 'config/restorations' / (args.target + '.json'))
    rom = (ROOT / 'local/restoration' / args.target / 'rom.sfc').read_bytes()
    if len(rom) != cfg['output']['size']:
        raise SystemExit('ROM size differs from the recipe')
    values = report(rom)
    print(args.target, values)
    for key, minimum in THRESHOLDS.items():
        if values[key] < minimum:
            raise SystemExit('space budget too low: %s %d < %d' % (key, values[key], minimum))
    print('Space budget passed')


if __name__ == '__main__':
    main()

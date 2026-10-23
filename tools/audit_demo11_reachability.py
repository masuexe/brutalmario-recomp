#!/usr/bin/env python3
"""Audit which differing rooms the Demo 1-1 line has actually exercised.

The two builds differ in 22 level streams. The rebase is only safe for World 1 if the
rooms a route reaches are either identical or intentionally newer. This tool collects
the rooms every capture taken on the head ROM actually entered, then intersects them
with the differing-room list to separate exercised differences from unvisited ones.
"""
import json
import sys
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from restore_star_world_1 import lz2, lorom

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-room0cb-gfx'


def main():
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    head_sha = cfg['output']['sha256']
    verify((ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes(), cfg['output'], HEAD)
    inventory = json.loads((ROOT / 'local/reports/demo11-additions-inventory.json').read_text())
    differing = {int(room, 16) for room in inventory['levels_with_differing_content']}

    rooms_seen, captures = {}, []
    for directory in sorted((ROOT / 'local/captures').iterdir()):
        if not directory.is_dir():
            continue
        receipt_path = directory / 'receipt.json'
        if not receipt_path.is_file():
            continue
        try:
            receipt = json.loads(receipt_path.read_text())
        except (OSError, ValueError):
            continue
        if receipt.get('rom_sha256') != head_sha:
            continue
        seen = set()
        for sample_path in directory.glob('*.wram.bin'):
            body = sample_path.read_bytes()
            if len(body) < 0x20000:
                continue
            room = body[0x10b] | (body[0x10c] << 8)
            if room < 0x200:
                seen.add(room)
        if not seen:
            continue
        captures.append(directory.name)
        for room in seen:
            rooms_seen.setdefault(room, set()).add(directory.name)

    exercised_differences = sorted(room for room in rooms_seen if room in differing)
    unvisited_differences = sorted(room for room in differing if room not in rooms_seen)
    intended = {0x0C5, 0x0C7, 0x105, 0x10E}
    unexpected = [room for room in exercised_differences if room not in intended]
    report = {
        'scope': __doc__.strip(),
        'head_sha256': head_sha,
        'captures_considered': len(captures),
        'rooms_exercised': len(rooms_seen),
        'differing_rooms_total': len(differing),
        'differing_rooms_exercised': [f'{room:03X}' for room in exercised_differences],
        'differing_rooms_unvisited': [f'{room:03X}' for room in unvisited_differences],
        'unvisited_detail': {f'{room:03X}': [] for room in unvisited_differences},
        'evidence': {f'{room:03X}': sorted(captures_list)[:4] for room, captures_list in sorted(rooms_seen.items())
                     if room in differing},
    }
    output = ROOT / 'local/reports/demo11-reachability.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'captures pinned to the head: {len(captures)}')
    print(f'rooms exercised: {len(rooms_seen)}')
    print('differing rooms exercised:', ' '.join(report['differing_rooms_exercised']))
    print('differing rooms never visited:', ' '.join(report['differing_rooms_unvisited']))
    print(f'report: {output.relative_to(ROOT)}')
    if unexpected:
        print('UNEXPECTED differing rooms exercised:', ' '.join(f'{room:03X}' for room in unexpected))
        return 1
    print('all exercised differing rooms are the intended ones (intro, map, 1-1, castle)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
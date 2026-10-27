#!/usr/bin/env python3
"""Measure the load-phase offset between the donor and a native target.

A room can reach the same state at a different frame on each host. This tool
finds the frame offset that makes the two row series agree best, and reports
the residual difference at that offset. It does not claim movement or a course
pass.
"""
import argparse
import json
from pathlib import Path

from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOMS = ('156', '157', '159', '15B')
MAX_OFFSET = 120
STEP = 10
FIRST_FRAME = 140
COUNT = 24


def readers(room, host):
    directory = ROOT/'local/captures'/f'spritefine-{room}-{host}-v1'
    series = {}
    for index in range(COUNT):
        frame = FIRST_FRAME+index*STEP
        path = directory/f'f{frame}.wram.bin'
        if not path.is_file():
            continue
        wram = path.read_bytes()
        rows = tuple((slot, wram[0x9E+slot], wram[0x1AB9E+slot],
                      wram[0xE4+slot] | (wram[0x14E0+slot] << 8),
                      wram[0xD8+slot] | (wram[0x14D4+slot] << 8))
                     for slot in range(12) if wram[0x14C8+slot])
        series[frame] = (wram[0x100], rows)
    return series


def measure(room):
    donor = readers(room, 'donor')
    native = readers(room, 'native')
    if not donor or not native:
        raise ValueError('missing a fine capture for room '+room)
    best = None
    for offset in range(-MAX_OFFSET, MAX_OFFSET+1, STEP):
        equal = 0
        checked = 0
        for frame, value in donor.items():
            other = native.get(frame+offset)
            if other is None:
                continue
            checked += 1
            equal += value == other
        if not checked:
            continue
        key = (equal, -abs(offset))
        if best is None or key > best[0]:
            best = (key, offset, equal, checked)
    (_, offset, equal, checked) = best
    aligned = 0
    for frame, value in donor.items():
        other = native.get(frame+offset)
        if other is not None and value == other:
            aligned += 1
    onset = {}
    for host, series in (('donor', donor), ('native', native)):
        first = None
        for frame in sorted(series):
            mode, rows = series[frame]
            if any(row[2] == 0x10 or row[2] == 0x11 for row in rows):
                first = frame
                break
        onset[host] = first
    return {'room': room, 'frames_checked': checked, 'equal_at_offset': equal,
            'offset': offset, 'best_equal': aligned,
            'donor_frames': len(donor), 'native_frames': len(native),
            'first_slot_onset': onset,
            'exact_without_offset': sum(1 for frame, value in donor.items()
                                        if native.get(frame) == value)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rooms', nargs='+', default=list(DEFAULT_ROOMS))
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-phase.json')
    args = parser.parse_args()
    report = {'scope': __doc__.strip(),
              'max_offset': MAX_OFFSET, 'step': STEP,
              'rooms': {room: measure(room) for room in args.rooms}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
    for room, entry in report['rooms'].items():
        print(room, 'offset', entry['offset'], 'aligned', entry['best_equal'],
              'of', entry['frames_checked'], 'exact', entry['exact_without_offset'])

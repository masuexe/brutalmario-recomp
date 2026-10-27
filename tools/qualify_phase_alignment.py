#!/usr/bin/env python3
"""Measure the load-phase offset between the donor and a native target.

A room can reach the same state at a different frame on each host. This tool
reads a two-frame capture series from both hosts, finds the frame offset that
makes the row series agree best, and reports the residual difference in the
steady state. It does not claim movement or a course pass.
"""
import argparse
import json
from pathlib import Path

from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = {
    '156': ('sprite156-two-donor-v1', 'sprite156-two-native-v1'),
    '157': ('sprite-two-157-donor-v1', 'sprite-two-157-native-v1'),
    '159': ('sprite-two-159-donor-v1', 'sprite-two-159-native-v1'),
    '15B': ('sprite-two-15B-donor-v1', 'sprite-two-15B-native-v1'),
}
FIRST = 200
STEP = 2
COUNT = 60
MAX_OFFSET = 60
STEADY_FIRST = 280


def series(directory):
    """Return the mode and actor rows for each captured frame."""
    result = {}
    for index in range(COUNT):
        frame = FIRST+index*STEP
        path = ROOT/'local/captures'/directory/f'g{frame}.wram.bin'
        if not path.is_file():
            continue
        wram = path.read_bytes()
        rows = tuple((slot, wram[0x9E+slot], wram[0x1AB9E+slot],
                      wram[0xE4+slot] | (wram[0x14E0+slot] << 8),
                      wram[0xD8+slot] | (wram[0x14D4+slot] << 8))
                     for slot in range(12) if wram[0x14C8+slot])
        result[frame] = (wram[0x100], rows)
    return result


def measure(room):
    donor_dir, native_dir = CAPTURES[room]
    donor = series(donor_dir)
    native = series(native_dir)
    if not donor or not native:
        return {'note': 'fine capture absent'}
    best = None
    for offset in range(-MAX_OFFSET, MAX_OFFSET+1):
        equal = checked = 0
        for frame, value in donor.items():
            other = native.get(frame+offset)
            if other is None:
                continue
            checked += 1
            equal += value == other
        if not checked:
            continue
        if best is None or (equal, -abs(offset)) > (best[1], -abs(best[0])):
            best = (offset, equal, checked)
    offset = best[0]
    steady = [frame for frame in sorted(donor)
              if frame >= STEADY_FIRST and (frame+offset) in native]
    mismatched = {frame: {'donor': donor[frame], 'native': native[frame+offset]}
                  for frame in steady if donor[frame] != native[frame+offset]}
    return {'offset': offset, 'equal': best[1], 'checked': best[2],
            'steady_frames': len(steady),
            'steady_mismatches': len(mismatched),
            'phase_exact': not mismatched,
            'mismatch_frames': sorted(mismatched)}


def measure_all():
    """Return the phase result for every room that has a two-frame capture."""
    return {room: measure(room) for room in sorted(CAPTURES)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rooms', nargs='+', default=sorted(CAPTURES))
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-phase.json')
    args = parser.parse_args()
    report = {'scope': __doc__.strip(), 'first_frame': FIRST, 'step': STEP,
              'count': COUNT, 'steady_first': STEADY_FIRST,
              'rooms': {room: measure(room) for room in args.rooms}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
    for room, entry in report['rooms'].items():
        print(room, 'offset', entry.get('offset'), 'steady',
              entry.get('steady_frames'), 'mismatch',
              entry.get('steady_mismatches'))
#!/usr/bin/env python3
"""Compare host/beam clocks and selected per-frame WRAM values.

Reference WRAM deltas are reconstructed, including frames with no writes.
This does not establish instruction, video, audio or full-state equivalence.
"""
import argparse
import csv
import json
from pathlib import Path

FIELD = 262 * 1364
FIRST_EDGE = 225 * 1364
FIELDS = {'counter13': 0x13, 'counter14': 0x14, 'mode': 0x100}


def reference_states(path, count):
    state = bytearray(8192)
    frame = 1
    result = {}
    with path.open() as source:
        for line in source:
            event = json.loads(line)
            next_frame = event['f']
            if next_frame < frame:
                raise ValueError('reference frame numbers decrease')
            while frame < next_frame and frame <= count:
                result[frame] = {name: state[addr] for name, addr in FIELDS.items()}
                frame += 1
            if frame > count:
                break
            address = int(event['adr'], 16)
            if address < len(state):
                state[address] = int(event['val'], 16)
    while frame <= count:
        result[frame] = {name: state[addr] for name, addr in FIELDS.items()}
        frame += 1
    return result


def analyze(directory, reference):
    with (directory / 'timing.csv').open() as source:
        rows = [r for r in csv.DictReader(source) if r['phase'] == 'run']
    if not rows:
        raise ValueError(f'{directory}: no completed frame observations')
    count = len(rows)
    ref = reference_states(reference / 'wram.jsonl', count)
    first = {}
    skipped = []
    previous_clock = 0
    inconsistent_positions = []
    max_boundary_overshoot = 0
    exact_selected_state_frames = 0
    for frame, row in enumerate(rows, 1):
        if int(row['frame']) != frame:
            raise ValueError('requires one uninterrupted session starting at frame 1')
        beam = int(row['beam_clock'])
        if (beam // 1364 % 262, beam % 1364) != (int(row['vpos']), int(row['hpos'])):
            inconsistent_positions.append(frame)
        field = (beam - FIRST_EDGE) // FIELD + 1
        # Small instruction/DMA overshoots can move time between adjacent
        # calls. Only report calls consuming at least two complete periods.
        if beam - previous_clock >= 2 * FIELD:
            skipped.append({'host_frame': frame, 'master_clocks': beam - previous_clock,
                            'field_periods': (beam - previous_clock) / FIELD})
        previous_clock = beam
        max_boundary_overshoot = max(max_boundary_overshoot,
                                    beam - (FIRST_EDGE + (frame - 1) * FIELD))
        values = {name: int(row[name]) for name in FIELDS}
        exact_selected_state_frames += values == ref[frame]
        for name in FIELDS:
            if name not in first and values[name] != ref[frame][name]:
                first[name] = {'host_frame': frame, 'reference': ref[frame][name],
                               'native': values[name]}
    samples = []
    for frame in [224, 225, 226, 227, 248, 249, 308, 600, 783, 1686, 2108, 2319, 2380, 2504, 6104]:
        if frame <= count:
            samples.append({'host_frame': frame, 'reference': ref[frame],
                            'native': {name: int(rows[frame - 1][name]) for name in FIELDS}})
    return {'capture': str(directory), 'host_frames': count,
            'clock_derived_fields_reached': field,
            'multi_field_calls': skipped,
            'beam_origin_mismatch_frames': len(inconsistent_positions),
            'first_beam_origin_mismatch_frame': next(iter(inconsistent_positions), None),
            'max_beam_overshoot_from_host_frame_grid': max_boundary_overshoot,
            'first_selected_value_mismatches': first,
            'frames_matching_all_three_selected_values': exact_selected_state_frames,
            'samples': samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('native', type=Path, nargs='+')
    args = parser.parse_args()
    print(json.dumps({'scope': __doc__.strip(), 'reference': str(args.reference),
                      'runs': [analyze(p, args.reference) for p in args.native]}, indent=2))


if __name__ == '__main__':
    main()

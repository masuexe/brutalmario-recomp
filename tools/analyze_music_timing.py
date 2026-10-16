#!/usr/bin/env python3
"""Track local energy-envelope lag inside a selected musical passage.

This measures drift in generated PCM, not BPM, pitch, note identity or device
playback speed. Constant lag is not evidence of a tempo change.
"""
import argparse
import json
from pathlib import Path
from compare_audio import load, align


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('native', type=Path)
    parser.add_argument('--start', type=float, required=True)
    parser.add_argument('--end', type=float, required=True)
    parser.add_argument('--window', type=float, default=2)
    parser.add_argument('--radius', type=float, default=.5)
    args = parser.parse_args()
    reference, a = load(args.reference)
    native, b = load(args.native)
    if reference['sample_rate'] != native['sample_rate']:
        parser.error('sample rates differ; explicitly resample copies first')
    if (args.start < 0 or args.end <= args.start or args.window <= 0 or args.radius < 0 or
            args.end > min(reference['seconds'], native['seconds'])):
        parser.error('invalid interval, window or search radius')
    period = reference['envelope_block_frames'] / reference['sample_rate']
    windows = []
    start = args.start
    while start + args.window <= args.end + 1e-9:
        match = align(a, b, round(start / period), round((start + args.window) / period),
                      round(args.radius / period))
        if match is not None:
            match['native_lag_seconds'] = match['lag_blocks'] * period
        windows.append({'start_seconds': start, 'end_seconds': start + args.window,
                        'alignment': match})
        start += args.window
    if not windows:
        parser.error('interval is shorter than one window')
    print(json.dumps({'scope': __doc__.strip(), 'reference': reference, 'native': native,
                      'envelope_resolution_seconds': period, 'windows': windows}, indent=2))


if __name__ == '__main__':
    main()

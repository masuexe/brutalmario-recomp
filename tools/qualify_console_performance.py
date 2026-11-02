#!/usr/bin/env python3
"""Compare fresh before/after host profiles and complete frame dumps.

This qualifies the captured frames only. Turbo/headless guest-stage timings
are throughput measurements, not a displayed FPS or whole-game guarantee.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

SUFFIXES = ('info.json', 'regs.json', 'wram.bin', 'sram.bin', 'vram.bin',
            'cgram.bin', 'oam.bin', 'fb.bgrx', 'fb.bmp', 'apu.tsv',
            'dma.tsv', 'ppuw.tsv')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(directory):
    log = (directory / 'run.log').read_text()
    end = re.search(r'exit: script quit after (\d+) frames', log)
    profile = re.search(r'stage=guest count=(\d+).*?mean_ms=([\d.]+)', log)
    if not end or not profile or end[1] != profile[1]:
        raise ValueError(f'{directory}: missing successful script completion/profile')
    if 'until timed out' in log or '[native-seven] rejected:' in log:
        raise ValueError(f'{directory}: capture failed')
    identity_path = next((directory / name for name in ('receipt.json', 'identity.json')
                          if (directory / name).is_file()), None)
    if identity_path is None:
        raise ValueError(f'{directory}: missing input identity')
    identity = json.loads(identity_path.read_text())
    return dict(directory=str(directory), log_sha256=digest(directory / 'run.log'),
                frames=int(end[1]), guest_mean_ms=float(profile[2]), identity=identity)


def qualify(before, after, normalize_text_newlines=False):
    left, right = capture(before), capture(after)
    for key in ('rom_sha256', 'script_sha256'):
        if left['identity'][key] != right['identity'][key]:
            raise ValueError(f'{key} differs')
    if left['frames'] != right['frames']:
        raise ValueError('completed frame counts differ')
    names = {p.name[:-len('.info.json')] for p in before.glob('*.info.json')}
    if not names or names != {p.name[:-len('.info.json')] for p in after.glob('*.info.json')}:
        raise ValueError('dump sets are empty or differ')
    hashes = {}
    for name in sorted(names):
        for suffix in SUFFIXES:
            filename = name + '.' + suffix
            a, b = before / filename, after / filename
            if not a.is_file() or not b.is_file():
                raise ValueError(f'dump missing: {filename}')
            normalize = normalize_text_newlines and suffix.endswith(('.json', '.tsv'))
            equal = a.read_text() == b.read_text() if normalize else a.read_bytes() == b.read_bytes()
            if not equal:
                raise ValueError(f'dump missing or differs: {filename}')
            if not a.stat().st_size and suffix.endswith('.bin'):
                raise ValueError(f'empty state dump: {filename}')
            hashes[filename] = dict(before_sha256=digest(a), after_sha256=digest(b),
                                    text_newlines_normalized=normalize)
        if f'dump {name} ok' not in (after / 'run.log').read_text():
            raise ValueError(f'dump completion missing: {name}')
    return dict(before=left, after=right, matching_files=hashes,
                guest_speedup=left['guest_mean_ms'] / right['guest_mean_ms'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--normalize-text-newlines', action='store_true',
                        help='Allow CRLF/LF differences in JSON/TSV for cross-platform checks')
    args = parser.parse_args()
    result = qualify(args.before, args.after, args.normalize_text_newlines)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"{len(result['matching_files'])} matching files; "
          f"guest stage {result['guest_speedup']:.2f}x faster")


if __name__ == '__main__':
    main()

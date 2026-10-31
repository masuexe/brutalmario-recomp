#!/usr/bin/env python3
"""Generate an assisted 9C reflection route without health or phase writes."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def route(donor=False):
    suffix = '-donor' if donor else ''
    text = (ROOT / f'recomp/inputs/mazo-9c-orb-sequence{suffix}.script').read_text()
    text = text.split('dump contact0')[0]
    text += '# Observe real reflected hits. Reposition only Mario to recollect the orb.\n'
    text += 'dump contact0\n'
    # Entry and permanent $1497 immunity come from the declared orb fixture.
    # Repeated placement permits real orb contact. Boss state remains untouched.
    for cycle in range(1, 13):
        if cycle > 1:
            text += 'poke 94 b400fa00\n'
        for sample in range(1, 33):
            text += f'wait 48\ndump c{cycle:02d}f{sample:02d}\n'
    return text + 'quit\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('use a fresh output path')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(route(args.donor))


if __name__ == '__main__':
    main()

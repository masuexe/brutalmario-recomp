#!/usr/bin/env python3
"""Generate the bounded, assisted Seven combat phase regression input."""
import argparse
from pathlib import Path

from restore_star_world_1 import write_verified

ROOT = Path(__file__).resolve().parents[1]


def route(host):
    source = ROOT / f'recomp/inputs/native-seven-{host}-opening.script'
    prefix = source.read_text().split('# Ordinary button inputs', 1)[0]
    result = ('# Assisted combat phase regression. Pipe entry is a room fixture.\n'
              '# Force only temporary damage immunity; do not write HP, phases or clear flags.\n'
              + prefix + '\nforcepoke 1497 ff\npress b 2\nwait 60\ndump protected_start\n'
              '# Wendy has reversed the controls at this boundary.\n'
              'press right 70\nwait 20\ndump aligned\n')
    for index in range(400):
        key = 'up+b' if index % 3 == 0 else 'up+a'
        result += f'press {key} 24\nwait 70\n'
        if index % 20 == 19:
            result += f'dump phase{index+1:04}\n'
    return result+'quit\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', choices=('native', 'donor'))
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_verified(args.output, route(args.host).encode())

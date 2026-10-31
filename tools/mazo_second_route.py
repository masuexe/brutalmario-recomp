#!/usr/bin/env python3
"""Generate assisted Mazo second-boss controls using normal jump input."""
import argparse
from pathlib import Path

from mazo_reflect_route import route


def second_route(donor=False, mode='jump', hops=80):
    # The pinned reflection captures reach counter 6 during these cycles.
    cycles = 6 if donor else 5
    text = route(donor).split('dump contact0')[0] + 'dump contact0\n'
    for cycle in range(1, cycles+1):
        if cycle > 1:
            text += 'poke 94 b400fa00\n'
        for sample in range(1, 33):
            text += f'wait 48\ndump c{cycle:02d}f{sample:02d}\n'
    if mode == 'idle':
        text += '# End orb placements here. Observe second-boss controls and survival.\ndump last_orb_cycle\n'
        for sample in range(1, 251):
            text += f'wait 24\ndump late{sample:03d}\n'
    else:
        text += ('# No more orb placements. Jump before the ground-check attack.\n'
                 'until cb == 08 15000\ndump ground_attack\n'
                 'until 15b5 == c0 512\ndump before_jump\npress b 16\n'
                 'dump jump_check\nwait 64\ndump survived_ground_attack\n')
        if mode == 'jump':
            for sample in range(1, 161):
                text += f'wait 24\ndump follow{sample:03d}\n'
        elif mode == 'highhop':
            text += '# Ground-triggered normal jumps; no additional position or boss-state writes.\n'
            for sample in range(1, hops+1):
                text += f'until 77 == 04 4000\npress b 24\ndump highhop{sample:03d}\n'
        else:
            raise ValueError('unknown route mode')
    return text + 'quit\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', action='store_true')
    parser.add_argument('--mode', choices=['idle', 'jump', 'highhop'], default='jump')
    parser.add_argument('--hops', type=int, default=80)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.hops < 1:
        parser.error('use a fresh output and a positive hop count')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(second_route(args.donor, args.mode, args.hops))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Follow the assisted Mazo fight into its scripted ending and ordinary goal."""
import argparse
from pathlib import Path

from mazo_second_route import second_route


def ending_route(donor=False, observe_only=False):
    text = second_route(donor, 'highhop', 120 if donor else 240)
    assert text.endswith('quit\n')
    text = text[:-5] + '# Observe the scripted transformation with no further input or state writes.\n'
    for sample in range(1, 161):
        text += f'wait 32\ndump scene{sample:03d}\n'
    if not observe_only:
        text += ('# Normal message dismissal and rightward movement toward the visible goal sphere.\n'
                 'press b 2\nwait 32\ndump dismissed\npress right 120\ndump walked\n'
                 'wait 900\ndump after_goal\nreset\nwait 600\npress start 2\n'
                 'wait 180\npress start 2\nwait 600\ndump file_reload\n')
    return text + 'quit\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor', action='store_true')
    p.add_argument('--observe-only', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('use a fresh output')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(ending_route(a.donor, a.observe_only))


if __name__ == '__main__':
    main()

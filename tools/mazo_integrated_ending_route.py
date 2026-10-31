#!/usr/bin/env python3
"""Follow the actual Mazo node, assisted corridor and fight to a real saved goal."""
import argparse
from pathlib import Path

from mazo_ending_route import ending_route

ROOT = Path(__file__).resolve().parents[1]


def route(legacy=False):
    node = (ROOT / 'recomp/inputs/mazo-node-save-boundary-settled.script').read_text()
    prefix = node.split('poke 94 80004001')[0]
    prefix = prefix.replace('# After real node entry, a primary pipe-action fixture skips room190 to192.',
                            '# After real node entry, a primary pipe-action fixture skips room190 to191.')
    prefix += '''# Position/pipe/immunity fixtures bypass room190 and the two room191 obstacles.
# The guest requests message2 and makes its own transition to the boss room151.
forcepoke 1497 ff
poke 94 80004001
poke 19b8 91
poke 19d8 05
poke 88 0000
poke 71 06
wait 180
dump corridor191
poke 94 c0006001
until 1426 == 02 300
wait 120
dump message191
press b 2
wait 120
until 010b == 51 800
until 0100 == 14 500
wait 180
dump fight_entry
# The established first-boss contact placements follow. No boss/HP/phase writes.
poke 94 b400fa00
dump contact0
'''
    original = ending_route().split('dump contact0\n', 1)[1]
    if legacy:
        return prefix + original
    # This entry reaches reflection marker6 during cycle3. Stop contact
    # placements during the ensuing first-boss death dialogue.
    for cycle in range(1, 4):
        if cycle > 1:
            prefix += 'poke 94 b400fa00\n'
        for sample in range(1, 33):
            prefix += f'wait 48\ndump c{cycle:02d}f{sample:02d}\n'
    ground = original.split('# No more orb placements. Jump before the ground-check attack.\n', 1)[1]
    ground = ground.split('# Ground-triggered normal jumps;', 1)[0]
    prefix += '# No more position writes. Follow the normal second-boss jump controls.\n' + ground
    for sample in range(1, 161):
        prefix += f'until 77 == 04 4000\npress b 24\ndump highhop{sample:03d}\n'
    prefix += '# Assert real cutscene state; never write it.\nuntil 1f413 == 03 0\nuntil 71 == 0b 0\n'
    return prefix + '# Observe' + original.split('# Observe', 1)[1]


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--legacy-probe', action='store_true')
    a = p.parse_args()
    if a.output.exists():
        p.error('use a fresh script path')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(route(a.legacy_probe))

#!/usr/bin/env python3
"""Generate assisted room-entry and normal Mazo message contact/close routes."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def route(room, donor=False):
    if room not in (0x191, 0x192):
        raise ValueError('only the reviewed message rooms are supported')
    suffix = '-donor' if donor else ''
    text = (ROOT/f'recomp/inputs/mazo-9c-orb-sequence{suffix}.script').read_text().split('dump before_contact')[0]
    text += ('# Assisted primary-room/pipe/immunity fixture; guest actor requests the message.\n'
             '# No message, font, boss, progression, completion or save writes.\n'
             f'poke 94 80004001\npoke 19b8 {room & 255:02x}\npoke 19d8 05\n'
             'poke 88 0000\npoke 71 06\nwait 180\ndump room_entry\n')
    if room == 0x191:
        text += '# Contact-position fixture bypasses the two entry obstacles; not ordinary traversal.\n'
        text += 'poke 94 c0006001\nuntil 1426 == 02 300\n'
    else:
        text += 'until 1426 == 01 300\n'
    text += 'wait 120\ndump message\npress b 2\nwait 120\ndump closed1\n'
    if room == 0x192:
        text += '# Direct pipe entry lets B0 request twice on its two active ticks; dismiss both normally.\n'
        text += 'press b 2\nwait 120\n'
    text += 'dump closed\n'
    if room == 0x191:
        text += 'wait 180\ndump following\n'
    else:
        text += 'press right 120\ndump walked\nwait 900\ndump after_goal\n'
    return text+'quit\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--room', choices=['191', '192'], required=True)
    p.add_argument('--donor', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('use a fresh output')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(route(int(a.room, 16), a.donor))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Qualify the bonus room exit repair from captured native runs.

The repair adds LDY #$00 at the entry of the 1-up scan in the bonus sprite
program. The scan result decides whether the program writes the bonus-game
end timer at $14AB. A stale Y value skipped that write, so the room never
started its exit.

This check reads two capture directories from the same fixture. One comes
from a patched target, one from an unpatched target. It asserts that the
patched run leaves the bonus room and that the unpatched run stays inside.

Usage:
  python3 tools/qualify_bonus_room_exit.py \
      --patched   local/captures/play-demo11-native-product-r16 \
      --unpatched local/captures/play-demo11-native-product-r14
"""
import argparse
from pathlib import Path
import sys

from qualify_world1_next_course import require

# Low WRAM addresses, from the Super Mario World variable map.
GAME_MODE = 0x0100
ROOM_LOW = 0x010B
ROOM_HIGH = 0x010C
BONUS_STARS = 0x0F48
FLAG_BONUS_GAME = 0x1425
TIMER_BONUS_END = 0x14AB

MODE_LEVEL = 0x14
MODE_MAP = 0x0E
BONUS_ROOMS = (0x000, 0x100)


def samples(directory):
    """Yield (tag, wram bytes) for each dump in the directory, in tag order."""
    directory = Path(directory)
    require(directory.is_dir(), 'missing capture directory: ' + str(directory))
    items = []
    for path in directory.glob('*.wram.bin'):
        items.append((path.name[: -len('.wram.bin')], path.read_bytes()))
    require(items, 'no wram dumps in ' + str(directory))
    items.sort(key=lambda item: item[0])
    return items


def room_of(wram):
    return wram[ROOM_LOW] | (wram[ROOM_HIGH] << 8)


def summarise(items):
    """Return the facts this check needs from one capture directory."""
    bonus = [(tag, w) for tag, w in items if room_of(w) in BONUS_ROOMS]
    require(bonus, 'the fixture never reached a bonus room')
    timers = [w[TIMER_BONUS_END] for _, w in bonus]
    modes = [w[GAME_MODE] for _, w in bonus]
    return {
        'bonus_samples': len(bonus),
        'first_bonus_tag': bonus[0][0],
        'timer_max': max(timers),
        'left_room': MODE_MAP in modes,
        'modes': sorted(set(modes)),
        'flag_seen': any(w[FLAG_BONUS_GAME] for _, w in bonus),
        'stars': bonus[0][1][BONUS_STARS],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--patched', required=True, help='capture from the patched target')
    parser.add_argument('--unpatched', required=True, help='capture from the unpatched target')
    args = parser.parse_args()

    patched = summarise(samples(args.patched))
    unpatched = summarise(samples(args.unpatched))

    require(patched['flag_seen'], 'the patched run never set the bonus-game flag')
    require(unpatched['flag_seen'], 'the unpatched run never set the bonus-game flag')

    require(patched['timer_max'] > 0,
            'the patched run never wrote the bonus-game end timer')
    require(patched['left_room'],
            'the patched run did not leave the bonus room')
    require(unpatched['timer_max'] == 0,
            'the unpatched run wrote the end timer; the control is not clean')
    require(not unpatched['left_room'],
            'the unpatched run left the bonus room; the control is not clean')

    print('patched   : bonus samples=%d first=%s timer_max=%02X modes=%s left=%s stars=%02X'
          % (patched['bonus_samples'], patched['first_bonus_tag'], patched['timer_max'],
             [hex(m) for m in patched['modes']], patched['left_room'], patched['stars']))
    print('unpatched : bonus samples=%d first=%s timer_max=%02X modes=%s left=%s stars=%02X'
          % (unpatched['bonus_samples'], unpatched['first_bonus_tag'], unpatched['timer_max'],
             [hex(m) for m in unpatched['modes']], unpatched['left_room'], unpatched['stars']))
    print('bonus room exit repair: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())

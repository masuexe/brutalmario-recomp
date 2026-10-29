#!/usr/bin/env python3
"""Launch the native product target with runtime practice cheats.

This tool builds a host script that writes the cheat fields, then starts the
game with a normal window. Use it to reach any room, any map position, or to
hold invincibility and air swim. It checks the ROM and binary identities first.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from restore_star_world_1 import sha

# Wait for the title, open the file, skip the intro, and reach the map.
STARTUP = '''wait 600
press start 2
wait 180
press start 2
wait 900
press b 30
wait 180
press a 30
wait 180
'''

# Fast-entry startup: poll game mode instead of fixed waits, skip the intro.
FAST_STARTUP = '''turbo on
until 0100 == 07 4000
press start 2
until 0100 == 08 900
press start 2
until 0100 == 14 2400
wait 780
press b 30
until 0100 == 0e 2400
'''

# Completion writes, copied from the accepted all-levels cheat.
COMPLETION = '''poke 1ea2 9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f
poke 1f02 ffffffffffffffffffffffffffffff
poke 1f27 01010101
poke 1f2e 60
poke 1f2f ffffffffffffffffffffffff
poke 1182c 000000000000000000000000000000000000000000000000
'''


def coordinate(text):
    try:
        return int(text[1:], 16) if text.startswith('$') else int(text, 0)
    except ValueError:
        raise argparse.ArgumentTypeError('use decimal or 0x-prefixed hex')


def validate_room(room):
    if not 0 <= room <= 0x1FF:
        raise ValueError('room id must be 0x000 to 0x1FF')
    return room


def validate_map(x, y):
    if not (0 <= x <= 0x1FF and 0 <= y <= 0x1FF):
        raise ValueError('map X and Y must be 0 to 0x1FF')
    return x, y


def map_teleport(map_id, x, y):
    coordinates = (x.to_bytes(2, 'little') + y.to_bytes(2, 'little')) * 2
    tiles = ((x >> 4).to_bytes(2, 'little') + (y >> 4).to_bytes(2, 'little')) * 2
    return (
        '\n# Practice map transfer: map %d, X=%d, Y=%d.\n' % (map_id, x, y) +
        'poke 1f11 %s\n' % (bytes([map_id, map_id]).hex()) +
        'poke 1f17 %s\n' % coordinates.hex() +
        'poke 1f1f %s\n' % tiles.hex() +
        'poke 0100 0b\nwait 240\n')


def room_teleport(room):
    # Enter the map 6 lower-left node, then apply the room transition.
    # $19B8 holds the room low byte. $19D8 holds 4 plus the room high byte.
    return (
        '\n# Practice room transfer: room 0x%03X.\n' % room +
        'poke 1f11 0606\n'
        'poke 1f17 2801e8012801e801\n'
        'poke 1f1f 12001e0012001e00\n'
        'poke 0100 0b\nwait 240\n'
        'poke d7e2 6a\npress y 2\nwait 240\n'
        'poke 94 80004001\n'
        'poke 19b8 %02x\n' % (room & 0xFF) +
        'poke 19d8 %02x\n' % (4 + (room >> 8)) +
        'poke 88 0000\n'
        'poke 71 06\nwait 180\n')


def fast_room_teleport(room):
    # Same targets as room_teleport but poll each transition instead of fixed waits.
    return (
        '\n# Fast room transfer: room 0x%03X.\n' % room +
        'poke 1f11 0606\n'
        'poke 1f17 2801e8012801e801\n'
        'poke 1f1f 12001e0012001e00\n'
        'poke 0100 0b\n'
        'until 0100 == 0e 1600\n'
        'poke d7e2 6a\n'
        'press y 2\n'
        'until 0100 == 14 1200\n'
        'poke 19b8 %02x\n' % (room & 0xFF) +
        'poke 19d8 %02x\n' % (4 + (room >> 8)) +
        'poke 88 0000\n'
        'poke 71 06\n'
        'until16 10b == %x 1600\n' % room)


def build_script(*, map_pos=None, room=None, air_swim=False, invincible=False,
                 complete_all=False, lives=None, fast=False):
    lines = [FAST_STARTUP if (fast and room is not None) else STARTUP]
    if lives is not None:
        lines.append('\n# Practice only: set the life counter.\npoke 0dbe %02x\n' % lives)
    if complete_all:
        lines.append(COMPLETION)
        lines.append('# Reload through the normal fade so the flags apply.\n')
        lines.append(map_teleport(6, 0x128, 0x1E8))
    if map_pos is not None:
        lines.append(map_teleport(*map_pos))
    if room is not None:
        lines.append(fast_room_teleport(room) if (fast and room is not None) else room_teleport(room))
    if air_swim:
        lines.append('\n# Practice only: treat every level as water.\nforcepoke 85 01\n')
    if invincible:
        lines.append('\n# Practice only: hold the star invincibility timer.\nforcepoke 1490 40\n')
    if not (map_pos or room is not None or air_swim or invincible or complete_all
            or lives is not None):
        lines.append('\n# No cheat selected. The game starts at the title screen.\n')
    lines.append('turbo off\n')
    return ''.join(lines)


def settings(target):
    path = ROOT / 'config/restorations' / (target + '.json')
    if not path.is_file():
        raise SystemExit('missing target config: ' + target)
    return json.loads(path.read_text())


def packs_env(target, cfg, env):
    if 'native_sprite_gap' in cfg:
        import native_sprite_gap
        native_sprite_gap.environment(target, env)
    elif 'native_seven' in cfg:
        import native_seven
        native_seven.environment(target, env)
    elif 'native_mazo' in cfg:
        import native_mazo
        native_mazo.environment(target, env)
    elif 'native_sprite' in cfg:
        import native_sprite
        native_sprite.environment(target, env)
    else:
        raise SystemExit('target holds no known content packs: ' + target)


def run_menu(args):
    """Fill the destination and toggle arguments from the terminal."""
    print('Native practice cheats for', args.target)
    print('  1. Map position (map, X, Y)')
    print('  2. Room id (0x000 to 0x1FF)')
    print('  3. Stay where the game starts')
    choice = input('Choose 1, 2 or 3: ').strip()
    if choice == '1':
        args.map = coordinate(input('Map id (e.g. 6): ').strip())
        args.x = coordinate(input('X (0 to 0x1FF): ').strip())
        args.y = coordinate(input('Y (0 to 0x1FF): ').strip())
    elif choice == '2':
        args.room = coordinate(input('Room id (e.g. 0x151): ').strip())
    answer = input('Toggles: i = invincible, s = air swim, c = complete all '
                   '(letters, then Enter): ').strip().lower()
    if 'i' in answer:
        args.invincible = True
    if 's' in answer:
        args.air_swim = True
    if 'c' in answer:
        args.complete_all = True


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--target', default='demo11-native-product')
    parser.add_argument('--map', type=coordinate, metavar='MAP',
                        help='map id for a position teleport, for example 6')
    parser.add_argument('--x', type=coordinate, help='map X for --map')
    parser.add_argument('--y', type=coordinate, help='map Y for --map')
    parser.add_argument('--room', type=coordinate, metavar='ROOM',
                        help='enter any room id from 0x000 to 0x1FF')
    parser.add_argument('--air-swim', action='store_true',
                        help='treat every level as water')
    parser.add_argument('--invincible', action='store_true',
                        help='hold star invincibility')
    parser.add_argument('--complete-all', action='store_true',
                        help='open every saved level slot, event and switch')
    parser.add_argument('--lives', type=coordinate, metavar='N',
                        help='set the life counter')
    parser.add_argument('--menu', action='store_true',
                        help='ask for the destination and the toggles interactively')
    parser.add_argument('--fast', action='store_true',
                        help='poll game mode and skip the intro (room entry is fast by default)')
    parser.add_argument('--legacy-entry', action='store_true',
                        help='use the original fixed-wait room entry')
    parser.add_argument('--emit', type=Path,
                        help='write the host script to a path and exit')
    parser.add_argument('--play-dir', type=Path,
                        help='session directory for saves; default local/play/<target>')
    args = parser.parse_args()

    if args.menu:
        run_menu(args)

    map_pos = None
    if args.map is not None or args.x is not None or args.y is not None:
        if args.map is None or args.x is None or args.y is None:
            raise SystemExit('--map needs --x and --y')
        x, y = validate_map(args.x, args.y)
        map_pos = (args.map, x, y)
    room = None
    if args.room is not None:
        try:
            room = validate_room(args.room)
        except ValueError as error:
            raise SystemExit(str(error))

    lives = None
    if args.lives is not None:
        lives = args.lives & 0xFF
    fast = room is not None and not args.legacy_entry
    if args.fast:
        fast = True
    script_text = build_script(map_pos=map_pos, room=room,
                               air_swim=args.air_swim,
                               invincible=args.invincible,
                               complete_all=args.complete_all, lives=lives, fast=fast)
    if args.emit:
        args.emit.write_text(script_text)
        print('wrote', args.emit)
        return

    from restoration_targets import RESTORATIONS
    target = args.target
    if target not in RESTORATIONS:
        raise SystemExit('unknown target: ' + target)
    binary_name = RESTORATIONS[target]['binary']
    cfg = settings(target)
    rom = ROOT / 'local/restoration' / target / 'rom.sfc'
    binary = ROOT / 'local/build' / target / binary_name
    if not rom.is_file() or not binary.is_file():
        raise SystemExit('missing build; run tools/m1.py build first')
    if sha(rom.read_bytes()) != cfg['output']['sha256']:
        raise SystemExit('ROM identity differs from the config')
    receipt = json.loads((binary.parent / 'm1-build.json').read_text())
    if receipt['binary_sha256'] != hashlib.sha256(binary.read_bytes()).hexdigest():
        raise SystemExit('binary differs from the build receipt; rebuild first')

    play_dir = (args.play_dir or ROOT / 'local/play' / target).resolve()
    saves = play_dir / 'saves'
    saves.mkdir(parents=True, exist_ok=True)
    if args.complete_all:
        current = saves / 'save.srm'
        if current.is_file():
            aside = saves / 'save.srm.before-cheat'
            if aside.exists():
                aside.unlink()
            current.rename(aside)
            print('moved the earlier save to', aside)

    script_path = play_dir / 'cheat.script'
    script_path.write_text(script_text)

    env = dict(os.environ)
    packs_env(target, cfg, env)
    command = [str(binary), '--no-launcher',
               '--config', str(ROOT / 'recomp/m1-config.ini'),
               '--rom', str(rom), '--script', str(script_path)]
    print('launch:', ' '.join(command))
    print('packs:', sum(1 for key in env if key.startswith('BM_')))
    print('session directory:', play_dir)
    if room is not None:
        print('room 0x%03X requested; the screen changes after the fade.' % room)
    subprocess.run(command, env=env, cwd=str(play_dir), check=False)


if __name__ == '__main__':
    main()
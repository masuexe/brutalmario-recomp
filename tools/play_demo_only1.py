#!/usr/bin/env python3
"""Launch demoOnly1 with isolated map teleport and boss practice sessions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from prepare_rom import verify
from runtime_patches import patch_plan
import windows_audio

ROOT = Path(__file__).resolve().parents[1]


# Named entrances use observed map positions; map IDs are not world numbers.
LEVELS = {
    'athletic-special': {'name': 'Athletic Special', 'map': 5,
                         'x': 0x138, 'y': 0x108, 'level': 0x134, 'moves': ()},
    'baby-yoshi-hill': {'name': 'Baby Yoshi Hill', 'map': 5,
                       'x': 0x178, 'y': 0x128, 'level': 0x126,
                       'moves': ('right', 'right')},
    'world1-castle': {'name': 'World 1 castle (Lemmy)', 'map': 0,
                      'x': 0x0a8, 'y': 0x1a8, 'level': 0x10e,
                      'teleport': (0, 0x0a8, 0x1a8)},
}


# Target-specific save flags, verified against the pinned demoOnly1 ROM.
# $03BA50 denies level entry when bits $80 and $20 are both set;
# $10CE2A marks clear ($80), clears the midway bit ($40), and clears custom
# midway masks. $4F8C45 and $0DB2CA read the saved DK/dragon-coin bitset.
COMPLETION_WRITES = (
    (0x1ea2, bytes([0x9f]) * 0x60),  # clear + $10/direction bits; no deny/midway
    (0x1f02, bytes([0xff]) * 0x0f),  # overworld event flags
    (0x1f27, bytes([1]) * 4),        # switch palaces
    (0x1f2e, bytes([0x60])),         # synthetic completion counter
    (0x1f2f, bytes([0xff]) * 12),    # saved per-translevel DK/dragon coins
    (0x1182c, bytes(24)),          # WRAM offset for $7F:182C, two custom midway masks
)


def completion_script():
    return ('\n# Practice: complete every saved level slot and DK coin bit.\n' +
            ''.join(f'poke {address:x} {data.hex()}\n'
                    for address, data in COMPLETION_WRITES))


def coordinate(text):
    try:
        return int(text[1:], 16) if text.startswith('$') else int(text, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError('use decimal or a hexadecimal value such as 0x58') from error


def validate_teleport(position):
    if len(position) != 3:
        raise ValueError('provide MAP X Y')
    map_id, x, y = position
    if not 0 <= map_id <= 6:
        raise ValueError('map must be between 0 and 6')
    if not (0 <= x <= 0x1ff and 0 <= y <= 0x1ff):
        raise ValueError('X and Y must be between 0 and 511 (0x1ff)')
    return map_id, x, y


def teleport_script(position):
    map_id, x, y = validate_teleport(position)
    coordinates = (x.to_bytes(2, 'little') + y.to_bytes(2, 'little')) * 2
    tiles = ((x >> 4).to_bytes(2, 'little') + (y >> 4).to_bytes(2, 'little')) * 2
    # The normal fade-out toggles the fade direction before the map loader
    # runs. Entering loader mode $0C directly from an idle map fades to black.
    return (f'\n# Practice map transfer: map {map_id}, X={x:#05x}, Y={y:#05x}.\n'
            f'poke 1f11 {bytes([map_id, map_id]).hex()}\n'
            f'poke 1f17 {coordinates.hex()}\n'
            f'poke 1f1f {tiles.hex()}\n'
            'poke 0100 0b\nwait 240\n')


def choose_position():
    while True:
        try:
            answer = input('Map X Y (e.g. 1 0x58 0x88; q to cancel): ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nCancelled.')
            return None
        if answer.lower() in ('q', 'quit'):
            return None
        try:
            return validate_teleport(tuple(coordinate(part) for part in answer.split()))
        except (ValueError, argparse.ArgumentTypeError) as error:
            print(error)


def print_levels():
    for key, entry in LEVELS.items():
        print(f"{key:22s} {entry['name']}")


def choose_level(complete_all=False):
    choices = {key: entry['name'] for key, entry in LEVELS.items()}
    choices['boss-door'] = 'Boss door (Athletic Special)'
    choices['teleport'] = 'Custom map position'
    keys = list(choices)
    print('demoOnly1 practice destinations (fresh, separate save)')
    for number, key in enumerate(keys, 1):
        print(f"  {number}. {choices[key]}")
    print(f"  c. All levels + DK coins: {'ON' if complete_all else 'OFF'} (toggle)")
    print('  q. Cancel')
    while True:
        try:
            answer = input('Choose a level: ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print('\nCancelled.')
            return None
        if answer in ('q', 'quit'):
            return None
        if answer == 'c':
            complete_all = not complete_all
            print(f"All levels + DK coins: {'ON' if complete_all else 'OFF'}")
            continue
        if answer in choices:
            return answer, complete_all
        if answer.isascii() and answer.isdecimal() and 1 <= int(answer) <= len(keys):
            return keys[int(answer) - 1], complete_all
        print(f'Enter a number from 1 to {len(keys)}, a level key, or q.')


def practice_script(*, boss_door=False, air_swim=False, level=None, teleport=None,
                    complete_all=False):
    if sum((bool(boss_door), level is not None, teleport is not None)) > 1:
        raise ValueError("choose one destination")
    full_route = (ROOT / 'recomp/inputs/demo-only-1-boss-door.script').read_text()
    full_route = full_route.replace('turbo off\n', '')
    startup, boss_tail = full_route.split('press y 30\n', 1)
    route = startup
    if complete_all:
        route += completion_script()
        # Reload through the normal fade so event tiles and Warp Stars agree
        # with the completed save flags before using any selected destination.
        route += teleport_script((5, 0x138, 0x108))
    if boss_door:
        route += 'press y 30\n' + boss_tail
    if level is not None:
        entry = LEVELS[level]
        if 'teleport' in entry:
            route += teleport_script(entry['teleport'])
        else:
            # Existing paths update the node and title through ordinary input.
            route += f"\n# Practice entrance: {entry['name']}. Keep exits/events intact.\n"
            for direction in entry['moves']:
                route += f'press {direction} 30\nwait 180\n'
    if teleport is not None:
        route += teleport_script(teleport)
    if air_swim:
        # $85 makes the guest apply its normal swimming physics, including
        # resetting $75 itself. Do not freeze Mario's position or velocity.
        route += '\n# Practice only: treat every level as water until process exit.\nforcepoke 85 01\n'
    return route + '\nturbo off\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument('--boss-door', action='store_true',
                             help='start a fresh practice session at the pre-boss top door')
    destination.add_argument('--special', action='store_true',
                             help='start a fresh practice session on the Special overworld')
    destination.add_argument('--level', choices=tuple(LEVELS),
                             help='start a fresh practice session at the selected map entrance')
    destination.add_argument('--teleport', nargs=3, type=coordinate, metavar=('MAP', 'X', 'Y'),
                             help='start a fresh practice session at any map position')
    destination.add_argument('--select-level', action='store_true',
                             help='choose a practice level from a terminal menu')
    destination.add_argument('--list-levels', action='store_true',
                             help='list named practice entrances and exit')
    parser.add_argument('--complete-all', action='store_true',
                        help='mark all levels, overworld events, switches and DK coins complete in a fresh practice save')
    parser.add_argument('--air-swim', action='store_true',
                        help='enable normal swimming in air for this practice session (tap jump to rise)')
    parser.add_argument('--show-location', action='store_true',
                        help='print map coordinates and room IDs in this terminal as they change')
    args = parser.parse_args()
    if args.list_levels:
        print_levels()
        return
    if args.select_level:
        selection = choose_level(args.complete_all)
        if selection is None:
            return
        selected, args.complete_all = selection
        if selected == 'boss-door':
            args.boss_door = True
        elif selected == 'teleport':
            args.teleport = choose_position()
            if args.teleport is None:
                return
        else:
            args.level = selected
    if args.teleport is not None:
        try:
            args.teleport = validate_teleport(args.teleport)
        except ValueError as error:
            parser.error(str(error))
    rom = ROOT / 'local/roms/demo-only-1.sfc'
    build = ROOT / 'local/build/demo-only-1'
    binary = build / 'BrutalMarioDemoOnly1SNESRecomp'
    manifest = json.loads((ROOT / 'config/demo-only-1.json').read_text())
    verify(rom.read_bytes(), manifest['output'], manifest['target'])
    receipt = json.loads((build / 'm1-build.json').read_text())
    if (receipt['binary_sha256'] != hashlib.sha256(binary.read_bytes()).hexdigest() or
            receipt['runtime_patches'] != patch_plan()):
        parser.error('binary differs from its current runtime receipt; rebuild demo-only-1 first')
    command = [str(binary), '--no-launcher', '--rom', str(rom)]
    if (args.boss_door or args.special or args.air_swim or args.level or
            args.teleport is not None or args.complete_all):
        practice_root = ROOT / 'local/play/demo-only-1/practice'
        practice_root.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix='session-', dir=practice_root))
        script = directory / 'input.script'
        script.write_text(practice_script(boss_door=args.boss_door, air_swim=args.air_swim,
                                          level=args.level, teleport=args.teleport,
                                          complete_all=args.complete_all))
        # An explicit config prevents the desktop host from changing cwd to
        # the executable directory, where the user's ordinary SRAM resides.
        config_source = build / 'config.ini'
        if not config_source.is_file():
            config_source = ROOT / 'recomp/m1-config.ini'
        config = directory / 'config.ini'
        config.write_bytes(config_source.read_bytes())
        command += ['--config', str(config), '--script', str(script)]
        # Retain device/queue counters and bounded frame timings for real
        # desktop sessions; explicit diagnostic environment settings win.
        os.environ.setdefault('SNESRECOMP_AUDIO_STATS', str(directory / 'audio-stats.txt'))
        os.environ.setdefault('SNESRECOMP_FRAME_TIMING', str(directory / 'frame-timing.csv'))
        print(f'Fresh practice session: {directory.relative_to(ROOT)}', flush=True)
        if args.level:
            print(f"Practice level: {LEVELS[args.level]['name']}. Use the normal level-entry button.", flush=True)
        if args.teleport is not None:
            map_id, x, y = args.teleport
            print(f'Map {map_id}, X={x:#05x}, Y={y:#05x}. Use the normal level-entry button.', flush=True)
        if args.complete_all:
            print('All levels + DK coins complete: ON (fresh practice save).', flush=True)
        if args.level == 'world1-castle' and args.complete_all:
            print('Lemmy castle is marked clear: press the L+R shoulder buttons together to re-enter.', flush=True)
        if args.air_swim:
            print('Air swim ON: tap jump repeatedly to rise; release to sink. Restart without --air-swim to disable.', flush=True)
    else:
        # Preserve the existing executable-relative normal save/config paths.
        directory = build
    if args.show_location:
        os.environ['M1_SHOW_LOCATION'] = '1'
        print('Location readout ON in this terminal. OW coordinates persist inside levels; room IDs may be stale on the map.', flush=True)
    os.chdir(directory)
    os.environ['SNESRECOMP_SEPARATE_ECHO'] = '1'
    if windows_audio.available(ROOT) and windows_audio.enabled(directory / 'config.ini'):
        result = windows_audio.run(command, directory, ROOT)
        if result is not None:
            raise SystemExit(result)
    os.execv(str(binary), command)


if __name__ == '__main__':
    main()

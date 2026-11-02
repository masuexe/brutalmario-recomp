#!/usr/bin/env python3
"""Run the native product on Windows with the same cheat switches as Linux.

The Linux launcher starts the built binary directly. A Windows build bakes the
ROM digest into the executable and refuses a different ROM. This tool copies
the shipped Windows executable, rewrites only the baked digest bytes to the
selected target ROM, and starts the copy. It then applies the same practice
cheat switches that tools/play_native_cheats.py supports on Linux.

The digest rewrite is a launcher convenience, not a game change. The generated
guest code and the content packs stay byte-identical to the shipped bundle.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from restore_star_world_1 import sha
from restoration_targets import RESTORATIONS

SHIPPED_BUNDLE = ROOT / 'local/release/product-r14-event30-v2'
SHIPPED_BINARY = SHIPPED_BUNDLE / 'bin' / 'BrutalMario.exe'
SHIPPED_ROM_SHA = 'a1c9d7c8f09399b60193302e33bb1c8111ac0fe8e5b1cb5684fb6f277fddbf91'
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
COMPLETION = '''poke 1ea2 9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f9f
poke 1f02 ffffffffffffffffffffffffffffff
poke 1f27 01010101
poke 1f2e 60
poke 1f2f ffffffffffffffffffffffffff
poke 1182c 000000000000000000000000000000000000000000000000
'''


def win(path):
    """Return the Windows form of a WSL path."""
    return subprocess.check_output(['wslpath', '-w', str(path)], text=True).strip()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def rewrite_identity(source, old_sha, new_sha, output):
    """Copy the executable and replace every baked ROM digest with the target.

    The build stores the digest three times: one hex string for the launcher
    warning and two binary arrays for the program module and the mod catalog.
    All three must name the selected ROM, or the runtime refuses it.
    """
    old_binary = bytes.fromhex(old_sha)
    new_binary = bytes.fromhex(new_sha)
    old_ascii = old_sha.encode('ascii')
    new_ascii = new_sha.encode('ascii')
    data = bytearray(source.read_bytes())
    binary_hits = 0
    cursor = 0
    while True:
        found = data.find(old_binary, cursor)
        if found < 0:
            break
        data[found:found + 32] = new_binary
        binary_hits += 1
        cursor = found + 32
    ascii_hits = data.count(old_ascii)
    if ascii_hits:
        data = bytearray(bytes(data).replace(old_ascii, new_ascii))
    if binary_hits == 0 or ascii_hits == 0:
        raise SystemExit('the shipped executable does not carry the expected digest; '
                         'refusing to patch an unknown binary')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bytes(data))
    # WSL interop runs the Windows image through its Linux path, so the copy
    # needs the execute bit before it can start.
    output.chmod(0o755)
    return {'binary_digest_sites': binary_hits, 'ascii_digest_sites': ascii_hits,
            'output_sha256': sha256(bytes(data))}


def add_music(script_text, slot):
    """Return the script with one music-slot request before the trailing stop.

    The Linux launcher has no music switch, so this write stays local to the
    Windows launcher instead of changing the shared cheat encoding.
    """
    slot &= 0xFF
    block = ('\n# Practice only: request a music slot.\n'
             'forcepoke 0dda %02x\nforcepoke 1dfb %02x\n' % (slot, slot))
    return script_text.replace('turbo off\n', block + 'turbo off\n')


def build_script(**options):
    """Return the host script for the requested practice switches.

    The encoding is identical on both hosts, so this reuses the Linux launcher
    instead of keeping a second copy of the cheat writes.
    """
    import play_native_cheats
    return play_native_cheats.build_script(**options)


def pack_environment(target):
    """Return the content pack variables for one target."""
    import native_sprite_gap
    directory = ROOT / 'local/restoration' / target
    return {pack['variable']: win(directory / pack['pack_file'])
            for pack in native_sprite_gap.packs(target)}


def launch_command(executable, rom, script_path, config):
    """Return the command that runs the Windows executable from this host.

    WSL interop runs a Windows executable by its Linux path, so no wslpath
    translation is needed there. On Windows itself the native paths apply.
    """
    if sys.platform == 'linux':
        return [str(executable), '--no-launcher', '--config', str(config),
                '--rom', str(rom), '--script', str(script_path)]
    return [win(executable), '--no-launcher', '--config', win(config),
            '--rom', win(rom), '--script', win(script_path)]


def coordinate(text):
    try:
        return int(text[1:], 16) if text.startswith('$') else int(text, 0)
    except ValueError:
        raise argparse.ArgumentTypeError('use decimal or 0x-prefixed hex')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--target', default='demo11-overworld-music')
    parser.add_argument('--map', type=coordinate, metavar='MAP', help='map id for a position transfer')
    parser.add_argument('--x', type=coordinate, help='map X for --map')
    parser.add_argument('--y', type=coordinate, help='map Y for --map')
    parser.add_argument('--room', type=coordinate, metavar='ROOM', help='enter a room id from 0x000 to 0x1FF')
    parser.add_argument('--air-swim', action='store_true', help='treat every level as water')
    parser.add_argument('--invincible', action='store_true', help='hold star invincibility')
    parser.add_argument('--complete-all', action='store_true', help='open every level, event and switch')
    parser.add_argument('--lives', type=coordinate, metavar='N', help='set the life counter')
    parser.add_argument('--stars', type=coordinate, metavar='N', help='seed the bonus star counter once')
    parser.add_argument('--music', type=coordinate, metavar='SLOT', help='request a music slot')
    parser.add_argument('--fast', action='store_true', help='poll game mode and skip the intro')
    parser.add_argument('--existing-save', action='store_true',
                        help='the save file already holds an overworld file')
    parser.add_argument('--emit', type=Path, help='write the host script and exit')
    parser.add_argument('--play-dir', type=Path, help='session directory; default local/play/<target>-windows')
    parser.add_argument('--exe', type=Path, help='Windows executable to patch and run')
    parser.add_argument('--dry-run', action='store_true', help='prepare the executable and script, then stop')
    args = parser.parse_args()

    if args.target not in RESTORATIONS:
        raise SystemExit('unknown target: ' + args.target)
    config = json.loads((ROOT / 'config/restorations' / (args.target + '.json')).read_text())
    rom = ROOT / 'local/restoration' / args.target / 'rom.sfc'
    if not rom.is_file():
        raise SystemExit('missing ROM; run the restoration builder first')
    rom_sha = sha(rom.read_bytes())
    if rom_sha != config['output']['sha256']:
        raise SystemExit('ROM identity differs from the config')

    map_pos = None
    if args.map is not None or args.x is not None or args.y is not None:
        if args.map is None or args.x is None or args.y is None:
            raise SystemExit('--map needs --x and --y')
        if not (0 <= args.x <= 0x1FF and 0 <= args.y <= 0x1FF):
            raise SystemExit('map X and Y must be 0 to 0x1FF')
        map_pos = (args.map, args.x, args.y)
    if args.room is not None and not 0 <= args.room <= 0x1FF:
        raise SystemExit('room id must be 0x000 to 0x1FF')

    script_text = build_script(map_pos=map_pos, room=args.room,
                               air_swim=args.air_swim, invincible=args.invincible,
                               complete_all=args.complete_all,
                               lives=args.lives, stars=args.stars,
                               fast=args.fast, existing_save=args.existing_save)
    if args.music is not None:
        script_text = add_music(script_text, args.music)
    if args.emit:
        args.emit.write_text(script_text)
        print('wrote', args.emit)
        return 0

    play_dir = (args.play_dir or ROOT / 'local/play' / (args.target + '-windows')).resolve()
    play_dir.mkdir(parents=True, exist_ok=True)
    source = (args.exe or SHIPPED_BINARY).resolve()
    if not source.is_file():
        raise SystemExit('missing Windows executable: ' + str(source))
    executable = play_dir / 'BrutalMario.exe'
    identity = rewrite_identity(source, SHIPPED_ROM_SHA, rom_sha, executable)
    print('patched Windows executable:', executable)
    print('  digest sites:', identity['binary_digest_sites'], 'binary,',
          identity['ascii_digest_sites'], 'hex string')

    script_path = play_dir / 'cheat.script'
    script_path.write_text(script_text)
    (play_dir / 'saves').mkdir(parents=True, exist_ok=True)
    config_path = play_dir / 'config.ini'
    if not config_path.exists():
        config_path.write_bytes((SHIPPED_BUNDLE / 'config' / 'config.ini').read_bytes())
    print('session directory:', play_dir)
    if args.dry_run:
        print('dry run: executable and script are ready')
        return 0

    environment = dict(os.environ)
    packs = pack_environment(args.target)
    environment.update(packs)
    if sys.platform == 'linux':
        # WSL interop does not forward ordinary variables to the Windows
        # process. WSLENV names the variables that cross the boundary.
        environment['WSLENV'] = ':'.join(sorted(packs))
    command = launch_command(executable, rom, script_path, config_path)
    print('launch:', ' '.join(command))
    print('packs:', len(environment) - len(os.environ))
    result = subprocess.run(command, env=environment, cwd=str(play_dir))
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())

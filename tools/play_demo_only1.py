#!/usr/bin/env python3
"""Launch demoOnly1, with optional fresh Special/Boss practice sessions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from prepare_rom import verify
from runtime_patches import patch_plan

ROOT = Path(__file__).resolve().parents[1]


def practice_script(*, boss_door=False, air_swim=False):
    route = (ROOT / 'recomp/inputs/demo-only-1-boss-door.script').read_text()
    if not boss_door:
        # The fresh ROM starts at Athletic Special. Stop before entering it.
        route = route.split('press y 30\n', 1)[0]
    route = route.replace('turbo off\n', '')
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
    parser.add_argument('--air-swim', action='store_true',
                        help='enable normal swimming in air for this practice session (tap jump to rise)')
    args = parser.parse_args()
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
    if args.boss_door or args.special or args.air_swim:
        practice_root = ROOT / 'local/play/demo-only-1/practice'
        practice_root.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix='session-', dir=practice_root))
        script = directory / 'input.script'
        script.write_text(practice_script(boss_door=args.boss_door, air_swim=args.air_swim))
        # An explicit config prevents the desktop host from changing cwd to
        # the executable directory, where the user's ordinary SRAM resides.
        config = build / 'config.ini'
        if not config.is_file():
            config = ROOT / 'recomp/m1-config.ini'
        command += ['--config', str(config), '--script', str(script)]
        print(f'Fresh practice session: {directory.relative_to(ROOT)}', flush=True)
        if args.air_swim:
            print('Air swim ON: tap jump repeatedly to rise; release to sink. Restart without --air-swim to disable.', flush=True)
    else:
        # Preserve the existing executable-relative normal save/config paths.
        directory = build
    os.chdir(directory)
    os.environ['SNESRECOMP_SEPARATE_ECHO'] = '1'
    os.execv(str(binary), command)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Launch a built native target for a human player test.

The capture path forces dummy video and audio drivers and runs a script. This
launcher does the opposite: it keeps the desktop drivers, mounts the content
packs for the target and starts the game with a normal window. It checks the ROM
and binary identities first, so a stale build cannot be played by mistake.
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default='demo11-native-product')
    parser.add_argument('--script', type=Path,
                        help='optional script file, for a smoke test')
    parser.add_argument('--print-env', action='store_true',
                        help='print the environment and exit')
    parser.add_argument('--complete-all', action='store_true',
                        help='open every saved level slot, overworld event and '
                             'switch before the player takes control')
    parser.add_argument('--play-dir', type=Path,
                        help='session directory for saves; default local/play/<target>')
    args = parser.parse_args()

    from restoration_targets import RESTORATIONS
    if args.target not in RESTORATIONS:
        raise SystemExit('unknown target: ' + args.target)
    binary_name = RESTORATIONS[args.target]['binary']
    cfg = settings(args.target)
    rom = ROOT / 'local/restoration' / args.target / 'rom.sfc'
    binary = ROOT / 'local/build' / args.target / binary_name
    if not rom.is_file() or not binary.is_file():
        raise SystemExit('missing build; run tools/m1.py build first')
    if sha(rom.read_bytes()) != cfg['output']['sha256']:
        raise SystemExit('ROM identity differs from the config')
    receipt = json.loads((binary.parent / 'm1-build.json').read_text())
    if receipt['binary_sha256'] != hashlib.sha256(binary.read_bytes()).hexdigest():
        raise SystemExit('binary differs from the build receipt; rebuild first')

    if args.complete_all and args.script:
        raise SystemExit('choose --complete-all or --script, not both')
    script = args.script
    if args.complete_all:
        script = ROOT / 'recomp/inputs/cheat-complete-all.script'

    play_dir = (args.play_dir or ROOT / 'local/play' / args.target).resolve()
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

    env = dict(os.environ)
    packs_env(args.target, cfg, env)
    if args.print_env:
        for key in sorted(env):
            if key.startswith('BM_'):
                print(key + '=' + env[key])
        return

    if script:
        scratch = ROOT / 'local/captures' / ('play-' + args.target)
        scratch.mkdir(parents=True, exist_ok=True)
        env.update(SNESRECOMP_DUMP_DIR=str(scratch))
    command = [str(binary), '--no-launcher',
               '--config', str(ROOT / 'recomp/m1-config.ini'),
               '--rom', str(rom)]
    if script:
        command += ['--script', str(script)]
    print('launch:', ' '.join(command))
    print('packs:', sum(1 for key in env if key.startswith('BM_')))
    print('session directory:', play_dir)
    subprocess.run(command, env=env, cwd=str(play_dir), check=False)


if __name__ == '__main__':
    main()
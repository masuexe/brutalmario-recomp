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

    env = dict(os.environ)
    packs_env(args.target, cfg, env)
    if args.print_env:
        for key in sorted(env):
            if key.startswith('BM_'):
                print(key + '=' + env[key])
        return

    if args.script:
        scratch = ROOT / 'local/captures' / ('play-' + args.target)
        scratch.mkdir(parents=True, exist_ok=True)
        env.update(SNESRECOMP_DUMP_DIR=str(scratch))
    command = [str(binary), '--no-launcher',
               '--config', str(ROOT / 'recomp/m1-config.ini'),
               '--rom', str(rom)]
    if args.script:
        command += ['--script', str(args.script)]
    print('launch:', ' '.join(command))
    print('packs:', sum(1 for key in env if key.startswith('BM_')))
    subprocess.run(command, env=env, check=False)


if __name__ == '__main__':
    main()
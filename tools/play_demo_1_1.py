#!/usr/bin/env python3
"""Launch the demo-1-1 build with the project's Windows-native audio path.

The desktop binary embeds both audio fixes, but they only engage when the
host is told to use Windows waveform output through a pipe. Launching the
executable directly leaves SDL on WSLg's RDP sink, which is the transport
that the audio-sync investigation found stalls and drifts. This launcher
applies the same verified path the demoOnly1 launcher already uses.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from prepare_rom import verify
from runtime_patches import patch_plan
import windows_audio

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path,
                        help='override the ROM path passed to the host')
    parser.add_argument('--no-windows-audio', action='store_true',
                        help='force the SDL/WSLg path for a controlled comparison')
    args = parser.parse_args()

    rom = args.rom.resolve() if args.rom else ROOT / 'local/roms/demo-1-1.sfc'
    build = ROOT / 'local/build/demo-1-1'
    binary = build / 'BrutalMarioDemo11SNESRecomp'
    if not binary.is_file():
        parser.error('missing executable; run python3 tools/m1.py build first')
    manifest = json.loads((ROOT / 'config/inputs.json').read_text())
    verify(rom.read_bytes(), manifest['output'], manifest['target'])
    receipt = json.loads((build / 'm1-build.json').read_text())
    if (receipt['binary_sha256'] != hashlib.sha256(binary.read_bytes()).hexdigest() or
            receipt['runtime_patches'] != patch_plan()):
        parser.error('binary differs from its current runtime receipt; rebuild demo-1-1 first')

    command = [str(binary), '--no-launcher', '--rom', str(rom)]
    config = build / 'config.ini'
    if config.is_file():
        command += ['--config', str(config)]

    if args.no_windows_audio:
        os.environ['SNESRECOMP_WINDOWS_AUDIO'] = '0'
    elif not windows_audio.available(ROOT) or not windows_audio.enabled(
            config if config.is_file() else ROOT / 'recomp/m1-config.ini'):
        print('[Audio] Windows native output not selected; using SDL. '
              'Set SNESRECOMP_WINDOWS_AUDIO=1 to force it.', file=sys.stderr, flush=True)
    else:
        os.chdir(build)
        result = windows_audio.run(command, build, ROOT)
        if result is not None:
            raise SystemExit(result)
        print('[Audio] Windows output unavailable; falling back to SDL.', file=sys.stderr, flush=True)

    os.chdir(build)
    os.execv(str(binary), command)


if __name__ == '__main__':
    main()

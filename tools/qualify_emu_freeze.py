#!/usr/bin/env python3
"""Show that the teleport fixture freezes the unmodified Demo 1-1 ROM too.

Six rooms freeze on the native target at the room entry. This tool runs the
same entry script on the reference emulator with the unmodified Demo 1-1 ROM.
A freeze there proves that the fixture, not the native runtime and not a gap
record, causes the stall. It does not claim movement or a course pass.
"""
import argparse
import json
import subprocess
from pathlib import Path

from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
ROM = 'local/restoration/demo11-base/rom.sfc'
MANIFEST = 'local/probes/demo11-base-probe.json'
ROUTES = {
    '085': 'room085-shared',
    '0A2': 'room0A2-shared',
    '0BA': 'room0BA-shared',
    '0BB': 'room0BB-fine',
    '0F3': 'room0F3-shared',
}


def capture(room, route):
    directory = ROOT/'local/captures'/f'emufreeze-{room}-emu'
    if directory.is_dir():
        return directory
    script = ROOT/'recomp/inputs'/(route+'.script')
    if not script.is_file():
        raise ValueError('missing route script '+route)
    env = {'SNESREF_CORE_OPTIONS': 'snes9x_echo_buffer_hack=enabled'}
    import os
    run_env = dict(os.environ, **env)
    subprocess.run(['python3', 'tools/probe_reference.py',
                    '--manifest', MANIFEST, '--rom', ROM,
                    '--script', str(script.relative_to(ROOT)),
                    '--capture', directory.name], cwd=ROOT, check=True,
                   env=run_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return directory


def measure(room, route):
    directory = capture(room, route)
    first = directory/'r1.wram.bin'
    second = directory/'r2.wram.bin'
    if not first.is_file():
        # fine fixtures dump f<frame> names instead; skip the load phase
        frames = sorted((int(path.name[1:].split('.')[0]), path)
                        for path in directory.glob('f*.wram.bin'))
        if not frames:
            raise ValueError('no dump in '+directory.name)
        late = [path for number, path in frames if number >= 200]
        first, second = (late[0], late[-1]) if late else (frames[0][1], frames[-1][1])
    a = first.read_bytes()
    b = second.read_bytes()
    frame_a = a[0x13] | (a[0x14] << 8)
    frame_b = b[0x13] | (b[0x14] << 8)
    return {'mode': a[0x100], 'frame_first': frame_a,
            'frame_last': frame_b, 'frozen': frame_a == frame_b,
            'rom': ROM, 'dumps': [first.name, second.name]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-emu-freeze.json')
    args = parser.parse_args()
    report = {'scope': __doc__.strip(), 'rom': ROM, 'rom_sha256': sha((ROOT/ROM).read_bytes()),
              'rooms': {room: measure(room, route) for room, route in ROUTES.items()}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
    for room, entry in report['rooms'].items():
        print(room, 'mode', hex(entry['mode']), 'frame', entry['frame_first'],
              entry['frame_last'], 'frozen', entry['frozen'])
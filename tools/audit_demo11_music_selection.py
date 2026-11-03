#!/usr/bin/env python3
"""Audit the played song of every reviewed level with a console teleport.

The level music retarget recipe rewrites music objects that the tool can
identify.  Some rooms hold no music object, some hold several, and some need a
song that Demo 1-1 does not carry.  This tool enters each of those rooms with
the built-in console teleport and reads $0DDA, so the report records what the
build actually plays.

The teleport is an assisted fixture.  It proves the song selection of a direct
room entry.  It does not prove an audible match or an ordinary course route.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

DEFAULT_TARGET = 'demo11-music-retarget'
PROBE_DIR = ROOT / 'local/probes/music-audit'
REPORT = ROOT / 'local/reports/demo11-music-audit.json'
CAPTURE_PREFIX = 'd11-music-audit-'

HEADER = """# Console teleport fixture for room 0x{room:03X} (assisted entry).
turbo on
wait 600
press start 2
wait 180
press start 2
wait 900
press b 30
wait 180
press a 30
wait 180
poke 1f11 0606
poke 1f17 2801e8012801e801
poke 1f1f 12001e0012001e00
poke 100 0b
wait 240
poke d7e2 6a
press y 2
wait 240
poke 94 80004001
poke 19b8 {low:02x}
poke 19d8 {high:02x}
poke 88 0000
poke 71 06
wait 240
dump arrived
wait 180
dump later
quit
"""


def script(room):
    return HEADER.format(room=room, low=room & 0xFF, high=4 + (room >> 8))


def prepare(rooms):
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    for room in rooms:
        path = PROBE_DIR / f'room-{room:03X}.script'
        content = script(room)
        if path.exists() and path.read_text() != content:
            raise SystemExit(f'refusing to replace a different script: {path}')
        path.write_text(content)
    print(f'prepared {len(rooms)} scripts in {PROBE_DIR.relative_to(ROOT)}')


def run(rooms, target):
    failures = []
    for room in rooms:
        name = f'{CAPTURE_PREFIX}{room:03X}'
        directory = ROOT / 'local/captures' / name
        done = directory / 'later.wram.bin'
        if done.exists() and done.stat().st_size == 0x20000:
            print(f'{room:03X} already captured')
            continue
        if directory.exists():
            import shutil
            shutil.rmtree(directory)
        command = [sys.executable, str(ROOT / 'tools/m1.py'), 'native', '--target', target,
                   '--script', str(PROBE_DIR / f'room-{room:03X}.script'),
                   '--capture', name]
        try:
            subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, timeout=180)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            failures.append((f'{room:03X}', str(error)[:160]))
            print(f'{room:03X} failed: {str(error)[:120]}')
            continue
        print(f'{room:03X} captured')
    if failures:
        print('Failures:')
        for key, reason in failures:
            print(f'  {key}: {reason}')
    return failures


def sample(room, tag):
    path = ROOT / 'local/captures' / f'{CAPTURE_PREFIX}{room:03X}' / f'{tag}.wram.bin'
    if not path.exists() or path.stat().st_size != 0x20000:
        return None
    body = path.read_bytes()
    return {'mode': f'{body[0x100]:02X}',
            'room': f'{int.from_bytes(body[0x10b:0x10d], "little"):03X}',
            'song': f'{body[0x0dda]:02X}'}


def report(rooms, target):
    targets = {int(entry['room'], 16): entry
               for entry in json.loads((ROOT / 'config/music-level-targets.json').read_text())['entries']}
    recipe = json.loads((ROOT / 'config/restorations' / (target + '.json')).read_text())
    patched = {int(patch['role'].split()[1], 16) for patch in recipe['code_patches']}
    entries = []
    for room in rooms:
        entry = targets.get(room, {})
        arrived, later = sample(room, 'arrived'), sample(room, 'later')
        target = entry.get('target')
        # The first sample after arrival is the reliable one: a short jingle
        # can finish inside the later wait, and the field then reads FF.
        played = arrived['song'] if arrived else None
        if arrived is None:
            status = 'no-sample'
        elif arrived['mode'] != '14':
            status = 'mode-' + arrived['mode']
        elif target is None:
            status = 'target-unknown'
        elif played == target:
            status = 'correct'
        else:
            status = 'wrong'
        entries.append({'room': f'{room:03X}', 'reviewed_target': target,
                        'played': played, 'status': status,
                        'patched': room in patched, 'note': entry.get('note', ''),
                        'arrived': arrived, 'later': later})
    counts = {}
    for item in entries:
        counts[item['status']] = counts.get(item['status'], 0) + 1
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({'target': target, 'host': 'native',
                                  'kind': 'console-teleport-assisted-entry',
                                  'counts': counts, 'entries': entries}, indent=2) + '\n')
    width = max(len(item['room']) for item in entries)
    print(f"{'room':<{width}}  target  played  status            patched")
    for item in entries:
        print(f"{item['room']:<{width}}  {item['reviewed_target'] or '-':>6}  "
              f"{item['played'] or '-':>6}  {item['status']:<17} {item['patched']}")
    print(f'Report: {REPORT.relative_to(ROOT)}')
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run', 'report', 'all'))
    parser.add_argument('--rooms', nargs='+', required=True,
                        help='internal room numbers, for example 0AA')
    parser.add_argument('--target', default=DEFAULT_TARGET)
    args = parser.parse_args()
    rooms = sorted({int(value, 16) for value in args.rooms})
    if args.action in ('prepare', 'all'):
        prepare(rooms)
    if args.action in ('run', 'all'):
        failures = run(rooms, args.target)
        if failures:
            return 1
    if args.action in ('report', 'all'):
        report(rooms, args.target)
    return 0


if __name__ == '__main__':
    sys.exit(main())

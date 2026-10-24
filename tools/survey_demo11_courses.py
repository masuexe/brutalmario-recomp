#!/usr/bin/env python3
"""Survey Demo 1-1 course loading with a bounded map-node level override.

The survey enters each requested translevel from the Star World lower-left map 6
node. The node's overworld tile level byte is overwritten with the target
translevel, so no donor map route is claimed. Each capture starts from a fresh
save. The report records the load result and the room mapping.

Actions:
  prepare  Write the probe scripts for a translevel range.
  run      Run the reference host for each prepared script.
  report   Summarize the captures into a JSON report and a text table.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-star-bgm'
MAP = 6
NODE_X = 0x128
NODE_Y = 0x1E8
PROBE_DIR = ROOT / 'local/probes/demo11-course-survey'
CAPTURE_PREFIX = 'd11-survey-'
REPORT = ROOT / 'local/reports/demo11-course-survey.json'


def node_tile_address(x, y):
    return 0xD400 + (y >> 4) * 16 + ((x >> 4) & 15) + (x >> 8) * 0x200


def startup():
    return (ROOT / 'recomp/inputs/m1-route.script').read_text().split('dump map')[0]


def script_for(translevel):
    coordinates = (NODE_X.to_bytes(2, 'little') + NODE_Y.to_bytes(2, 'little')) * 2
    tiles = ((NODE_X >> 4).to_bytes(2, 'little') + (NODE_Y >> 4).to_bytes(2, 'little')) * 2
    address = node_tile_address(NODE_X, NODE_Y)
    return (startup() +
            '# Survey: override the map 6 lower-left node level and enter it.\n'
            f'poke 1f11 {MAP:02x}{MAP:02x}\n'
            f'poke 1f17 {coordinates.hex()}\n'
            f'poke 1f1f {tiles.hex()}\n'
            'poke 0100 0b\nwait 240\n'
            f'poke {address:x} {translevel & 0xff:02x}\n'
            'press y 2\n'
            'wait 240\ndump entry240\n'
            'wait 360\ndump entry600\n'
            'quit\n')


def prepare(first, last):
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for translevel in range(first, last + 1):
        path = PROBE_DIR / f'course-{translevel:03X}.script'
        content = script_for(translevel)
        if path.exists() and path.read_text() != content:
            raise SystemExit(f'refusing to overwrite a different script: {path}')
        path.write_text(content)
        total += 1
    print(f'Prepared {total} scripts in {PROBE_DIR.relative_to(ROOT)}')


def capture_name(prefix, translevel):
    return f'{prefix}{translevel:03X}'


def run(first, last, target=TARGET, prefix=CAPTURE_PREFIX):
    failures = []
    for translevel in range(first, last + 1):
        script = PROBE_DIR / f'course-{translevel:03X}.script'
        if not script.exists():
            failures.append((f'{translevel:03X}', 'missing script'))
            continue
        name = capture_name(prefix, translevel)
        directory = ROOT / 'local/captures' / name
        if (directory / 'entry600.wram.bin').exists():
            print(f'{translevel:03X} already captured')
            continue
        if directory.exists():
            import shutil
            shutil.rmtree(directory)
        command = [sys.executable, str(ROOT / 'tools/m1.py'), 'reference',
                   '--target', target, '--script', str(script), '--capture', name]
        try:
            subprocess.run(command, cwd=ROOT, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                           timeout=180)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            failures.append((f'{translevel:03X}', str(error)[:160]))
            print(f'{translevel:03X} failed: {str(error)[:120]}')
            continue
        print(f'{translevel:03X} captured')
    if failures:
        print('Failures:')
        for key, reason in failures:
            print(f'  {key}: {reason}')
    return 1 if failures else 0


def sample(directory, tag):
    path = directory / f'{tag}.wram.bin'
    if not path.exists():
        return None
    body = path.read_bytes()
    return {'mode': f'{body[0x100]:02X}',
            'room': f'{int.from_bytes(body[0x10b:0x10d], "little"):03X}',
            'translevel': f'{body[0x13bf]:02X}',
            'player_x': int.from_bytes(body[0x94:0x96], 'little'),
            'player_y': int.from_bytes(body[0x96:0x98], 'little'),
            'lives_minus_one': body[0x0dbe]}


def report(first, last, target=TARGET, prefix=CAPTURE_PREFIX, report_path=REPORT):
    entries = []
    for translevel in range(first, last + 1):
        directory = ROOT / 'local/captures' / capture_name(prefix, translevel)
        entry = {'translevel': f'{translevel:03X}',
                 'capture': str(directory.relative_to(ROOT))}
        if not directory.exists():
            entry['result'] = 'missing'
        else:
            receipt = directory / 'receipt.json'
            if receipt.exists():
                entry['rom_sha256'] = json.loads(receipt.read_text())['rom_sha256']
            early = sample(directory, 'entry240')
            late = sample(directory, 'entry600')
            entry['samples'] = {'entry240': early, 'entry600': late}
            if late is None:
                entry['result'] = 'no-sample'
            elif late['mode'] == '14':
                entry['result'] = 'playable'
            elif late['mode'] == '12':
                entry['result'] = 'mario-start-stall'
            else:
                entry['result'] = f"mode-{late['mode']}"
        entries.append(entry)
        late = entry.get('samples', {}).get('entry600') or {}
        print(f"{entry['translevel']} {entry['result']:20s} "
              f"room={late.get('room', '-')} mode={late.get('mode', '-')}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({'target': target, 'host': 'reference',
                                       'first': f'{first:03X}', 'last': f'{last:03X}',
                                       'entries': entries}, indent=2) + '\n')
    print(f'Report: {report_path.relative_to(ROOT)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'report'])
    parser.add_argument('--first', type=lambda text: int(text, 0), default=0x001)
    parser.add_argument('--last', type=lambda text: int(text, 0), default=0x020)
    parser.add_argument('--target', default=TARGET)
    parser.add_argument('--prefix', default=CAPTURE_PREFIX)
    parser.add_argument('--report', type=Path, default=REPORT)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.first, args.last)
    elif args.action == 'run':
        raise SystemExit(run(args.first, args.last, args.target, args.prefix))
    else:
        report(args.first, args.last, args.target, args.prefix, args.report)


if __name__ == '__main__':
    main()

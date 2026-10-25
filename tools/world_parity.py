#!/usr/bin/env python3
"""Run a reference/native parity triage for one world.

For each room in the world, the tool runs the existing survey script on both
hosts when the captures are missing, then compares the matched dumps:

- game mode, level, player position and lives,
- the sprite status and number arrays,
- the framebuffer on a 5-bit grid.

A large disagreement marks a candidate recomp defect. Equal samples mark
parity only for the sampled scene.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE_DIR = ROOT / 'local/probes/demo11-course-survey'


def load(path):
    return json.loads(Path(path).read_text())


def scene(directory, tag):
    wram = (directory / (tag + '.wram.bin')).read_bytes()
    info = load(directory / (tag + '.info.json'))
    framebuffer = (directory / (tag + '.fb.bgrx')).read_bytes()
    return {
        'frame': info['frame'],
        'mode': wram[0x100],
        'level': int.from_bytes(wram[0x10B:0x10D], 'little'),
        'player_x': int.from_bytes(wram[0x94:0x96], 'little'),
        'player_y': int.from_bytes(wram[0x96:0x98], 'little'),
        'lives': wram[0xDBE],
        'sprite_status': wram[0x14C8:0x14D4].hex(),
        'sprite_numbers': wram[0x161A:0x1626].hex(),
        'wram': wram,
        'framebuffer': framebuffer,
    }


def compare(left, right):
    result = {'frame_equal': left['frame'] == right['frame'],
              'mode': (left['mode'], right['mode']),
              'level': (left['level'], right['level']),
              'player': ((left['player_x'], left['player_y']),
                         (right['player_x'], right['player_y'])),
              'lives': (left['lives'], right['lives']),
              'sprite_status_equal': left['sprite_status'] == right['sprite_status'],
              'sprite_numbers_equal': left['sprite_numbers'] == right['sprite_numbers'],
              'wram_different_bytes': sum(a != b for a, b in zip(left['wram'], right['wram']))}
    width, height = 256, 224
    expected = width * height * 4
    left_fb, right_fb = left['framebuffer'], right['framebuffer']
    if len(left_fb) != expected or len(right_fb) != expected:
        result['framebuffer'] = 'size mismatch'
        return result
    exact = 0
    small = 0
    mid = 0
    large = 0
    for i in range(0, expected, 4):
        delta = 0
        for k in range(3):
            difference = abs(left_fb[i + k] - right_fb[i + k])
            if difference > delta:
                delta = difference
        if delta == 0:
            exact += 1
        elif delta <= 16:
            small += 1
        elif delta <= 64:
            mid += 1
        else:
            large += 1
    result['rgb5_different_pixels'] = sum(
        any(left_fb[i + k] >> 3 != right_fb[i + k] >> 3 for k in range(3))
        for i in range(0, expected, 4))
    result['delta_histogram'] = {'exact': exact, 'small': small, 'mid': mid, 'large': large}
    return result


def classify(tag, rows):
    state = rows['entry240']
    mismatches = []
    if not state['frame_equal']:
        mismatches.append('frame')
    if state['mode'][0] != state['mode'][1]:
        mismatches.append('mode')
    if state['level'][0] != state['level'][1]:
        mismatches.append('level')
    if abs(state['player'][0][0] - state['player'][1][0]) > 8 or abs(state['player'][0][1] - state['player'][1][1]) > 8:
        mismatches.append('player')
    if state['lives'][0] != state['lives'][1]:
        mismatches.append('lives')
    if not state['sprite_status_equal']:
        mismatches.append('sprite-status')
    if not state['sprite_numbers_equal']:
        mismatches.append('sprite-numbers')
    if state['rgb5_different_pixels'] > 500:
        mismatches.append('framebuffer')
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', required=True)
    parser.add_argument('--target', default='demo11-fix-batch-p')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    world_map = load(ROOT / 'config/world-map.json')['worlds']
    if args.world not in world_map:
        raise SystemExit('unknown world')
    world = world_map[args.world]
    index = load(ROOT / 'config/demo11-level-index.json')['entries']
    by_level = {}
    for entry in index:
        by_level.setdefault(entry['level'], []).append(entry)

    report = {'world': args.world, 'name': world['name'], 'target': args.target, 'rooms': {}}
    for room_hex in world['rooms']:
        entries = by_level.get(room_hex, [])
        if not entries:
            report['rooms'][room_hex] = {'status': 'no-entry'}
            continue
        translevel = entries[0]['translevel']
        script = PROBE_DIR / ('course-%s.script' % translevel)
        if not script.exists():
            report['rooms'][room_hex] = {'status': 'no-script', 'translevel': translevel}
            continue
        captures = {}
        for host in ('reference', 'native'):
            capture_name = 'world-%s-%s-%s' % (args.world, translevel, host)
            directory = ROOT / 'local/captures' / capture_name
            info_path = directory / 'entry240.info.json'
            ready = (directory / 'entry240.wram.bin').exists() and info_path.exists()                 and info_path.stat().st_size > 0
            need = args.force or not ready
            if need:
                if directory.exists():
                    import shutil
                    shutil.rmtree(directory)
                result = subprocess.run([sys.executable, str(ROOT / 'tools/m1.py'), host,
                                         '--target', args.target, '--script', str(script),
                                         '--capture', capture_name],
                                        cwd=ROOT, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    captures[host] = None
                    continue
            captures[host] = directory
        if captures.get('reference') is None or captures.get('native') is None:
            report['rooms'][room_hex] = {'status': 'capture-failed', 'translevel': translevel}
            continue
        rows = {}
        try:
            for tag in ('entry240', 'entry600'):
                left = scene(captures['reference'], tag)
                right = scene(captures['native'], tag)
                rows[tag] = compare(left, right)
        except (OSError, ValueError, KeyError) as error:
            report['rooms'][room_hex] = {'status': 'dump-missing', 'translevel': translevel,
                                         'error': str(error)[:120]}
            continue
        mismatches = classify(translevel, rows)
        report['rooms'][room_hex] = {
            'status': 'divergence' if mismatches else 'parity',
            'translevel': translevel,
            'entry240': rows['entry240'],
            'entry600': rows['entry600'],
            'mismatches': mismatches,
        }

    output = ROOT / 'local/reports' / ('world-parity-%s.json' % args.world)
    output.write_text(json.dumps(report, indent=2) + '\n')
    for room_hex, row in report['rooms'].items():
        if row['status'] == 'parity':
            print(' room', room_hex, 'parity', 'translevel', row['translevel'])
        else:
            print(' room', room_hex, row['status'], row.get('translevel'),
                  row.get('mismatches', ''), 'fb5', row.get('entry240', {}).get('rgb5_different_pixels'))
    print('report:', output.relative_to(ROOT))


if __name__ == '__main__':
    main()

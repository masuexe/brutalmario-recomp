#!/usr/bin/env python3
"""Compare the full gap target with the baseline on unchanged routes.

The target adds 33 custom sprite records and 35 packs. This tool runs the same
route script on the baseline target and on the gap target, and compares every
dump. It shows that the added packs do not change an unchanged route. It does
not claim movement or a course pass.
"""
import argparse
import json
import subprocess
from pathlib import Path

from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
BASE = 'demo11-native-sprite9e'
GAP = 'demo11-native-sprite-full'
ROUTES = ('demo11-s004-entry', 'demo11-sky-visuals', 'demo11-forest-attack')


def capture(target, route):
    directory = ROOT/'local/captures'/f'gapregress-{target[-6:]}-{route}'
    if directory.is_dir():
        return directory
    script = ROOT/'recomp/inputs'/(route+'.script')
    if not script.is_file():
        raise ValueError('missing route script '+route)
    subprocess.run(['python3', 'tools/m1.py', '--target', target, 'native',
                    '--script', str(script.relative_to(ROOT)),
                    '--capture', directory.name], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return directory


def compare(route, gap_target=None):
    base = capture(BASE, route)
    gap = capture(gap_target or GAP, route)
    names = sorted({path.name for path in base.glob('*.wram.bin')} |
                   {path.name for path in gap.glob('*.wram.bin')})
    if not names:
        raise ValueError('no dump in route '+route)
    points = {}
    for name in names:
        left, right = base/name, gap/name
        if not left.is_file() or not right.is_file():
            points[name] = {'equal': False, 'note': 'dump absent'}
            continue
        a, b = left.read_bytes(), right.read_bytes()
        points[name] = {'equal': a == b, 'size': len(a),
                        'baseline_sha256': sha(a), 'gap_sha256': sha(b)}
    equal = sum(1 for entry in points.values() if entry['equal'])
    return {'route': route, 'points': points, 'equal': equal,
            'total': len(points)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--routes', nargs='+', default=list(ROUTES))
    parser.add_argument('--gap', default=GAP)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'local/reports/native-sprite-full-regression.json')
    args = parser.parse_args()
    report = {'scope': __doc__.strip(), 'baseline': BASE, 'gap': args.gap,
              'routes': {route: compare(route, args.gap) for route in args.routes}}
    total = sum(entry['total'] for entry in report['routes'].values())
    equal = sum(entry['equal'] for entry in report['routes'].values())
    report['total'] = total
    report['equal'] = equal
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.gap != GAP:
        args.output = args.output.with_name(args.output.stem+'-'+args.gap.split('-')[-1]+'.json')
    args.output.write_text(json.dumps(report, indent=2)+chr(10))
    print(args.output, sha(args.output.read_bytes()))
    print('equal', equal, 'of', total)
    for route, entry in report['routes'].items():
        print(route, entry['equal'], 'of', entry['total'])
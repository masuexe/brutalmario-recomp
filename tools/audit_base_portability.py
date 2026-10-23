#!/usr/bin/env python3
"""Compare base ROMs for restoration portability.

Read-only. For every restoration recipe, checks whether its pinned patch sites
still hold their expected `before` bytes in a candidate base ROM. That measures how
much of the restoration chain would have to be re-derived if the recipient base
changed, without building or running anything.
"""
import glob, json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom

ROOT = Path(__file__).resolve().parents[1]


def read(path, size):
    off = lorom(int(path, 16) if isinstance(path, str) else path)
    return off


def main():
    versions = {v['id']: v for v in json.loads((ROOT / 'config/content-versions.json').read_text())['versions']}
    bodies = {}
    for name in ('demo-only-1', 'demo-1-1'):
        body = (ROOT / 'local/content-versions' / name / 'rom.sfc').read_bytes()
        verify(body, versions[name]['output'], name)
        bodies[name] = body
    rows, details = [], []
    for path in sorted(glob.glob(str(ROOT / 'config/restorations/*.json'))):
        cfg = json.loads(Path(path).read_text())
        sites = []
        for patch in cfg.get('code_patches', []):
            if patch.get('before'):
                sites.append((str(patch['address']), patch['before']))
        sprite = cfg.get('custom_sprite')
        if sprite and sprite.get('before'):
            sites.append((str(sprite['destination_record_address']), sprite['before']))
        agrees = differs = 0
        for address, before in sites:
            size = len(bytes.fromhex(before))
            try:
                off = lorom(int(address, 16))
            except ValueError:
                differs += 1
                continue
            state = {}
            for name, body in bodies.items():
                state[name] = body[off:off + size].hex()
            if state['demo-1-1'] == before:
                agrees += 1
            else:
                differs += 1
                details.append({'recipe': cfg['id'], 'address': address, 'before': before,
                                'demo_1_1': state['demo-1-1'], 'demo_only_1': state['demo-only-1']})
        rows.append({'recipe': cfg['id'], 'sites': len(sites),
                     'agrees_on_demo_1_1': agrees, 'differs_on_demo_1_1': differs})
    report = {
        'scope': __doc__.strip(),
        'base_checked': 'demo-1-1',
        'reference': 'demo-only-1',
        'recipes': rows,
        'details': details,
        'limits': ['Patch-site agreement is a lower bound on porting cost: a site can',
                   'coincidentally match while neighbouring data or allocations differ.',
                   'Allocation space, asset pins and qualification captures are not',
                   'checked here.']}
    out = ROOT / 'local/reports/base-portability.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    total = sum(r['sites'] for r in rows)
    agree = sum(r['agrees_on_demo_1_1'] for r in rows)
    print('patch sites checked: %d, agree on demo-1-1: %d (%.0f%%)' % (total, agree, 100.0 * agree / total if total else 0))
    for r in rows:
        if r['sites']:
            print('  %-26s %2d/%2d agree' % (r['recipe'], r['agrees_on_demo_1_1'], r['sites']))
    print('report:', out.relative_to(ROOT))


if __name__ == '__main__':
    main()
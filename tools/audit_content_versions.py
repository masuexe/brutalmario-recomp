#!/usr/bin/env python3
"""Compare pinned local versions without inferring chronology or playability.

Optional ROM copies are isolated under local/content-versions/. Existing
accepted targets and user inputs are never overwritten. Run from any cwd.
"""
import argparse
import json
from pathlib import Path
import re

from inventory import digest, rom_info
from prepare_rom import prepare_bytes, verify, write_new_or_verify

ROOT = Path(__file__).resolve().parents[1]
BANK_SIZE = 0x8000


def audit(manifest, base_path, *, prepare=False):
    if manifest['schema'] != 1:
        raise ValueError('unsupported content-version manifest')
    base = base_path.read_bytes()
    verify(base, manifest['base'], 'base ROM')
    patch_root = (ROOT / manifest['patch_root']).resolve()
    images, pins = {}, {}
    for version in manifest['versions']:
        key = version['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', key) or key in images:
            raise ValueError('invalid or duplicate version ID')
        patch = patch_root / version['ips_path']
        if patch_root not in patch.resolve().parents:
            raise ValueError('patch path leaves the configured input tree')
        pin = dict(version, base=manifest['base'], target=key)
        body = prepare_bytes(base, patch.read_bytes(), pin)
        readme = version.get('bundled_readme')
        if readme and digest((patch_root / readme['path']).read_bytes()) != readme['sha256']:
            raise ValueError('bundled readme differs from pinned bytes: ' + key)
        images[key], pins[key] = body, pin
    baselines = [v['id'] for v in manifest['versions'] if v['role'] == 'recipient-baseline']
    versions = []
    for version in manifest['versions']:
        key = version['id']
        body = images[key]
        banks = [digest(body[i:i+BANK_SIZE]) for i in range(0, len(body), BANK_SIZE)]
        comparisons = {}
        for baseline in baselines:
            reference = images[baseline]
            other_banks = [digest(reference[i:i+BANK_SIZE])
                           for i in range(0, len(reference), BANK_SIZE)]
            comparisons[baseline] = {
                'different_bytes_at_same_offset': sum(a != b for a, b in zip(body, reference))
                                                 + abs(len(body) - len(reference)),
                'identical_32k_banks_at_same_offset': sum(a == b for a, b in zip(banks, other_banks)),
                'scope': 'Whole-image byte layout only; relocated assets count as differences.',
            }
        record = dict(version, rom=rom_info(body), comparisons=comparisons)
        if prepare:
            directory = ROOT / 'local/content-versions' / key
            write_new_or_verify(directory / 'rom.sfc', body)
            encoded = (json.dumps(pins[key], indent=2) + '\n').encode()
            write_new_or_verify(directory / 'input-manifest.json', encoded)
            record['isolated_rom'] = str((directory / 'rom.sfc').relative_to(ROOT))
        versions.append(record)
    return {
        'scope': manifest['scope'],
        'base_sha256': digest(base),
        'versions': versions,
        'limits': [
            'Donor +512 alignment is a structural candidate, not a gameplay qualification.',
            'Whole-ROM similarity does not identify matching rooms or engine compatibility.',
            'No level, graphics, sprite, music or ASM data is transplanted by this tool.',
            'No authoritative release chronology or latest official version is established.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path,
                        default=ROOT.parent / 'roms/Super Mario World (U) [!].smc')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'config/content-versions.json')
    parser.add_argument('--prepare-local-roms', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'local/reports/content-versions.json')
    args = parser.parse_args()
    try:
        if not args.output.resolve().is_relative_to((ROOT / 'local/reports').resolve()):
            raise ValueError('report output must remain under local/reports')
        report = audit(json.loads(args.manifest.read_text()), args.base,
                       prepare=args.prepare_local_roms)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        for item in report['versions']:
            diff = item['comparisons']['demo-only-1']
            print(f"{item['id']}: {item['output']['size']} bytes; "
                  f"{diff['different_bytes_at_same_offset']:,} bytes differ from demoOnly1; "
                  f"{diff['identical_32k_banks_at_same_offset']}/128 banks identical")
        print('Report:', args.output)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f'content audit: {exc}\n')


if __name__ == '__main__':
    main()

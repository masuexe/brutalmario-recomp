#!/usr/bin/env python3
"""Build the pinned Demo 1-1 locally without modifying any existing file."""
import argparse
import json
import os
from pathlib import Path
import tempfile

from inventory import digest, ips_info, rom_info

PROJECT = Path(__file__).resolve().parents[1]


def verify(data, expected, label):
    if len(data) != expected['size'] or digest(data) != expected['sha256']:
        raise ValueError(f'{label} size/SHA-256 does not match pinned input manifest')


def prepare_bytes(base, ips, manifest):
    verify(base, manifest['base'], 'base ROM')
    verify(ips, manifest['ips'], 'IPS')
    prefix = manifest['copier_prefix_bytes']
    info, records = ips_info(ips)
    limit = manifest['output']['size'] + prefix
    if info['max_end_exclusive'] > limit:
        raise ValueError('IPS writes beyond pinned output extent')
    if info['explicit_final_size'] not in (None, limit):
        raise ValueError('IPS final size conflicts with pinned output extent')
    image = bytearray(bytes(prefix) + base)
    image.extend(bytes(limit - len(image)))
    for offset, payload, _ in records:
        image[offset:offset + len(payload)] = payload
    output = bytes(image[prefix:])
    verify(output, manifest['output'], 'target ROM')
    return output


def write_new_or_verify(output, data):
    """Atomically publish a new file; never overwrite an existing destination."""
    if output.is_symlink():
        raise ValueError('refusing a symlink output')
    if output.exists():
        if output.read_bytes() != data:
            raise ValueError('output exists with different contents; refusing overwrite')
        return 'verified_existing'
    output.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.rom-', delete=False) as temp:
            name = temp.name
            temp.write(data)
            temp.flush()
            os.fsync(temp.fileno())
        os.link(name, output)
    finally:
        if name is not None:
            Path(name).unlink()
    return 'created'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--ips', type=Path, default=PROJECT.parent / 'patches/1-1.ips')
    parser.add_argument('--output', type=Path, default=PROJECT / 'local/roms/demo-1-1.sfc')
    parser.add_argument('--manifest', type=Path, default=PROJECT / 'config/inputs.json',
                        help='pinned input/output manifest; alternate versions require an explicit output path')
    args = parser.parse_args()
    try:
        if args.output.resolve() in (args.base.resolve(), args.ips.resolve()):
            raise ValueError('output must differ from input paths')
        manifest = json.loads(args.manifest.read_text())
        base, ips = args.base.read_bytes(), args.ips.read_bytes()
        data = prepare_bytes(base, ips, manifest)
        status = write_new_or_verify(args.output, data)
        print(json.dumps({'target': manifest['target'], 'status': status,
                          'base': str(args.base), 'ips': str(args.ips),
                          'output': str(args.output), 'rom': rom_info(data)}, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'prepare_rom: {exc}\n')


if __name__ == '__main__':
    main()

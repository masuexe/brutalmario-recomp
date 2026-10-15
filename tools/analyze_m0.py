#!/usr/bin/env python3
"""Summarize supplied M0 inputs; virtual IPS application only, no ROM output.

Run after inventory.py. Paths reflect this project's supplied sibling layout.
"""
from collections import Counter
import json
from pathlib import Path

from inventory import digest, ips_info, rom_info


def signature_offsets(body):
    signature = bytes.fromhex('8ff1ff7fa91f6b8ff3ff7f')
    start = 0
    while True:
        offset = body.find(signature, start)
        if offset < 0:
            return
        yield offset
        start = offset + 1


def preview(base, patch, prefix):
    info, records = ips_info(patch)
    image = bytearray(bytes(prefix) + base)
    for offset, payload, _ in records:
        end = offset + len(payload)
        if end > len(image):
            image.extend(bytes(end - len(image)))
        image[offset:end] = payload
    size = info['explicit_final_size']
    if size is not None:
        if size > len(image):
            image.extend(bytes(size - len(image)))
        del image[size:]
    return bytes(image[prefix:])


def main():
    inventory = json.loads(Path('local/reports/inventory.json').read_text())
    archive_matches = []
    for root in inventory['inputs']:
        hashes = {f['sha256'] for f in root['files']}
        for f in root['files']:
            if 'zip' in f:
                members = [m for m in f['zip']['members'] if 'sha256' in m]
                archive_matches.append({'path': root['root'] + '/' + f['path'],
                                        'hashed_members': len(members),
                                        'members_with_loose_hash_match': sum(m['sha256'] in hashes for m in members)})
    ref = Path('../references/drive-download-20261015T041215Z-1-001')
    roots = {'data': ref / 'data/data', 'data1': ref / 'data1', 'data2': ref / 'data2'}
    trees, packages = {}, {}
    for label, root in roots.items():
        files = {p.relative_to(root).as_posix(): p.read_bytes()
                 for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()}
        trees[label] = {k.replace('sprites - kopie/', 'sprites/'): v for k, v in files.items()}
        missing = []
        for name, data in files.items():
            if not name.endswith('.cfg'):
                continue
            for line in data.decode('ascii', errors='replace').splitlines():
                if line.strip().lower().endswith('.asm'):
                    target = (Path(name).parent / line.strip()).as_posix()
                    if target not in files:
                        missing.append({'cfg': name, 'target': target,
                                        'case_only': target.lower() in {k.lower() for k in files}})
        packages[label] = {'file_count': len(files),
                           'extensions': dict(Counter(Path(k).suffix for k in files)),
                           'missing_exact_cfg_asm_targets': missing}
    differences = []
    for a, b in [('data', 'data1'), ('data1', 'data2')]:
        aa, bb = trees[a], trees[b]
        common = set(aa) & set(bb)
        differences.append({'a': a, 'b': b,
                            'equal': sum(aa[k] == bb[k] for k in common),
                            'changed': sorted(k for k in common if aa[k] != bb[k]),
                            'only_a': sorted(set(aa) - set(bb)),
                            'only_b': sorted(set(bb) - set(aa))})
    roms = list(Path('../roms').glob('*.smc')) + list(Path('../roms').glob('*.sfc'))
    if len(roms) != 1:
        raise ValueError('expected exactly one local base ROM')
    base = roms[0].read_bytes()
    if len(base) != 0x80000 or digest(base) != '0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b':
        raise ValueError('unexpected base ROM; review before reusing preview assumptions')
    previews = []
    for patch in sorted(Path('../patches').rglob('*.ips')):
        variants = []
        for prefix in (0, 512):
            body = preview(base, patch.read_bytes(), prefix)
            # Interpret the caller-selected boundary, not a second size heuristic.
            header = rom_info(body[:0x10000])['headers'][0]
            variants.append({'prefix_before_patch': prefix, 'body_size': len(body),
                             'body_sha256': digest(body), 'lorom_header': header,
                             'body_sum16': f'{sum(body) & 65535:04x}',
                             'levelasm_stub_signature_offsets': list(signature_offsets(body))})
        previews.append({'patch': patch.as_posix(), 'variants': variants})
    print(json.dumps({'archive_loose_hash_matches': archive_matches, 'source_packages': packages,
                      'source_differences': differences, 'virtual_patch_previews': previews}, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Read-only local archive/IPS/ROM inventory; JSON goes to stdout, never extracts.

No third-party packages. ZIP members are hashed only within fixed resource limits.
Paths in reports are relative to each input root. Original files are never changed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
import zlib

MAX_MEMBER = 64 * 1024 * 1024
MAX_ARCHIVE = 256 * 1024 * 1024
MAX_ENTRIES = 10000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def ips_info(data):
    """Strict IPS parser, retaining records internally for bounded virtual previews."""
    if not data.startswith(b'PATCH'):
        raise ValueError('missing PATCH signature')
    pos, records, write_bytes = 5, [], 0
    while True:
        if pos + 3 > len(data):
            raise ValueError('missing EOF')
        offset = data[pos:pos + 3]
        pos += 3
        if offset == b'EOF':
            break
        if pos + 2 > len(data):
            raise ValueError('truncated record size')
        size = int.from_bytes(data[pos:pos + 2], 'big')
        pos += 2
        start = int.from_bytes(offset, 'big')
        if size:
            write_bytes += size
            if write_bytes > MAX_ARCHIVE:
                raise ValueError('IPS expanded write budget exceeded')
            if pos + size > len(data):
                raise ValueError('truncated data')
            payload = data[pos:pos + size]
            pos += size
            records.append((start, payload, False))
        else:
            if pos + 3 > len(data):
                raise ValueError('truncated RLE')
            size = int.from_bytes(data[pos:pos + 2], 'big')
            if not size:
                raise ValueError('zero-length RLE')
            write_bytes += size
            if write_bytes > MAX_ARCHIVE:
                raise ValueError('IPS expanded write budget exceeded')
            records.append((start, data[pos + 2:pos + 3] * size, True))
            pos += 3
    tail = data[pos:]
    if len(tail) not in (0, 3):
        raise ValueError('unexpected bytes after EOF')
    end = max((o + len(b) for o, b, _ in records), default=0)
    info = {
        'records': len(records), 'rle_records': sum(r for _, _, r in records),
        'write_bytes_including_overlaps': sum(len(b) for _, b, _ in records),
        'min_offset': min((o for o, _, _ in records), default=None),
        'max_end_exclusive': end,
        'explicit_final_size': int.from_bytes(tail, 'big') if tail else None,
        'warning': 'IPS has no base ROM hash; write extent alone is not final ROM size',
    }
    return info, records


def rom_info(data):
    prefix = 512 if len(data) % 0x8000 == 512 else 0
    body = data[prefix:]
    result = {'size': len(data), 'candidate_copier_header': prefix,
              'body_sha256': digest(body), 'body_crc32': f'{zlib.crc32(body):08x}',
              'body_sum16': f'{sum(body) & 65535:04x}', 'headers': []}
    for mapping, offset in [('LoROM', 0x7fc0), ('HiROM', 0xffc0), ('ExHiROM', 0x40ffc0)]:
        h = body[offset:offset + 64]
        if len(h) != 64:
            continue
        checksum = int.from_bytes(h[30:32], 'little')
        complement = int.from_bytes(h[28:30], 'little')
        result['headers'].append({
            'candidate': mapping, 'offset': offset,
            'title': h[:21].decode('ascii', errors='replace'),
            'map_mode': f'{h[21]:02x}', 'cartridge_type': f'{h[22]:02x}',
            'rom_size_exponent': h[23], 'sram_size_exponent': h[24],
            'region': h[25], 'revision': h[27],
            'checksum': f'{checksum:04x}', 'complement': f'{complement:04x}',
            'checksum_pair_valid': checksum ^ complement == 0xffff,
            'reset_vector': f'{int.from_bytes(h[60:62], "little"):04x}',
        })
    return result


def zip_info(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ENTRIES:
            raise ValueError('ZIP entry limit exceeded')
        total = sum(i.file_size for i in entries)
        result = {'entries': len(entries), 'uncompressed_bytes': total, 'members': []}
        budget, names = 0, set()
        for i in entries:
            name = i.filename.replace('\\', '/')
            mode = i.external_attr >> 16
            unsafe = (name.startswith('/') or '..' in PurePosixPath(name).parts
                      or bool(re.match(r'^[a-zA-Z]:', name)) or stat.S_ISLNK(mode))
            item = {'name': i.filename, 'size': i.file_size,
                    'compressed_size': i.compress_size, 'unsafe_path_or_symlink': unsafe,
                    'duplicate_name': name in names}
            names.add(name)
            if not i.is_dir():
                if unsafe or i.flag_bits & 1 or i.file_size > MAX_MEMBER or budget + i.file_size > MAX_ARCHIVE:
                    item['skipped'] = 'path, encryption, or resource limit'
                else:
                    with archive.open(i) as source:
                        data = source.read(MAX_MEMBER + 1)
                    if len(data) > MAX_MEMBER or len(data) != i.file_size:
                        raise ValueError('ZIP member size mismatch')
                    budget += len(data)
                    item['sha256'] = digest(data)
                    if name.lower().endswith('.ips'):
                        item['ips'] = ips_info(data)[0]
            result['members'].append(item)
        return result


def scan(root):
    files, errors = [], []
    # Do not follow symlinks, including directories, into unrelated input trees.
    def walk(directory):
        for path in sorted(directory.iterdir()):
            if path.is_symlink():
                continue
            if path.is_dir():
                yield from walk(path)
            elif path.is_file():
                yield path
    for path in walk(root):
        item = {'path': path.relative_to(root).as_posix(), 'size': path.stat().st_size,
                'extension': path.suffix.lower()}
        sha = hashlib.sha256()
        with path.open('rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                sha.update(block)
        item['sha256'] = sha.hexdigest()
        try:
            if path.suffix.lower() == '.zip':
                item['zip'] = zip_info(path)
            elif path.suffix.lower() in ('.ips', '.sfc', '.smc'):
                if item['size'] > MAX_MEMBER:
                    raise ValueError('binary input size limit exceeded')
                data = path.read_bytes()
                item['ips' if path.suffix.lower() == '.ips' else 'rom'] = (
                    ips_info(data)[0] if path.suffix.lower() == '.ips' else rom_info(data))
        except (ValueError, OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
            item['error'] = str(exc)
            errors.append(item['path'])
        files.append(item)
    return {'root': root.as_posix(), 'file_count': len(files),
            'extensions': dict(sorted(Counter(i['extension'] for i in files).items())),
            'errors': errors, 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roots', nargs='+', type=Path)
    args = parser.parse_args()
    for root in args.roots:
        if not root.is_dir() or root.is_symlink():
            parser.error(f'not a regular directory: {root}')
    results = [scan(root) for root in args.roots]
    print(json.dumps({'schema': 1, 'inputs': results}, ensure_ascii=True, indent=2))
    return int(any(r['errors'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())

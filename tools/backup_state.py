#!/usr/bin/env python3
"""Snapshot the restoration state so a migration can be reverted.

Copies every recipe-backed restoration ROM, the native build receipts and binaries,
and the practice-save tree into `local/backups/<label>-<timestamp>/`, with a JSON
manifest of SHA-256 identities and the current git HEAD. Read-only with respect to
the live tree; nothing is deleted or moved.
"""
import argparse, hashlib, json, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def git_head():
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    stamp = time.strftime('%Y%m%d-%H%M%S')
    destination = ROOT / 'local/backups' / ('%s-%s' % (args.label, stamp))
    if destination.exists():
        raise SystemExit('backup directory already exists: %s' % destination)
    destination.mkdir(parents=True)
    manifest = {'label': args.label, 'created': stamp, 'git_head': git_head(), 'roms': {}, 'binaries': {}}

    recipes = sorted((ROOT / 'config/restorations').glob('*.json'))
    for recipe in recipes:
        config = json.loads(recipe.read_text())
        target = config['id']
        rom = ROOT / 'local/restoration' / target / 'rom.sfc'
        if not rom.is_file():
            continue
        copy = destination / 'roms' / (target + '.sfc')
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(rom, copy)
        manifest['roms'][target] = {'sha256': sha(copy), 'bytes': copy.stat().st_size}
        build = ROOT / 'local/build' / target
        receipt = build / 'm1-build.json'
        if receipt.is_file():
            info = json.loads(receipt.read_text())
            binary = build / info.get('binary_name', '') if info.get('binary_name') else None
            candidates = [p for p in build.iterdir() if p.is_file() and p.suffix == '' and p.stat().st_size > 100000] if build.is_dir() else []
            record = {'receipt': json.loads(receipt.read_text())}
            if candidates:
                source = candidates[0]
                copy_binary = destination / 'binaries' / source.name
                copy_binary.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, copy_binary)
                record['binary'] = {'name': source.name, 'sha256': sha(copy_binary), 'bytes': copy_binary.stat().st_size}
            manifest['binaries'][target] = record

    saves = ROOT / 'local/play'
    if saves.is_dir():
        target_saves = destination / 'saves'
        shutil.copytree(saves, target_saves)
        manifest['saves'] = {'path': 'saves', 'files': sum(1 for _ in target_saves.rglob('*') if _.is_file())}

    manifest_path = destination / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('backup:', destination.relative_to(ROOT))
    print('roms:', len(manifest['roms']), 'binaries:', len(manifest['binaries']))
    print('saves:', manifest.get('saves', {}).get('files', 0), 'files')
    print('manifest sha256:', sha(manifest_path))


if __name__ == '__main__':
    main()
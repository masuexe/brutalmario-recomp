"""Verified generator overlay; pinned upstream tracked files remain untouched."""
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'local/upstream/snesrecomp'
OVERLAY = ROOT / 'local/generator'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(target):
    policy = ROOT / 'recomp/targets' / target / 'timing.json'
    if not policy.is_file():
        return None
    manifest = json.loads((ROOT / 'config/generator-patches.json').read_text())
    for item in manifest['patches']:
        if sha(ENGINE / item['source']) != item['source_sha256']:
            raise ValueError('generator source hash mismatch: ' + item['source'])
        if sha(ROOT / item['patch']) != item['patch_sha256']:
            raise ValueError('generator patch hash mismatch: ' + item['patch'])
    return {'patches': manifest['patches'], 'policy_sha256': sha(policy),
            'instruction_bus_sha256': sha(ROOT / 'recomp/generator/instruction_bus.py'),
            'runtime_support_sha256': sha(ROOT / 'recomp/aot_timing.c')}


def prepare(target):
    result = identity(target)
    if result is None:
        return ENGINE
    policy = json.loads((ROOT / 'recomp/targets' / target / 'timing.json').read_text())
    variants = policy['instruction_bus_variants']
    if (policy['schema'] != 1 or not isinstance(variants, list) or
            not all(isinstance(v, str) and re.fullmatch(r'[0-9A-F]{6}:M[01]X[01]', v)
                    for v in variants)):
        raise ValueError('invalid generator timing policy')
    OVERLAY.mkdir(parents=True, exist_ok=True)
    patched = {item['source']: item for item in result['patches']}
    tracked = subprocess.check_output(['git', '-C', str(ENGINE), 'ls-files', '-z',
                                       'recompiler', 'tools']).split(b'\0')
    for name in filter(None, tracked):
        relative = name.decode()
        source, target_path = ENGINE / relative, OVERLAY / relative
        if not source.is_file():
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if not target_path.exists():
            shutil.copy2(source, target_path)
        accepted = {sha(source)}
        if relative in patched:
            accepted.add(patched[relative]['result_sha256'])
        if sha(target_path) not in accepted:
            raise ValueError('unexpected generator override: ' + relative)
    for path in ENGINE.iterdir():
        destination = OVERLAY / path.name
        if path.name not in ('.git', 'tools', 'recompiler') and not destination.exists():
            destination.symlink_to(path.resolve(), target_is_directory=path.is_dir())
    for item in result['patches']:
        path = OVERLAY / item['source']
        if sha(path) != item['result_sha256']:
            subprocess.run(['git', 'apply', '--directory=local/generator',
                            str(ROOT / item['patch'])], cwd=ROOT, check=True)
            if sha(path) != item['result_sha256']:
                raise ValueError('generator output hash mismatch')
    shutil.copy2(ROOT / 'recomp/generator/instruction_bus.py',
                 OVERLAY / 'recompiler/v2/instruction_bus.py')
    (OVERLAY / 'recompiler/v2/project_aot_policy.py').write_text(
        '# Generated from the checked-in timing policy; part of the generator digest.\n'
        'INSTRUCTION_BUS_VARIANTS = ' + repr(tuple(sorted(set(variants)))) + '\n')
    return OVERLAY

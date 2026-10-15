"""Materialize verified runtime overrides without changing upstream checkouts."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patch_plan():
    manifest = json.loads((ROOT / 'config/runtime-patches.json').read_text())
    for item in manifest['patches']:
        source = ROOT / 'local/upstream/snesrecomp' / item['source']
        patch = ROOT / item['patch']
        if sha(source.read_bytes()) != item['source_sha256']:
            raise ValueError(f'{item["id"]}: upstream source hash mismatch')
        if sha(patch.read_bytes()) != item['patch_sha256']:
            raise ValueError(f'{item["id"]}: patch hash mismatch')
    return manifest['patches']


def prepare_runtime():
    items = patch_plan()
    outputs = []
    for item in items:
        target = ROOT / 'local/runtime' / item['source']
        if target.exists():
            actual = sha(target.read_bytes())
            if actual == item['result_sha256']:
                outputs.append(target)
                continue
            if actual != item['source_sha256']:
                raise ValueError(f'{target}: unexpected local override; refusing to replace it')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / 'local/upstream/snesrecomp' / item['source']).read_bytes())
        command = ['git', 'apply', '--directory=local/runtime']
        patch = ROOT / item['patch']
        subprocess.run(command + ['--check', str(patch)], cwd=ROOT, check=True)
        subprocess.run(command + [str(patch)], cwd=ROOT, check=True)
        if sha(target.read_bytes()) != item['result_sha256']:
            raise ValueError(f'{item["id"]}: patched output hash mismatch')
        outputs.append(target)
    return outputs


def configure_runtime(experiment, target='BrutalMarioDemo11SNESRecomp'):
    outputs = prepare_runtime()
    items = patch_plan()
    path = experiment / 'CMakeLists.txt'
    source = path.read_text()
    begin = '# BEGIN project runtime overrides'
    end = '# END project runtime overrides'
    lines = [begin, f'get_target_property(_m1_sources {target} SOURCES)']
    for item in items:
        lines.append(f'list(REMOVE_ITEM _m1_sources "${{SNESRECOMP_ROOT}}/{item["source"]}")')
    lines.append(f'set_property(TARGET {target} PROPERTY SOURCES ${{_m1_sources}})')
    for output in outputs:
        lines.append(f'target_sources({target} PRIVATE "{output.as_posix()}")')
    lines.append(end)
    block = '\n'.join(lines)
    if begin in source:
        first = source.index(begin)
        last = source.index(end, first) + len(end)
        source = source[:first] + block + source[last:]
    else:
        source += '\n' + block + '\n'
    if source != path.read_text():
        path.write_text(source)

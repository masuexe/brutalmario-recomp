#!/usr/bin/env python3
"""Build a read-only Snes9x boot trace probe in a fresh local source copy."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from m1 import ROOT, pins_check, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'local/diagnostics/snes9x-boot-probe')
    args = parser.parse_args()
    pins = pins_check()
    pin = pins['repositories']['snes9x_reference']
    source = ROOT / pin['local_path']
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'local'):
        parser.error('output must be a fresh directory under local/')
    output.mkdir(parents=True, exist_ok=False)
    tracked = subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).split(b'\0')
    for name in tracked:
        if name:
            relative = Path(name.decode())
            # Gitlinks are directories, not source files; the libretro build
            # used here needs none of the optional external submodules.
            if (source / relative).is_dir():
                continue
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, destination)
    patch = ROOT / 'patches/diagnostics/snes9x-boot-trace.patch'
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=output, check=True)
    subprocess.run(['git', 'apply', str(patch)], cwd=output, check=True)
    run(['make', '-C', output / 'libretro', '-j2', 'GIT_VERSION=' + pin['commit'][:8]],
        log=output / 'build.log')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    (output / 'probe-build.json').write_text(json.dumps({
        'source_pin': pin, 'patch_sha256': sha(patch),
        'modified_source_sha256': sha(output / 'cpuexec.cpp'),
        'core_sha256': sha(output / 'libretro/snes9x_libretro.so'),
        'scope': 'Optional read-only BM_BOOT_TRACE; stock reference core unchanged',
    }, indent=2) + '\n')
    print(output / 'libretro/snes9x_libretro.so')


if __name__ == '__main__':
    main()

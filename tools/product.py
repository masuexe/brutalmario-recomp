#!/usr/bin/env python3
"""Build, verify and package the configured native PC product."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from native_sprite_gap import packs
from qualify_console_performance import qualify

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / 'config/products/native.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def inputs(config_path, platform, binary):
    config = json.loads(config_path.read_text())
    target = config['target']
    spec = config['platforms'][platform]
    directory = ROOT / 'local/restoration' / target
    rom = directory / 'rom.sfc'
    expected = json.loads((ROOT / 'config/restorations' / (target + '.json')).read_text())['output']['sha256']
    if sha(rom) != expected:
        raise ValueError('ROM differs from restoration recipe')
    data = binary.read_bytes()
    if expected.encode() not in data:
        raise ValueError('binary ROM identity differs from product')
    if config['features']['console'] and b'PRACTICE CHEAT CONSOLE' not in data:
        raise ValueError('binary has no built-in console')
    if not data.startswith(b'MZ' if platform == 'windows' else b'\x7fELF'):
        raise ValueError('binary platform differs')
    assets = packs(target)
    for asset in assets:
        path = directory / asset['pack_file']
        if path.stat().st_size != asset['size'] or sha(path) != asset['sha256']:
            raise ValueError('pack differs: ' + str(path))
    identity = dict(target=target, platform=platform, binary_sha256=sha(binary),
                    rom_sha256=expected, config_sha256=sha(config_path),
                    packs={a['variable']: a['sha256'] for a in assets})
    return config, spec, directory, assets, identity


def host_path(path, platform):
    if platform == 'windows' and sys.platform != 'win32':
        return subprocess.check_output(['wslpath', '-w', str(path)], text=True).strip()
    return str(path)


def verify(config_path, platform, binary, output):
    config, _, directory, assets, identity = inputs(config_path, platform, binary)
    output.mkdir(parents=True, exist_ok=False)
    frames = config['verification']['frames']
    script = output / 'probe.script'
    script.write_text(f'turbo on\nwait {frames}\ndump probe\nquit\n')
    identity['script_sha256'] = sha(script)
    executable = binary
    if platform == 'windows' and sys.platform != 'win32':
        executable = output / 'probe.exe'
        shutil.copyfile(binary, executable)
        executable.chmod(0o755)
    for mode in ('closed', 'console'):
        capture = output / mode
        capture.mkdir()
        env = dict(os.environ)
        # Do not inherit diagnostics, cheat channels or save overrides.
        for key in list(env):
            if key.startswith(('BM_', 'SNESRECOMP_', 'M1_')):
                del env[key]
        env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   SNESRECOMP_HOST_PROFILE='1',
                   SNESRECOMP_DUMP_DIR=host_path(capture, platform))
        for asset in assets:
            env[asset['variable']] = host_path(directory / asset['pack_file'], platform)
        if mode == 'console':
            env.update(SNESRECOMP_CHEAT_CONSOLE='1', SNESRECOMP_CHEAT_CONSOLE_COMMANDS='help;close')
        if platform == 'windows' and sys.platform != 'win32':
            forwarded = [k for k in env if k.startswith(('BM_', 'SNESRECOMP_', 'SDL_'))]
            env['WSLENV'] = ':'.join(forwarded)
        command = [str(executable), '--no-launcher', '--config', host_path(ROOT / 'recomp/m1-config.ini', platform),
                   '--rom', host_path(directory / 'rom.sfc', platform), '--script', host_path(script, platform)]
        write_json(capture / 'receipt.json', dict(identity, command=command))
        with (capture / 'run.log').open('w') as log:
            subprocess.run(command, env=env, cwd=capture, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=60)
    for mode in ('closed', 'console'):
        capture = output / mode
        info = json.loads((capture / 'probe.info.json').read_text())
        if info['frame'] != frames:
            raise ValueError('dump frame differs from probe endpoint')
        sizes = {'wram.bin': 0x20000, 'vram.bin': 0x10000,
                 'cgram.bin': 512, 'oam.bin': 544, 'sram.bin': info['sram_size']}
        for suffix, size in sizes.items():
            if (capture / ('probe.' + suffix)).stat().st_size != size:
                raise ValueError('dump size differs: ' + suffix)
    result = qualify(output / 'closed', output / 'console')
    log = (output / 'console/run.log').read_text()
    if 'practice cheat console OPEN' not in log or 'practice cheat console CLOSED' not in log:
        raise ValueError('console lifecycle missing')
    for side in ('before', 'after'):
        if result[side]['frames'] != frames or result[side]['guest_mean_ms'] > config['verification']['max_guest_mean_ms']:
            raise ValueError('frame count or performance gate failed')
    write_json(output / 'verification.json', dict(identity=identity, passed=True, comparison=result))
    return output / 'verification.json'


LAUNCHER = '''#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parent
cfg = json.loads((root / 'product.json').read_text())
env = dict(os.environ)
for key, filename in cfg['packs'].items():
    env[key] = str(root / 'data/packs' / filename)
command = [str(root / 'bin' / cfg['binary']), '--no-launcher',
           '--config', str(root / 'config/config.ini'), '--rom', str(root / 'data/rom.sfc')]
raise SystemExit(subprocess.call(command + sys.argv[1:], cwd=root / 'saves', env=env))
'''


def package(config_path, platform, binary, verification, output):
    config, spec, directory, assets, identity = inputs(config_path, platform, binary)
    receipt = json.loads(verification.read_text())
    if not receipt.get('passed') or any(receipt['identity'].get(k) != v for k, v in identity.items()):
        raise ValueError('verification does not match selected product inputs')
    archive = output.with_name(output.name + '.zip')
    if output.exists() or archive.exists():
        raise ValueError('output or archive exists; choose a fresh destination')
    output.mkdir(parents=True)
    for name in ('bin', 'data/packs', 'config', 'saves'):
        (output / name).mkdir(parents=True)
    shutil.copy2(binary, output / 'bin' / spec['binary'])
    shutil.copy2(directory / 'rom.sfc', output / 'data/rom.sfc')
    for asset in assets:
        shutil.copy2(directory / asset['pack_file'], output / 'data/packs' / asset['pack_file'])
    text = (ROOT / 'recomp/m1-config.ini').read_text().replace('OutputMethod=SDL-Software', 'OutputMethod=' + spec['output_method'])
    (output / 'config/config.ini').write_text(text)
    write_json(output / 'product.json', dict(target=config['target'], binary=spec['binary'],
               features=config['features'], packs={a['variable']: a['pack_file'] for a in assets}))
    (output / 'play.py').write_text(LAUNCHER)
    if platform == 'linux':
        entry = output / 'play.sh'
        entry.write_text('#!/bin/sh\ncd -- "$(dirname -- "$0")" || exit 1\nexec python3 play.py "$@"\n')
        entry.chmod(0o755)
    else:
        (output / 'play.bat').write_bytes(b'@echo off\r\ncd /d "%~dp0"\r\npython play.py %*\r\n')
    shutil.copy2(verification, output / 'verification.json')
    (output / 'README.txt').write_text('Launch with play.sh (Linux) or play.bat (Windows). Python 3 is required.\nPress backquote (`) for the console; help lists commands; Escape closes.\nSaves are stored in saves/.\n')
    write_json(output / 'files.json', {str(p.relative_to(output)): sha(p) for p in output.rglob('*') if p.is_file()})
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(output.rglob('*')):
            zipped.write(path, Path(output.name) / path.relative_to(output))
    write_json(archive.with_name(archive.name + '.receipt.json'), dict(identity, archive_sha256=sha(archive)))
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'verify', 'package'])
    parser.add_argument('--platform', required=True, choices=['linux', 'windows'])
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build-dir', type=Path, help='configured CMake directory; required for build')
    parser.add_argument('--verification', type=Path, help='verification.json; required for package')
    args = parser.parse_args()
    binary, output = args.binary.resolve(), args.output.resolve()
    if args.action == 'build':
        if not args.build_dir:
            parser.error('build requires --build-dir (configure CMake for the selected platform first)')
        if output.exists():
            raise ValueError('build receipt already exists')
        subprocess.run(['cmake', '--build', str(args.build_dir.resolve()), '--config', 'Release'], check=True)
        *_, identity = inputs(args.config, args.platform, binary)
        write_json(output, dict(identity, build_dir=str(args.build_dir.resolve())))
        print(output)
    elif args.action == 'verify':
        print(verify(args.config, args.platform, binary, output))
    else:
        if not args.verification:
            parser.error('package requires --verification')
        print(package(args.config, args.platform, binary, args.verification, output))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Reproduce the local M1 experiment using the checked-in upstream/input pins.

Run stages in order: check, scaffold, generate, build, reference, native.
Source downloads and Rust installation are explicit setup steps (docs/m1.md).
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from prepare_rom import verify

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'local/upstream/snesrecomp'
EXPERIMENT = ROOT / 'local/experiments/BrutalMarioDemo11SNESRecomp'
ROM = ROOT / 'local/roms/demo-1-1.sfc'
BUILD = ROOT / 'local/build/demo-1-1'


def install_metrics():
    main = EXPERIMENT / 'src/main.c'
    source = main.read_text()
    if 'M1MetricsRegister();' not in source:
        entry = 'int main(int argc, char **argv)\n{\n'
        if source.count(entry) != 1:
            raise ValueError('unexpected host main template; review instrumentation')
        source = source.replace(entry, 'extern void M1MetricsRegister(void);\n\n' +
                                entry + '    M1MetricsRegister();\n')
        main.write_text(source)
    cmake = EXPERIMENT / 'CMakeLists.txt'
    source = cmake.read_text()
    if '# M1 metrics' not in source:
        source += ('\n# M1 metrics: project-owned instrumentation, no guest changes.\n'
                   f'target_sources(BrutalMarioDemo11SNESRecomp PRIVATE "{ROOT / "recomp/m1_metrics.c"}")\n')
        cmake.write_text(source)


def pins_check():
    pins = json.loads((ROOT / 'config/upstreams.json').read_text())
    inputs = json.loads((ROOT / 'config/inputs.json').read_text())
    verify(ROM.read_bytes(), inputs['output'], 'target ROM')
    for label, pin in pins['repositories'].items():
        directory = ROOT / pin['local_path']
        actual = subprocess.check_output(['git', '-C', str(directory), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != pin['commit']:
            raise ValueError(f'{label}: checkout differs from pinned commit')
        changes = subprocess.check_output(['git', '-C', str(directory), 'status', '--porcelain', '--untracked-files=no'], text=True)
        if changes.strip():
            raise ValueError(f'{label}: tracked upstream files are modified')
        if hashlib.sha256((directory / 'LICENSE').read_bytes()).hexdigest() != pin['license_sha256']:
            raise ValueError(f'{label}: license digest mismatch')
    return pins


def run(command, *, log, cwd=ROOT, env=None, seconds=600, memory_gib=None):
    log.parent.mkdir(parents=True, exist_ok=True)
    limit = None
    if memory_gib is not None:
        import resource
        def limit():
            size = memory_gib * 1024 ** 3
            resource.setrlimit(resource.RLIMIT_AS, (size, size))
    started = time.monotonic()
    with log.open('w') as output:
        process = subprocess.Popen([str(x) for x in command], cwd=cwd, env=env,
                                   stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True, preexec_fn=limit)
        try:
            code = process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise RuntimeError(f'timed out after {seconds}s; see {log}')
    if code:
        raise RuntimeError(f'exit {code}; see {log}')
    print(f'{log.relative_to(ROOT)}: passed ({time.monotonic() - started:.2f}s)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['check', 'scaffold', 'generate', 'build', 'reference', 'native'])
    parser.add_argument('--capture', help='new capture name; refuses existing directories')
    parser.add_argument('--interpreter-only', action='store_true',
                        help='native diagnostic: exclude every generated PC from AOT bouncing')
    args = parser.parse_args()
    if args.interpreter_only and args.stage != 'native':
        parser.error('--interpreter-only applies only to the native stage')
    pins = pins_check()
    reports = ROOT / 'local/reports'
    reports.mkdir(parents=True, exist_ok=True)
    if args.stage == 'check':
        print('Pinned source revisions, licenses, clean worktrees and target ROM verified.')
    elif args.stage == 'scaffold':
        if EXPERIMENT.exists():
            raise ValueError('experiment already exists; refusing to replace it')
        run(['sh', ENGINE / 'tools/new_project/setup_project.sh', '--rom', ROM,
             '--dir', EXPERIMENT.parent, '--name', 'Brutal Mario Demo 1-1',
             '--players', '1', '--yes', '--no-submodules', '--no-netplay',
             '--no-ci', '--no-recomp-ui', '--no-fetch-boxart', '--no-generate',
             '--no-build', '--no-github'], log=reports / 'scaffold.log')
        (EXPERIMENT / 'framework_pins.txt').write_text('snesrecomp=' + pins['repositories']['snesrecomp']['commit'] + '\n')
        install_metrics()
    elif args.stage == 'generate':
        cfg = EXPERIMENT / 'recomp'
        run([sys.executable, ENGINE / 'tools/v2_sync_funcs_h.py', '--cfg-dir', cfg,
             '--out', cfg / 'funcs.h'], log=reports / 'sync-funcs.log')
        command = [sys.executable, ENGINE / 'tools/v2_emit.py', '--rom', ROM,
                   '--cfg-dir', cfg, '--out-dir', EXPERIMENT / 'src/gen',
                   '--analysis-backend', 'native', '--no-hle']
        for name in ('main.c', 'game_rtl.c', 'host_contract.c'):
            command.extend(['--source-root', EXPERIMENT / 'src' / name])
        run(command, log=reports / 'emission-repeat.log', memory_gib=4)
    elif args.stage == 'build':
        install_metrics()
        run(['cmake', '-S', EXPERIMENT, '-B', BUILD, '-G', 'Ninja',
             '-DCMAKE_BUILD_TYPE=Release', f'-DSNESRECOMP_ROOT={ENGINE}',
             '-DSNESRECOMP_SDL_BACKEND=SDL2', '-DSNESRECOMP_SDL3_FETCH=OFF',
             '-DSNESRECOMP_FRAME_IMPL=LLE'], log=reports / 'native-configure.log')
        run(['cmake', '--build', BUILD, '--parallel', '2'], log=reports / 'native-build.log')
    else:
        name = args.capture or args.stage + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise ValueError('capture name must contain only letters, digits, hyphens or underscores')
        directory = ROOT / 'local/captures' / name
        directory.mkdir(parents=True, exist_ok=False)
        env = os.environ.copy()
        script = ROOT / 'recomp/inputs/m1-route.script'
        if args.stage == 'reference':
            env.update(SNESREF_HEADLESS='1', SNESREF_WRAM_FILL='0',
                       SNESREF_SCRIPT=str(script), SNESREF_DUMP_DIR=str(directory),
                       SNESREF_TRACE_FILE=str(directory / 'wram.jsonl'),
                       SNESREF_WAV=str(directory / 'audio.wav'))
            command = [ROOT / 'local/build/snesref/snesref',
                       ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so', ROM]
        else:
            script_copy = directory / 'input.script'
            script_copy.write_text('turbo on\n' + script.read_text())
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                       SNESRECOMP_REWIND='0', SNESRECOMP_CPU_TRACE_RING_ENTRIES='65536',
                       SNESRECOMP_COVERAGE_DIR=str(directory / 'coverage'),
                       SNESRECOMP_DUMP_DIR=str(directory),
                       SNESRECOMP_STATE_TRACE=str(directory / 'state-trace.txt'))
            if args.interpreter_only:
                manifest = json.loads((EXPERIMENT / 'src/gen/program_manifest.json').read_text())
                pcs = {int(key.split(':')[0], 16) for key in manifest['nodes']}
                # The upstream gate canonicalizes LoROM mirrors at some sites.
                pcs |= {pc ^ 0x800000 for pc in pcs}
                targets = directory / 'interpreted-targets.txt'
                targets.write_text(''.join(f'{pc:06X}\n' for pc in sorted(pcs)))
                env['SNESRECOMP_LLE_INTERP_TARGET_FILE'] = str(targets)
                env['SNESRECOMP_LLE_BOUNCE'] = '0'
            command = [BUILD / 'BrutalMarioDemo11SNESRecomp', '--no-launcher',
                       '--config', ROOT / 'recomp/m1-config.ini', '--coverage-capture=on',
                       '--script', script_copy, '--rom', ROM]
        receipt = {
            'stage': args.stage,
            'upstream_pins': pins,
            'rom_sha256': hashlib.sha256(ROM.read_bytes()).hexdigest(),
            'route_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
            'host_binary_sha256': hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
            'initial_state': 'Fresh capture directory; no imported SRAM or savestate',
            'lle_bounce_override': env.get('SNESRECOMP_LLE_BOUNCE', 'upstream default'),
            'interpreter_only_requested': args.interpreter_only,
        }
        (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        run(command, log=directory / 'run.log', cwd=directory, env=env, seconds=180)
        if args.interpreter_only and '[m1] aot_bridge_entries=0 ' not in (directory / 'run.log').read_text():
            raise RuntimeError('interpreter-only diagnostic still executed compiled bodies; reject comparison')
        print(f'Capture: {directory.relative_to(ROOT)}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit(f'm1: {exc}')

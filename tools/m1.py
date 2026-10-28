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
from runtime_patches import configure_runtime, patch_plan
from native_content import identity as content_identity, configure as configure_content
from native_sprite import identity as sprite_identity, configure as configure_sprite, environment as sprite_environment
from native_seven import identity as seven_identity, configure as configure_seven, environment as seven_environment
from native_mazo import identity as mazo_identity, configure as configure_mazo, environment as mazo_environment
from native_sprite_gap import (identity as gap_identity, configure as configure_gap,
                               environment as gap_environment)
from native_seven_child import identity as child_identity, configure as configure_child, environment as child_environment
from generator_patches import identity as generator_identity, prepare as prepare_generator
from restoration_targets import RESTORATIONS

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'local/upstream/snesrecomp'
EXPERIMENT = ROOT / 'local/experiments/BrutalMarioDemo11SNESRecomp'
ROM = ROOT / 'local/roms/demo-1-1.sfc'
BUILD = ROOT / 'local/build/demo-1-1'
TARGET = 'BrutalMarioDemo11SNESRecomp'
TITLE = 'Brutal Mario Demo 1-1'
INPUT_MANIFEST = ROOT / 'config/inputs.json'
TARGET_ID = 'demo-1-1'
SEPARATE_ECHO = False


def verify_scaffold_rom(experiment, rom):
    identity = (experiment / 'rom_identity.txt').read_text()
    match = re.search(r'^expected_sha256\s*=\s*([0-9a-f]{64})\s*$', identity, re.MULTILINE)
    if not match or match[1] != hashlib.sha256(rom.read_bytes()).hexdigest():
        raise ValueError('restoration scaffold ROM identity is stale; recreate the scaffold for this candidate')


def install_metrics():
    glue = EXPERIMENT / 'src/game_rtl.c'
    source = glue.read_text()
    if 'M1TimingSample("begin");' not in source:
        source = source.replace('#include "beam_frame_driver.h"',
                                '#include "beam_frame_driver.h"\n\nextern void M1TimingSample(const char *phase);')
        source = source.replace('    snes_beam_frame_driver_run_frame();',
                                '    M1TimingSample("begin");\n    snes_beam_frame_driver_run_frame();\n    M1TimingSample("run");')
        source = source.replace('    snes_beam_frame_driver_draw_ppu_frame();',
                                '    snes_beam_frame_driver_draw_ppu_frame();\n    M1TimingSample("draw");')
        glue.write_text(source)
    # Console reset resets the hardware, then must discard the driver's old
    # resume PC/WAI state so the next frame starts at the ROM reset vector.
    # The scaffold only wires session_reset; RtlReset calls hardware_reset.
    if '    .hardware_reset = &GameSessionReset,' not in source:
        entry = '    .session_reset = &GameSessionReset,\n'
        if source.count(entry) != 1:
            raise ValueError('unexpected game reset template; review reset hooks')
        source = source.replace(entry, entry + '    .hardware_reset = &GameSessionReset,\n')
        glue.write_text(source)
    main = EXPERIMENT / 'src/main.c'
    source = main.read_text()
    if '.on_shutdown        = &M1AudioShutdown,' not in source:
        source = source.replace('static const SnesDesktopHostGame kGameHost = {',
                                'extern void M1AudioShutdown(void);\n\nstatic const SnesDesktopHostGame kGameHost = {\n'
                                '    .on_shutdown        = &M1AudioShutdown,')
    if '.after_run_frame    = &M1LocationSample,' not in source:
        source = source.replace('static const SnesDesktopHostGame kGameHost = {',
                                'extern void M1LocationSample(const SnesDesktopHostFrameStats *stats);\n\n'
                                'static const SnesDesktopHostGame kGameHost = {\n'
                                '    .after_run_frame    = &M1LocationSample,')
    if 'M1MetricsRegister();' not in source:
        entry = 'int main(int argc, char **argv)\n{\n'
        if source.count(entry) != 1:
            raise ValueError('unexpected host main template; review instrumentation')
        source = source.replace(entry, 'extern void M1MetricsRegister(void);\n\n' +
                                entry + '    M1MetricsRegister();\n')
    if source != main.read_text():
        main.write_text(source)
    cmake = EXPERIMENT / 'CMakeLists.txt'
    source = cmake.read_text()
    if '# M1 metrics' not in source:
        source += ('\n# M1 metrics: project-owned instrumentation, no guest changes.\n'
                   f'target_sources({TARGET} PRIVATE "{ROOT / "recomp/m1_metrics.c"}")\n')
        cmake.write_text(source)
    if SEPARATE_ECHO and '# demoOnly1 legacy audio default' not in source:
        source += ('\n# demoOnly1 legacy audio default (explicit environment override remains available).\n'
                   f'target_compile_definitions({TARGET} PRIVATE M1_SEPARATE_ECHO_DEFAULT=1)\n')
        cmake.write_text(source)


def analysis_identity():
    cfg = EXPERIMENT / 'recomp'
    files = sorted(cfg.glob('bank*.cfg')) + [cfg / 'symbols.toml']
    generated = EXPERIMENT / 'src/gen'
    result = {
        'generated_sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(generated.iterdir())
                              if p.suffix in ('.c', '.h')},
        'generator': generator_identity(TARGET_ID),
        'inputs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in files if p.is_file()},
        'program_manifest_sha256': hashlib.sha256(
            (EXPERIMENT / 'src/gen/program_manifest.json').read_bytes()).hexdigest(),
    }
    if TARGET_ID in RESTORATIONS:
        result['rom_sha256'] = hashlib.sha256(ROM.read_bytes()).hexdigest()
    return result


def pins_check():
    pins = json.loads((ROOT / 'config/upstreams.json').read_text())
    inputs = json.loads(INPUT_MANIFEST.read_text())
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
    global BUILD, EXPERIMENT, ROM, TARGET, TITLE, INPUT_MANIFEST, TARGET_ID, SEPARATE_ECHO
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['check', 'scaffold', 'generate', 'build', 'reference', 'native'])
    parser.add_argument('--target', choices=['demo-1-1', 'demo-only-1', *RESTORATIONS], default='demo-1-1',
                        help='isolated ROM, scaffold, generated code, binary and captures')
    parser.add_argument('--capture', help='new capture name; refuses existing directories')
    parser.add_argument('--script', type=Path, help='alternate deterministic input script')
    parser.add_argument('--renderer', choices=['legacy', 'optimized'],
                        help='native renderer override; the default follows recomp/m1-config.ini')
    parser.add_argument('--interpreter-only', action='store_true',
                        help='native diagnostic: exclude every generated PC from AOT bouncing')
    parser.add_argument('--audio', action='store_true',
                        help='build/native: isolated full-history audio build; native runs without turbo')
    parser.add_argument('--audio-device-rate', type=int, choices=[32000, 32040, 48000],
                        help='native --audio only: override the isolated SDL device rate')
    args = parser.parse_args()
    TARGET_ID = args.target
    SEPARATE_ECHO = args.target == 'demo-only-1' or args.target in RESTORATIONS
    if args.target == 'demo-only-1':
        TARGET = 'BrutalMarioDemoOnly1SNESRecomp'
        TITLE = 'Brutal Mario Demo Only1'
        EXPERIMENT = ROOT / 'local/experiments' / TARGET
        ROM = ROOT / 'local/roms/demo-only-1.sfc'
        INPUT_MANIFEST = ROOT / 'config/demo-only-1.json'
        BUILD = ROOT / 'local/build/demo-only-1'
    elif args.target in RESTORATIONS:
        TARGET = RESTORATIONS[args.target]['binary']
        TITLE = RESTORATIONS[args.target]['title']
        EXPERIMENT = ROOT / 'local/experiments' / TARGET
        ROM = ROOT / 'local/restoration' / args.target / 'rom.sfc'
        INPUT_MANIFEST = ROOT / 'config/restorations' / (args.target + '.json')
        BUILD = ROOT / 'local/build' / args.target
    if args.audio_device_rate and (args.stage != 'native' or not args.audio):
        parser.error('--audio-device-rate requires native --audio')
    if args.audio:
        if args.stage not in ('build', 'native'):
            parser.error('--audio applies only to build/native stages')
        BUILD = BUILD.with_name(BUILD.name + '-audio')
    if args.interpreter_only and args.stage != 'native':
        parser.error('--interpreter-only applies only to the native stage')
    if args.renderer and args.stage != 'native':
        parser.error('--renderer applies only to the native stage')
    pins = pins_check()
    runtime_patches = patch_plan()
    native_sprite = sprite_identity(args.target)
    native_mazo = mazo_identity(args.target)
    native_gap = gap_identity(args.target)
    native_seven = None if (native_mazo or native_gap) else seven_identity(args.target)
    native_child = child_identity(args.target)
    native_content = (content_identity(args.target) or native_sprite or native_seven or
                      native_child or native_mazo or native_gap)
    if native_content and args.stage == 'reference':
        parser.error('this content target requires the native PC runtime')
    generator_identity(args.target)
    if args.target in RESTORATIONS and args.stage in ('generate', 'build', 'native'):
        verify_scaffold_rom(EXPERIMENT, ROM)
    if args.stage in ('build', 'native'):
        if generator_identity(args.target) is not None or args.target in RESTORATIONS:
            generation_receipt = EXPERIMENT / 'recomp/generation.json'
            if (not generation_receipt.is_file() or
                    json.loads(generation_receipt.read_text()) != analysis_identity()):
                raise ValueError('generator policy or generated sources changed; run tools/m1.py generate first')
        owned_symbols = ROOT / 'recomp/targets' / args.target / 'symbols.toml'
        if (owned_symbols.is_file() and
                owned_symbols.read_bytes() != (EXPERIMENT / 'recomp/symbols.toml').read_bytes()):
            raise ValueError('analysis symbols changed; run tools/m1.py generate for this target first')
    if args.stage == 'native':
        receipt_path = BUILD / 'm1-build.json'
        if not receipt_path.is_file():
            raise ValueError('missing build receipt; run tools/m1.py build first')
        build_receipt = json.loads(receipt_path.read_text())
        if args.target in RESTORATIONS and build_receipt.get('rom_sha256') != hashlib.sha256(ROM.read_bytes()).hexdigest():
            raise ValueError('restoration ROM differs from its build receipt; regenerate and rebuild')
        binary_sha = hashlib.sha256((BUILD / TARGET).read_bytes()).hexdigest()
        if (build_receipt['runtime_patches'] != runtime_patches or
                build_receipt.get('native_content') != native_content or
                build_receipt['binary_sha256'] != binary_sha or
                build_receipt.get('audio_diagnostics', False) != args.audio or
                (build_receipt.get('analysis') is not None and
                 build_receipt['analysis'] != analysis_identity())):
            raise ValueError('binary does not match the current runtime patch receipt; rebuild first')
    reports = ROOT / 'local/reports'
    if args.target != 'demo-1-1':
        reports = reports / args.target
    reports.mkdir(parents=True, exist_ok=True)
    if args.stage == 'check':
        print('Pinned source revisions, licenses, clean worktrees and target ROM verified.')
    elif args.stage == 'scaffold':
        if EXPERIMENT.exists():
            raise ValueError('experiment already exists; refusing to replace it')
        run(['sh', ENGINE / 'tools/new_project/setup_project.sh', '--rom', ROM,
             '--dir', EXPERIMENT.parent, '--name', TITLE,
             '--players', '1', '--yes', '--no-submodules', '--no-netplay',
             '--no-ci', '--no-recomp-ui', '--no-fetch-boxart', '--no-generate',
             '--no-build', '--no-github'], log=reports / 'scaffold.log')
        (EXPERIMENT / 'framework_pins.txt').write_text('snesrecomp=' + pins['repositories']['snesrecomp']['commit'] + '\n')
        install_metrics()
    elif args.stage == 'generate':
        cfg = EXPERIMENT / 'recomp'
        owned_symbols = ROOT / 'recomp/targets' / args.target / 'symbols.toml'
        if owned_symbols.is_file():
            (cfg / 'symbols.toml').write_bytes(owned_symbols.read_bytes())
        # Synchronize declarations before funcs.h so new roots are declared.
        run([sys.executable, ENGINE / 'tools/sync_symbols.py', '--cfg-dir', cfg],
            log=reports / 'sync-symbols.log')
        run([sys.executable, ENGINE / 'tools/v2_sync_funcs_h.py', '--cfg-dir', cfg,
             '--out', cfg / 'funcs.h'], log=reports / 'sync-funcs.log')
        generator = prepare_generator(args.target)
        command = [sys.executable, generator / 'tools/v2_emit.py', '--rom', ROM,
                   '--cfg-dir', cfg, '--out-dir', EXPERIMENT / 'src/gen',
                   '--analysis-backend', 'native', '--no-hle']
        for name in ('main.c', 'game_rtl.c', 'host_contract.c'):
            command.extend(['--source-root', EXPERIMENT / 'src' / name])
        run(command, log=reports / 'emission-repeat.log', memory_gib=4)
        (cfg / 'generation.json').write_text(json.dumps(analysis_identity(), indent=2) + '\n')
    elif args.stage == 'build':
        install_metrics()
        configure_runtime(EXPERIMENT, TARGET)
        configure_content(EXPERIMENT, TARGET, args.target)
        configure_sprite(EXPERIMENT, TARGET, args.target)
        if native_seven:
            configure_seven(EXPERIMENT, TARGET, args.target)
        configure_child(EXPERIMENT, TARGET, args.target)
        configure_mazo(EXPERIMENT, TARGET, args.target)
        configure_gap(EXPERIMENT, TARGET, args.target)
        # Diagnostic only: log the first read of every ROM address so a capture
        # can show which stream feeds a graphics buffer. Off unless asked.
        if os.environ.get('BM_DIAG_ROM_TRACE') == '1':
            runtime_cart = (ROOT / 'local/native-content-runtime' / args.target /
                            'runner/src/snes/cart.c')
            if runtime_cart.is_file():
                text = runtime_cart.read_text()
                helper = (
                    '/* Diagnostic ROM read trace (env gated, BM_DIAG_ROM_TRACE). */\n'
                    'static void bm_rom_trace(uint8_t bank, uint16_t adr) {\n'
                    '  static FILE *f; static int init, seen[0x80000 / 4];\n'
                    '  static long n, max = 200000;\n'
                    '  if (!init) { init = 1; const char *p = getenv("BM_ROM_TRACE_LOG");\n'
                    '    if (p && *p) f = fopen(p, "w");\n'
                    '    const char *m = getenv("BM_ROM_TRACE_MAX"); if (m && *m) max = strtol(m, NULL, 0); }\n'
                    '  if (!f || n >= max) return;\n'
                    '  unsigned off = ((unsigned)(bank & 0x7F) << 15) | (adr & 0x7FFF);\n'
                    '  if (off >= 0x400000u) return;\n'
                    '  unsigned bit = off >> 5, msk = 1u << (off & 31);\n'
                    '  if (seen[bit] & msk) return; seen[bit] |= msk;\n'
                    '  { extern int snes_frame_counter;\n'
                    '    fprintf(f, "%d %06X\\n", snes_frame_counter, off); }\n'
                    '  fflush(f); ++n; }\n')
                call = ('  bm_rom_trace(bank, adr);\n  uint8_t *native = bm_content_resolve(cart->rom, bank, adr);')
                if 'bm_rom_trace' not in text:
                    text = text.replace('uint8_t *cart_getRomPtr(Cart *cart, uint8_t bank, uint16_t adr) {',
                                        helper + 'uint8_t *cart_getRomPtr(Cart *cart, uint8_t bank, uint16_t adr) {')
                    text = text.replace('  uint8_t *native = bm_content_resolve(cart->rom, bank, adr);', call)
                    runtime_cart.write_text(text)
                    print('rom trace injected into', runtime_cart)
        # Room-scoped VRAM patch (env gated, BM_VRAM_PATCH=<pack>). Loads a
        # packed VRAM image once, when the game enters the given room.
        if os.environ.get('BM_DIAG_VRAM_PATCH') == '1':
            runtime_cart = (ROOT / 'local/native-content-runtime' / args.target /
                            'runner/src/snes/cart.c')
            if runtime_cart.is_file():
                text = runtime_cart.read_text()
                if 'bm_vram_patch' not in text:
                    helper = (
                        '/* Room-scoped VRAM patch (env gated, BM_VRAM_PATCH). */\n'
                        'static void bm_vram_patch(void) {\n'
                        '  extern Snes *g_snes;\n'
                        '  static int state;\n'
                        '  if (state || !g_snes || !g_snes->ram || !g_snes->ppu) return;\n'
                        '  unsigned room = (unsigned)g_snes->ram[0x10B] |\n'
                        '                  ((unsigned)g_snes->ram[0x10C] << 8);\n'
                        '  if (room != 0x0190u) return;\n'
                        '  const char *p = getenv("BM_VRAM_PATCH");\n'
                        '  if (!p || !*p) { state = 1; return; }\n'
                        '  FILE *f = fopen(p, "rb");\n'
                        '  if (!f) { state = 1; return; }\n'
                        '  unsigned n = 0;\n'
                        '  if (fread(&n, 4, 1, f) != 1) { fclose(f); state = 1; return; }\n'
                        '  for (unsigned i = 0; i < n; i++) {\n'
                        '    unsigned short a, c, w;\n'
                        '    if (fread(&a, 2, 1, f) != 1) break;\n'
                        '    if (fread(&c, 2, 1, f) != 1) break;\n'
                        '    for (unsigned k = 0; k < c; k++) {\n'
                        '      if (fread(&w, 2, 1, f) != 1) { a = 0; c = 0; break; }\n'
                        '      g_snes->ppu->vram[(a + k) & 0x7FFF] = w;\n'
                        '    }\n'
                        '  }\n'
                        '  fclose(f); state = 1; }\n')
                    text = text.replace('uint8_t *cart_getRomPtr(Cart *cart, uint8_t bank, uint16_t adr) {',
                                        helper + 'uint8_t *cart_getRomPtr(Cart *cart, uint8_t bank, uint16_t adr) {')
                    text = text.replace('  if (bank == 0x7e || bank == 0x7f) return NULL;',
                                        '  if (bank == 0x7e || bank == 0x7f) return NULL;\n  bm_vram_patch();')
                    runtime_cart.write_text(text)
                    print('vram patch injected into', runtime_cart)
        cmake = EXPERIMENT / 'CMakeLists.txt'
        support = f'target_sources({TARGET} PRIVATE "{ROOT / "recomp/aot_timing.c"}")'
        if support not in cmake.read_text():
            cmake.write_text(cmake.read_text() + '\n# Instruction-paced AOT support.\n' + support + '\n')
        cmake_args = ['cmake', '-S', EXPERIMENT, '-B', BUILD, '-G', 'Ninja',
                      '-DCMAKE_BUILD_TYPE=Release', f'-DSNESRECOMP_ROOT={ENGINE}',
                      '-DSNESRECOMP_SDL_BACKEND=SDL2', '-DSNESRECOMP_SDL3_FETCH=OFF',
                      '-DSNESRECOMP_AUDIO_TRACE_HISTORY=' + ('FULL' if args.audio else 'SMALL'),
                      '-DSNESRECOMP_FRAME_IMPL=LLE']
        # Diagnostic only: enable the PPU/DMA history rings so a capture can log
        # the DMA source address of a VRAM transfer. Off unless the operator asks.
        if os.environ.get('BM_DIAG_PPU_DMA_HISTORY') == '1':
            cmake_args.append('-DSNESRECOMP_ENABLE_PPU_DMA_HISTORY=ON')
        # Diagnostic only: compile the CPU trace facility (block/DB/ring probes).
        if os.environ.get('BM_DIAG_CPU_TRACE') == '1':
            cmake_args.append('-DSNESRECOMP_ENABLE_TRACE=ON')
        run(cmake_args, log=reports / 'native-configure.log')
        run(['cmake', '--build', BUILD, '--parallel', '2'], log=reports / 'native-build.log')
        (BUILD / 'm1-build.json').write_text(json.dumps({
            'rom_sha256': hashlib.sha256(ROM.read_bytes()).hexdigest(),
            'binary_sha256': hashlib.sha256((BUILD / TARGET).read_bytes()).hexdigest(),
            'runtime_patches': runtime_patches,
            'native_content': native_content,
            'audio_diagnostics': args.audio,
            'analysis': analysis_identity(),
        }, indent=2) + '\n')
    else:
        name = args.capture or args.stage + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise ValueError('capture name must contain only letters, digits, hyphens or underscores')
        directory = ROOT / 'local/captures' / name
        directory.mkdir(parents=True, exist_ok=False)
        env = os.environ.copy()
        script = args.script.resolve() if args.script else ROOT / 'recomp/inputs/m1-route.script'
        if args.stage == 'reference':
            env.update(SNESREF_HEADLESS='1', SNESREF_WRAM_FILL='0',
                       SNESREF_SCRIPT=str(script), SNESREF_DUMP_DIR=str(directory),
                       SNESREF_TRACE_FILE=str(directory / 'wram.jsonl'),
                       SNESREF_WAV=str(directory / 'audio.wav'))
            if SEPARATE_ECHO and 'snes9x_echo_buffer_hack=' not in env.get('SNESREF_CORE_OPTIONS', ''):
                env['SNESREF_CORE_OPTIONS'] = ';'.join(filter(None, [
                    env.get('SNESREF_CORE_OPTIONS'), 'snes9x_echo_buffer_hack=enabled']))
            command = [ROOT / 'local/build/snesref/snesref',
                       ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so', ROM]
        else:
            script_copy = directory / 'input.script'
            script_copy.write_text(('' if args.audio else 'turbo on\n') + script.read_text())
            config_file = ROOT / 'recomp/m1-config.ini'
            if args.renderer or args.audio_device_rate:
                config_file = directory / 'config.ini'
                settings = (ROOT / 'recomp/m1-config.ini').read_text()
                if args.renderer:
                    settings = settings.replace('NewRenderer=0', 'NewRenderer=' + str(int(args.renderer == 'optimized')))
                if args.audio_device_rate:
                    settings = settings.replace('EnableAudio=1', 'EnableAudio=1\nAudioFreq=' + str(args.audio_device_rate))
                config_file.write_text(settings)
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                       M1_APU_DUMP=str(directory / 'apu-ram.bin'),
                       M1_TIMING_TRACE=str(directory / 'timing.csv'),
                       SNESRECOMP_REWIND='0', SNESRECOMP_CPU_TRACE_RING_ENTRIES='65536',
                       SNESRECOMP_COVERAGE_DIR=str(directory / 'coverage'),
                       SNESRECOMP_DUMP_DIR=str(directory),
                       SNESRECOMP_STATE_TRACE=str(directory / 'state-trace.txt'))
            if args.audio:
                env.update(M1_AUDIO_WAV=str(directory / 'audio.wav'),
                           M1_AUDIO_REPORT=str(directory / 'audio-stats.json'),
                           SNESRECOMP_AUDIO_STATS=str(directory / 'audio-stats.txt'))
            if SEPARATE_ECHO:
                env.setdefault('SNESRECOMP_SEPARATE_ECHO', '1')
            env.setdefault('SNESRECOMP_APU_MASTER_CLOCK', '1')
            if native_child:
                child_environment(args.target, env)
            elif native_mazo:
                mazo_environment(args.target, env)
            elif native_gap:
                gap_environment(args.target, env)
            elif native_seven:
                seven_environment(args.target, env)
            elif native_sprite:
                sprite_environment(args.target, env)
            elif native_content:
                from native_content import settings
                spec = settings(args.target)[1]
                pack = ROOT / 'local/restoration' / args.target / spec['pack_file']
                verify(pack.read_bytes(), spec['payload'], 'native external pack')
                env['BM_NATIVE_CONTENT_PACK'] = str(pack)
            if args.interpreter_only:
                manifest = json.loads((EXPERIMENT / 'src/gen/program_manifest.json').read_text())
                pcs = {int(key.split(':')[0], 16) for key in manifest['nodes']}
                # The upstream gate canonicalizes LoROM mirrors at some sites.
                pcs |= {pc ^ 0x800000 for pc in pcs}
                targets = directory / 'interpreted-targets.txt'
                targets.write_text(''.join(f'{pc:06X}\n' for pc in sorted(pcs)))
                env['SNESRECOMP_LLE_INTERP_TARGET_FILE'] = str(targets)
                env['SNESRECOMP_LLE_BOUNCE'] = '0'
            command = [BUILD / TARGET, '--no-launcher',
                       '--config', config_file, '--coverage-capture=on',
                       '--script', script_copy, '--rom', ROM]
        if args.stage == 'native':
            (directory / 'program-manifest.json').write_bytes(
                (EXPERIMENT / 'src/gen/program_manifest.json').read_bytes())
        receipt = {
            'stage': args.stage,
            'target': args.target,
            'upstream_pins': pins,
            'runtime_patches': runtime_patches,
            'native_content': native_content,
            'rom_sha256': hashlib.sha256(ROM.read_bytes()).hexdigest(),
            'route_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
            'host_binary_sha256': hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
            'initial_state': 'Fresh capture directory; no imported SRAM or savestate',
            'lle_bounce_override': env.get('SNESRECOMP_LLE_BOUNCE', 'upstream default'),
            'interpreter_only_requested': args.interpreter_only,
            'renderer_override': args.renderer,
            'audio_diagnostics': args.audio,
            'audio_device_rate_override': args.audio_device_rate,
            'separate_echo_compatibility': env.get('SNESRECOMP_SEPARATE_ECHO', '0'),
            'apu_master_clock_override': env.get('SNESRECOMP_APU_MASTER_CLOCK', '0'),
            'analysis': analysis_identity() if args.stage == 'native' else None,
            'boot_instruction_trace': env.get('M1_BOOT_TRACE'),
            'instruction_trace_frames': env.get('M1_TRACE_FRAMES'),
            'reference_core_options': env.get('SNESREF_CORE_OPTIONS', 'defaults'),
        }
        (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        run(command, log=directory / 'run.log', cwd=directory, env=env, seconds=900)
        if args.interpreter_only and '[m1] aot_bridge_entries=0 ' not in (directory / 'run.log').read_text():
            raise RuntimeError('interpreter-only diagnostic still executed compiled bodies; reject comparison')
        print(f'Capture: {directory.relative_to(ROOT)}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit(f'm1: {exc}')
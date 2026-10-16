#!/usr/bin/env python3
"""Run an isolated, pinned reference capture for a separately prepared ROM.

Alternate versions and diagnostic ROM edits are exploration, not primary-target
qualification. Every capture records its ROM manifest and exact input script.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

from m1 import ROOT, pins_check, run
from prepare_rom import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--capture', required=True)
    parser.add_argument('--core', type=Path, help='explicit diagnostic core override, recorded by binary hash')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.capture):
        parser.error('capture name must contain only letters, digits, hyphens or underscores')
    pins = pins_check()
    manifest = json.loads(args.manifest.read_text())
    verify(args.rom.read_bytes(), manifest['output'], manifest['target'])
    directory = ROOT / 'local/captures' / args.capture
    directory.mkdir(parents=True, exist_ok=False)
    script = args.script.resolve()
    (directory / 'input.script').write_bytes(script.read_bytes())
    binary = ROOT / 'local/build/snesref/snesref'
    core = args.core.resolve() if args.core else ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so'
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    receipt = {'scope': __doc__.strip(), 'target_manifest': manifest,
               'upstream_pins': pins, 'rom_sha256': sha(args.rom),
               'script_sha256': sha(script), 'frontend_sha256': sha(binary),
               'core_sha256': sha(core), 'initial_state': 'Fresh capture directory; no imported SRAM or state'}
    receipt['diagnostic_core_override'] = str(core) if args.core else None
    receipt['instruction_trace'] = os.environ.get('BM_BOOT_TRACE')
    receipt['instruction_trace_frames'] = os.environ.get('BM_TRACE_FRAMES')
    (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    env = os.environ.copy()
    env.update(SNESREF_HEADLESS='1', SNESREF_WRAM_FILL='0',
               SNESREF_SCRIPT=str(directory / 'input.script'), SNESREF_DUMP_DIR=str(directory),
               SNESREF_TRACE_FILE=str(directory / 'wram.jsonl'),
               SNESREF_WAV=str(directory / 'audio.wav'))
    run([binary, core, args.rom.resolve()], log=directory / 'run.log', cwd=directory,
        env=env, seconds=120)


if __name__ == '__main__':
    main()

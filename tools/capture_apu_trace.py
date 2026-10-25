#!/usr/bin/env python3
"""Capture a reference run with an APU RAM trace.

The trace uses the diagnostic snes9x core patch at
patches/diagnostic/snes9x-apuram.patch. Apply the patch to
local/upstream/snes9x, rebuild the core, then restore the upstream tree before
this tool runs. The patched core binary stays in place, and the pinned
repository check expects a clean tree.

The trace is a JSON-lines changed-byte log. The first entry set is a full
0x10000-byte snapshot at frame 0. Later lines record per-frame changes.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--capture', required=True)
    parser.add_argument('--trace', type=Path, required=True)
    args = parser.parse_args()
    trace = args.trace.resolve()
    trace.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['SNESREF_APURAM_TRACE_FILE'] = str(trace)
    command = [sys.executable, str(ROOT / 'tools/probe_reference.py'),
               '--manifest', str(args.manifest.resolve()),
               '--rom', str(args.rom.resolve()),
               '--script', str(args.script.resolve()),
               '--capture', args.capture]
    result = subprocess.run(command, cwd=ROOT, env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    if not trace.exists():
        raise SystemExit('the core produced no APU trace; apply and rebuild the diagnostic patch')
    print(f'APU trace: {trace} ({trace.stat().st_size} bytes)')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Launch a native product build for interactive play.

The build needs the same environment variables that tools/m1.py sets for its
native stage. Without them the content packs are rejected at load. This tool
builds that environment, then starts the binary without a script so the user
can play.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def environment(target):
    """Return the environment that the native stage uses for this target."""
    sys.path.insert(0, str(ROOT / "tools"))
    import native_sprite
    import native_seven
    import native_mazo
    import native_sprite_gap
    import native_seven_child
    import native_content

    env = os.environ.copy()
    env.setdefault("SNESRECOMP_APU_MASTER_CLOCK", "1")
    env["SNESRECOMP_REWIND"] = "0"
    child = native_seven_child.identity(target)
    mazo = native_mazo.identity(target)
    gap = native_sprite_gap.identity(target)
    seven = None if (mazo or gap) else native_seven.identity(target)
    sprite = native_sprite.identity(target)
    if child:
        native_seven_child.environment(target, env)
    elif mazo:
        native_mazo.environment(target, env)
    elif gap:
        native_sprite_gap.environment(target, env)
    elif seven:
        native_seven.environment(target, env)
    elif sprite:
        native_sprite.environment(target, env)
    elif native_content.identity(target):
        from native_content import settings
        spec = settings(target)[1]
        pack = ROOT / "local/restoration" / target / spec["pack_file"]
        env["BM_NATIVE_CONTENT_PACK"] = str(pack)
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="demo11-native-product-r47")
    parser.add_argument("--lang", choices=["en", "ja", "auto"],
                        help="override runtime language via BM_LANG (en, ja, or auto)")
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--extra", nargs=argparse.REMAINDER,
                        help="arguments passed to the binary after the standard ones")
    args = parser.parse_args()
    build = ROOT / "local/build" / args.target
    names = [p for p in build.iterdir()
             if p.is_file() and p.name.startswith("BrutalMario")]
    if not names:
        raise SystemExit("no binary in " + str(build))
    binary = names[0]
    rom = args.rom or (ROOT / "local/restoration" / args.target / "rom.sfc")
    config = args.config or (build / "rom.cfg")
    command = [str(binary), "--no-launcher",
               "--config", str(config), "--rom", str(rom)]
    if args.extra:
        command.extend(args.extra)
    env = environment(args.target)
    if args.lang is not None:
        env["BM_LANG"] = args.lang
    print("launch:", " ".join(command))
    print("packs:", {k: v for k, v in env.items() if k.startswith("BM_")})
    return subprocess.call(command, cwd=str(build), env=env)


if __name__ == "__main__":
    sys.exit(main())

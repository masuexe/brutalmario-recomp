#!/usr/bin/env python3
"""Prepare demo11-native-product-r48: fix Room 0x116 countdown sprite GFX corruption when $1F01 bit 7 is set."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import native_sprite_gap
from restore_star_world_1 import lorom, sha, write_verified

PARENT = "demo11-native-product-r47"
TARGET = "demo11-native-product-r48"
R47_SHA = "2123f5e3415364d3a5def92b8ac3ab1f581ec68f0cf6469ffda12f4a9da80b0a"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"


def build_patches() -> list[dict]:
    """Return the 3 ROM patches against demo11-native-product-r47."""
    return [
        {
            "offset": lorom(0x00AA6F),
            "before": "c001",
            "after": "c901",
            "role": (
                "Check effective GFX indicator A == $01 (CMP #$01) instead of stale vanilla "
                "Y == $01 (CPY #$01) at $00:AA6F before $1F01 bit 7 GFX 0x31 overwrite."
            ),
        },
        {
            "offset": lorom(0x0FF19B),
            "before": "20b7f1",
            "after": "208cf8",
            "role": (
                "Route Vanilla / Standard GFX Bypass $0F:F19B JSR $F1B7 through $0F:F88C "
                "to preserve 8-bit GFX ID in A across decompression."
            ),
        },
        {
            "offset": lorom(0x0FF884),
            "before": "a9016020b7f180f5ffffffffffffffffffffffffffffffffffffffffffff",
            "after": "a902604c92f8eaea4820b7f168604820b7f168c90100d0e5287afaa90160",
            "role": (
                "Update $0F:F840 Super GFX Bypass epilogue ($0F:F884..$0F:F8A1) to return "
                "A=$01 iff effective decompressed GFX ID == $0001 and A=$02 otherwise, "
                "preserving Y and $0F:F160 entry stack depth."
            ),
        },
    ]


def write_symbols_toml() -> None:
    """Copy r47 symbols.toml to r48 with updated header comment."""
    r47_sym = ROOT / "recomp/targets" / PARENT / "symbols.toml"
    r48_sym = ROOT / "recomp/targets" / TARGET / "symbols.toml"
    r48_sym.parent.mkdir(parents=True, exist_ok=True)
    text = r47_sym.read_text(encoding="utf-8")
    old_hdr = "# Symbol map for Brutal Mario Demo11 Product R47."
    new_hdr = "# Symbol map for Brutal Mario Demo11 Product R48."
    assert old_hdr in text, "unexpected r47 symbols.toml header"
    r48_sym.write_text(text.replace(old_hdr, new_hdr, 1), encoding="utf-8")


def prepare() -> None:
    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text(encoding="utf-8"))
    r47_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r47_rom = r47_rom_path.read_bytes()
    assert len(r47_rom) == 4194304, len(r47_rom)
    assert sha(r47_rom) == R47_SHA, f"r47 ROM SHA-256 mismatch: {sha(r47_rom)}"
    assert parent_cfg["output"]["sha256"] == R47_SHA

    patches = build_patches()
    patched_rom = bytearray(r47_rom)
    for patch in patches:
        off = patch["offset"]
        before = bytes.fromhex(patch["before"])
        after = bytes.fromhex(patch["after"])
        assert len(before) == len(after)
        assert patched_rom[off : off + len(before)] == before, (
            hex(off),
            patched_rom[off : off + len(before)].hex(),
            patch["before"],
        )
        patched_rom[off : off + len(after)] = after
    r48_sha = sha(bytes(patched_rom))

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["target"] = "Brutal Mario Demo11 Product R48"
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R47_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["scope"] = (
        "Fix Room 0x116 countdown sprite GFX corruption when $1F01 bit 7 (overworld/complete "
        "flag) is set: return effective decompressed GFX indicator in A from $0F:F160/$0F:F840 "
        "(A=$01 iff effective GFX == $0001, A=$02 for other Super GFX Bypass slots, preserving "
        "vanilla Y and entry stack depth) and test CMP #$01 at $00:AA6F instead of stale CPY #$01."
    )
    cfg["native_sprite_gap"]["frozen_manifests"] = list(
        cfg["native_sprite_gap"]["manifests"]
    )
    cfg["native_sprite_gap"]["extra_patches"] = patches
    cfg["code_patches"] = [
        {
            "address": f"{p['offset']:06X}",
            "before": p["before"],
            "after": p["after"],
            "role": p["role"],
        }
        for p in patches
    ]
    cfg["output"] = {"size": 4194304, "sha256": r48_sha}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    write_symbols_toml()
    native_sprite_gap.prepare(TARGET)

    r47_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r47_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r48_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r48_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 71, f"expected 71 packs, got {len(collected)}"
    print(f"Prepared {TARGET}: rom_sha256={r48_sha}, packs={len(collected)}")


if __name__ == "__main__":
    prepare()

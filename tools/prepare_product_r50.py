#!/usr/bin/env python3
"""Prepare demo11-native-product-r50: cumulative r49 + Demo 6 / Demo 7 New-Save Yoshi's House spawn."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import native_sprite_gap
from restore_star_world_1 import lorom, sha, write_verified

PARENT = "demo11-native-product-r49"
TARGET = "demo11-native-product-r50"
R49_SHA = "bbd52ff43fe86e872ee2c55da7adf40ca0eb52e117d529bc5449f3aae5b1bc52"
DEMO7_SHA = "f462ddd7c30a641e57b586ebae003adc5eb3a5f19579d2348022b2be8934eae4"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"
EXPECTED_R50_ROM_SHA = "81ef0720233c18a2fa687f3d0d69768ce7c94904e21f00cceaed5379e88909a4"

EXPECTED_DEMO7_INITIAL_SAVE_DATA = bytes.fromhex(
    "00000200020068009801680098010600190006001900"
)


def build_patches() -> list[dict]:
    """Return the 4 SMW InitialSaveData patches against demo11-native-product-r49."""
    return [
        {
            "offset": lorom(0x009EF6),
            "before": "4800",
            "after": "6800",
            "role": (
                "Restore demo6/demo7 Mario New-Save Overworld X ($1FB8+6 -> $1F17) "
                "from 1-1 (72) to Yoshi's House (104)."
            ),
        },
        {
            "offset": lorom(0x009EFA),
            "before": "4800",
            "after": "6800",
            "role": (
                "Restore demo6/demo7 Luigi New-Save Overworld X ($1FB8+10 -> $1F1B) "
                "from 1-1 (72) to Yoshi's House (104)."
            ),
        },
        {
            "offset": lorom(0x009EFE),
            "before": "0400",
            "after": "0600",
            "role": (
                "Restore demo6/demo7 Mario New-Save Overworld X>>4 tile ($1FB8+14 -> $1F1F) "
                "from 4 to 6."
            ),
        },
        {
            "offset": lorom(0x009F02),
            "before": "0400",
            "after": "0600",
            "role": (
                "Restore demo6/demo7 Luigi New-Save Overworld X>>4 tile ($1FB8+18 -> $1F23) "
                "from 4 to 6."
            ),
        },
    ]


def verify_demo7_reference() -> bytes:
    """Verify local demo7 ROM matches config/content-versions.json and pinned InitialSaveData."""
    versions_cfg = json.loads(
        (ROOT / "config/content-versions.json").read_text(encoding="utf-8")
    )
    demo7_entry = next(
        (v for v in versions_cfg["versions"] if v["id"] == "demo7"),
        None,
    )
    assert demo7_entry is not None, "missing demo7 entry in config/content-versions.json"
    assert demo7_entry["output"]["size"] == 4194304, demo7_entry["output"]
    assert demo7_entry["output"]["sha256"] == DEMO7_SHA, demo7_entry["output"]

    demo7_rom_path = ROOT / "local/content-versions/demo7/rom.sfc"
    demo7_rom = demo7_rom_path.read_bytes()
    assert len(demo7_rom) == 4194304, len(demo7_rom)
    assert sha(demo7_rom) == DEMO7_SHA, f"demo7 ROM SHA-256 mismatch: {sha(demo7_rom)}"
    save_off = lorom(0x009EF0)
    assert demo7_rom[save_off : save_off + 22] == EXPECTED_DEMO7_INITIAL_SAVE_DATA, (
        demo7_rom[save_off : save_off + 22].hex()
    )
    return demo7_rom


def write_symbols_toml() -> None:
    """Copy r49 symbols.toml to r50 with updated header comment."""
    r49_sym = ROOT / "recomp/targets" / PARENT / "symbols.toml"
    r50_sym = ROOT / "recomp/targets" / TARGET / "symbols.toml"
    r50_sym.parent.mkdir(parents=True, exist_ok=True)
    text = r49_sym.read_text(encoding="utf-8")
    old_hdr = "# Symbol map for Brutal Mario Demo11 Product R49."
    new_hdr = "# Symbol map for Brutal Mario Demo11 Product R50."
    assert old_hdr in text, "unexpected r49 symbols.toml header"
    r50_sym.write_text(text.replace(old_hdr, new_hdr, 1), encoding="utf-8")


def prepare() -> None:
    demo7_rom = verify_demo7_reference()

    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text(encoding="utf-8"))
    r49_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r49_rom = r49_rom_path.read_bytes()
    assert len(r49_rom) == 4194304, len(r49_rom)
    assert sha(r49_rom) == R49_SHA, f"r49 ROM SHA-256 mismatch: {sha(r49_rom)}"
    assert parent_cfg["output"]["sha256"] == R49_SHA

    patches = build_patches()
    patched_rom = bytearray(r49_rom)
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

    save_off = lorom(0x009EF0)
    assert patched_rom[save_off : save_off + 22] == demo7_rom[save_off : save_off + 22]
    r50_sha = sha(bytes(patched_rom))
    assert r50_sha == EXPECTED_R50_ROM_SHA, f"r50 ROM SHA-256 mismatch: {r50_sha}"

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["target"] = "Brutal Mario Demo11 Product R50"
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R49_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["scope"] = (
        "Cumulative r49 (r48 Room 0x116 countdown ExGFX 0x12A + Demo 7 English Overworld names) "
        "+ Demo 6 / Demo 7 New-Save Yoshi's House Overworld spawn in SMW InitialSaveData "
        "($00:9EF0..$00:9F05): restore Mario/Luigi Overworld X ($1F17/$1F1B) from 72 (0x0048) "
        "to 104 (0x0068) and X>>4 tile ($1F1F/$1F23) from 4 (0x0004) to 6 (0x0006)."
    )
    cfg["native_sprite_gap"]["frozen_manifests"] = list(
        parent_cfg["native_sprite_gap"]["frozen_manifests"]
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
    cfg["output"] = {"size": 4194304, "sha256": r50_sha}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    write_symbols_toml()
    native_sprite_gap.prepare(TARGET)

    r49_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r49_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r50_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r50_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 71, f"expected 71 packs, got {len(collected)}"
    print(f"Prepared {TARGET}: rom_sha256={r50_sha}, packs={len(collected)}")


if __name__ == "__main__":
    prepare()

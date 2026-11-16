#!/usr/bin/env python3
"""Prepare demo11-native-product-r51: cumulative r50 + World 4 & World 6 Overworld map BGM repair."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import native_sprite_gap
from restore_star_world_1 import lorom, sha, write_verified

PARENT = "demo11-native-product-r50"
TARGET = "demo11-native-product-r51"
R50_SHA = "81ef0720233c18a2fa687f3d0d69768ce7c94904e21f00cceaed5379e88909a4"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"
EXPECTED_OVERWORLD_MUSIC_TABLE = bytes.fromhex("1e232225292726")
EXPECTED_R50_INITIAL_SAVE_DATA = bytes.fromhex(
    "00000200020068009801680098010600190006001900"
)
EXPECTED_R51_ROM_SHA = "be82cf49edd22a975fbce35ac7d570260494fc7812715fd2862f497504ce5948"


def build_patches() -> list[dict]:
    """Return the 4 OverworldMusic / OverworldMusic2 byte patches against demo11-native-product-r50."""
    return [
        {
            "offset": lorom(0x048D8B),
            "before": "22",
            "after": "23",
            "role": "OverworldMusic submap 1 (World 6 Sky): 0x22 -> 0x23 (match demoOnly1)",
        },
        {
            "offset": lorom(0x048D8C),
            "before": "27",
            "after": "22",
            "role": "OverworldMusic submap 2 (World 4 Cave): 0x27 -> 0x22 (match demoOnly1)",
        },
        {
            "offset": lorom(0x04DBC9),
            "before": "22",
            "after": "23",
            "role": "OverworldMusic2 submap 1 (World 6 Sky): 0x22 -> 0x23 (match demoOnly1)",
        },
        {
            "offset": lorom(0x04DBCA),
            "before": "27",
            "after": "22",
            "role": "OverworldMusic2 submap 2 (World 4 Cave): 0x27 -> 0x22 (match demoOnly1)",
        },
    ]


def verify_demo_only_1_reference() -> bytes:
    """Verify local demo-only-1 ROM matches config/content-versions.json and pinned Overworld music tables."""
    versions_cfg = json.loads(
        (ROOT / "config/content-versions.json").read_text(encoding="utf-8")
    )
    do1_entry = next(
        (v for v in versions_cfg["versions"] if v["id"] == "demo-only-1"),
        None,
    )
    assert do1_entry is not None, "missing demo-only-1 entry in config/content-versions.json"
    expected_size = do1_entry["output"]["size"]
    expected_sha = do1_entry["output"]["sha256"]
    assert expected_size == 4194304, do1_entry["output"]

    do1_rom_path = ROOT / "local/content-versions/demo-only-1/rom.sfc"
    do1_rom = do1_rom_path.read_bytes()
    assert len(do1_rom) == expected_size, len(do1_rom)
    assert sha(do1_rom) == expected_sha, f"demo-only-1 ROM SHA-256 mismatch: {sha(do1_rom)}"

    table_a = lorom(0x048D8A)
    table_b = lorom(0x04DBC8)
    assert do1_rom[table_a : table_a + 7] == EXPECTED_OVERWORLD_MUSIC_TABLE, (
        do1_rom[table_a : table_a + 7].hex()
    )
    assert do1_rom[table_b : table_b + 7] == EXPECTED_OVERWORLD_MUSIC_TABLE, (
        do1_rom[table_b : table_b + 7].hex()
    )
    return do1_rom


def write_symbols_toml() -> None:
    """Copy r50 symbols.toml to r51 with updated header comment."""
    r50_sym = ROOT / "recomp/targets" / PARENT / "symbols.toml"
    r51_sym = ROOT / "recomp/targets" / TARGET / "symbols.toml"
    r51_sym.parent.mkdir(parents=True, exist_ok=True)
    text = r50_sym.read_text(encoding="utf-8")
    old_hdr = "# Symbol map for Brutal Mario Demo11 Product R50."
    new_hdr = "# Symbol map for Brutal Mario Demo11 Product R51."
    assert old_hdr in text, "unexpected r50 symbols.toml header"
    r51_sym.write_text(text.replace(old_hdr, new_hdr, 1), encoding="utf-8")


def prepare() -> None:
    do1_rom = verify_demo_only_1_reference()

    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text(encoding="utf-8"))
    r50_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r50_rom = r50_rom_path.read_bytes()
    assert len(r50_rom) == 4194304, len(r50_rom)
    assert sha(r50_rom) == R50_SHA, f"r50 ROM SHA-256 mismatch: {sha(r50_rom)}"
    assert parent_cfg["output"]["sha256"] == R50_SHA

    patches = build_patches()
    patched_rom = bytearray(r50_rom)
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

    table_a = lorom(0x048D8A)
    table_b = lorom(0x04DBC8)
    assert patched_rom[table_a : table_a + 7] == EXPECTED_OVERWORLD_MUSIC_TABLE
    assert patched_rom[table_b : table_b + 7] == EXPECTED_OVERWORLD_MUSIC_TABLE
    assert patched_rom[table_a : table_a + 7] == do1_rom[table_a : table_a + 7]
    assert patched_rom[table_b : table_b + 7] == do1_rom[table_b : table_b + 7]

    save_off = lorom(0x009EF0)
    assert patched_rom[save_off : save_off + 22] == EXPECTED_R50_INITIAL_SAVE_DATA

    r51_sha = sha(bytes(patched_rom))
    assert r51_sha == EXPECTED_R51_ROM_SHA, f"r51 ROM SHA-256 mismatch: {r51_sha}"

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["target"] = "Brutal Mario Demo11 Product R51"
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R50_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["scope"] = (
        "Cumulative r50 (r49 Demo 7 English Overworld names + r48 Room 0x116 countdown ExGFX 0x12A + "
        "Demo 6/7 Yoshi's House InitialSaveData) + Overworld map BGM repair for World 4 and World 6: "
        "restore OverworldMusic ($04:8D8A) and OverworldMusic2 ($04:DBC8) submap 1 (World 6 Sky) "
        "0x22 -> 0x23 and submap 2 (World 4 Cave) 0x27 -> 0x22 to match demoOnly1 (1E 23 22 25 29 27 26)."
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
    cfg["output"] = {"size": 4194304, "sha256": r51_sha}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    write_symbols_toml()
    native_sprite_gap.prepare(TARGET)

    r50_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r50_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r51_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r51_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 71, f"expected 71 packs, got {len(collected)}"
    print(f"Prepared {TARGET}: rom_sha256={r51_sha}, packs={len(collected)}")


if __name__ == "__main__":
    prepare()

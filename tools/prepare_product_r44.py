#!/usr/bin/env python3
"""Prepare demo11-native-product-r44: upgrade ExGFX 0x1B2 from cheap-demo to demo-only-1."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import native_sprite_gap
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset, sha, write_verified

PARENT = "demo11-native-product-r43"
TARGET = "demo11-native-product-r44"
R43_SHA = "8400f89dcc552170373548d1f10a6dd147df9e7c7622e1ecf3ceb6f0b8180dbd"
R44_SHA = "8014c789ac9bf9f79d2972f7100ae2c677d7f7489e49c87801dadd4340d4a69b"
DONOR_SHA = "b8d86f894f6c07aeb74794c59adab8f336080285b4781a3e1c921615a2d8216b"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"

GFX_ID = 0x1B2
DONOR_PTR = 0x20F10C
STREAM_SIZE = 2175
STREAM_SHA = "c045d50b8c107e807c9c661177940667f47b8c38ae0674203a035d8ee0f22778"
DECODED_SIZE = 4096
DECODED_SHA = "23c81a9ae6106d21facd642e54e1a6b9ec338c2f19ca1b03f06548198b14d529"
PACK_ADDRESS = 0xD28000
PACK_SOURCE = "local/native-modules/exgfx-1b2-v1"
PACK_FILE = "exgfx-1b2.bin"
PACK_VAR = "BM_EXGFX_1B2_PACK"
PTR_PC_OFFSET = 0x0A021E  # 655902 == lorom(0x14821E)


def find_donor_rom() -> Path:
    for rel in (
        "local/content-versions/demo-only-1/rom.sfc",
        "local/roms/demo-only-1.sfc",
    ):
        candidate = ROOT / rel
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("demo-only-1 donor ROM not found")


def prepare() -> None:
    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text())
    r43_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r43_rom = r43_rom_path.read_bytes()
    assert len(r43_rom) == 4194304, len(r43_rom)
    assert sha(r43_rom) == R43_SHA, f"r43 ROM SHA-256 mismatch: {sha(r43_rom)}"
    assert parent_cfg["output"]["sha256"] == R43_SHA

    # Verify bank D2 is unoccupied in parent packs.
    assert all(
        int(p["address"], 16) >> 16 != PACK_ADDRESS >> 16
        for p in native_sprite_gap.packs(PARENT)
    ), "native bank D2 already occupied"

    donor_rom = find_donor_rom().read_bytes()
    assert len(donor_rom) == 4194304, len(donor_rom)
    assert sha(donor_rom) == DONOR_SHA, f"demo-only-1 SHA-256 mismatch: {sha(donor_rom)}"

    ptr = graphics_pointer(donor_rom, GFX_ID)
    assert ptr == DONOR_PTR, f"unexpected donor pointer: 0x{ptr:06X}"
    decoded, stream = lz2(donor_rom, ptr, limit=0x10000)
    assert len(stream) == STREAM_SIZE, len(stream)
    assert sha(stream) == STREAM_SHA, sha(stream)
    assert len(decoded) == DECODED_SIZE, len(decoded)
    assert sha(decoded) == DECODED_SHA, sha(decoded)

    off = pointer_offset(GFX_ID)
    assert off == PTR_PC_OFFSET == 655902, off
    assert lorom(0x14821E) == PTR_PC_OFFSET
    assert r43_rom[off : off + 3] == bytes.fromhex("38f22f"), r43_rom[off : off + 3].hex()

    pack_dir = ROOT / PACK_SOURCE
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_path = pack_dir / PACK_FILE
    if pack_path.exists():
        assert pack_path.read_bytes() == stream, "existing exgfx-1b2.bin differs"
    else:
        write_verified(pack_path, stream)

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R43_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["scope"] = (
        "Upgrade ExGFX 0x1B2 pointer at $14:821E (PC 0x0A021E) from older "
        "cheap-demo ROM stream ($2F:F238, 1930B) to the demo-only-1 stream in "
        "native bank D2 ($D2:8000, 2175B), restoring sun, horizon glow, and "
        "moving snow/ice platform tiles in room 0x134."
    )
    cfg["native_sprite_gap"]["frozen_manifests"] = list(
        cfg["native_sprite_gap"]["manifests"]
    )
    cfg["native_sprite_gap"]["extra_packs"].append(
        {
            "variable": PACK_VAR,
            "pack_file": PACK_FILE,
            "address": f"{PACK_ADDRESS:06X}",
            "size": STREAM_SIZE,
            "sha256": STREAM_SHA,
            "executable": False,
            "source": PACK_SOURCE,
        }
    )
    cfg["native_sprite_gap"]["extra_patches"] = [
        {
            "offset": PTR_PC_OFFSET,
            "before": "38f22f",
            "after": "0080d2",
            "role": (
                "Upgrade ExGFX 1B2 pointer at 0x0A021E from older cheap-demo "
                "ROM copy ($2F:F238) to demo-only-1 stream in native bank D2 ($D2:8000)."
            ),
        }
    ]
    cfg["code_patches"] = [
        {
            "address": "0A021E",
            "before": "38f22f",
            "after": "0080d2",
            "role": (
                "Upgrade ExGFX 1B2 pointer at $14:821E (PC 0x0A021E) from older "
                "cheap-demo ROM copy ($2F:F238) to demo-only-1 stream in native bank D2 ($D2:8000)."
            ),
        }
    ]
    cfg["output"] = {"size": 4194304, "sha256": R44_SHA}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_text = json.dumps(cfg, indent=2) + "\n"
    if cfg_path.exists():
        assert cfg_path.read_text() == cfg_text, "existing r44 config differs"
    else:
        cfg_path.write_text(cfg_text)

    native_sprite_gap.prepare(TARGET)

    r43_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r43_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r44_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r44_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 66, f"expected 66 packs, got {len(collected)}"
    print(f"Prepared {TARGET}: rom_sha256={R44_SHA}, packs={len(collected)}")


if __name__ == "__main__":
    prepare()

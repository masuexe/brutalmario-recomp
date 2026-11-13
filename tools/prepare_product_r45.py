#!/usr/bin/env python3
"""Prepare demo11-native-product-r45: restore corrupted 0x257, 5 pure-addition ExGFX, and 2 NULL $0F:F600 pointers."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import native_sprite_gap
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset, sha, write_verified

PARENT = "demo11-native-product-r44"
TARGET = "demo11-native-product-r45"
R44_SHA = "8014c789ac9bf9f79d2972f7100ae2c677d7f7489e49c87801dadd4340d4a69b"
R45_SHA = "d13003a1e9a7c0a473f97af885a0740cdb40539d2b10b30c4f5fa676de7611e2"
BOSS_SHA = "337fe036f943dafb0df70bdb556e588b785c58ff019b1b00c08f77743e2b3ccd"
DO1_SHA = "b8d86f894f6c07aeb74794c59adab8f336080285b4781a3e1c921615a2d8216b"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"

PACK_ADDRESS = 0xD38000
PACK_SIZE = 14530
PACK_SHA = "965b85b0ea22473deb44a74eab0e57c0a0f2d38658cbbf16420f8089df22252a"
PACK_SOURCE = "local/native-modules/exgfx-r45-v1"
PACK_FILE = "exgfx-r45.bin"
PACK_VAR = "BM_EXGFX_R45_PACK"

EXGFX_SPECS = [
    {
        "gid": 0x257,
        "donor": "boss",
        "donor_ptr": 0x3C921A,
        "stream_size": 2204,
        "stream_sha": "ffed9c3992e3ecad0e65ef8104c2c7a7256ead4f10f2a5ec061d43d183574cc7",
        "decoded_sha": "a62fe2a792e7f230f26bd492ed7d26ff5afe88fb59faa6c782f71a5b59404895",
        "pc_offset": 0x0A040D,
        "before": "88cc42",
        "kind": "corrupt_r34",
        "role": (
            "Restore ExGFX 0x257 pointer at $14:840D (PC 0x0A040D) from r34-corrupted "
            "stream ($42:CC88) to boss/cheap-demo stream in native bank D3 ($D3:8000) "
            "for sprite2e Wily Capsule P2."
        ),
    },
    {
        "gid": 0x1E3,
        "donor": "boss",
        "donor_ptr": 0x32E5D0,
        "stream_size": 2551,
        "pc_offset": 0x0A02B1,
        "before": "49c44c",
        "kind": "pure_add",
        "added_tiles": 105,
        "role": (
            "Upgrade ExGFX 0x1E3 pointer at $14:82B1 (PC 0x0A02B1) from $4C:C449 to "
            "boss pure +105-tile stream in native bank D3 ($D3:889C) for room 0x0E4 SP4."
        ),
    },
    {
        "gid": 0x163,
        "donor": "demo-only-1",
        "donor_ptr": 0x20C8CA,
        "stream_size": 1148,
        "pc_offset": 0x0A0131,
        "before": "08b24c",
        "kind": "pure_add",
        "added_tiles": 1,
        "role": (
            "Upgrade ExGFX 0x163 pointer at $14:8131 (PC 0x0A0131) from $4C:B208 to "
            "demo-only-1 pure +1-tile stream in native bank D3 ($D3:9293) for rooms "
            "0x072, 0x117, 0x125, 0x176 SP2."
        ),
    },
    {
        "gid": 0x18F,
        "donor": "demo-only-1",
        "donor_ptr": 0x20D41C,
        "stream_size": 1213,
        "pc_offset": 0x0A01B5,
        "before": "2dbd5c",
        "kind": "pure_add",
        "added_tiles": 8,
        "role": (
            "Upgrade ExGFX 0x18F pointer at $14:81B5 (PC 0x0A01B5) from $5C:BD2D to "
            "demo-only-1 pure +8-tile stream in native bank D3 ($D3:970F) for rooms "
            "0x022, 0x097, 0x098, 0x09D, 0x175 SP4."
        ),
    },
    {
        "gid": 0x192,
        "donor": "demo-only-1",
        "donor_ptr": 0x20DBB6,
        "stream_size": 917,
        "pc_offset": 0x0A01BE,
        "before": "f8b65c",
        "kind": "pure_add",
        "added_tiles": 8,
        "role": (
            "Upgrade ExGFX 0x192 pointer at $14:81BE (PC 0x0A01BE) from $5C:B6F8 to "
            "demo-only-1 pure +8-tile stream in native bank D3 ($D3:9BCC) for rooms "
            "0x022, 0x175 BG3."
        ),
    },
    {
        "gid": 0x1AE,
        "donor": "demo-only-1",
        "donor_ptr": 0x20DF53,
        "stream_size": 1548,
        "pc_offset": 0x0A0212,
        "before": "d8d934",
        "kind": "pure_add",
        "added_tiles": 5,
        "role": (
            "Upgrade ExGFX 0x1AE pointer at $14:8212 (PC 0x0A0212) from $34:D9D8 to "
            "demo-only-1 pure +5-tile stream in native bank D3 ($D3:9F61) for rooms "
            "0x117, 0x176 BG2."
        ),
    },
    {
        "gid": 0x0DA,
        "donor": "boss",
        "donor_ptr": 0x4A94A6,
        "stream_size": 2768,
        "pc_offset": 0x07F70E,
        "before": "000000",
        "kind": "null_ptr",
        "role": (
            "Restore NULL ExGFX 0x0DA pointer at $0F:F70E (PC 0x07F70E) from 000000 "
            "to boss stream in native bank D3 ($D3:A56D) for rooms 0x0EE, 0x152 BG3."
        ),
    },
    {
        "gid": 0x0BE,
        "donor": "demo-only-1",
        "donor_ptr": 0x28DCE8,
        "stream_size": 2181,
        "pc_offset": 0x07F6BA,
        "before": "000000",
        "kind": "null_ptr",
        "role": (
            "Restore NULL ExGFX 0x0BE pointer at $0F:F6BA (PC 0x07F6BA) from 000000 "
            "to demo-only-1 stream in native bank D3 ($D3:B03D) for rooms "
            "0x062, 0x06C, 0x0C2 ANM."
        ),
    },
]


def find_donor_rom(name: str) -> Path:
    candidates = {
        "boss": ("local/content-versions/boss/rom.sfc", "local/roms/boss.sfc"),
        "demo-only-1": ("local/content-versions/demo-only-1/rom.sfc", "local/roms/demo-only-1.sfc"),
    }[name]
    for rel in candidates:
        candidate = ROOT / rel
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"{name} donor ROM not found")


def exgfx_pc_offset(gid: int) -> int:
    if 0x80 <= gid < 0x100:
        return lorom(0x0FF600) + (gid - 0x80) * 3
    return pointer_offset(gid)


def tile_diff_counts(dec_before: bytes, dec_after: bytes) -> tuple[int, int, int]:
    added = modified = zeroed = 0
    zero_tile = b"\x00" * 32
    for idx in range(128):
        a = dec_before[idx * 32 : (idx + 1) * 32]
        b = dec_after[idx * 32 : (idx + 1) * 32]
        if a == b:
            continue
        if a == zero_tile and b != zero_tile:
            added += 1
        elif b == zero_tile:
            zeroed += 1
        else:
            modified += 1
    return added, modified, zeroed


def prepare() -> None:
    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text())
    r44_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r44_rom = r44_rom_path.read_bytes()
    assert len(r44_rom) == 4194304, len(r44_rom)
    assert sha(r44_rom) == R44_SHA, f"r44 ROM SHA-256 mismatch: {sha(r44_rom)}"
    assert parent_cfg["output"]["sha256"] == R44_SHA

    # Verify bank D3 is unoccupied in parent packs.
    assert all(
        int(p["address"], 16) >> 16 != PACK_ADDRESS >> 16
        for p in native_sprite_gap.packs(PARENT)
    ), "native bank D3 already occupied"

    boss_rom = find_donor_rom("boss").read_bytes()
    assert len(boss_rom) == 4194304 and sha(boss_rom) == BOSS_SHA, sha(boss_rom)
    do1_rom = find_donor_rom("demo-only-1").read_bytes()
    assert len(do1_rom) == 4194304 and sha(do1_rom) == DO1_SHA, sha(do1_rom)
    donors = {"boss": boss_rom, "demo-only-1": do1_rom}

    pack_buf = bytearray()
    extra_patches = []
    code_patches = []
    cursor_addr = PACK_ADDRESS

    for spec in EXGFX_SPECS:
        gid = spec["gid"]
        donor_rom = donors[spec["donor"]]
        ptr = graphics_pointer(donor_rom, gid)
        assert ptr == spec["donor_ptr"], f"0x{gid:03X}: unexpected donor ptr 0x{ptr:06X}"

        decoded, stream = lz2(donor_rom, ptr, limit=0x10000)
        assert len(stream) == spec["stream_size"], (hex(gid), len(stream))
        assert len(decoded) == 4096, (hex(gid), len(decoded))
        assert any(decoded), f"0x{gid:03X}: decoded stream is all zero"
        if "stream_sha" in spec:
            assert sha(stream) == spec["stream_sha"], (hex(gid), sha(stream))
        if "decoded_sha" in spec:
            assert sha(decoded) == spec["decoded_sha"], (hex(gid), sha(decoded))

        off = exgfx_pc_offset(gid)
        assert off == spec["pc_offset"], (hex(gid), hex(off))
        assert r44_rom[off : off + 3] == bytes.fromhex(spec["before"]), (
            hex(gid),
            r44_rom[off : off + 3].hex(),
        )

        if spec["kind"] == "corrupt_r34":
            dec_r44, _ = lz2(r44_rom, graphics_pointer(r44_rom, gid), limit=0x10000)
            assert len(dec_r44) != 4096, "expected corrupted non-4096 decode in r44"
        elif spec["kind"] == "pure_add":
            dec_r44, _ = lz2(r44_rom, graphics_pointer(r44_rom, gid), limit=0x10000)
            assert len(dec_r44) == 4096
            added, modified, zeroed = tile_diff_counts(dec_r44, decoded)
            assert modified == 0 and zeroed == 0, (hex(gid), added, modified, zeroed)
            assert added == spec["added_tiles"], (hex(gid), added)
        elif spec["kind"] == "null_ptr":
            assert graphics_pointer(r44_rom, gid) == 0

        after_hex = bytes(
            [cursor_addr & 0xFF, (cursor_addr >> 8) & 0xFF, (cursor_addr >> 16) & 0xFF]
        ).hex()
        extra_patches.append(
            {
                "offset": off,
                "before": spec["before"],
                "after": after_hex,
                "role": spec["role"],
            }
        )
        code_patches.append(
            {
                "address": f"{off:06X}",
                "before": spec["before"],
                "after": after_hex,
                "role": spec["role"],
            }
        )
        pack_buf.extend(stream)
        cursor_addr += len(stream)

    pack_bytes = bytes(pack_buf)
    assert len(pack_bytes) == PACK_SIZE, len(pack_bytes)
    assert sha(pack_bytes) == PACK_SHA, sha(pack_bytes)

    pack_dir = ROOT / PACK_SOURCE
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_path = pack_dir / PACK_FILE
    if pack_path.exists():
        assert pack_path.read_bytes() == pack_bytes, "existing exgfx-r45.bin differs"
    else:
        write_verified(pack_path, pack_bytes)

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R44_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["scope"] = (
        "Consolidate 8 official ExGFX repairs in native bank D3 ($D3:8000, BM_EXGFX_R45_PACK, "
        "14530B): restore r34-corrupted 0x257 for sprite2e Wily Capsule P2, upgrade 5 pure-addition "
        "ExGFX sets (0x1E3, 0x163, 0x18F, 0x192, 0x1AE), and restore 2 NULL $0F:F600 pointers "
        "(0x0DA, 0x0BE)."
    )
    cfg["native_sprite_gap"]["frozen_manifests"] = list(
        cfg["native_sprite_gap"]["manifests"]
    )
    cfg["native_sprite_gap"]["extra_packs"].append(
        {
            "variable": PACK_VAR,
            "pack_file": PACK_FILE,
            "address": f"{PACK_ADDRESS:06X}",
            "size": PACK_SIZE,
            "sha256": PACK_SHA,
            "executable": False,
            "source": PACK_SOURCE,
        }
    )
    cfg["native_sprite_gap"]["extra_patches"] = extra_patches
    cfg["code_patches"] = code_patches
    cfg["output"] = {"size": 4194304, "sha256": R45_SHA}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_text = json.dumps(cfg, indent=2) + "\n"
    if cfg_path.exists():
        assert cfg_path.read_text() == cfg_text, "existing r45 config differs"
    else:
        cfg_path.write_text(cfg_text)

    native_sprite_gap.prepare(TARGET)

    r44_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r44_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r45_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r45_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 67, f"expected 67 packs, got {len(collected)}"
    print(f"Prepared {TARGET}: rom_sha256={R45_SHA}, packs={len(collected)}")


if __name__ == "__main__":
    prepare()

#!/usr/bin/env python3
"""Prepare demo11-native-product-r46: port cheap-demo Room 0x1C5 opening story cutscene."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import native_sprite_gap
from restore_star_world_1 import graphics_pointer, lorom, lz2, sha, write_verified

PARENT = "demo11-native-product-r45"
TARGET = "demo11-native-product-r46"
R45_SHA = "d13003a1e9a7c0a473f97af885a0740cdb40539d2b10b30c4f5fa676de7611e2"
CHEAP_DEMO_SHA = "f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"

PACK_SOURCE = "local/native-modules/room1c5-r46-v1"

DATA_PACK_ADDRESS = 0xD48000
DATA_PACK_SIZE = 14181
DATA_PACK_FILE = "room1c5-r46-data.bin"
DATA_PACK_VAR = "BM_ROOM1C5_R46_DATA_PACK"

CODE_PACK_ADDRESS = 0x89B000
CODE_PACK_FILE = "room1c5-r46-code.bin"
CODE_PACK_VAR = "BM_ROOM1C5_R46_CODE_PACK"

JP_GFX02A_SHA = "2f0619a305c515d72c4707dd7f18a792dcc376d3a5ac65adab35e68e75e15e1f"
EN_GFX02A_SHA = "310facf09c5f280859dcfcf4da215c63089377af4802aabea31e49ce5f09d0fa"

EXGFX_23A_PTR = 0x45CF66
EXGFX_239_PTR = 0x43EB1E
EXGFX_23C_PTR = 0x45E484
PAL_1C5_PTR = 0x57DA95
L1_1C5_PTR = 0x57A065
L2_1C5_PTR = 0x57A28F
SPR_1C5_PTR = 0x57DC9F

DATA_OFFSETS = {
    "exgfx_23a": 0x0000,   # $D4:8000 (3099 B)
    "exgfx_239": 0x0C1B,   # $D4:8C1B (3250 B)
    "exgfx_23c": 0x18CD,   # $D4:98CD (2655 B)
    "pal_1c5": 0x232C,     # $D4:A32C (514 B)
    "l1_1c5": 0x252E,      # $D4:A52E (546 B)
    "l2_1c5": 0x2750,      # $D4:A750 (16 B Layer 2 BG RLE stream)
    "spr_1c5": 0x2760,     # $D4:A760 (5 B)
    "jp_gfx02a": 0x2765,   # $D4:A765 (2048 B)
    "en_gfx02a": 0x2F65,   # $D4:AF65 (2048 B)
}


def find_cheap_demo_rom() -> Path:
    for rel in ("local/content-versions/cheap-demo/rom.sfc", "local/roms/cheap-demo.sfc"):
        candidate = ROOT / rel
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("cheap-demo donor ROM not found")


def _dma2_gfx02a_routine(src_addr: int, tail_hex: str) -> bytes:
    """Emit 65816 routine that DMAs 2048 B from $D4:src_addr to VRAM word $4800,
    preserving full 16-bit C (including hidden B), X, Y, DB, D, and P before
    replaying the replaced instruction bytes in tail_hex and returning via RTL."""
    lo = src_addr & 0xFF
    hi = (src_addr >> 8) & 0xFF
    bank = (src_addr >> 16) & 0xFF
    return (
        bytes.fromhex(
            "08"        # PHP
            "c220"      # REP #$20
            "48"        # PHA (16-bit C)
            "e220"      # SEP #$20
            "a9808d1521"        # LDA #$80; STA $2115
            "c220"              # REP #$20
            "a900488d1621"      # LDA #$4800; STA $2116
            "a901188d2043"      # LDA #$1801; STA $4320
        )
        + bytes([0xA9, lo, hi, 0x8D, 0x22, 0x43])   # LDA #src_lo16; STA $4322
        + bytes.fromhex("a900088d2543" "e220")      # LDA #$0800; STA $4325; SEP #$20
        + bytes([0xA9, bank, 0x8D, 0x24, 0x43])     # LDA #src_bank; STA $4324
        + bytes.fromhex(
            "a9048d0b42"        # LDA #$04; STA $420B
            "c220"              # REP #$20
            "68"                # PLA (16-bit C)
            "28"                # PLP
            + tail_hex
            + "6b"              # RTL
        )
    )


def build_code_pack() -> bytes:
    """Build BM_ROOM1C5_R46_CODE_PACK ($89:B000):
    - $89:B000: upload Japanese GFX 0x02A ($D4:A765) -> replay LDA #$FF; STA $18BD; RTL
    - $89:B040: restore English GFX 0x02A ($D4:AF65) -> replay STZ $18BD; LDA #$A0; RTL
    """
    init_fn = _dma2_gfx02a_routine(
        DATA_PACK_ADDRESS + DATA_OFFSETS["jp_gfx02a"],
        "a9ff8dbd18",  # LDA #$FF; STA $18BD
    )
    exit_fn = _dma2_gfx02a_routine(
        DATA_PACK_ADDRESS + DATA_OFFSETS["en_gfx02a"],
        "9cbd18a9a0",  # STZ $18BD; LDA #$A0
    )
    assert len(init_fn) <= 0x40, len(init_fn)
    buf = bytearray(0x40 + len(exit_fn))
    buf[0 : len(init_fn)] = init_fn
    buf[0x40 : 0x40 + len(exit_fn)] = exit_fn
    return bytes(buf)


def build_data_pack(cheap_rom: bytes, r45_rom: bytes) -> bytes:
    """Assemble BM_ROOM1C5_R46_DATA_PACK at $D4:8000 (14166 B)."""
    assert graphics_pointer(cheap_rom, 0x23A) == EXGFX_23A_PTR
    assert graphics_pointer(cheap_rom, 0x239) == EXGFX_239_PTR
    assert graphics_pointer(cheap_rom, 0x23C) == EXGFX_23C_PTR

    dec_23a, raw_23a = lz2(cheap_rom, EXGFX_23A_PTR, limit=0x10000)
    dec_239, raw_239 = lz2(cheap_rom, EXGFX_239_PTR, limit=0x10000)
    dec_23c, raw_23c = lz2(cheap_rom, EXGFX_23C_PTR, limit=0x10000)
    assert len(dec_23a) == 4096 and len(raw_23a) == 3099
    assert len(dec_239) == 4096 and len(raw_239) == 3250
    assert len(dec_23c) == 4096 and len(raw_23c) == 2655

    pal_1c5 = cheap_rom[lorom(PAL_1C5_PTR) : lorom(PAL_1C5_PTR) + 514]
    assert len(pal_1c5) == 514

    l1_1c5 = bytearray(cheap_rom[lorom(L1_1C5_PTR) : lorom(L1_1C5_PTR) + 546])
    assert len(l1_1c5) == 546
    assert l1_1c5[-4:] == bytes.fromhex("406044ff"), l1_1c5[-4:].hex()
    # Map legacy song $43 (OBJ_26 param 0x44) -> modern recipient slot $59 (param 0x5A).
    l1_1c5[-4:] = bytes.fromhex("40605aff")

    l2_1c5 = cheap_rom[lorom(L2_1C5_PTR) : lorom(L2_1C5_PTR) + 16]
    assert l2_1c5 == bytes.fromhex("ff00ff00ff00ff00ff00ff00df00ffff"), l2_1c5.hex()

    spr_1c5 = cheap_rom[lorom(SPR_1C5_PTR) : lorom(SPR_1C5_PTR) + 5]
    assert spr_1c5 == bytes.fromhex("00e83000ff"), spr_1c5.hex()

    jp_02a, _ = lz2(cheap_rom, graphics_pointer(cheap_rom, 0x2A), limit=0x10000)
    assert len(jp_02a) == 2048 and sha(jp_02a) == JP_GFX02A_SHA, sha(jp_02a)

    en_02a, _ = lz2(r45_rom, graphics_pointer(r45_rom, 0x2A), limit=0x10000)
    assert len(en_02a) == 2048 and sha(en_02a) == EN_GFX02A_SHA, sha(en_02a)

    buf = bytearray()
    pieces = [
        ("exgfx_23a", raw_23a),
        ("exgfx_239", raw_239),
        ("exgfx_23c", raw_23c),
        ("pal_1c5", pal_1c5),
        ("l1_1c5", bytes(l1_1c5)),
        ("l2_1c5", l2_1c5),
        ("spr_1c5", spr_1c5),
        ("jp_gfx02a", jp_02a),
        ("en_gfx02a", en_02a),
    ]
    for name, chunk in pieces:
        assert len(buf) == DATA_OFFSETS[name], (name, hex(len(buf)), hex(DATA_OFFSETS[name]))
        buf.extend(chunk)

    assert len(buf) == DATA_PACK_SIZE, len(buf)
    return bytes(buf)


def build_patches() -> list[dict]:
    """Return exact ROM patches against demo11-native-product-r45."""
    return [
        {
            "offset": lorom(0x05E54F),
            "before": "19c749",
            "after": "2ea5d4",
            "role": "Point Room 0x1C5 Layer 1 ($05:E54F) to cheap-demo L1 in native bank D4 ($D4:A52E, song byte $44->$5A).",
        },
        {
            "offset": lorom(0x05EB4F),
            "before": "00d9ff",
            "after": "50a7d4",
            "role": "Point Room 0x1C5 Layer 2 ($05:EB4F) to cheap-demo 16B Layer 2 RLE stream in native bank D4 ($D4:A750).",
        },
        {
            "offset": lorom(0x05EF8A),
            "before": "49ca",
            "after": "60a7",
            "role": "Point Room 0x1C5 Sprite list low16 ($05:EF8A) to $A760 in native bank D4.",
        },
        {
            "offset": lorom(0x0EF2C5),
            "before": "49",
            "after": "d4",
            "role": "Point Room 0x1C5 Sprite list bank ($0E:F2C5) to native bank D4.",
        },
        {
            "offset": lorom(0x0EFB4F),
            "before": "3fc849",
            "after": "2ca3d4",
            "role": "Point Room 0x1C5 Custom Palette ($0E:FB4F) to cheap-demo 514B palette in native bank D4 ($D4:A32C).",
        },
        {
            "offset": lorom(0x05F1C5),
            "before": "5b",
            "after": "83",
            "role": "Restore cheap-demo Room 0x1C5 $05:F000 level table byte ($5B -> $83).",
        },
        {
            "offset": lorom(0x0EF4D5),
            "before": "00",
            "after": "02",
            "role": "Restore cheap-demo Room 0x1C5 $0E:F310 level table byte ($00 -> $02).",
        },
        {
            "offset": lorom(0x14E5A8),
            "before": "0100" + "ff" * 30,
            "after": "01803a0239023c023b020f004402010000007f00ffffffffffffffffffffffff",
            "role": "Restore cheap-demo Room 0x1C5 Super GFX Bypass table ($14:E5A8, 32 B).",
        },
        {
            "offset": lorom(0x1483B6),
            "before": "ffffff",
            "after": "0080d4",
            "role": "Mount cheap-demo ExGFX 0x23A pointer ($14:83B6) at $D4:8000.",
        },
        {
            "offset": lorom(0x1483B3),
            "before": "ffffff",
            "after": "1b8cd4",
            "role": "Mount cheap-demo ExGFX 0x239 pointer ($14:83B3) at $D4:8C1B.",
        },
        {
            "offset": lorom(0x1483BC),
            "before": "ffffff",
            "after": "cd98d4",
            "role": "Mount cheap-demo ExGFX 0x23C pointer ($14:83BC) at $D4:98CD.",
        },
        {
            "offset": lorom(0x009724),
            "before": "01",
            "after": "1e",
            "role": "Use cheap-demo New-Save ($0109==$E9) silence slot $1E at $00:9724 during intro cutscene.",
        },
        {
            "offset": lorom(0x13EDAF),
            "before": "98f006",
            "after": "eaeaea",
            "role": "Allow New Save ($0100>=$0B && $0109!=0) to enter Room 0x1C5 even when World 1 $1F11==0x00.",
        },
        {
            "offset": lorom(0x3FE296),
            "before": "a9ff8dbd18",
            "after": "2200b089ea",
            "role": "Hook custom sprite 0x00 INIT ($3F:E296) -> JSL $89B000; NOP to upload Japanese GFX 0x02A.",
        },
        {
            "offset": lorom(0x3FE44D),
            "before": "9cbd18a9a0",
            "after": "2240b089ea",
            "role": "Hook 0x14D Overworld exit ($3F:E44D) -> JSL $89B040; NOP to restore English GFX 0x02A.",
        },
    ]


def prepare() -> None:
    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text())
    r45_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r45_rom = r45_rom_path.read_bytes()
    assert len(r45_rom) == 4194304, len(r45_rom)
    assert sha(r45_rom) == R45_SHA, f"r45 ROM SHA-256 mismatch: {sha(r45_rom)}"
    assert parent_cfg["output"]["sha256"] == R45_SHA

    # Verify banks $D4 and $89 are unoccupied in parent packs.
    occupied_banks = {int(p["address"], 16) >> 16 for p in native_sprite_gap.packs(PARENT)}
    assert (DATA_PACK_ADDRESS >> 16) not in occupied_banks, "native bank D4 already occupied"
    assert (CODE_PACK_ADDRESS >> 16) not in occupied_banks, "native bank 89 already occupied"

    cheap_rom = find_cheap_demo_rom().read_bytes()
    assert len(cheap_rom) == 4194304 and sha(cheap_rom) == CHEAP_DEMO_SHA, sha(cheap_rom)

    data_bytes = build_data_pack(cheap_rom, r45_rom)
    code_bytes = build_code_pack()
    data_sha = sha(data_bytes)
    code_sha = sha(code_bytes)

    pack_dir = ROOT / PACK_SOURCE
    pack_dir.mkdir(parents=True, exist_ok=True)
    for fname, blob in ((DATA_PACK_FILE, data_bytes), (CODE_PACK_FILE, code_bytes)):
        fpath = pack_dir / fname
        if fpath.exists():
            assert fpath.read_bytes() == blob, f"existing {fpath} differs"
        else:
            write_verified(fpath, blob)

    patches = build_patches()
    patched_rom = bytearray(r45_rom)
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
    r46_sha = sha(bytes(patched_rom))

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["target"] = "Brutal Mario Demo11 Product R46"
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R45_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["scope"] = (
        "Port cheap-demo Room 0x1C5 opening story cutscene (0x1C5 -> 0x14B -> 0x14C -> 0x14D -> Overworld): "
        "mount ExGFX 0x23A/0x239/0x23C, Room 0x1C5 assets, and Japanese/English GFX 0x02A pair in native "
        "bank D4 ($D4:8000, BM_ROOM1C5_R46_DATA_PACK, 14181B), add room-scoped GFX 0x02A DMA swapper in "
        "LoROM mirror bank 89 ($89:B000, BM_ROOM1C5_R46_CODE_PACK), route New Save ($0109!=0) into 0x1C5 "
        "with silence slot $1E, and remap Room 0x1C5 music byte $44->$5A (slot $59)."
    )
    cfg["native_sprite_gap"]["frozen_manifests"] = list(
        cfg["native_sprite_gap"]["manifests"]
    )
    cfg["native_sprite_gap"]["extra_packs"].extend(
        [
            {
                "variable": DATA_PACK_VAR,
                "pack_file": DATA_PACK_FILE,
                "address": f"{DATA_PACK_ADDRESS:06X}",
                "size": len(data_bytes),
                "sha256": data_sha,
                "executable": False,
                "source": PACK_SOURCE,
            },
            {
                "variable": CODE_PACK_VAR,
                "pack_file": CODE_PACK_FILE,
                "address": f"{CODE_PACK_ADDRESS:06X}",
                "size": len(code_bytes),
                "sha256": code_sha,
                "executable": True,
                "source": PACK_SOURCE,
            },
        ]
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
    cfg["output"] = {"size": 4194304, "sha256": r46_sha}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_text = json.dumps(cfg, indent=2) + "\n"
    if cfg_path.exists():
        assert cfg_path.read_text() == cfg_text, "existing r46 config differs"
    else:
        cfg_path.write_text(cfg_text)

    native_sprite_gap.prepare(TARGET)

    r45_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r45_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r46_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r46_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 69, f"expected 69 packs, got {len(collected)}"
    print(
        f"Prepared {TARGET}: rom_sha256={r46_sha}, "
        f"data_pack=({len(data_bytes)}B, {data_sha}), "
        f"code_pack=({len(code_bytes)}B, {code_sha}), packs={len(collected)}"
    )


if __name__ == "__main__":
    prepare()

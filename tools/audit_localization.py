#!/usr/bin/env python3
"""Audit official Brutal Mario ROMs for r47 multi-language localization.

Reproducibly inspects all 10 official local ROMs (`demo6`, `demo7`, `cheap-demo`,
`ow`, `mazo`, `7hero`, `boss`, `demo-only-1`, `demo-1-1`, and
`demo11-native-product-r46`), verifies Layer 3 GFX `0x28..0x2B` VRAM destinations,
Overworld banner & SMW Message Box VRAM/stripe addresses, Overworld HUD safety,
per-tile glyph translations, merged `ja` / `en` OW names, message boxes, custom
room message mappings (`$10:B6A6`), Mazo `0x191`/`0x192` messages, Title/File-Select/
Credits Stripe images, and all 512 room `needs_jp_font` tags, and writes
`config/native-content/localization-audit-r47.json`.
"""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))
from restore_star_world_1 import graphics_pointer, lorom, lz2, sha  # noqa: E402

DEFAULT_OUTPUT = ROOT / "config/native-content/localization-audit-r49.json"

PINNED_ROMS: dict[str, tuple[str, str]] = {
    "demo6": (
        "content-versions/demo6/rom.sfc",
        "c305c896395baac1d933a7e96ddd97cb9c2704f199e513a7ce2447253d1f26a6",
    ),
    "demo7": (
        "content-versions/demo7/rom.sfc",
        "f462ddd7c30a641e57b586ebae003adc5eb3a5f19579d2348022b2be8934eae4",
    ),
    "cheap-demo": (
        "content-versions/cheap-demo/rom.sfc",
        "f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822",
    ),
    "ow": (
        "content-versions/ow/rom.sfc",
        "b5116eba4d88f0b254a17aae845a44a30f7000566ac21c1fca5b1403c0296d6e",
    ),
    "mazo": (
        "content-versions/mazo/rom.sfc",
        "94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1",
    ),
    "7hero": (
        "content-versions/7hero/rom.sfc",
        "dd7007ad45da87647bbd7e6d3bda13b8555c05b64793a92824f12b347c7a2395",
    ),
    "boss": (
        "content-versions/boss/rom.sfc",
        "337fe036f943dafb0df70bdb556e588b785c58ff019b1b00c08f77743e2b3ccd",
    ),
    "demo-only-1": (
        "content-versions/demo-only-1/rom.sfc",
        "b8d86f894f6c07aeb74794c59adab8f336080285b4781a3e1c921615a2d8216b",
    ),
    "demo-1-1": (
        "content-versions/demo-1-1/rom.sfc",
        "314496f67caf53d1d74873333de366a07a2b2446d7bbb5f27eeeb9aa69894f32",
    ),
    "r46": (
        "restoration/demo11-native-product-r46/rom.sfc",
        "142ee768d1d5cd436a17d459719b30a02ba5dafaa79271b9d3c37da4965a0b7e",
    ),
}

GFX_029_SHA = "733ad11d07dc83a8f422ec645532a65eb990c35d57a69b0c4317d859d6cdaadd"

# Official demo chronology (oldest -> newest) per AGENTS.md
CHRONOLOGY = (
    "demo6",
    "demo7",
    "cheap-demo",
    "ow",
    "mazo",
    "7hero",
    "boss",
    "demo-only-1",
    "demo-1-1",
)

# Verified demoOnly1 English Overworld level names (9 slots).
DEMO_ONLY_1_EN_OW_SLOTS = (0x0A, 0x0C, 0x0D, 0x34, 0x3A, 0x4A, 0x4E, 0x51, 0x58)
# Verified Demo 1-1 English Overworld level name (1 slot).
DEMO_1_1_EN_OW_SLOTS = (0x29,)
# Verified blank (all 0x1F space) Overworld slots in boss/Demo 1-1.
BLANK_OW_SLOTS = (0x00, 0x4F, 0x5F)
# Pinned Demo 7 English Overworld level-name recipe & post-demo7 JP fallback slots.
DEMO7_EN_OW_CFG_PATH = ROOT / "config/native-content/demo7-en-ow-names.json"
DEMO7_EN_SHA = "7c98fe8e0f95efbe5c186bf379a1682310304307551d62ab64dcc466719baafa"
POST_DEMO7_JP_OW_SLOTS = (0x01, 0x10, 0x30, 0x3D, 0x46, 0x47, 0x48, 0x4D, 0x50, 0x59, 0x5A, 0x5D)
# Verified Demo 1-1 English Message Box slots (all other non-empty slots are Japanese).
DEMO_1_1_EN_MSG_SLOTS = (6, 7, 82, 83)

# Persistent Japanese Layer 3 rooms (keep ja_gfx02a across room / after $05:B11D close).
PERSISTENT_JP_ROOMS = (0x0FF, 0x14B, 0x14C, 0x14D, 0x17B, 0x1C5)
# Mazo message-scoped JP rooms (swap to ja_gfx02a during message, restore en_gfx02a on close in EN).
MAZO_MSG_ROOMS = (0x191, 0x192)
# Shop rooms (sprite A2, use ExGFX/sprites rather than Layer 3 GFX 0x2A/0x2B).
SHOP_ROOMS = (0x104, 0x182)

# Verified Demo 1-1 / US SMW GFX 0x2A character decoding (0x00..0x7F).
EN_GFX02A_CHARS: dict[int, str] = {
    **{i: chr(ord("A") + i) for i in range(26)},
    0x1A: "!",
    0x1B: ".",
    0x1C: "-",
    0x1D: ",",
    0x1E: "?",
    0x1F: " ",
    0x20: "'",
    0x21: "Z",
    **{0x22 + i: str(i) for i in range(10)},
    0x2C: "B",
    0x2D: "C",
    0x2E: "*",
    0x2F: "T",
    0x30: "M",
    0x31: "S",
    0x38: "Y",
    0x3D: "?",
    0x3E: "O",
    0x3F: "!",
    **{0x40 + i: chr(ord("a") + i) for i in range(26)},
    0x5A: "#",
    0x5B: "(",
    0x5C: ")",
    0x5D: "'",
    0x5E: '"',
    **{0x64 + i: str(i + 1) for i in range(8)},
    0x78: "°",
    0x7A: "R",
    0x7B: "[",
    0x7C: "L",
}


def resolve_local_dir(override: str | None = None) -> Path:
    """Locate the shared `local/` storage directory (works inside git worktrees)."""
    if override:
        p = Path(override).resolve()
        if not p.is_dir():
            raise FileNotFoundError(f"local dir not found: {p}")
        return p
    direct = ROOT / "local"
    if direct.is_dir():
        return direct
    try:
        common = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "--git-common-dir"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        candidate = (ROOT / common).resolve().parent / "local"
        if candidate.is_dir():
            return candidate
    except Exception:
        pass
    raise FileNotFoundError(
        "Could not locate `local/` storage directory; pass --local-dir."
    )


def decode_en_bytes(data: bytes) -> str:
    """Decode Demo 1-1 / US SMW message or OW bytes into readable ASCII/tags."""
    out = []
    for b in data:
        if b == 0xFE:
            out.append("<END>")
        elif b == 0xB3:
            out.append("<DOWN_ARROW>")
        elif b in EN_GFX02A_CHARS:
            out.append(EN_GFX02A_CHARS[b])
        else:
            out.append(f"<{b:02X}>")
    return "".join(out)


def read_ow_table(rom: bytes) -> tuple[int, list[bytes]]:
    """Read the 96 x 19-byte Overworld level name table pointed to by $03:BB56."""
    off = lorom(0x03BB56)
    assert rom[off] == 0xBF, f"expected LDA long ($BF) at $03:BB56, got {rom[off]:02X}"
    base = rom[off + 1] | (rom[off + 2] << 8) | (rom[off + 3] << 16)
    f_base = lorom(base)
    return base, [rom[f_base + i * 19 : f_base + (i + 1) * 19] for i in range(96)]


def read_msg_table(rom: bytes) -> tuple[int, list[tuple[int, bytes]]]:
    """Read the 144 SMW message boxes ($03:BE80 offsets + $03:BC0A 24-bit base)."""
    off = lorom(0x03BC0A)
    assert rom[off] == 0xBF, f"expected LDA long ($BF) at $03:BC0A, got {rom[off]:02X}"
    base = rom[off + 1] | (rom[off + 2] << 8) | (rom[off + 3] << 16)
    tbl = lorom(0x03BE80)
    out: list[tuple[int, bytes]] = []
    for i in range(144):
        rel = rom[tbl + i * 2] | (rom[tbl + i * 2 + 1] << 8)
        start = lorom(base + rel)
        end = start
        while end < len(rom) and rom[end] != 0xFE and (end - start) < 256:
            end += 1
        if end < len(rom) and rom[end] == 0xFE:
            end += 1
        out.append((rel, rom[start:end]))
    return base, out


def read_custom_room_msg_remap(rom: bytes) -> list[dict]:
    """Extract the $10:B6A6 custom room -> $13BF message level remap table."""
    hook_off = lorom(0x03BB90)
    assert rom[hook_off : hook_off + 4] == bytes.fromhex("5ca6b610"), (
        f"unexpected $03:BB90 bytes: {rom[hook_off:hook_off+4].hex()}"
    )
    lo_off = lorom(0x10B6DF)
    hi_off = lorom(0x10B6E3)
    lv_off = lorom(0x10B6E6)
    entries = []
    idx = 0
    while rom[lo_off + idx] != 0x00 and idx < 8:
        room = rom[lo_off + idx] | (rom[hi_off + idx] << 8)
        msg_level = rom[lv_off + idx]
        entries.append(
            {
                "room": f"0x{room:03X}",
                "room_int": room,
                "message_level": f"0x{msg_level:02X}",
                "message_level_int": msg_level,
            }
        )
        idx += 1
    return entries


def parse_room_sprites(rom: bytes, room: int) -> list[tuple[int, int]]:
    """Return list of (sprite_id, extra_bits) for a room (`0x000..0x1FF`)."""
    lo = rom[lorom(0x05EC00) + room * 2] | (rom[lorom(0x05EC00) + room * 2 + 1] << 8)
    bk = rom[lorom(0x0EF100) + room]
    if bk in (0x00, 0xFF):
        return []
    try:
        pos = lorom((bk << 16) | lo) + 1
    except ValueError:
        return []
    out = []
    while pos + 2 < len(rom) and rom[pos] != 0xFF:
        b0 = rom[pos]
        spr = rom[pos + 2]
        ee = (b0 & 0x0C) >> 2
        out.append((spr, ee))
        pos += 3
    return out


def diff_gfx_tiles(a: bytes, b: bytes) -> list[int]:
    """Return sorted tile indices (`0x00..0x7F`) whose 16B 2bpp data differs."""
    assert len(a) == 2048 and len(b) == 2048
    return [t for t in range(128) if a[t * 16 : (t + 1) * 16] != b[t * 16 : (t + 1) * 16]]


def build_en_tile_translator() -> dict:
    """Build verified demo6/demo7/US-SMW -> Demo 1-1 (r46) GFX 0x2A translator.

    Because demo6/demo7 English strings use US SMW GFX 0x2A tile indices, and
    r46 (Demo 1-1) preserves 114/128 tiles identically from US SMW (differing on
    0x22..0x2B plain vs outlined digits, 0x6C, 0x77, 0x7B, 0x7C), standard
    English alphanumeric & punctuation bytes (0x00..0x1F, 0x22..0x2B, 0x3F..0x5E,
    0x64..0x6B) translate 1:1 while keeping 0x22..0x2B / 0x64..0x6B digit parity.
    """
    identity_ranges = (
        list(range(0x00, 0x21))  # A-Z, ! . - , ? space '
        + list(range(0x22, 0x2C))  # 0-9 (plain in r46/boss, outlined in SMWU/demo6/demo7)
        + list(range(0x2C, 0x32))  # B C * T M S
        + [0x38, 0x3D, 0x3E, 0x3F]  # Y ? O !
        + list(range(0x40, 0x5F))  # a-z # ( ) ' "
        + list(range(0x64, 0x6C))  # 1-8 (plain message/OW digits, byte-identical!)
        + [0x78, 0x7A]  # degree, R
    )
    table = {f"0x{t:02X}": f"0x{t:02X}" for t in identity_ranges}
    return {
        "description": (
            "Maps US-SMW-encoded English GFX 0x2A tile indices (used in demo6/demo7 "
            "English strings) to Demo 1-1 (r46) GFX 0x2A tile indices."
        ),
        "smwu_vs_r46_differing_tiles": [
            "0x22..0x2B (outlined digits in SMWU/demo6/demo7 -> plain digits in r46/boss; visually valid 0-9)",
            "0x6C (US HUD tile -> JP SA in r46; unused in message/OW strings)",
            "0x77 (US HUD tile -> JP WO in r46; unused in message/OW strings)",
            "0x7B..0x7C (US Title/HUD tiles -> box corners in r46; unused in message/OW strings)",
        ],
        "identity_tile_map": table,
    }


def load_demo7_en_ow_recipe(local_dir: Path) -> dict[int, dict]:
    """Load, validate, and optionally ROM-verify the pinned Demo 7 English OW name recipe."""
    cfg = json.loads(DEMO7_EN_OW_CFG_PATH.read_text())
    assert cfg.get("schema") == 1, f"unexpected schema in {DEMO7_EN_OW_CFG_PATH}"
    donor = cfg["donor"]
    assert donor["headerless_sha256"] == DEMO7_EN_SHA
    assert donor["ow_table_base"] == "$13E1D7"

    excluded = tuple(sorted(int(e["slot"]) for e in cfg["excluded_post_demo7_slots"]))
    assert excluded == POST_DEMO7_JP_OW_SLOTS, (excluded, POST_DEMO7_JP_OW_SLOTS)

    by_slot: dict[int, dict] = {}
    for entry in cfg["slots"]:
        slot = int(entry["slot"])
        assert slot not in by_slot, f"duplicate slot 0x{slot:02X}"
        assert entry["slot_hex"] == f"0x{slot:02X}"
        donor_bytes = bytes.fromhex(entry["donor_hex"])
        adapted_bytes = bytes.fromhex(entry["adapted_hex"])
        assert len(donor_bytes) == 19 and len(adapted_bytes) == 19
        for b in adapted_bytes:
            assert b < 0x80 and b in EN_GFX02A_CHARS, (
                f"demo7-en adapted slot 0x{slot:02X} uses unsupported tile 0x{b:02X}"
            )
        by_slot[slot] = entry

    covered = (
        set(DEMO_1_1_EN_OW_SLOTS)
        | set(DEMO_ONLY_1_EN_OW_SLOTS)
        | set(BLANK_OW_SLOTS)
        | set(POST_DEMO7_JP_OW_SLOTS)
        | set(by_slot.keys())
    )
    assert len(by_slot) == 71, len(by_slot)
    assert len(covered) == 96 and covered == set(range(96)), len(covered)
    assert (
        len(DEMO_1_1_EN_OW_SLOTS)
        + len(DEMO_ONLY_1_EN_OW_SLOTS)
        + len(BLANK_OW_SLOTS)
        + len(POST_DEMO7_JP_OW_SLOTS)
        + len(by_slot)
        == 96
    )

    # Cross-check against extracted local ROM or archival .smc if present on disk.
    rom_candidates = [
        local_dir / donor["local_relative_path"],
        Path("/home/harp/projects/sfc/roms/Super Kitiku Brutal Mario/Brutal Mario 7 SMWCentral")
        / donor["source_filename"],
    ]
    for cand in rom_candidates:
        if cand.is_file():
            raw = cand.read_bytes()
            if len(raw) % 1024 == 512:
                raw = raw[512:]
            assert len(raw) == 4194304, (cand, len(raw))
            assert sha(raw) == DEMO7_EN_SHA, (cand, sha(raw))
            base, table = read_ow_table(raw)
            assert base == 0x13E1D7, hex(base)
            for slot, entry in by_slot.items():
                assert table[slot].hex() == entry["donor_hex"], (
                    f"demo7-en ROM mismatch at slot 0x{slot:02X}"
                )
            break

    return by_slot


def translate_en_bytes(raw: bytes) -> bytes:
    """Translate US-SMW / demo6 / demo7 English tile bytes to Demo 1-1 (r46) bytes."""
    # Direct 1:1 for all valid English alphanumeric/punctuation tiles (0x00..0x20,
    # 0x22..0x2B, 0x3F, 0x40..0x5E, 0x64..0x6B, 0xFE).
    return raw


def pack_messages(msgs: list[bytes]) -> tuple[list[int], bytes]:
    """Deduplicate and pack 144 0xFE-terminated messages into a single blob."""
    blob = bytearray(b"\xfe")
    offsets: dict[bytes, int] = {b"\xfe": 0}
    ptrs: list[int] = []
    for msg in msgs:
        if msg not in offsets:
            offsets[msg] = len(blob)
            blob.extend(msg)
        ptrs.append(offsets[msg])
    return ptrs, bytes(blob)


def build_bmlg_pack(audit: dict, local_dir: Path | None = None) -> bytes:
    """Assemble the <=32 KiB `"BMLG"` v1 binary data pack for `$D5:8000`."""
    boss_rom = (resolve_local_dir(str(local_dir) if local_dir else None) / PINNED_ROMS["boss"][0]).read_bytes()
    r46_rom = (resolve_local_dir(str(local_dir) if local_dir else None) / PINNED_ROMS["r46"][0]).read_bytes()

    ja_028 = lz2(boss_rom, graphics_pointer(boss_rom, 0x28), 2048)[0]
    ja_02a = lz2(boss_rom, graphics_pointer(boss_rom, 0x2A), 2048)[0]
    ja_02b = lz2(boss_rom, graphics_pointer(boss_rom, 0x2B), 2048)[0]
    en_028 = lz2(r46_rom, graphics_pointer(r46_rom, 0x28), 2048)[0]
    en_02a = lz2(r46_rom, graphics_pointer(r46_rom, 0x2A), 2048)[0]
    en_02b = lz2(r46_rom, graphics_pointer(r46_rom, 0x2B), 2048)[0]

    ja_ow = b"".join(bytes.fromhex(e["hex"]) for e in audit["ja"]["ow_names"])
    en_ow = b"".join(bytes.fromhex(e["hex"]) for e in audit["en"]["ow_names"])
    ow_flags = bytes(e["needs_jp_font"] for e in audit["en"]["ow_names"])
    assert len(ja_ow) == 96 * 19 and len(en_ow) == 96 * 19 and len(ow_flags) == 96

    ja_ptrs, ja_blob = pack_messages([bytes.fromhex(e["hex"]) for e in audit["ja"]["messages"]])
    en_ptrs, en_blob = pack_messages([bytes.fromhex(e["hex"]) for e in audit["en"]["messages"]])
    msg_flags = bytes(e["needs_jp_font"] for e in audit["en"]["messages"])
    assert len(ja_ptrs) == 144 and len(en_ptrs) == 144 and len(msg_flags) == 144

    mazo_192 = bytes.fromhex(audit["mazo_messages"]["0x192"]["hex"])
    mazo_191 = bytes.fromhex(audit["mazo_messages"]["0x191"]["hex"])
    assert len(mazo_192) == 70 and len(mazo_191) == 86

    room_policy = bytes(e["persistent_jp_font"] for e in audit["rooms"])
    assert len(room_policy) == 512

    remap_entries = audit["custom_room_messages"]["entries"]
    remap_bytes = bytearray([len(remap_entries)])
    for r in remap_entries:
        remap_bytes.extend(struct.pack("<HB", r["room_int"], r["message_level_int"]))

    ja_title_stripe = bytes.fromhex(audit["stripe_audit"]["boss_title_stripe_hex"])

    HEADER_SIZE = 64
    cursor = HEADER_SIZE

    def place(chunk: bytes) -> tuple[int, bytes]:
        nonlocal cursor
        off = cursor
        cursor += len(chunk)
        return off, chunk

    ja_028_off, c1 = place(ja_028)
    ja_02a_off, c2 = place(ja_02a)
    ja_02b_off, c3 = place(ja_02b)
    en_028_off, c4 = place(en_028)
    en_02a_off, c5 = place(en_02a)
    en_02b_off, c6 = place(en_02b)
    ja_ow_off, c7 = place(ja_ow)
    en_ow_off, c8 = place(en_ow)
    ow_flags_off, c9 = place(ow_flags)
    ja_ptrs_bytes = b"".join(struct.pack("<H", p) for p in ja_ptrs)
    ja_ptrs_off, c10 = place(ja_ptrs_bytes)
    ja_blob_off, c11 = place(ja_blob)
    en_ptrs_bytes = b"".join(struct.pack("<H", p) for p in en_ptrs)
    en_ptrs_off, c12 = place(en_ptrs_bytes)
    en_blob_off, c13 = place(en_blob)
    msg_flags_off, c14 = place(msg_flags)
    mazo_192_off, c15 = place(mazo_192)
    mazo_191_off, c16 = place(mazo_191)
    room_policy_off, c17 = place(room_policy)
    remap_off, c18 = place(bytes(remap_bytes))
    ja_title_off, c19 = place(ja_title_stripe)

    total_size = cursor
    assert total_size <= 32768, f"BMLG pack exceeds 32 KiB LoROM bank: {total_size}"

    header = struct.pack(
        "<4sHHI22H8x",
        b"BMLG",
        1,
        HEADER_SIZE,
        total_size,
        ja_028_off,
        ja_02a_off,
        ja_02b_off,
        en_028_off,
        en_02a_off,
        en_02b_off,
        ja_ow_off,
        en_ow_off,
        ow_flags_off,
        ja_ptrs_off,
        ja_blob_off,
        len(ja_blob),
        en_ptrs_off,
        en_blob_off,
        len(en_blob),
        msg_flags_off,
        mazo_192_off,
        mazo_191_off,
        room_policy_off,
        remap_off,
        ja_title_off,
        len(ja_title_stripe),
    )
    assert len(header) == HEADER_SIZE
    pack = header + c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11 + c12 + c13 + c14 + c15 + c16 + c17 + c18 + c19
    assert len(pack) == total_size
    return pack


def generate_audit(local_dir: Path | None = None, include_demo7_en_ow: bool = True) -> dict:
    """Run the complete localization audit and return the structured JSON dict."""
    ldir = resolve_local_dir(str(local_dir) if local_dir else None)

    roms: dict[str, bytes] = {}
    rom_records: dict[str, dict] = {}
    for name, (rel_path, expected_sha) in PINNED_ROMS.items():
        fpath = ldir / rel_path
        blob = fpath.read_bytes()
        actual_sha = sha(blob)
        assert len(blob) == 4194304, f"{name} unexpected size {len(blob)}"
        assert actual_sha == expected_sha, f"{name} sha mismatch: {actual_sha} != {expected_sha}"
        roms[name] = blob
        rom_records[name] = {
            "relative_path": rel_path,
            "size": len(blob),
            "sha256": actual_sha,
        }

    # Verify GFX 0x28..0x2B across all 10 ROMs.
    gfx_audit: dict[str, dict] = {}
    gfx_decoded: dict[str, dict[int, bytes]] = {}
    for name, rom in roms.items():
        gfx_decoded[name] = {}
        entry = {}
        for gfx_id in (0x28, 0x29, 0x2A, 0x2B):
            ptr = graphics_pointer(rom, gfx_id)
            dec, comp = lz2(rom, ptr, 2048)
            assert len(dec) == 2048
            gfx_decoded[name][gfx_id] = dec
            entry[f"0x{gfx_id:02X}"] = {
                "pointer": f"${ptr:06X}",
                "compressed_size": len(comp),
                "compressed_sha256": sha(comp),
                "decoded_size": len(dec),
                "decoded_sha256": sha(dec),
            }
        gfx_audit[name] = entry

    for name in ("cheap-demo", "ow", "mazo", "7hero", "boss", "demo-only-1", "demo-1-1", "r46"):
        assert gfx_decoded[name][0x29] == gfx_decoded["boss"][0x29]
        assert sha(gfx_decoded[name][0x29]) == GFX_029_SHA

    # Per-tile comparisons across demo6, demo7, boss, r46.
    tile_diffs = {}
    for gfx_id in (0x28, 0x2A, 0x2B):
        key = f"0x{gfx_id:02X}"
        tile_diffs[key] = {
            "demo6_vs_demo7": [f"0x{t:02X}" for t in diff_gfx_tiles(gfx_decoded["demo6"][gfx_id], gfx_decoded["demo7"][gfx_id])],
            "demo7_vs_boss": [f"0x{t:02X}" for t in diff_gfx_tiles(gfx_decoded["demo7"][gfx_id], gfx_decoded["boss"][gfx_id])],
            "boss_vs_r46": [f"0x{t:02X}" for t in diff_gfx_tiles(gfx_decoded["boss"][gfx_id], gfx_decoded["r46"][gfx_id])],
        }

    # Verify Overworld HUD/border safety: all shared GFX 0x2A tiles (including digits 0x22..0x2B and space 0x1F) match.
    same_2a = [
        t for t in range(128)
        if gfx_decoded["boss"][0x2A][t * 16 : (t + 1) * 16]
        == gfx_decoded["r46"][0x2A][t * 16 : (t + 1) * 16]
    ]
    assert all(t in same_2a for t in range(0x22, 0x2C)), "digits 0x22..0x2B must match between boss and r46"
    assert 0x1F in same_2a, "space 0x1F must match between boss and r46"

    # Overworld level names across ROMs.
    ow_tables = {name: read_ow_table(rom) for name, rom in roms.items()}
    assert ow_tables["r46"][1] == ow_tables["demo-1-1"][1]
    demo7_en_by_slot = load_demo7_en_ow_recipe(ldir) if include_demo7_en_ow else {}

    ja_ow_names = []
    en_ow_names = []
    for slot in range(96):
        boss_raw = ow_tables["boss"][1][slot]
        d11_raw = ow_tables["demo-1-1"][1][slot]
        do1_raw = ow_tables["demo-only-1"][1][slot]

        ja_ow_names.append(
            {
                "slot": slot,
                "slot_hex": f"0x{slot:02X}",
                "source": "boss",
                "hex": boss_raw.hex(),
            }
        )

        if slot in DEMO_1_1_EN_OW_SLOTS:
            en_raw = d11_raw
            source = "demo-1-1"
            text = decode_en_bytes(en_raw).rstrip()
            needs_jp = 0
        elif slot in DEMO_ONLY_1_EN_OW_SLOTS:
            en_raw = do1_raw
            source = "demo-only-1"
            text = decode_en_bytes(en_raw).rstrip()
            needs_jp = 0
        elif slot in demo7_en_by_slot:
            d7e_entry = demo7_en_by_slot[slot]
            en_raw = bytes.fromhex(d7e_entry["adapted_hex"])
            source = (
                "demo7-en"
                if d7e_entry["adapted_hex"] == d7e_entry["donor_hex"]
                else "demo7-en (adapted)"
            )
            text = decode_en_bytes(en_raw).rstrip()
            assert text == d7e_entry["text"], f"slot 0x{slot:02X}: {text!r} != {d7e_entry['text']!r}"
            needs_jp = 0
        elif slot in BLANK_OW_SLOTS:
            en_raw = d11_raw
            assert en_raw == b"\x1f" * 19
            source = "demo-1-1"
            text = ""
            needs_jp = 0
        elif include_demo7_en_ow:
            assert slot in POST_DEMO7_JP_OW_SLOTS, f"unclassified OW slot 0x{slot:02X}"
            en_raw = boss_raw
            source = "boss (post-demo7 JP fallback)"
            text = None
            needs_jp = 1
        else:
            en_raw = d11_raw
            source = "demo-1-1" if d11_raw != boss_raw else "demo-1-1 (matches boss)"
            text = None
            needs_jp = 1

        if needs_jp == 0:
            for b in en_raw:
                assert b < 0x80 and b in EN_GFX02A_CHARS, (
                    f"OW slot 0x{slot:02X} uses non-English tile 0x{b:02X}"
                )

        en_ow_names.append(
            {
                "slot": slot,
                "slot_hex": f"0x{slot:02X}",
                "source": source,
                "needs_jp_font": needs_jp,
                "text": text,
                "hex": en_raw.hex(),
            }
        )

    # Message boxes across ROMs.
    msg_tables = {name: read_msg_table(rom) for name, rom in roms.items()}
    assert msg_tables["r46"][1] == msg_tables["demo-1-1"][1]

    ja_messages = []
    en_messages = []
    for slot in range(144):
        lvl = slot // 2
        msg_num = (slot % 2) + 1
        boss_rel, boss_raw = msg_tables["boss"][1][slot]
        d11_rel, d11_raw = msg_tables["demo-1-1"][1][slot]

        ja_messages.append(
            {
                "slot": slot,
                "level": f"0x{lvl:02X}",
                "message": msg_num,
                "source": "boss",
                "relative_offset": f"0x{boss_rel:04X}",
                "length": len(boss_raw),
                "hex": boss_raw.hex(),
            }
        )

        if slot in DEMO_1_1_EN_MSG_SLOTS:
            en_raw = d11_raw
            source = "demo-1-1"
            text = decode_en_bytes(en_raw)
            needs_jp = 0
        elif d11_raw == b"\xfe":
            en_raw = d11_raw
            source = "demo-1-1"
            text = "<END>"
            needs_jp = 0
        else:
            en_raw = d11_raw
            source = "demo-1-1 (matches boss)" if d11_raw == boss_raw else "demo-1-1"
            text = None
            needs_jp = 1

        en_messages.append(
            {
                "slot": slot,
                "level": f"0x{lvl:02X}",
                "message": msg_num,
                "source": source,
                "needs_jp_font": needs_jp,
                "length": len(en_raw),
                "text": text,
                "hex": en_raw.hex(),
            }
        )

    # Mazo 0x191 / 0x192 messages from mazo-messages-v2.json + mazo ROM verification.
    mazo_cfg = json.loads((ROOT / "config/native-content/mazo-messages-v2.json").read_text())
    mazo_rom = roms["mazo"]
    mazo_msgs: dict[str, dict] = {}
    for entry in mazo_cfg["messages"]:
        addr = int(entry["source_address"], 16)
        size = entry["size"]
        raw = mazo_rom[lorom(addr) : lorom(addr) + size]
        assert sha(raw) == entry["sha256"], f"mazo msg {entry['room']} sha mismatch"
        assert raw[-1] == 0xFE
        mazo_msgs[f"0x{int(entry['room'], 16):03X}"] = {
            "room": f"0x{int(entry['room'], 16):03X}",
            "request": entry["request"],
            "source_address": f"${addr:06X}",
            "size": size,
            "sha256": entry["sha256"],
            "needs_jp_font": 1,
            "hex": raw.hex(),
        }

    # Custom room message remap ($10:B6A6) in demo-1-1 / r46.
    custom_remaps = read_custom_room_msg_remap(roms["r46"])
    remap_by_room = {r["room_int"]: r["message_level_int"] for r in custom_remaps}

    # Build room -> translevel mapping from config/demo11-level-index.json + InfoBox scan.
    lvl_idx_data = json.loads((ROOT / "config/demo11-level-index.json").read_text())["entries"]
    room_to_translevel = {
        int(e["level"], 16): int(e["translevel"], 16) for e in lvl_idx_data
    }

    en_msg_jp_flags = {m["slot"]: m["needs_jp_font"] for m in en_messages}
    rooms_audit = []
    for room in range(0x200):
        sprites = parse_room_sprites(roms["r46"], room)
        has_infobox = any(spr == 0xB9 and ee == 0 for spr, ee in sprites)
        has_shop = room in SHOP_ROOMS
        is_persistent_jp = room in PERSISTENT_JP_ROOMS
        is_mazo_msg = room in MAZO_MSG_ROOMS
        eff_level = remap_by_room.get(room, room_to_translevel.get(room))

        has_jp_infobox = False
        if has_infobox and eff_level is not None and eff_level < 72:
            s1, s2 = eff_level * 2, eff_level * 2 + 1
            if en_msg_jp_flags.get(s1, 0) or en_msg_jp_flags.get(s2, 0):
                has_jp_infobox = True

        needs_jp = 1 if (is_persistent_jp or is_mazo_msg or has_jp_infobox) else 0
        if is_persistent_jp:
            scope = "room_persistent"
        elif is_mazo_msg:
            scope = "mazo_message_scoped"
        elif has_jp_infobox:
            scope = "infobox_message_scoped"
        elif has_shop:
            scope = "shop_exgfx_no_layer3_font"
        else:
            scope = "none"

        rooms_audit.append(
            {
                "room": f"0x{room:03X}",
                "room_int": room,
                "translevel": f"0x{room_to_translevel[room]:03X}" if room in room_to_translevel else None,
                "effective_message_level": f"0x{eff_level:02X}" if eff_level is not None and eff_level < 72 else None,
                "has_infobox_b9": has_infobox,
                "has_shop_a2": has_shop,
                "needs_jp_font": needs_jp,
                "persistent_jp_font": 1 if is_persistent_jp else 0,
                "scope": scope,
            }
        )

    # Audit Stripe images ($00:84D0..85BC covering $00:84F9 and $10:E207 Title stripe).
    boss_title_rats = lorom(0x10E1FF)
    assert roms["boss"][boss_title_rats : boss_title_rats + 4] == b"STAR"
    sz = (roms["boss"][boss_title_rats + 4] | (roms["boss"][boss_title_rats + 5] << 8)) + 1
    boss_title_stripe = roms["boss"][lorom(0x10E207) : lorom(0x10E207) + sz]

    stripe_diffs_pre_credits = []
    for k in range(0, 0x21, 3):
        a = 0x0084D0 + k
        o = lorom(a)
        pb = roms["boss"][o] | (roms["boss"][o + 1] << 8) | (roms["boss"][o + 2] << 16)
        pr = roms["r46"][o] | (roms["r46"][o + 1] << 8) | (roms["r46"][o + 2] << 16)
        if pb != pr:
            stripe_diffs_pre_credits.append((a, pb, pr))
    assert not stripe_diffs_pre_credits, f"unexpected pre-credits stripe pointer diff: {stripe_diffs_pre_credits}"

    credits_ptr_diffs = 0
    for k in range(0x21, 0xC9, 3):
        o = lorom(0x0084D0 + k)
        pb = roms["boss"][o] | (roms["boss"][o + 1] << 8) | (roms["boss"][o + 2] << 16)
        pr = roms["r46"][o] | (roms["r46"][o + 1] << 8) | (roms["r46"][o + 2] << 16)
        if pb != pr:
            credits_ptr_diffs += 1

    audit = {
        "schema": 1,
        "target": "demo11-native-product-r49" if include_demo7_en_ow else "demo11-native-product-r47",
        "roms": rom_records,
        "vram_layout": {
            "loader_routine": "$00:A993..A9C8",
            "bg3_char_base_word": "0x4000",
            "bg3_tilemap_base_word": "0x5000",
            "bgsc_2_register": "0x53",
            "modes_verified": ["title_fileselect_07_08", "overworld_0E", "level_14"],
            "gfx_slots": {
                "0x28": {"vram_word": "0x4000..0x43FF", "vram_byte": "0x8000..0x87FF", "bg3_tiles": "0x000..0x07F"},
                "0x29": {"vram_word": "0x4400..0x47FF", "vram_byte": "0x8800..0x8FFF", "bg3_tiles": "0x080..0x0FF"},
                "0x2A": {"vram_word": "0x4800..0x4BFF", "vram_byte": "0x9000..0x97FF", "bg3_tiles": "0x100..0x17F"},
                "0x2B": {"vram_word": "0x4C00..0x4FFF", "vram_byte": "0x9800..0x9FFF", "bg3_tiles": "0x180..0x1FF"},
            },
            "ow_level_name_banner": {
                "routine": "$03:BB20..BB6B",
                "tile_count": 19,
                "vram_words": "0x508B..0x509D",
                "vram_bytes": "0xA116..0xA13B",
                "attr_byte": "0x39",
                "wram_stripe_index": "$7F:837B",
                "wram_stripe_buffer": "$7F:837D",
                "stripe_header_hex": "508b0025",
            },
            "smw_message_box": {
                "routine": "$03:BB90..BC8F",
                "close_routine": "$05:B11D",
                "row_vram_table": "$03:BC7F..BC8E",
                "dimensions": "8x18 (rows 6..13, cols 7..24)",
                "row_vram_words": [
                    "0x50C7..0x50D8",
                    "0x50E7..0x50F8",
                    "0x5107..0x5118",
                    "0x5127..0x5138",
                    "0x5147..0x5158",
                    "0x5167..0x5178",
                    "0x5187..0x5198",
                    "0x51A7..0x51B8",
                ],
                "attr_byte": "0x39",
                "end_byte": "0xFE",
                "pad_byte": "0x1F",
                "wram_stripe_index": "$7F:837B",
                "wram_stripe_buffer": "$7F:837D",
            },
            "ow_hud_switch_safety": {
                "safe_to_swap_gfx02a_on_ow": True,
                "reason": (
                    "All 36 shared GFX 0x2A tiles (including space 0x1F and digits 0x22..0x2B "
                    "used by OW life counter at VRAM 0x5087..0x5088, plus File-Select MARIO/PLAYER/"
                    "ERASE DATA tiles) are byte-for-byte identical between boss (ja) and r46 (en). "
                    "MARIO label on OW is not in BG3 GFX 0x2A."
                ),
                "identical_gfx02a_tiles": [f"0x{t:02X}" for t in same_2a],
            },
        },
        "gfx_audit": gfx_audit,
        "tile_diffs": tile_diffs,
        "en_tile_translator": build_en_tile_translator(),
        "ja": {
            "gfx_donor": "boss",
            "ow_table_base": f"${ow_tables['boss'][0]:06X}",
            "msg_table_base": f"${msg_tables['boss'][0]:06X}",
            "ow_names": ja_ow_names,
            "messages": ja_messages,
        },
        "en": (
            {
                "priority": ["demo-1-1", "demo-only-1", "demo7-en", "demo6"],
                "ow_summary": {
                    "total": 96,
                    "english": len(DEMO_1_1_EN_OW_SLOTS) + len(DEMO_ONLY_1_EN_OW_SLOTS) + len(demo7_en_by_slot),
                    "blank": len(BLANK_OW_SLOTS),
                    "japanese_fallback": len(POST_DEMO7_JP_OW_SLOTS),
                    "demo11_en_slots": [f"0x{s:02X}" for s in DEMO_1_1_EN_OW_SLOTS],
                    "demo_only_1_en_slots": [f"0x{s:02X}" for s in DEMO_ONLY_1_EN_OW_SLOTS],
                    "demo7_en_slots": [f"0x{s:02X}" for s in sorted(demo7_en_by_slot)],
                    "excluded_post_demo7_slots": [f"0x{s:02X}" for s in POST_DEMO7_JP_OW_SLOTS],
                },
                "message_summary": {
                    "total": 144,
                    "english": len(DEMO_1_1_EN_MSG_SLOTS),
                    "empty": sum(1 for m in en_messages if m["hex"] == "fe"),
                    "japanese_fallback": sum(1 for m in en_messages if m["needs_jp_font"] == 1),
                    "demo11_en_slots": list(DEMO_1_1_EN_MSG_SLOTS),
                    "excluded_demo6_vanilla_smw_slots": [10, 16, 42, 43, 74, 75, 76, 77, 78, 79, 81, 126],
                },
                "ow_names": en_ow_names,
                "messages": en_messages,
            }
            if include_demo7_en_ow
            else {
                "priority": ["demo-1-1", "demo-only-1", "demo7", "demo6"],
                "ow_summary": {
                    "total": 96,
                    "english": len(DEMO_1_1_EN_OW_SLOTS) + len(DEMO_ONLY_1_EN_OW_SLOTS),
                    "blank": len(BLANK_OW_SLOTS),
                    "japanese_fallback": 96 - len(DEMO_1_1_EN_OW_SLOTS) - len(DEMO_ONLY_1_EN_OW_SLOTS) - len(BLANK_OW_SLOTS),
                    "demo11_en_slots": [f"0x{s:02X}" for s in DEMO_1_1_EN_OW_SLOTS],
                    "demo_only_1_en_slots": [f"0x{s:02X}" for s in DEMO_ONLY_1_EN_OW_SLOTS],
                    "excluded_demo6_demo7_vanilla_slots": ["0x5A (STAR WORLD 5)"],
                },
                "message_summary": {
                    "total": 144,
                    "english": len(DEMO_1_1_EN_MSG_SLOTS),
                    "empty": sum(1 for m in en_messages if m["hex"] == "fe"),
                    "japanese_fallback": sum(1 for m in en_messages if m["needs_jp_font"] == 1),
                    "demo11_en_slots": list(DEMO_1_1_EN_MSG_SLOTS),
                    "excluded_demo6_vanilla_smw_slots": [10, 16, 42, 43, 74, 75, 76, 77, 78, 79, 81, 126],
                },
                "ow_names": en_ow_names,
                "messages": en_messages,
            }
        ),
        "custom_room_messages": {
            "hook_address": "$03:BB90 -> JML $10:B6A6",
            "entries": custom_remaps,
        },
        "mazo_messages": mazo_msgs,
        "stripe_audit": {
            "pointer_table": "$00:84D0..85BC (includes $00:84F9 inside credits block $00:84F1..8598)",
            "pre_credits_pointer_diffs": len(stripe_diffs_pre_credits),
            "credits_pointer_diffs_boss_vs_r46": credits_ptr_diffs,
            "title_stripe_address": "$10:E207",
            "title_stripe_note": (
                "boss uses GFX 0x28 tiles 38,39,48,49,55,56,65,66 for JP Title border/subtitle; "
                "r46 blanks 55,56,65,66 and replaces them with 57,58,59 brick border. "
                "File-Select stripes ($05:B0FF, $05:B91C, $05:B872, $05:B8C7) are identical between boss and r46 "
                "and use only shared GFX 0x28/0x29/0x2A/0x2B tiles."
            ),
            "boss_title_stripe_size": len(boss_title_stripe),
            "boss_title_stripe_sha256": sha(boss_title_stripe),
            "boss_title_stripe_hex": boss_title_stripe.hex(),
        },
        "rooms": rooms_audit,
        "room_summary": {
            "total": len(rooms_audit),
            "needs_jp_font_count": sum(r["needs_jp_font"] for r in rooms_audit),
            "persistent_jp_font_rooms": [f"0x{r:03X}" for r in PERSISTENT_JP_ROOMS],
            "mazo_message_rooms": [f"0x{r:03X}" for r in MAZO_MSG_ROOMS],
            "shop_rooms": [f"0x{r:03X}" for r in SHOP_ROOMS],
        },
    }

    pack = build_bmlg_pack(audit, local_dir=ldir)
    audit["bmlg_pack"] = {
        "magic": "BMLG",
        "version": 1,
        "bank_address": "D58000",
        "header_size": 64,
        "total_size": len(pack),
        "sha256": sha(pack),
        "control_block_address": "908FF0",
        "control_block_size": 16,
        "effective_lang_address": "908FF0",
        "header_fields": [
            {"offset": "0x00", "size": 4, "name": "magic", "value": "BMLG"},
            {"offset": "0x04", "size": 2, "name": "version", "value": 1},
            {"offset": "0x06", "size": 2, "name": "header_size", "value": 64},
            {"offset": "0x08", "size": 4, "name": "total_size"},
            {"offset": "0x0C", "size": 2, "name": "ja_gfx028_off"},
            {"offset": "0x0E", "size": 2, "name": "ja_gfx02a_off"},
            {"offset": "0x10", "size": 2, "name": "ja_gfx02b_off"},
            {"offset": "0x12", "size": 2, "name": "en_gfx028_off"},
            {"offset": "0x14", "size": 2, "name": "en_gfx02a_off"},
            {"offset": "0x16", "size": 2, "name": "en_gfx02b_off"},
            {"offset": "0x18", "size": 2, "name": "ja_ow_names_off"},
            {"offset": "0x1A", "size": 2, "name": "en_ow_names_off"},
            {"offset": "0x1C", "size": 2, "name": "ow_needs_jp_font_off"},
            {"offset": "0x1E", "size": 2, "name": "ja_msg_ptrs_off"},
            {"offset": "0x20", "size": 2, "name": "ja_msg_blob_off"},
            {"offset": "0x22", "size": 2, "name": "ja_msg_blob_size"},
            {"offset": "0x24", "size": 2, "name": "en_msg_ptrs_off"},
            {"offset": "0x26", "size": 2, "name": "en_msg_blob_off"},
            {"offset": "0x28", "size": 2, "name": "en_msg_blob_size"},
            {"offset": "0x2A", "size": 2, "name": "msg_needs_jp_font_off"},
            {"offset": "0x2C", "size": 2, "name": "mazo_msg_192_off"},
            {"offset": "0x2E", "size": 2, "name": "mazo_msg_191_off"},
            {"offset": "0x30", "size": 2, "name": "room_font_policy_off"},
            {"offset": "0x32", "size": 2, "name": "room_msg_remap_off"},
            {"offset": "0x34", "size": 2, "name": "ja_title_stripe_off"},
            {"offset": "0x36", "size": 2, "name": "ja_title_stripe_size"},
            {"offset": "0x38", "size": 8, "name": "reserved"},
        ],
    }
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dir", help="Override local/ directory path.")
    parser.add_argument(
        "--legacy-r47",
        action="store_true",
        help="Generate the legacy r47 audit (10 EN OW slots, lang-r47-v1).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output JSON path (default: config/native-content/localization-audit-r49.json).",
    )
    args = parser.parse_args()
    audit = generate_audit(
        Path(args.local_dir) if args.local_dir else None,
        include_demo7_en_ow=not args.legacy_r47,
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, indent=2) + "\n")
    print(
        f"Wrote {out_path} (BMLG pack={audit['bmlg_pack']['total_size']} B, "
        f"sha256={audit['bmlg_pack']['sha256'][:16]})"
    )


if __name__ == "__main__":
    main()

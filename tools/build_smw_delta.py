#!/usr/bin/env python3
"""Build and verify BMPT v1 delta patches against vanilla Super Mario World (U) [!].

A BMPT v1 patch reconstructs the target ROM (data/rom.sfc) and all external
native content packs (data/packs/*.bin) from a player-supplied unmodified US
Super Mario World (U) [!] ROM (524,288 bytes headerless, or 524,800 bytes with
a 512-byte copier header stripped by the patcher).

Every contiguous match >= MIN_MATCH bytes present in the vanilla SMW base ROM
is encoded as OP_COPY(src_offset, length), and zero-byte runs >= MIN_ZERO bytes
are encoded as OP_ZERO(length), so unmodified vanilla SMW segments are copied
from the player's own ROM rather than shipped as literal bytes.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

MAGIC = b"BMPT\x01\x00\x00\x00"
OP_COPY = 1
OP_ZERO = 2
OP_LITERAL = 3

MIN_MATCH = 12
MIN_ZERO = 12
ANCHOR_LEN = 8

BASE_SIZE = 524288
BASE_SHA256 = "0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_base_rom(raw: bytes) -> bytes:
    """Accept 524,288-byte headerless or 524,800-byte SMC-headered US SMW ROM."""
    if len(raw) == BASE_SIZE + 512:
        raw = raw[512:]
    if len(raw) != BASE_SIZE:
        raise ValueError(f"unexpected base ROM size {len(raw)} (expected {BASE_SIZE} or {BASE_SIZE + 512})")
    digest = sha256_bytes(raw)
    if digest != BASE_SHA256:
        raise ValueError(f"base ROM SHA-256 {digest} does not match US Super Mario World (U) [!] ({BASE_SHA256})")
    return raw


def build_base_index(base: bytes) -> dict[bytes, list[int]]:
    """Index 8-byte anchors across the 512 KB base ROM."""
    index: dict[bytes, list[int]] = {}
    limit = len(base) - ANCHOR_LEN + 1
    # Step by 1 so any aligned or unaligned vanilla block (including relocated
    # SPC700 music blocks in rom.sfc and music-pack.bin) is matched cleanly.
    for pos in range(limit):
        key = base[pos : pos + ANCHOR_LEN]
        if key == b"\x00" * ANCHOR_LEN:
            continue
        bucket = index.get(key)
        if bucket is None:
            index[key] = [pos]
        elif len(bucket) < 64:
            bucket.append(pos)
    return index


def encode_stream(target: bytes, base: bytes, index: dict[bytes, list[int]]) -> list[tuple]:
    """Encode target bytes into (OP_COPY, off, len), (OP_ZERO, len), (OP_LITERAL, bytes)."""
    ops: list[tuple] = []
    lit_start = 0
    pos = 0
    n = len(target)
    base_len = len(base)
    mv_t = memoryview(target)
    mv_b = memoryview(base)

    def flush_literal(upto: int) -> None:
        if upto > lit_start:
            ops.append((OP_LITERAL, bytes(mv_t[lit_start:upto])))

    while pos < n:
        # 1. Check zero run first (very fast and avoids false base zero matches)
        if target[pos] == 0 and pos + MIN_ZERO <= n and mv_t[pos : pos + MIN_ZERO] == b"\x00" * MIN_ZERO:
            end = pos + MIN_ZERO
            while end < n and target[end] == 0:
                end += 1
            flush_literal(pos)
            ops.append((OP_ZERO, end - pos))
            pos = end
            lit_start = pos
            continue

        # 2. Check base ROM match
        if pos + MIN_MATCH <= n:
            candidates = index.get(bytes(mv_t[pos : pos + ANCHOR_LEN]))
            if candidates:
                best_off = -1
                best_len = MIN_MATCH - 1
                max_possible = n - pos
                for cand in candidates:
                    # Quick check at best_len before scanning
                    if cand + best_len >= base_len:
                        continue
                    if target[pos + best_len] != base[cand + best_len]:
                        continue
                    limit = min(max_possible, base_len - cand)
                    mlen = ANCHOR_LEN
                    while mlen < limit and target[pos + mlen] == base[cand + mlen]:
                        mlen += 1
                    if mlen > best_len:
                        best_len = mlen
                        best_off = cand
                        if best_len == max_possible:
                            break
                if best_off >= 0:
                    flush_literal(pos)
                    ops.append((OP_COPY, best_off, best_len))
                    pos += best_len
                    lit_start = pos
                    continue

        pos += 1

    flush_literal(n)
    return ops


def collect_target_packs(target: str) -> list[dict]:
    """Collect ALL runtime packs for a target (sprite_gap + music_region + sprite_graphics)."""
    import native_sprite_gap
    import native_sprite_graphics

    cfg = json.loads((ROOT / "config/restorations" / f"{target}.json").read_text())
    rest_dir = ROOT / "local/restoration" / target
    entries: list[dict] = []

    for p in native_sprite_gap.packs(target):
        path = rest_dir / p["pack_file"]
        data = path.read_bytes()
        if len(data) != p["size"] or sha256_bytes(data) != p["sha256"]:
            raise ValueError(f"pack mismatch for {p['variable']}: {path}")
        entries.append({
            "variable": p["variable"],
            "pack_file": p["pack_file"],
            "rel_path": f"data/packs/{p['pack_file']}",
            "size": p["size"],
            "sha256": p["sha256"],
            "source_path": path,
        })

    region = cfg.get("music_region_pack")
    if region:
        path = rest_dir / region["pack_file"]
        data = path.read_bytes()
        if len(data) != region["pack_size"] or sha256_bytes(data) != region["pack_sha256"]:
            raise ValueError(f"music region pack mismatch: {path}")
        entries.append({
            "variable": "BM_NATIVE_CONTENT_PACK",
            "pack_file": region["pack_file"],
            "rel_path": f"data/packs/{region['pack_file']}",
            "size": region["pack_size"],
            "sha256": region["pack_sha256"],
            "source_path": path,
        })

    for p in native_sprite_graphics.packs(target):
        path = rest_dir / p["pack_file"]
        data = path.read_bytes()
        if len(data) != p["size"] or sha256_bytes(data) != p["sha256"]:
            raise ValueError(f"sprite graphics pack mismatch for {p['variable']}: {path}")
        entries.append({
            "variable": p["variable"],
            "pack_file": p["pack_file"],
            "rel_path": f"data/packs/{p['pack_file']}",
            "size": p["size"],
            "sha256": p["sha256"],
            "source_path": path,
        })

    # Deduplicate files if two variables ever alias the same pack_file while preserving all variables
    return entries


def build_patch_bytes(target: str, base_rom_path: Path) -> tuple[bytes, dict]:
    """Build BMPT v1 patch bytes and return (patch_bytes, stats)."""
    base = normalize_base_rom(base_rom_path.read_bytes())
    index = build_base_index(base)

    cfg = json.loads((ROOT / "config/restorations" / f"{target}.json").read_text())
    rest_dir = ROOT / "local/restoration" / target
    rom_path = rest_dir / "rom.sfc"
    rom_bytes = rom_path.read_bytes()
    if len(rom_bytes) != cfg["output"]["size"] or sha256_bytes(rom_bytes) != cfg["output"]["sha256"]:
        raise ValueError("restoration ROM differs from recipe output")

    pack_entries = collect_target_packs(target)
    # Unique output files in deterministic order: data/rom.sfc followed by unique data/packs/*
    files_to_encode: list[tuple[str, bytes]] = [("data/rom.sfc", rom_bytes)]
    seen_paths = {"data/rom.sfc"}
    for item in pack_entries:
        rel = item["rel_path"]
        if rel not in seen_paths:
            seen_paths.add(rel)
            files_to_encode.append((rel, item["source_path"].read_bytes()))

    out = bytearray()
    out += MAGIC
    out += struct.pack("<I", BASE_SIZE)
    out += bytes.fromhex(BASE_SHA256)
    out += struct.pack("<I", len(files_to_encode))

    total_copy_bytes = 0
    total_zero_bytes = 0
    total_literal_bytes = 0
    total_output_bytes = 0

    for rel_path, content in files_to_encode:
        rel_utf8 = rel_path.encode("utf-8")
        digest = bytes.fromhex(sha256_bytes(content))
        ops = encode_stream(content, base, index)
        out += struct.pack("<H", len(rel_utf8))
        out += rel_utf8
        out += struct.pack("<I", len(content))
        out += digest
        out += struct.pack("<I", len(ops))
        for op in ops:
            kind = op[0]
            if kind == OP_COPY:
                _, src_off, length = op
                out += struct.pack("<BII", OP_COPY, src_off, length)
                total_copy_bytes += length
            elif kind == OP_ZERO:
                _, length = op
                out += struct.pack("<BI", OP_ZERO, length)
                total_zero_bytes += length
            elif kind == OP_LITERAL:
                _, chunk = op
                out += struct.pack("<BI", OP_LITERAL, len(chunk))
                out += chunk
                total_literal_bytes += len(chunk)
            else:
                raise AssertionError(f"unknown op {kind}")
        total_output_bytes += len(content)

    patch_body_sha = hashlib.sha256(out).digest()
    out += patch_body_sha
    stats = {
        "target": target,
        "file_count": len(files_to_encode),
        "pack_env_count": len(pack_entries),
        "total_output_bytes": total_output_bytes,
        "copied_from_base_bytes": total_copy_bytes,
        "zero_run_bytes": total_zero_bytes,
        "literal_diff_bytes": total_literal_bytes,
        "patch_size_bytes": len(out),
        "patch_sha256": sha256_bytes(bytes(out)),
    }
    return bytes(out), stats


def apply_patch_bytes(raw_base: bytes, patch_data: bytes) -> dict[str, bytes]:
    """Reference BMPT v1 decoder for testing and verification."""
    if len(patch_data) < 8 + 4 + 32 + 4 + 32:
        raise ValueError("patch file is truncated")
    body, expected_patch_sha = patch_data[:-32], patch_data[-32:]
    if hashlib.sha256(body).digest() != expected_patch_sha:
        raise ValueError("patch integrity SHA-256 mismatch")

    mv = memoryview(body)
    if bytes(mv[:8]) != MAGIC:
        raise ValueError("invalid BMPT magic")
    (expected_base_size,) = struct.unpack_from("<I", mv, 8)
    expected_base_sha = bytes(mv[12:44]).hex()
    (file_count,) = struct.unpack_from("<I", mv, 44)
    cursor = 48

    if len(raw_base) == expected_base_size + 512:
        base = raw_base[512:]
    else:
        base = raw_base
    if len(base) != expected_base_size or sha256_bytes(base) != expected_base_sha:
        raise ValueError("base ROM does not match expected size/SHA-256")

    outputs: dict[str, bytes] = {}
    for _ in range(file_count):
        (path_len,) = struct.unpack_from("<H", mv, cursor)
        cursor += 2
        rel_path = bytes(mv[cursor : cursor + path_len]).decode("utf-8")
        cursor += path_len
        out_size, = struct.unpack_from("<I", mv, cursor)
        cursor += 4
        expected_sha = bytes(mv[cursor : cursor + 32]).hex()
        cursor += 32
        (op_count,) = struct.unpack_from("<I", mv, cursor)
        cursor += 4

        buf = bytearray()
        for _ in range(op_count):
            kind = mv[cursor]
            cursor += 1
            if kind == OP_COPY:
                src_off, length = struct.unpack_from("<II", mv, cursor)
                cursor += 8
                if src_off + length > len(base):
                    raise ValueError("OP_COPY out of base bounds")
                buf += base[src_off : src_off + length]
            elif kind == OP_ZERO:
                (length,) = struct.unpack_from("<I", mv, cursor)
                cursor += 4
                buf += b"\x00" * length
            elif kind == OP_LITERAL:
                (length,) = struct.unpack_from("<I", mv, cursor)
                cursor += 4
                buf += mv[cursor : cursor + length]
                cursor += length
            else:
                raise ValueError(f"invalid BMPT opcode {kind}")
        if len(buf) != out_size:
            raise ValueError(f"decoded size mismatch for {rel_path}: {len(buf)} != {out_size}")
        if sha256_bytes(bytes(buf)) != expected_sha:
            raise ValueError(f"decoded SHA-256 mismatch for {rel_path}")
        outputs[rel_path] = bytes(buf)

    if cursor != len(mv):
        raise ValueError("trailing bytes in patch body")
    return outputs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="demo11-native-product-r45")
    parser.add_argument("--base", type=Path, default=ROOT.parent / "roms/Super Mario World (U) [!].smc")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    patch_bytes, stats = build_patch_bytes(args.target, args.base)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patch_bytes)
    print(json.dumps(stats, indent=2))

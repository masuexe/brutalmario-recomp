#!/usr/bin/env python3
"""Qualify the overworld map music correction for World 4 and World 6.

Checks:
  1. The base product ROM identity and the four reviewed table bytes.
  2. That patching the base ROM reproduces the target ROM byte for byte.
  3. Reference-host music requests: World 6 (submap 1) changes 0x22 -> 0x23,
     World 4 (submap 2) changes 0x27 -> 0x22, and submap 3 / Special World
     (submap 5) stay unchanged.
  4. Native runtime music requests on the same submaps when the dense captures
     are present.

The table is OverworldMusic ($04:8D8A) and its duplicate OverworldMusic2
($04:DBC8). Each entry is one byte per submap.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BASE_TARGET = "demo11-native-product"
BASE_SHA = "a1c9d7c8f09399b60193302e33bb1c8111ac0fe8e5b1cb5684fb6f277fddbf91"
TARGET = "demo11-overworld-music"
TARGET_SHA = "4ee6d47e0f3a6bfb5395d7531f683ab8aaedf6b29de15ab877341adbd0b71e8b"

# file offset, before, after
PATCHES = [
    (0x20D8B, 0x22, 0x23, "OverworldMusic submap 1 (World 6 Sky)"),
    (0x20D8C, 0x27, 0x22, "OverworldMusic submap 2 (World 4 Cave)"),
    (0x25BC9, 0x22, 0x23, "OverworldMusic2 submap 1 (World 6 Sky)"),
    (0x25BCA, 0x27, 0x22, "OverworldMusic2 submap 2 (World 4 Cave)"),
]
TABLE_A = 0x20D8A
TABLE_B = 0x25BC8
EXPECTED_TABLE = bytes([0x1E, 0x23, 0x22, 0x25, 0x29, 0x27, 0x26])

# submap -> expected last music request (1DFB) before / after
REFERENCE = {
    1: (0x22, 0x23),
    2: (0x27, 0x22),
    3: (0x25, 0x25),
    5: (0x27, 0x27),
}
NATIVE = {1: (0x22, 0x23), 2: (0x27, 0x22)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)


def last_music(trace_path):
    last = 0
    for line in trace_path.read_text().splitlines():
        entry = json.loads(line)
        if entry["adr"].lower() == "0x01dfb" and entry["val"] != "0x00":
            last = int(entry["val"], 16)
    return last


def dense_music(capture):
    """Return the set of nonzero 1DFB values across dense native dumps."""
    found = set()
    for path in sorted(capture.glob("d*.wram.bin")):
        data = path.read_bytes()
        if data[0x1DFB]:
            found.add(data[0x1DFB])
    return found


def main():
    base = (ROOT / "local/restoration" / BASE_TARGET / "rom.sfc").read_bytes()
    require(sha(base) == BASE_SHA, "base product ROM identity changed")

    rebuilt = bytearray(base)
    for offset, before, after, role in PATCHES:
        require(rebuilt[offset] == before,
                f"{role} before byte is not {before:#04x}")
        rebuilt[offset] = after
    rebuilt = bytes(rebuilt)
    require(sha(rebuilt) == TARGET_SHA, "rebuilt ROM identity differs")

    target = (ROOT / "local/restoration" / TARGET / "rom.sfc").read_bytes()
    require(target == rebuilt, "target ROM differs from the reviewed rebuild")

    require(target[TABLE_A:TABLE_A + 7] == EXPECTED_TABLE,
            "OverworldMusic table bytes differ")
    require(target[TABLE_B:TABLE_B + 7] == EXPECTED_TABLE,
            "OverworldMusic2 table bytes differ")
    # Nothing else in the table or its neighbours moved.
    for start in range(TABLE_A - 16, TABLE_A + 16):
        if start not in {p[0] for p in PATCHES}:
            require(target[start] == base[start], f"unexpected byte at {start:#x}")
    for start in range(TABLE_B - 16, TABLE_B + 16):
        if start not in {p[0] for p in PATCHES}:
            require(target[start] == base[start], f"unexpected byte at {start:#x}")

    checked = 0
    for submap, (before, after) in REFERENCE.items():
        base_trace = ROOT / "local/captures" / f"owm-ref-base-map{submap}" / "wram.jsonl"
        patch_trace = ROOT / "local/captures" / f"owm-ref-patch-map{submap}" / "wram.jsonl"
        if not base_trace.is_file() or not patch_trace.is_file():
            print(f"  reference submap {submap}: captures absent, skipped")
            continue
        require(last_music(base_trace) == before,
                f"reference base submap {submap} requested {last_music(base_trace):#04x}, "
                f"expected {before:#04x}")
        require(last_music(patch_trace) == after,
                f"reference patched submap {submap} requested {last_music(patch_trace):#04x}, "
                f"expected {after:#04x}")
        checked += 1

    for submap, (before, after) in NATIVE.items():
        base_cap = ROOT / "local/captures" / f"owm-d2-base-map{submap}"
        new_cap = ROOT / "local/captures" / f"owm-d2-new-map{submap}"
        if not base_cap.is_dir() or not new_cap.is_dir():
            print(f"  native submap {submap}: captures absent, skipped")
            continue
        base_seen = dense_music(base_cap)
        new_seen = dense_music(new_cap)
        require(before in base_seen, f"native base submap {submap} never requested {before:#04x}: {sorted(base_seen)}")
        require(after in new_seen, f"native patched submap {submap} never requested {after:#04x}: {sorted(new_seen)}")
        checked += 1

    print(f"PASS: overworld music table corrected; {checked} submap checks; "
          f"target ROM {TARGET_SHA[:16]}")


if __name__ == "__main__":
    main()

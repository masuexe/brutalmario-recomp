#!/usr/bin/env python3
"""Qualify the sprite 34 light circle fix for room 16A.

The checker verifies the r24 image, the single patched byte and the sprite
state in two rooms. Room 16A must now run the circle branch. Room 167 must
keep the accepted frame.
"""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_rom import verify
from qualify_world1_next_course import require
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = "demo11-native-product-r24"
PARENT = "demo11-native-product-r22"
PATCH_OFFSET = 0x1F6C06


def body(directory, tag):
    path = ROOT / "local/captures" / directory / (tag + ".wram.bin")
    return path.read_bytes()


def frame(directory, tag):
    path = ROOT / "local/captures" / directory / (tag + ".fb.bgrx")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state(data, slot):
    """Return the state word and the world position of one sprite slot."""
    return dict(state=data[0x1504 + slot],
                x=data[0xE4 + slot] + 256 * data[0x14E0 + slot],
                y=data[0xD8 + slot] + 256 * data[0x14D4 + slot])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "use a fresh report path")

    cfg = json.loads((ROOT / "config/restorations" / (TARGET + ".json")).read_text())
    parent = json.loads((ROOT / "config/restorations" / (PARENT + ".json")).read_text())
    require(cfg["base_restoration"] == PARENT, "target lineage differs")
    rom = (ROOT / "local/restoration" / TARGET / "rom.sfc").read_bytes()
    verify(rom, cfg["output"], "sprite 34 candidate")

    patches = cfg["native_sprite_gap"]["extra_patches"]
    require(len(patches) == 1, "the target must hold one extra patch")
    patch = patches[0]
    require(patch["offset"] == PATCH_OFFSET, "patch offset differs")
    require(patch["before"] == "6b" and patch["after"] == "ea",
            "patch bytes differ from the review")

    base = (ROOT / "local/restoration" / PARENT / "rom.sfc").read_bytes()
    require(base[PATCH_OFFSET:PATCH_OFFSET + 1] == bytes.fromhex("6b"),
            "the parent byte differs from the review")
    require(rom[PATCH_OFFSET:PATCH_OFFSET + 1] == bytes.fromhex("ea"),
            "the candidate byte differs from the review")
    differing = [index for index in range(len(rom)) if rom[index] != base[index]]
    require(differing == [PATCH_OFFSET], "the candidate changed more than one byte")

    room16a = state(body("r24-room16a-v1", "r2"), 7)
    room16a_parent = state(body("r22-room16a-v1", "r2"), 7)
    require(room16a_parent["state"] == 0, "the parent sprite state differs")
    require(room16a["state"] == 0x0C, "the candidate sprite state differs")
    require(room16a["x"] != room16a_parent["x"] or room16a["y"] != room16a_parent["y"],
            "the candidate sprite did not move")

    room167 = state(body("r24-room167-v1", "r2"), 6)
    room167_parent = state(body("r22-room167-v1", "r2"), 6)
    require(room167 == room167_parent, "room 167 state changed")
    require(frame("r24-room167-v1", "r2") == frame("r22-room167-v1", "r2"),
            "room 167 frame changed")
    require(frame("r24-room16a-v1", "r2") != frame("r22-room16a-v1", "r2"),
            "room 16A frame did not change")

    report = dict(
        target=TARGET, parent=PARENT, rom_sha256=cfg["output"]["sha256"],
        patch=dict(offset=f"{PATCH_OFFSET:06X}", before="6b", after="ea",
                   changed_bytes=len(differing)),
        room16a=dict(candidate=room16a, parent=room16a_parent,
                     frame_candidate=frame("r24-room16a-v1", "r2"),
                     frame_parent=frame("r22-room16a-v1", "r2")),
        room167=dict(candidate=room167, parent=room167_parent,
                     frame_candidate=frame("r24-room167-v1", "r2"),
                     frame_parent=frame("r22-room167-v1", "r2")),
        checker_sha256=sha(Path(__file__).read_bytes()),
        scope=__doc__.strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + chr(10))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

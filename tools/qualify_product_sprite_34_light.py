#!/usr/bin/env python3
"""Qualify the boss sprite 34 light circle in the product line.

The checker verifies the r25 image, the module recipe and the code pack. It
then reads two captures. Room 16A must run the light circle. Room 167 must
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
TARGET = "demo11-native-product-r25"
PARENT = "demo11-native-product-r22"
MODULE_BANK = 0x80


def body(directory, tag):
    return (ROOT / "local/captures" / directory / (tag + ".wram.bin")).read_bytes()


def frame(directory, tag):
    path = ROOT / "local/captures" / directory / (tag + ".fb.bgrx")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slot_state(data, slot):
    return dict(state=data[0x1504 + slot],
                timer=data[0x151C + slot],
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

    recipe = json.loads(
        (ROOT / "config/native-content/sprite34-boss-module.json").read_text())
    require(recipe["code"]["size"] == 5645, "module size differs")
    require(recipe["record"]["slot"] == "34", "module slot differs")
    require(recipe["code"]["native_address"][:2] == "80",
            "module must live in bank 80; bank C0 does not resolve")
    require(int(recipe["code"]["native_address"], 16) >> 16 == MODULE_BANK,
            "module bank differs from the review")

    base = (ROOT / "local/restoration" / PARENT / "rom.sfc").read_bytes()
    patch = recipe["unapplied_rom_patches"][0]
    require(rom[patch["offset"]:patch["offset"] + 16] == bytes.fromhex(patch["after"]),
            "the candidate record differs from the review")
    differing = [index for index in range(len(rom)) if rom[index] != base[index]]
    record_end = patch["offset"] + 16
    require(all(patch["offset"] <= index < record_end for index in differing),
            "the candidate changed a byte outside the record")
    require(len(differing) == 6, "the candidate must change the six pointer bytes")

    room16a = slot_state(body("r25b80-16a-v1", "r2"), 7)
    require(room16a["state"] == 0x0E, "room 16A state differs")
    require(room16a["timer"] != 0, "room 16A timer did not advance")
    require(room16a["x"] != 0, "room 16A sprite did not move")

    room167 = slot_state(body("r25b80-167-v1", "r2"), 6)
    require(room167["state"] == 0x0C, "room 167 state differs")
    require(frame("r25b80-167-v1", "r2") == frame("r22-room167-v1", "r2"),
            "room 167 frame changed")
    require(frame("r25b80-16a-v1", "r2") != frame("r22-room16a-v1", "r2"),
            "room 16A frame did not change")

    report = dict(
        target=TARGET, parent=PARENT, rom_sha256=cfg["output"]["sha256"],
        module=dict(native_address=recipe["code"]["native_address"],
                    size=recipe["code"]["size"],
                    sha256=recipe["code"]["sha256"],
                    record=recipe["record"]["native_raw"]),
        room16a=room16a, room167=room167,
        frames=dict(room16a_candidate=frame("r25b80-16a-v1", "r2"),
                    room16a_parent=frame("r22-room16a-v1", "r2"),
                    room167_candidate=frame("r25b80-167-v1", "r2"),
                    room167_parent=frame("r22-room167-v1", "r2")),
        checker_sha256=sha(Path(__file__).read_bytes()),
        scope=__doc__.strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + chr(10))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

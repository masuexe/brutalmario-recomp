#!/usr/bin/env python3
"""Qualify the room 167 and room 175 sprite graphics packs.

The checker verifies the r22 image, both packs and their pins. It then reads
one capture in each named room and one capture in a room that the manifests do
not name. It requires the VRAM write in each named room and no write in the
other room. For room 167 it also requires that the object character slot
matches the reviewed reference capture.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from qualify_world1_next_course import require
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = "demo11-native-product-r22"
PARENT = "demo11-native-product-r21"


def frame(directory, tag):
    return (ROOT / "local/captures" / directory / (tag + ".vram.bin")).read_bytes()


def applied(directory):
    log = (ROOT / "local/captures" / directory / "run.log").read_text()
    rows = [line for line in log.splitlines()
            if line.startswith("[native-sprite-gfx] applied=")]
    require(len(rows) == 1, "graphics provider did not report one applied count")
    return int(rows[0].split("=")[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "use a fresh report path")

    cfg = json.loads((ROOT / "config/restorations" / (TARGET + ".json")).read_text())
    parent = json.loads((ROOT / "config/restorations" / (PARENT + ".json")).read_text())
    require(cfg["base_restoration"] == PARENT, "target lineage differs")
    require(cfg["output"] == parent["output"], "target must not change image bytes")
    rom = (ROOT / "local/restoration" / TARGET / "rom.sfc").read_bytes()
    verify(rom, cfg["output"], "sprite graphics candidate")

    import native_sprite_graphics as graphics
    packs = graphics.packs(TARGET)
    require(len(packs) == 2, "graphics pack count differs")
    by_room = {}
    for pack in packs:
        data = (ROOT / "local/restoration" / TARGET / pack["pack_file"]).read_bytes()
        verify(data, {"size": pack["size"], "sha256": pack["sha256"]}, "graphics pack")
        require(len(pack["rooms"]) == 1, "a pack must name one room")
        by_room[pack["rooms"][0]] = pack
    require(sorted(by_room) == [0x167, 0x175], "graphics room list differs")

    # Room 175 keeps the accepted pilot range.
    p175 = by_room[0x175]
    require(p175["ranges"] == [[0x6000, 0x8000]], "room 175 range differs")
    require(p175["size"] == 16392, "room 175 pack size differs")
    require(p175["sha256"] ==
            "58ee028b92d17b340abf052386de3ea2c3369f17c37d55b0c8580ac737a9dd82",
            "room 175 pack hash differs")

    # Room 167 supplies the object character slot at VRAM word 7800.
    p167 = by_room[0x167]
    require(p167["ranges"] == [[0x7800, 0x8000]], "room 167 range differs")
    require(p167["size"] == 4104, "room 167 pack size differs")
    require(p167["sha256"] ==
            "85491c48d953b8a0ad15d61817b3f6bdb8d90201c6e6e6c44f53c9a3aff70562",
            "room 167 pack hash differs")

    require(applied("r22-room167-v1") > 0, "room 167 pack was not applied")
    require(applied("r22-room175-v1") > 0, "room 175 pack was not applied")

    # Room 167 object slot must equal the reviewed reference capture.
    reference = frame("cheap167-pipe-ref-v1", "f256")
    cand167 = frame("r22-room167-v1", "r2")
    parent167 = frame("product-r20-room167-direct-v1", "r2")
    require(cand167[0xF000:0x10000] == reference[0xF000:0x10000],
            "room 167 object slot differs from the reference")
    require(parent167[0xF000:0x10000] != reference[0xF000:0x10000],
            "the parent already held the reference object slot")

    # The room 167 pack must not touch VRAM below its range.
    require(sum(1 for i in range(0, 0xF000) if cand167[i] != parent167[i]) == 0,
            "the room 167 pack wrote below its range")

    # Room 175 keeps its accepted VRAM measurement.
    cand175 = frame("r22-room175-v1", "f512")
    parent175 = frame("product-r20-room175-native-v1", "f512")
    donor175 = frame("donor175-native-oam-v2", "f512")
    start, end = p175["ranges"][0]
    require(sum(1 for i in range(start * 2, end * 2) if cand175[i] != donor175[i]) <= 16,
            "room 175 object VRAM differs from the donor inside the range")
    require(sum(1 for i in range(0, start * 2) if cand175[i] != parent175[i]) == 0,
            "room 175 pack wrote outside its range")

    report = dict(
        target=TARGET, parent=PARENT, rom_sha256=cfg["output"]["sha256"],
        packs=[dict(variable=pack["variable"], size=pack["size"], sha256=pack["sha256"],
                    rooms=[f"{room:03X}" for room in pack["rooms"]],
                    ranges=[[f"{a:04X}", b - a] for a, b in pack["ranges"]],
                    persist=pack["persist"])
               for pack in (p167, p175)],
        applied=dict(room167=applied("r22-room167-v1"), room175=applied("r22-room175-v1")),
        room167=dict(
            object_slot_matches_reference=(
                cand167[0xF000:0x10000] == reference[0xF000:0x10000]),
            object_slot_parent_matches_reference=(
                parent167[0xF000:0x10000] == reference[0xF000:0x10000]),
            object_slot_changed_bytes=sum(
                1 for i in range(0xF000, 0x10000) if cand167[i] != parent167[i]),
            below_range_changed_bytes=sum(
                1 for i in range(0, 0xF000) if cand167[i] != parent167[i]),
        ),
        room175=dict(
            inside_vs_donor=sum(
                1 for i in range(start * 2, end * 2) if cand175[i] != donor175[i]),
            outside_vs_parent=sum(
                1 for i in range(0, start * 2) if cand175[i] != parent175[i]),
        ),
        checker_sha256=sha(Path(__file__).read_bytes()),
        scope=__doc__.strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + chr(10))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

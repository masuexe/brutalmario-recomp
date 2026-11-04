#!/usr/bin/env python3
"""Qualify the external sprite graphics provider.

The checker verifies the r21 image, the packs and their pins. It then reads
one capture in the named room and one capture in a room that the manifest does
not name. It requires the VRAM write in the named room and no write in the
other room.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from qualify_sprite95_rooms import body, functional
from qualify_world1_next_course import require
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-product-r21'
PARENT = 'demo11-native-product-r20'


def frame(directory, tag):
    return (ROOT / 'local/captures' / directory / (tag + '.vram.bin')).read_bytes()


def applied(directory):
    log = (ROOT / 'local/captures' / directory / 'run.log').read_text()
    rows = [line for line in log.splitlines() if line.startswith('[native-sprite-gfx] applied=')]
    require(len(rows) == 1, 'graphics provider did not report one applied count')
    return int(rows[0].split('=')[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'use a fresh report path')
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    parent = json.loads((ROOT / 'config/restorations' / (PARENT + '.json')).read_text())
    require(cfg['base_restoration'] == PARENT, 'target lineage differs')
    require(cfg['output'] == parent['output'], 'target must not change image bytes')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'sprite graphics candidate')

    import native_sprite_graphics as graphics
    packs = graphics.packs(TARGET)
    require(len(packs) == 1, 'graphics pack count differs')
    pack = packs[0]
    data = (ROOT / 'local/restoration' / TARGET / pack['pack_file']).read_bytes()
    verify(data, {'size': pack['size'], 'sha256': pack['sha256']}, 'graphics pack')
    require(pack['rooms'] == [0x175], 'graphics room list differs')

    donor = frame('donor175-native-oam-v2', 'f512')
    candidate = frame('product-r21-room175-gfx-v1', 'f512')
    baseline = frame('product-r20-room175-native-v1', 'f512')
    require(applied('product-r21-room175-gfx-v1') == 1, 'graphics pack was not applied')
    require(applied('product-r21-room154-scope-v1') == 0, 'graphics pack leaked to another room')

    start, end = pack['ranges'][0]
    inside = lambda a, b: sum(1 for i in range(start * 2, end * 2) if a[i] != b[i])
    outside = lambda a, b: (sum(1 for i in range(0, start * 2) if a[i] != b[i]) +
                            sum(1 for i in range(end * 2, 0x10000) if a[i] != b[i]))
    require(inside(candidate, donor) == 0, 'candidate VRAM differs from the donor inside the range')
    require(inside(candidate, baseline) > 0, 'candidate VRAM equals the parent inside the range')
    require(outside(candidate, baseline) == 0, 'graphics pack wrote outside its range')

    scope = frame('product-r21-room154-scope-v1', 'r3')
    scope_parent = frame('product-r20-room154-native-v1', 'r3')
    require(scope == scope_parent, 'a room outside the manifest changed its VRAM')

    report = dict(
        target=TARGET, parent=PARENT, rom_sha256=cfg['output']['sha256'],
        pack=dict(variable=pack['variable'], size=pack['size'], sha256=pack['sha256'],
                  rooms=[f'{room:03X}' for room in pack['rooms']],
                  ranges=[[f'{a:04X}', b - a] for a, b in pack['ranges']]),
        applied=dict(named_room=1, other_room=0),
        vram=dict(inside_range_vs_donor=inside(candidate, donor),
                  inside_range_vs_parent=inside(candidate, baseline),
                  outside_range_vs_parent=outside(candidate, baseline)),
        frames=dict(named_room=dict(
            identical_to_parent=(ROOT / 'local/captures/product-r21-room175-gfx-v1/f512.fb.bgrx').read_bytes()
            == (ROOT / 'local/captures/product-r20-room175-native-v1/f512.fb.bgrx').read_bytes()),
            differs_from_donor=sum(1 for a, b in zip(
                (ROOT / 'local/captures/product-r21-room175-gfx-v1/f512.fb.bgrx').read_bytes(),
                donor_frame()) if a != b)),
        checker_sha256=sha(Path(__file__).read_bytes()),
        scope=__doc__.strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + chr(10))
    print(json.dumps(report, indent=2))


def donor_frame():
    return (ROOT / 'local/captures/donor175-native-oam-v2/f512.fb.bgrx').read_bytes()


if __name__ == '__main__':
    main()

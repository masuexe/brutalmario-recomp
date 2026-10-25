#!/usr/bin/env python3
"""Qualify the room 0x146 HP HUD upload.

Room 0x146 fills the legacy $7F:FFE0 HP row and sets $7F:FFDF, but Demo 1-1
omits the legacy HUD upload for it. The recipe extends the accepted HP-bar shim
to that room. The gameplay field must stay byte-identical; only the HUD row may
change.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import lorom

ROOT = Path(ROOT)
TARGET = 'demo11-hp-room146'
BASE = 'demo11-hp-room128'
HUD_WORD = 0x5028
VRAM_ROW = HUD_WORD * 2


def load(path):
    return json.loads(Path(path).read_text())


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    require(cfg['base_restoration'] == BASE, 'base target differs')
    require(cfg['base_output']['sha256'] == base_cfg['output']['sha256'], 'base identity differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'candidate identity differs')

    block = cfg['raw_blocks'][0]
    data = bytes.fromhex(block['bytes'])
    require(sha(data) == block['data']['sha256'], 'block payload hash differs')
    header = lorom(int(block['rats_address'], 16))
    destination = lorom(int(block['destination_address'], 16))
    hook = lorom(0x008DE1)
    changed = [index for index, (left, right) in enumerate(zip(base, rom)) if left != right]
    require(changed, 'candidate is identical to the base')
    for index in changed:
        require(header <= index < header + 8 + len(data) or hook <= index < hook + 4,
                'unexpected changed byte: ' + hex(index))
    require(rom[header:header + 4] == b'STAR', 'RATS header missing')
    require(rom[destination:destination + len(data)] == data, 'installed block differs')
    patch = cfg['code_patches'][0]
    require(base[hook:hook + 4].hex() == patch['before'], 'hook source differs')
    require(rom[hook:hook + 4].hex() == patch['after'], 'hook result differs')
    require(int.from_bytes(bytes.fromhex(patch['after'])[1:], 'little') ==
            int(block['destination_address'], 16), 'hook target differs')

    old = ROOT / 'local/captures' / 'room146-base'
    new = ROOT / 'local/captures' / 'room146-fixed'
    for name, directory in (('base', old), ('fixed', new)):
        body = (directory / 'entry600.wram.bin').read_bytes()
        require(body[0x100] == 0x14, name + ' capture does not reach gameplay')
        require(int.from_bytes(body[0x10B:0x10D], 'little') == 0x146,
                name + ' capture is not room 146')
        require(body[0x1FFDF] == 1, name + ' legacy HUD flag is not set')
        require(any(body[0x1FFE0:0x1FFF0]), name + ' legacy HP row is empty')
    old_fb = (old / 'entry600.fb.bgrx').read_bytes()
    new_fb = (new / 'entry600.fb.bgrx').read_bytes()
    hud_diff = sum(1 for y in range(24) for x in range(256)
                   for i in (4 * (y * 256 + x),)
                   if old_fb[i:i + 3] != new_fb[i:i + 3])
    field_diff = sum(1 for y in range(24, 224) for x in range(256)
                     for i in (4 * (y * 256 + x),)
                     if old_fb[i:i + 3] != new_fb[i:i + 3])
    require(hud_diff > 0, 'HP HUD row did not change')
    require(field_diff == 0, 'gameplay field changed')
    body = (new / 'entry600.wram.bin').read_bytes()
    row = body[0x1FFE0:0x1FFF0]
    old_v = (old / 'entry600.vram.bin').read_bytes()
    new_v = (new / 'entry600.vram.bin').read_bytes()
    for index, value in enumerate(row):
        require(new_v[VRAM_ROW + index * 2] == value,
                'uploaded character differs at ' + str(index))
        require(new_v[VRAM_ROW + index * 2 + 1] == old_v[VRAM_ROW + index * 2 + 1],
                'attribute byte changed at ' + str(index))
    require(old_v[VRAM_ROW:VRAM_ROW + 0x20] != new_v[VRAM_ROW:VRAM_ROW + 0x20],
            'VRAM HP row did not change')

    build = ROOT / 'local/build' / TARGET / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Room 146 HP checks passed: HUD row uploaded, gameplay field unchanged')


if __name__ == '__main__':
    main()

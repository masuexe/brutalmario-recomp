#!/usr/bin/env python3
"""Qualify the boss room graphics and sprite batch.

Room 0x0BC (the middle boss room behind the level 0x15F corridor) referenced
seven empty extended graphics IDs and placed custom sprite 0x2B with the default
record. The chain frees a window in bank 0x39, ports sprite 0x2B, and installs
the 159 extended graphics IDs of the remaining subrooms.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import file_to_lorom, graphics_pointer, lorom, lz2, pointer_offset, sprite_rooms

ROOT = Path(ROOT)
BASE = 'demo11-music-109-49'
SPRITE_TARGET = 'demo11-boss-room-sprites'
FINAL = 'demo11-gfx-boss76'
RECORD_TABLE = 0x188272
DEFAULT = bytes.fromhex('0000ffffffffffff218001218001ffff')
RELOCATED = [(0x14E, 0x1CCB60, 0x1C0F00, 3039), (0x14D, 0x1CD73F, 0x1E1200, 2785),
             (0x14C, 0x1CE220, 0x1E3200, 2698)]


def load(path):
    return json.loads(Path(path).read_text())


def main():
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    sprite_cfg = load(ROOT / 'config/restorations' / (SPRITE_TARGET + '.json'))
    require(sprite_cfg['base_restoration'] == BASE, 'sprite base differs')
    require(sprite_cfg['base_output']['sha256'] == base_cfg['output']['sha256'], 'sprite base identity differs')
    sprite_rom = (ROOT / 'local/restoration' / SPRITE_TARGET / 'rom.sfc').read_bytes()
    require(sha(sprite_rom) == sprite_cfg['output']['sha256'], 'sprite candidate identity differs')
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()

    for gfx, source, destination, size in RELOCATED:
        slot = pointer_offset(gfx)
        require('pointer_after' in sprite_cfg['relocations'][0], 'relocation schema differs')
        require(sprite_rom[destination:destination + size] == base[source:source + size],
                'relocated block differs: %03X' % gfx)
        expected = file_to_lorom(destination + 8).to_bytes(3, 'little')
        require(sprite_rom[slot:slot + 3] == expected, 'relocated pointer differs: %03X' % gfx)
        require(sprite_rom[slot:slot + 3] != base[slot:slot + 3], 'relocated pointer did not change')
        require(base[slot:slot + 3] != bytes(3), 'original pointer was empty')

    sprite = sprite_cfg['custom_sprites'][0]
    require(sprite['id'] == '2B', 'sprite id differs')
    slot = RECORD_TABLE + 0x2B * 16
    require(base[slot:slot + 16] == DEFAULT, 'base record was not default')
    require(sprite_rom[slot:slot + 16].hex() == sprite['record_after'], 'installed 2B record differs')
    source = lorom(int(sprite['source_address'], 16))
    block = donor[source:source + sprite['block']['size']]
    require(sha(block) == sprite['block']['sha256'], '2B donor block differs')
    destination = lorom(int(sprite['destination_address'], 16))
    require(sprite_rom[destination:destination + len(block)] == block, '2B block differs')
    require(sprite['rooms'] == [0xBC], '2B room dependencies differ')

    previous = sprite_cfg['output']['sha256']
    previous_rom = sprite_rom
    count = 0
    for index in range(1, 77):
        target = 'demo11-gfx-boss%d' % index
        cfg = load(ROOT / 'config/restorations' / (target + '.json'))
        require(cfg['base_output']['sha256'] == previous, target + ' base identity differs')
        current = (ROOT / 'local/restoration' / target / 'rom.sfc').read_bytes()
        require(sha(current) == cfg['output']['sha256'], target + ' output identity differs')
        donor_data = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
        for asset in cfg['assets']:
            gfx = int(asset['source_id'], 16)
            require(graphics_pointer(donor_data, gfx) == int(asset['source_address'], 16),
                    target + ' donor pointer differs')
            decoded, compressed = lz2(donor_data, int(asset['source_address'], 16))
            require(sha(decoded) == asset['decoded']['sha256'], target + ' decoded differs')
            require(sha(compressed) == asset['compressed']['sha256'], target + ' compressed differs')
            installed = int.from_bytes(current[pointer_offset(gfx):pointer_offset(gfx) + 3], 'little')
            require(installed == int(asset['destination_address'], 16) if 'destination_address' in asset
                    else True, target + ' installed pointer differs')
            count += 1
        previous = cfg['output']['sha256']
        previous_rom = current
    require(count == 159, 'installed asset count differs: ' + str(count))
    final = (ROOT / 'local/restoration' / FINAL / 'rom.sfc').read_bytes()
    require(sha(final) == previous, 'final identity differs')

    build = ROOT / 'local/build' / FINAL / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / FINAL / RESTORATIONS[FINAL]['binary']
        require(identity['rom_sha256'] == previous, 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')

    bossroom = ROOT / 'local/captures' / 'bossroom76'
    body = (bossroom / 's40.wram.bin').read_bytes()
    require(body[0x100] == 0x14, 'boss room does not reach gameplay')
    require(int.from_bytes(body[0x10B:0x10D], 'little') == 0x0BC, 'boss room is not room 0BC')
    fb = (bossroom / 's48.fb.bgrx').read_bytes()
    mean = sum(fb[i] for i in range(0, len(fb), 4)) / (len(fb) // 4)
    require(mean > 40, 'boss room frame is black: ' + str(round(mean, 1)))
    for tag in ('038', '042', '047'):
        old = (ROOT / 'local/captures' / ('reloc-base-' + tag) / 'entry600.fb.bgrx').read_bytes()
        new = (ROOT / 'local/captures' / ('reloc2-' + tag) / 'entry600.fb.bgrx').read_bytes()
        differ = sum(any(old[i + k] >> 3 != new[i + k] >> 3 for k in range(3))
                     for i in range(0, 256 * 224 * 4, 4))
        require(differ == 0, 'relocated graphics changed rendering: ' + tag)
    print('Boss room graphics and sprite checks passed: 159 assets, sprite 2B')


if __name__ == '__main__':
    main()

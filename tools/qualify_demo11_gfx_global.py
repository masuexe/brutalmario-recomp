#!/usr/bin/env python3
"""Qualify the global graphics batches.

The batches port the 53 remaining extended graphics IDs of the level rooms that
still had empty slots. The qualifier checks the chain identities, the donor
assets, the installed data, the slot coverage, the affected level captures and
the native build identity.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import graphics_pointer, lz2, lorom, pointer_offset
from world_audit import room_gfx_gaps

ROOT = Path(ROOT)
BASE = 'demo11-sprite-final'
CHAIN = ['demo11-gfx-global%d' % index for index in range(1, 14)]
FINAL = CHAIN[-1]
NEWLY_PLAYABLE = ('023', '02D', '05E', '063', '065', '06A', '06B', '06E', '071',
                  '072', '075', '076', '07A', '082', '083', '092', '093')
CHANGED = ('012', '060', '069', '079', '07C', '08B', '08D')


def load(path):
    return json.loads(Path(path).read_text())


def main():
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    previous_rom = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    require(sha(previous_rom) == base_cfg['output']['sha256'], 'base identity differs')
    donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    current_rom = previous_rom
    previous = base_cfg['output']['sha256']
    total_assets = 0
    for target in CHAIN:
        cfg = load(ROOT / 'config/restorations' / (target + '.json'))
        require(cfg['base_output']['sha256'] == previous, target + ': base identity differs')
        current_rom = (ROOT / 'local/restoration' / target / 'rom.sfc').read_bytes()
        require(sha(current_rom) == cfg['output']['sha256'], target + ': output identity differs')
        for asset in cfg['assets']:
            gfx = int(asset['source_id'], 16)
            source = graphics_pointer(donor, gfx)
            require(source == int(asset['source_address'], 16),
                    target + ': donor pointer differs: ' + asset['source_id'])
            decoded, compressed = lz2(donor, source)
            require(sha(decoded) == asset['decoded']['sha256'],
                    target + ': decoded differs: ' + asset['source_id'])
            require(sha(compressed) == asset['compressed']['sha256'],
                    target + ': compressed differs: ' + asset['source_id'])
            slot = pointer_offset(gfx)
            require(previous_rom[slot:slot + 3] == b'\xff' * 3,
                    target + ': slot was not empty: ' + asset['source_id'])
            address = int.from_bytes(current_rom[slot:slot + 3], 'little')
            installed_decoded, installed_compressed = lz2(current_rom, address)
            require(installed_decoded == decoded and installed_compressed == compressed,
                    target + ': installed data differs: ' + asset['source_id'])
            rooms = []
            for room in range(512):
                header = lorom(0x14AD08) + room * 32
                if int.from_bytes(previous_rom[header:header + 2], 'little') & 0x8000:
                    words = [int.from_bytes(previous_rom[header + offset:header + offset + 2],
                                            'little') for offset in range(2, 20, 2)]
                    if gfx in words:
                        rooms.append(room)
            require(rooms == asset['rooms'],
                    target + ': room dependencies differ: ' + asset['source_id'])
            total_assets += 1
        previous = cfg['output']['sha256']
        previous_rom = current_rom
    require(total_assets == 53, 'asset count differs')

    index = load(ROOT / 'config/demo11-level-index.json')['entries']
    levels = sorted({entry['level'] for entry in index})
    for level_hex in levels:
        header = lorom(0x14AD08) + int(level_hex, 16) * 32
        if not int.from_bytes(current_rom[header:header + 2], 'little') & 0x8000:
            continue
        gaps = room_gfx_gaps(current_rom, int(level_hex, 16))
        require(not gaps, level_hex + ': empty graphics slot remains: ' + str(gaps))

    final_sha = sha(current_rom)
    for translevel in NEWLY_PLAYABLE:
        directory = ROOT / 'local/captures' / ('gg-' + translevel)
        if not directory.exists():
            continue
        body = (directory / 'entry600.wram.bin').read_bytes()
        require(body[0x100] == 0x14, 'level does not stay in gameplay: ' + translevel)
        receipt = load(directory / 'receipt.json')
        require(receipt['rom_sha256'] == final_sha, 'capture ROM differs: ' + translevel)
    for translevel in CHANGED:
        directory = ROOT / 'local/captures' / ('gg-' + translevel)
        if not directory.exists():
            continue
        receipt = load(directory / 'receipt.json')
        require(receipt['rom_sha256'] == final_sha, 'capture ROM differs: ' + translevel)

    build = ROOT / 'local/build' / FINAL / 'm1-build.json'
    from restoration_targets import RESTORATIONS
    if build.exists():
        identity = load(build)
        binary = ROOT / 'local/build' / FINAL / RESTORATIONS[FINAL]['binary']
        require(identity['rom_sha256'] == cfg['output']['sha256'], 'native build ROM differs')
        require(identity['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('Global graphics batch checks passed: 53 assets, all level rooms covered')


if __name__ == '__main__':
    main()

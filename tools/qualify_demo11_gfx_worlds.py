#!/usr/bin/env python3
"""Qualify the world-by-world extended graphics batches.

The batches close every empty extended graphics slot of Worlds 2-8. Several
rooms also move from a map return or death mode to gameplay once the graphics
exist. The qualifier checks the chain identities, the graphics data, the slot
coverage, the captures and the native build identity.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset
from world_audit import room_gfx_gaps

ROOT = Path(ROOT)
CHAIN = ['demo11-gfx-world23', 'demo11-gfx-world4a', 'demo11-gfx-world4b',
         'demo11-gfx-world5', 'demo11-gfx-world6', 'demo11-gfx-world7',
         'demo11-gfx-world8a', 'demo11-gfx-world8b', 'demo11-gfx-world8c']
BASE = 'demo11-fix-batch-p'
FINAL = CHAIN[-1]
# Rooms whose entry mode changed because the missing graphics blocked loading.
NEWLY_PLAYABLE = ('047', '041', '037', '016', '031', '022', '020', '04C')
PLAYABLE = ('025', '01C', '02E', '057', '019')
SPECIAL = {'05F': 0x17}
NATIVE_SUBSET = ('025', '01C', '019', '041', '031', '047')


def scenario(capture, tag):
    body = (ROOT / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
    return {'mode': body[0x100], 'room': int.from_bytes(body[0x10B:0x10D], 'little'),
            'lives': body[0x0DBE], 'translevel': body[0x13BF]}


def load(path):
    return json.loads(Path(path).read_text())


def main():
    previous_rom = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    previous = load(ROOT / 'config/restorations' / (BASE + '.json'))['output']['sha256']
    require(sha(previous_rom) == previous, 'base ROM differs')
    donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    current_rom = previous_rom

    for target in CHAIN:
        cfg = load(ROOT / 'config/restorations' / (target + '.json'))
        require(cfg['base_output']['sha256'] == previous, target + ': base identity differs')
        current_rom = (ROOT / 'local/restoration' / target / 'rom.sfc').read_bytes()
        require(sha(current_rom) == cfg['output']['sha256'], target + ': output identity differs')
        total = 0
        for asset in cfg['assets']:
            gfx = int(asset['source_id'], 16)
            pointer = graphics_pointer(donor, gfx)
            decoded, compressed = lz2(donor, pointer)
            require(sha(decoded) == asset['decoded']['sha256'], target + ': decoded differs')
            require(sha(compressed) == asset['compressed']['sha256'], target + ': compressed differs')
            total += len(compressed) + 8
            slot = pointer_offset(gfx)
            require(previous_rom[slot:slot + 3] == b'\xff' * 3, target + ': slot was not empty')
            address = int.from_bytes(current_rom[slot:slot + 3], 'little')
            data = lorom(address)
            header = current_rom[data - 8:data]
            require(header[:4] == b'STAR', target + ': RATS block missing')
            installed_decoded, installed_compressed = lz2(current_rom, address)
            require(installed_decoded == decoded and installed_compressed == compressed,
                    target + ': graphics data differs')
            rooms = []
            for room in range(512):
                header_address = lorom(0x14AD08) + room * 32
                if int.from_bytes(previous_rom[header_address:header_address + 2], 'little') & 0x8000:
                    words = [int.from_bytes(previous_rom[header_address + offset:header_address + offset + 2],
                                            'little') for offset in range(2, 20, 2)]
                    if gfx in words:
                        rooms.append(room)
            require(rooms == asset['rooms'], target + ': room dependencies differ')
        require(total + 0x100 <= cfg['allocation']['size'], target + ': allocation too small')
        previous = cfg['output']['sha256']
        previous_rom = current_rom

    world_map = load(ROOT / 'config/world-map.json')['worlds']
    for world in ('world2', 'world3', 'world4', 'world5', 'world6', 'world7', 'world8'):
        for room_hex in world_map[world]['rooms']:
            gaps = room_gfx_gaps(current_rom, int(room_hex, 16))
            require(not gaps, world + '/' + room_hex + ': empty graphics slot remains: ' + str(gaps))

    final_sha = sha(current_rom)
    for translevel in NEWLY_PLAYABLE + PLAYABLE:
        capture = 'gfxw-' + translevel
        early = scenario(capture, 'entry240')
        late = scenario(capture, 'entry600')
        require(early['mode'] == 0x14 or late['mode'] == 0x14, 'no gameplay: ' + translevel)
        require(late['mode'] == 0x14, 'gameplay does not persist: ' + translevel)
        receipt = load(ROOT / 'local/captures' / capture / 'receipt.json')
        require(receipt['rom_sha256'] == final_sha, 'capture ROM differs: ' + translevel)
    for translevel, mode in SPECIAL.items():
        late = scenario('gfxw-' + translevel, 'entry600')
        require(late['mode'] == mode, 'special mode changed: ' + translevel)

    for translevel in NATIVE_SUBSET:
        native = 'gfxwn-' + translevel
        reference = 'gfxw-' + translevel
        if not (ROOT / 'local/captures' / native).exists():
            continue
        for tag in ('entry240', 'entry600'):
            left = scenario(reference, tag)
            right = scenario(native, tag)
            for key in ('mode', 'room', 'lives', 'translevel'):
                require(left[key] == right[key],
                        'native differs: ' + translevel + '/' + tag + '/' + key)
        native_receipt = load(ROOT / 'local/captures' / native / 'receipt.json')
        require(native_receipt['rom_sha256'] == final_sha, 'native capture ROM differs')

    build = load(ROOT / 'local/build' / FINAL / 'm1-build.json')
    from restoration_targets import RESTORATIONS
    binary = ROOT / 'local/build' / FINAL / RESTORATIONS[FINAL]['binary']
    require(build['rom_sha256'] == final_sha, 'native build ROM differs')
    require(build['binary_sha256'] == sha(binary.read_bytes()), 'native binary differs')
    print('World graphics batches checks passed: Worlds 2-8 have no empty graphics slots')


if __name__ == '__main__':
    main()

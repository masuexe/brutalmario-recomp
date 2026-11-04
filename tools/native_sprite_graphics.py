#!/usr/bin/env python3
"""External sprite graphics packs: manifests, header, runtime wiring.

A pack holds reviewed VRAM ranges. The runtime writes them when the game
enters a room that the manifest names. The manifest pins the pack size and the
SHA-256. The build refuses a manifest that does not match its pins.
"""
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
KEY = 'native_sprite_graphics'


def settings(target):
    path = ROOT / 'config/restorations' / (target + '.json')
    if not path.is_file():
        return None
    cfg = json.loads(path.read_text())
    paths = cfg.get(KEY)
    if not paths:
        return None
    specs = []
    for index, relative in enumerate(paths):
        spec = json.loads((ROOT / relative).read_text())
        if spec.get('schema') != 1 or not spec.get('id'):
            raise ValueError('sprite graphics manifest schema differs')
        variable = 'BM_SPRITE_GRAPHICS_PACK' if index == 0 \
            else 'BM_SPRITE_GRAPHICS_PACK_' + str(index + 1)
        specs.append({'variable': variable, 'manifest': relative, 'spec': spec})
    return cfg, specs


def room_bitmap(rooms):
    bitmap = bytearray(64)
    for text in rooms:
        room = int(text, 16)
        if not 0 <= room < 512:
            raise ValueError('sprite graphics room is out of range')
        bitmap[room >> 3] |= 1 << (room & 7)
    return bytes(bitmap)


def reviewed(spec):
    """Return the validated pack description for one manifest."""
    rooms = spec['rooms']
    ranges = spec['ranges']
    if not rooms or not ranges:
        raise ValueError('sprite graphics manifest is empty')
    expected = 4
    seen = []
    for item in ranges:
        vram, words = int(item['vram'], 16), int(item['words'])
        if vram < 0 or words <= 0 or vram + words > 0x8000:
            raise ValueError('sprite graphics range is out of VRAM')
        for start, end in seen:
            if vram < end and start < vram + words:
                raise ValueError('sprite graphics ranges overlap')
        seen.append((vram, vram + words))
        expected += 4 + words * 2
    if expected != spec['size']:
        raise ValueError('sprite graphics size does not match the ranges')
    return dict(id=spec['id'], slot=spec['slot'], rooms=[int(r, 16) for r in rooms],
                bitmap=room_bitmap(rooms).hex(),
                ranges=[[start, end] for start, end in seen], pack_file=spec['pack_file'],
                size=spec['size'], sha256=spec['sha256'])


def packs(target):
    pair = settings(target)
    if pair is None:
        return []
    cfg, specs = pair
    return [dict(variable=item['variable'], manifest=item['manifest'],
                 source=item['spec']['source_directory'], **reviewed(item['spec']))
            for item in specs]


def header(target):
    packs_ = packs(target)
    if not packs_:
        return ''
    digest = lambda value: '{' + ','.join(str(n) for n in bytes.fromhex(value)) + '}'
    text = ('/* Generated external sprite graphics packs. */\n#include <stdint.h>\n'
            f'#define BM_SPRITE_GRAPHICS_PACKS {len(packs_)}u\n'
            'typedef struct { const char *variable; unsigned size; uint8_t rooms[64]; '
            'uint8_t sha256[32]; } BmSpriteGraphicsPack;\n'
            'static const BmSpriteGraphicsPack bm_sprite_graphics_packs[BM_SPRITE_GRAPHICS_PACKS] = {\n')
    for pack in packs_:
        rooms = '{' + ','.join(str(n) for n in bytes.fromhex(pack['bitmap'])) + '}'
        text += ('{"' + pack['variable'] + '",' + str(pack['size']) + 'u,' + rooms + ',' +
                 digest(pack['sha256']) + '},\n')
    return text + '};\n'


def prepare(target):
    packs_ = packs(target)
    if not packs_:
        return
    directory = ROOT / 'local/restoration' / target
    directory.mkdir(parents=True, exist_ok=True)
    for pack in packs_:
        data = (ROOT / pack['source'] / pack['pack_file']).read_bytes()
        verify(data, {'size': pack['size'], 'sha256': pack['sha256']},
               'sprite graphics pack')
        write_verified(directory / pack['pack_file'], data)


def environment(target, env):
    for pack in packs(target):
        path = ROOT / 'local/restoration' / target / pack['pack_file']
        verify(path.read_bytes(), {'size': pack['size'], 'sha256': pack['sha256']},
               pack['variable'])
        env[pack['variable']] = str(path)


def configure(experiment, binary, target):
    packs_ = packs(target)
    if not packs_:
        return
    import patch_sprite_graphics
    directory = ROOT / 'local/native-content-runtime' / target
    cart = directory / 'runner/src/snes/cart.c'
    if not cart.is_file():
        raise ValueError('sprite graphics provider needs a cartridge copy')
    text, changed = patch_sprite_graphics.patch(cart.read_text())
    if changed:
        cart.write_text(text)
    write_verified(directory / 'native_sprite_graphics_manifest.h',
                   header(target).encode())
    cmake = experiment / 'CMakeLists.txt'
    current = cmake.read_text()
    begin, end = '# BEGIN native sprite graphics', '# END native sprite graphics'
    block = '\n'.join([begin,
        f'target_sources({binary} PRIVATE "{ROOT / "recomp/native_sprite_graphics.c"}")',
        f'target_include_directories({binary} PRIVATE "{ROOT / "recomp"}" '
        f'"{ROOT / "local/upstream/snesrecomp/runner/src/snes"}")', end])
    if begin in current:
        current = current[:current.index(begin)] + block + current[current.index(end) + len(end):]
    else:
        current += '\n' + block + '\n'
    cmake.write_text(current)

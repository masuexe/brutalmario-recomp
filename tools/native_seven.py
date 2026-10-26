#!/usr/bin/env python3
"""Build/configure the isolated cumulative Seven Koopalings entry target."""
import json
from pathlib import Path
import subprocess

from prepare_rom import verify
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-seven-font-entry'


def settings(target):
    path = ROOT / 'config/restorations' / (target+'.json')
    if not path.is_file():
        return None
    cfg = json.loads(path.read_text())
    if 'native_seven' not in cfg:
        return None
    if cfg['schema'] != 1 or cfg['id'] != target:
        raise ValueError('Seven target identity differs')
    from prepare_seven_module import read_recipe
    return cfg, read_recipe(ROOT / cfg['native_seven']['manifest'])


def packs(target):
    cfg, recipe = settings(target)
    previous = json.loads((ROOT / 'config/native-content/sprite9e.json').read_text())
    pins = [('BM_SEVEN_CODE_PACK', dict(recipe['code'], **recipe['code'].get('native_payload', {})),
             recipe['code']['native_address'], recipe['code']['adapted_sha256'], True)]
    if 'graphics_pack' in recipe:
        pins.append(('BM_SEVEN_GRAPHICS_PACK', recipe['graphics_pack'],
                     recipe['graphics_pack']['native_address'],
                     recipe['graphics_pack']['sha256'], False))
    pins.extend((
        ('BM_NATIVE_SPRITE_PACK', previous['code'], previous['code']['native_address'],
         previous['code']['sha256'], True),
        ('BM_NATIVE_GRAPHICS_PACK', dict(previous['graphics']['payload'],
         pack_file=previous['graphics']['pack_file']), previous['graphics']['native_address'],
         previous['graphics']['payload']['sha256'], False),
    ))
    result = []
    for variable, item, address, digest, executable in pins:
        result.append(dict(variable=variable, pack_file=item['pack_file'],
                           address=address, size=item['size'], sha256=digest, executable=executable))
    return result


def header(target):
    cfg, _ = settings(target)
    data = packs(target)
    digest = lambda value: '{'+','.join(str(n) for n in bytes.fromhex(value))+'}'
    text = ('/* Generated immutable cumulative module descriptors. */\n#include <stdint.h>\n'
            f'#define BM_SEVEN_ROM_SIZE {cfg["output"]["size"]}u\n'
            f'#define BM_SEVEN_PACKS {len(data)}u\n'
            'typedef struct { const char *variable; unsigned bank, offset, size, executable, '
            'first_page, last_page; uint8_t sha256[32]; } BmSevenPack;\n'
            'static const uint8_t bm_seven_rom_sha[32] = '+digest(cfg['output']['sha256'])+';\n'
            'static const BmSevenPack bm_seven_packs[BM_SEVEN_PACKS] = {\n')
    for pack in data:
        address = int(pack['address'], 16)
        text += ('{"'+pack['variable']+'",'+','.join(str(n)+'u' for n in
                 (address >> 16, lorom(address), pack['size'], int(pack['executable']),
                  address >> 8, (address+pack['size']-1) >> 8))+','+digest(pack['sha256'])+'},\n')
    return text+'};\n'


def identity(target):
    pair = settings(target)
    if pair is None:
        return None
    cfg, recipe = pair
    previous = json.loads((ROOT / 'config/native-content/sprite9e.json').read_text())
    cart = ROOT / 'local/upstream/snesrecomp/runner/src/snes/cart.c'
    verify(cart.read_bytes(), {'size': cart.stat().st_size,
           'sha256': previous['runtime_source_sha256']}, 'Seven cartridge source')
    patch = ROOT / previous['runtime_patch']
    if sha(patch.read_bytes()) != previous['runtime_patch_sha256']:
        raise ValueError('Seven cartridge patch differs')
    paths = [ROOT / 'config/restorations' / (target+'.json'),
             ROOT / cfg['native_seven']['manifest'], ROOT / 'config/native-content/sprite9e.json',
             ROOT / recipe['donor_manifest'], ROOT / 'tools/prepare_seven_module.py',
             ROOT / 'tools/audit_boss_dependencies.py', ROOT / 'tools/native_seven.py',
             ROOT / 'recomp/native_seven.c', ROOT / 'recomp/native_content.h', patch]
    if 'base_manifest' in recipe:
        paths.append(ROOT / recipe['base_manifest'])
    if 'graphics_pack' not in recipe:
        paths.append(ROOT / 'tools/prepare_mazo_module.py')
    kind = 'immutable-mazo-entry' if 'graphics_pack' not in recipe else 'immutable-seven-entry'
    return {'kind': kind,
            'files': {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in paths},
            'packs': packs(target), 'generated_header_sha256': sha(header(target).encode()),
            'runtime_source_sha256': previous['runtime_source_sha256'],
            'runtime_result_sha256': previous['runtime_result_sha256']}


def prepare(target=TARGET):
    cfg, recipe = settings(target)
    module_dir = ROOT / 'local/native-modules' / (target+'-final')
    if 'graphics_pack' in recipe:
        import prepare_seven_module
        prepare_seven_module.prepare(module_dir, ROOT / cfg['native_seven']['manifest'])
    else:
        import prepare_mazo_module
        prepare_mazo_module.prepare(module_dir, ROOT / cfg['native_seven']['manifest'])
    base_dir = ROOT / 'local/restoration' / cfg['base_restoration']
    base = (base_dir / 'rom.sfc').read_bytes()
    verify(base, cfg['base_output'], 'Seven recipient base')
    out = bytearray(base)
    for patch in recipe['unapplied_rom_patches']:
        offset, before, after = patch['offset'], bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if out[offset:offset+len(before)] != before or len(before) != len(after):
            raise ValueError('Seven recipient patch differs')
        out[offset:offset+len(after)] = after
    verify(out, cfg['output'], 'Seven native descendant')
    directory = ROOT / 'local/restoration' / target
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'rom.sfc', out)
    for pack in packs(target):
        source = module_dir if pack['variable'].startswith('BM_SEVEN_') else base_dir
        data = (source / pack['pack_file']).read_bytes()
        verify(data, pack, 'cumulative module pack')
        write_verified(directory / pack['pack_file'], data)
    receipt = {'config': cfg, 'content': identity(target),
               'module_receipt_sha256': sha((module_dir / 'preparation-receipt.json').read_bytes())}
    write_verified(directory / 'input-manifest.json', (json.dumps(receipt, indent=2)+'\n').encode())
    print(target, sha(out))
    return bytes(out)


def environment(target, env):
    for pack in packs(target):
        path = ROOT / 'local/restoration' / target / pack['pack_file']
        verify(path.read_bytes(), pack, pack['variable'])
        env[pack['variable']] = str(path)


def configure(experiment, binary, target):
    if settings(target) is None:
        return
    feature = identity(target)
    program = json.loads((experiment / 'src/gen/program_manifest.json').read_text())
    forbidden = (0x22, 0xa2, 0x25, 0xa5, 0x26, 0xa6, 0x36, 0xb6)
    if any(int(key.split(':')[0], 16) >> 16 in forbidden for key in program['nodes']):
        raise ValueError('Seven entry forbids AOT in independently mapped banks and aliases')
    directory = ROOT / 'local/native-content-runtime' / target
    cart = directory / 'runner/src/snes/cart.c'
    cart.parent.mkdir(parents=True, exist_ok=True)
    if not cart.exists():
        cart.write_bytes((ROOT / 'local/upstream/snesrecomp/runner/src/snes/cart.c').read_bytes())
    previous = json.loads((ROOT / 'config/native-content/sprite9e.json').read_text())
    if sha(cart.read_bytes()) == feature['runtime_source_sha256']:
        subprocess.run(['git', 'apply', '--directory='+str(directory.relative_to(ROOT)),
                       str(ROOT / previous['runtime_patch'])], cwd=ROOT, check=True)
    if sha(cart.read_bytes()) != feature['runtime_result_sha256']:
        raise ValueError('Seven runtime override differs')
    write_verified(directory / 'native_seven_manifest.h', header(target).encode())
    cmake = experiment / 'CMakeLists.txt'
    text = cmake.read_text()
    begin, end = '# BEGIN native seven entry', '# END native seven entry'
    block = '\n'.join([begin, f'get_target_property(_seven_sources {binary} SOURCES)',
        'list(REMOVE_ITEM _seven_sources "${SNESRECOMP_ROOT}/runner/src/snes/cart.c")',
        f'set_property(TARGET {binary} PROPERTY SOURCES ${{_seven_sources}})',
        f'target_sources({binary} PRIVATE "{cart}" "{ROOT / "recomp/native_seven.c"}")',
        f'target_include_directories({binary} PRIVATE "{directory}" "{ROOT / "recomp"}" "{ROOT / "local/upstream/snesrecomp/runner/src/snes"}")', end])
    if begin in text:
        text = text[:text.index(begin)]+block+text[text.index(end)+len(end):]
    else:
        text += '\n'+block+'\n'
    cmake.write_text(text)


if __name__ == '__main__':
    prepare()

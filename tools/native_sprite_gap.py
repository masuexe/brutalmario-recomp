#!/usr/bin/env python3
"""Build/configure isolated sprite-gap module targets.

The line keeps its own identity. A change to this file or the sprite gap
preparation tool does not relocate the Seven Koopalings or mazo targets.
"""
import json
from pathlib import Path
import subprocess

from prepare_rom import verify
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]


def manifests(cfg):
    """Return the gap recipes in review order for one target config."""
    spec = cfg["native_sprite_gap"]
    paths = spec.get("manifests") or [spec["manifest"]]
    recipes = [json.loads((ROOT / path).read_text()) for path in paths]
    for recipe in recipes:
        if not recipe["id"].startswith("sprite"):
            raise ValueError("sprite gap recipe id differs")
    if not recipes:
        raise ValueError("sprite gap target holds no recipe")
    banks = [int(recipe["code"]["native_address"], 16) >> 16 for recipe in recipes]
    if len(set(banks)) != len(banks):
        raise ValueError("sprite gap recipes share a code bank")
    return paths, recipes


def settings(target):
    path = ROOT / "config/restorations" / (target+".json")
    if not path.is_file():
        return None
    cfg = json.loads(path.read_text())
    if "native_sprite_gap" not in cfg:
        return None
    if cfg["schema"] != 1 or cfg["id"] != target:
        raise ValueError("sprite gap target identity differs")
    paths, recipes = manifests(cfg)
    return cfg, list(zip(paths, recipes))


def module_dirs(target):
    """Return one module directory per recipe in review order."""
    cfg, pairs = settings(target)
    recipes = [recipe for _, recipe in pairs]
    if len(recipes) == 1:
        return [ROOT / "local/native-modules" / (target+"-final")]
    return [ROOT / "local/native-modules" / (target+"-final-"+recipe["record"]["slot"])
            for recipe in recipes]


def packs(target):
    cfg, pairs = settings(target)
    recipes = [recipe for _, recipe in pairs]
    previous = json.loads((ROOT / "config/native-content/sprite9e.json").read_text())
    pins = []
    for index, recipe in enumerate(recipes):
        variable = "BM_SEVEN_CODE_PACK" if index == 0 else "BM_SEVEN_CODE_PACK_"+str(index+1)
        payload = recipe["code"].get("native_payload", {})
        pins.append((variable, dict(recipe["code"], **payload),
                     recipe["code"]["native_address"],
                     payload.get("sha256", recipe["code"]["adapted_sha256"]), True))
    pins.append(("BM_NATIVE_SPRITE_PACK", previous["code"], previous["code"]["native_address"],
                 previous["code"]["sha256"], True))
    pins.append(("BM_NATIVE_GRAPHICS_PACK", dict(previous["graphics"]["payload"],
                 pack_file=previous["graphics"]["pack_file"]), previous["graphics"]["native_address"],
                 previous["graphics"]["payload"]["sha256"], False))
    result = []
    for variable, item, address, digest, executable in pins:
        result.append(dict(variable=variable, pack_file=item["pack_file"], address=address,
                           size=item["size"], sha256=digest, executable=executable))
    return result

def header(target):
    cfg, _ = settings(target)
    data = packs(target)
    digest = lambda value: '{'+','.join(str(n) for n in bytes.fromhex(value))+'}';
    text = ('/* Generated immutable sprite gap descriptors. */\n#include <stdint.h>\n'
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
    cfg, pairs = pair
    recipes = [recipe for _, recipe in pairs]
    previous = json.loads((ROOT / 'config/native-content/sprite9e.json').read_text())
    cart = ROOT / 'local/upstream/snesrecomp/runner/src/snes/cart.c'
    verify(cart.read_bytes(), {
        'size': cart.stat().st_size, 'sha256': previous['runtime_source_sha256']},
        'sprite gap cartridge source')
    patch = ROOT / previous['runtime_patch']
    if sha(patch.read_bytes()) != previous['runtime_patch_sha256']:
        raise ValueError('sprite gap cartridge patch differs')
    paths = [ROOT / 'config/restorations' / (target+'.json'),
             ROOT / 'config/native-content/sprite9e.json',
             ROOT / 'tools/prepare_sprite_module.py', ROOT / 'tools/native_sprite_gap.py',
             ROOT / 'recomp/native_seven.c', ROOT / 'recomp/native_content.h', patch]
    for path, recipe in pairs:
        paths.append(ROOT / path)
        paths.append(ROOT / recipe['donor_manifest'])
    return {'kind': 'immutable-sprite-gap-entry',
            'files': {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in paths},
            'packs': packs(target),
            'generated_header_sha256': sha(header(target).encode()),
            'runtime_source_sha256': previous['runtime_source_sha256'],
            'runtime_result_sha256': previous['runtime_result_sha256']}


def prepare(target):
    cfg, pairs = settings(target)
    recipes = [recipe for _, recipe in pairs]
    directories = module_dirs(target)
    import prepare_sprite_module
    for directory, (path, _) in zip(directories, pairs):
        prepare_sprite_module.prepare(directory, ROOT / path)
    base_dir = ROOT / 'local/restoration' / cfg['base_restoration']
    base = (base_dir / 'rom.sfc').read_bytes()
    verify(base, cfg['base_output'], 'sprite gap recipient base')
    out = bytearray(base)
    for recipe in recipes:
        for patch in recipe['unapplied_rom_patches']:
            offset = patch['offset']
            before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
            if out[offset:offset+len(before)] != before or len(before) != len(after):
                raise ValueError('sprite gap recipient patch differs')
            out[offset:offset+len(after)] = after
    verify(out, cfg['output'], 'sprite gap native descendant')
    directory = ROOT / 'local/restoration' / target
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'rom.sfc', out)
    module_by_variable = {}
    for index, module in enumerate(directories):
        module_by_variable['BM_SEVEN_CODE_PACK' if index == 0
                           else 'BM_SEVEN_CODE_PACK_'+str(index+1)] = module
    for pack in packs(target):
        source = module_by_variable.get(pack['variable'], base_dir)
        data = (source / pack['pack_file']).read_bytes()
        verify(data, pack, 'sprite gap module pack')
        write_verified(directory / pack['pack_file'], data)
    receipts = {str(module.relative_to(ROOT)): sha((module / 'preparation-receipt.json').read_bytes())
                for module in directories}
    receipt = {'config': cfg, 'content': identity(target),
               'module_receipt_sha256': receipts}
    write_verified(directory / 'input-manifest.json',
                   (json.dumps(receipt, indent=2)+chr(10)).encode())
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
    forged = {int(pack['address'], 16) >> 16 for pack in feature['packs']}
    forbidden = set((0x22, 0xa2, 0x25, 0xa5, 0x26, 0xa6, 0x36, 0xb6, 0x23, 0xa3, 0x24, 0xa4)) | forged
    if any(int(key.split(':')[0], 16) >> 16 in forbidden for key in program['nodes']):
        raise ValueError('sprite gap entry forbids AOT in mapped banks and aliases')
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
        raise ValueError('sprite gap runtime override differs')
    write_verified(directory / 'native_seven_manifest.h', header(target).encode())
    cmake = experiment / 'CMakeLists.txt'
    text = cmake.read_text()
    begin, end = '# BEGIN native sprite gap entry', '# END native sprite gap entry'
    block = '\n'.join([begin,
        'get_target_property(_gap_sources '+binary+' SOURCES)',
        'list(REMOVE_ITEM _gap_sources "${SNESRECOMP_ROOT}/runner/src/snes/cart.c")',
        'set_property(TARGET '+binary+' PROPERTY SOURCES ${_gap_sources})',
        'target_sources('+binary+' PRIVATE "'+str(cart)+'" "'+str(ROOT / 'recomp/native_seven.c')+'")',
        'target_include_directories('+binary+' PRIVATE "'+str(directory)+'" "'+str(ROOT / 'recomp')+'" "'+str(ROOT / 'local/upstream/snesrecomp/runner/src/snes')+'")', end])
    if begin in text:
        text = text[:text.index(begin)]+block+text[text.index(end)+len(end):]
    else:
        text += '\n'+block+'\n'
    cmake.write_text(text)
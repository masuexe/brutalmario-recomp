#!/usr/bin/env python3
"""Prepare and configure the isolated native external-graphics pilot."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-pack-pilot'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def settings(target):
    path = ROOT / 'config/restorations' / (target + '.json')
    if not path.is_file():
        return None
    cfg = json.loads(path.read_text())
    if 'native_content' not in cfg:
        return None
    manifest = ROOT / cfg['native_content']['manifest']
    spec = json.loads(manifest.read_text())
    if cfg['schema'] != 1 or spec['schema'] != 1 or cfg['id'] != target:
        raise ValueError('native content schema or target differs')
    return cfg, spec


def identity(target):
    pair = settings(target)
    if pair is None:
        return None
    cfg, spec = pair
    patch = ROOT / spec['runtime_patch']
    source = ROOT / 'local/upstream/snesrecomp/runner/src/snes/cart.c'
    for path, expected in ((source, spec['runtime_source_sha256']),
                           (patch, spec['runtime_patch_sha256'])):
        if sha(path.read_bytes()) != expected:
            raise ValueError('native content runtime pin differs: ' + str(path))
    paths = [ROOT / 'config/restorations' / (target + '.json'),
             ROOT / cfg['native_content']['manifest'], patch,
             ROOT / spec['source_recipe'], ROOT / 'tools/native_content.py',
             ROOT / 'recomp/native_content.c', ROOT / 'recomp/native_content.h']
    return {'files': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths},
            'payload': spec['payload'], 'native_address': spec['native_address'],
            'runtime_source_sha256': spec['runtime_source_sha256'],
            'runtime_result_sha256': spec['runtime_result_sha256'],
            'generated_header_sha256': sha(header(target).encode())}


def prepare(target=TARGET):
    from prepare_rom import verify
    from restore_star_world_1 import graphics_pointer, lorom, lz2, write_verified
    cfg, spec = settings(target)
    identity(target)
    base = (ROOT / 'local/restoration' / cfg['base_restoration'] / 'rom.sfc').read_bytes()
    verify(base, cfg['base_output'], 'native content base')
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    pin = next(v for v in versions if v['id'] == cfg['donor'])
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    verify(donor, pin['output'], 'native content official donor')
    original, native = (int(spec[k], 16) for k in ('original_address', 'native_address'))
    if native != original | 0x800000 or original >> 16 >= 0x40:
        raise ValueError('pilot must split one upper LoROM mirror bank')
    gfx = int(spec['recipient_gfx_id'], 16)
    if graphics_pointer(base, gfx) != original:
        raise ValueError('resource pointer differs')
    decoded, payload = lz2(base, original)
    donor_decoded, donor_payload = lz2(donor, int(spec['source_address'], 16))
    verify(payload, spec['payload'], 'external payload')
    verify(decoded, spec['decoded'], 'decoded payload')
    if (payload, decoded) != (donor_payload, donor_decoded):
        raise ValueError('payload differs from official donor')
    start, slot = lorom(original), spec['pointer_offset']
    if (start + len(payload) - 1) // 0x8000 != start // 0x8000:
        raise ValueError('pilot payload crosses a bank')
    if base[slot:slot + 3] != original.to_bytes(3, 'little'):
        raise ValueError('resource pointer slot differs')
    out = bytearray(base)
    out[start:start + len(payload)] = bytes(len(payload))
    out[slot:slot + 3] = native.to_bytes(3, 'little')
    verify(out, cfg['output'], 'native content descendant')
    directory = ROOT / 'local/restoration' / target
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'rom.sfc', out)
    write_verified(directory / spec['pack_file'], payload)
    receipt = {'config': cfg, 'content': identity(target), 'donor': pin['output'],
               'base': cfg['base_output'], 'output': cfg['output']}
    (directory / 'input-manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'{target}: ROM {sha(out)}, external bytes {len(payload)}')
    return bytes(out)


def header(target):
    from restore_star_world_1 import lorom
    cfg, spec = settings(target)
    def digest(name, value):
        return 'static const uint8_t ' + name + '[32] = {' + ','.join(
            '0x' + value[i:i + 2] for i in range(0, 64, 2)) + '};\n'
    return ('/* Generated from pinned native content recipes. */\n'
            '#include <stdint.h>\n'
            f'#define BM_CONTENT_ID "{spec["id"]}"\n'
            f'#define BM_CONTENT_BANK 0x{int(spec["native_address"], 16) >> 16:02X}u\n'
            f'#define BM_CONTENT_OFFSET {lorom(int(spec["original_address"], 16))}u\n'
            f'#define BM_CONTENT_SIZE {spec["payload"]["size"]}u\n'
            f'#define BM_CONTENT_ROM_SIZE {cfg["output"]["size"]}u\n' +
            digest('bm_content_rom_sha', cfg['output']['sha256']) +
            digest('bm_content_payload_sha', spec['payload']['sha256']))


def configure(experiment, binary, target):
    from restore_star_world_1 import write_verified
    info = identity(target)
    if info is None:
        return
    cfg, spec = settings(target)
    directory = ROOT / 'local/native-content-runtime' / target
    directory.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'local/upstream/snesrecomp/runner/src/snes/cart.c'
    # Never touch shared runtime/upstream trees or discard an unknown override.
    temporary = directory / 'runner/src/snes/cart.c'
    temporary.parent.mkdir(parents=True, exist_ok=True)
    if not temporary.exists():
        temporary.write_bytes(source.read_bytes())
    actual = sha(temporary.read_bytes())
    if actual not in (spec['runtime_source_sha256'], spec['runtime_result_sha256']):
        raise ValueError('refusing to replace an unknown native runtime override')
    if actual == spec['runtime_source_sha256']:
        subprocess.run(['git', 'apply', '--directory=' + str(directory.relative_to(ROOT)),
                        str(ROOT / spec['runtime_patch'])], cwd=ROOT, check=True)
    if sha(temporary.read_bytes()) != spec['runtime_result_sha256']:
        raise ValueError('patched native runtime identity differs')
    write_verified(directory / 'native_content_manifest.h', header(target).encode())
    cmake = experiment / 'CMakeLists.txt'
    text = cmake.read_text()
    begin, end = '# BEGIN native content pilot', '# END native content pilot'
    block = '\n'.join([begin,
        f'get_target_property(_bm_sources {binary} SOURCES)',
        'list(REMOVE_ITEM _bm_sources "${SNESRECOMP_ROOT}/runner/src/snes/cart.c")',
        f'set_property(TARGET {binary} PROPERTY SOURCES ${{_bm_sources}})',
        f'target_sources({binary} PRIVATE "{temporary}" "{ROOT / "recomp/native_content.c"}")',
        f'target_include_directories({binary} PRIVATE "{directory}" "{ROOT / "recomp"}" "{ROOT / "local/upstream/snesrecomp/runner/src/snes"}")', end])
    if begin in text:
        first, last = text.index(begin), text.index(end) + len(end)
        text = text[:first] + block + text[last:]
    else:
        text += '\n' + block + '\n'
    cmake.write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default=TARGET)
    args = parser.parse_args()
    prepare(args.target)

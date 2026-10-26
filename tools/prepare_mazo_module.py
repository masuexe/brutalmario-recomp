#!/usr/bin/env python3
"""Prepare the reviewed mazo 9C module without changing a game target.

The tool verifies the pinned mazo donor, the 9C record, the protected program,
the reviewed dispatch tables and the 72 source-bank call patches. It writes an
unapplied code pack and a receipt. Graphics, the external-pack runtime mapping
and gameplay stay separate gates.
"""
import argparse
import json
from pathlib import Path
import sys

from audit_star_boss_donors import sprite_table
from prepare_rom import prepare_bytes, verify
from prepare_seven_module import analyze
from restore_star_world_1 import lorom, sha, sprite_rooms, write_verified

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'config/native-content/mazo-9c-module.json'
MANIFEST = ROOT / 'config/mazo-donor.json'


def read_recipe(path=RECIPE):
    return json.loads(Path(path).read_text())


def prepare_donor(manifest_path=MANIFEST):
    manifest = json.loads(Path(manifest_path).read_text())
    patch = manifest['authoritative_patch']
    rom = prepare_bytes((ROOT / patch['base_path']).read_bytes(),
                        (ROOT / patch['ips_path']).read_bytes(),
                        dict(patch, output=manifest['output']))
    verify(rom, manifest['output'], 'prepared mazo donor')
    return rom


def check_record(donor, recipe):
    record = recipe['record']
    constructor, body, table = sprite_table(donor)
    slot = int(record['slot'], 16)
    offset = lorom(table) + slot*16
    raw = donor[offset:offset+16]
    if raw.hex() != record['raw']:
        raise ValueError('9C record differs from the review')
    if f'{int.from_bytes(raw[8:11], "little"):06X}' != record['init']:
        raise ValueError('9C init address differs from the review')
    if f'{int.from_bytes(raw[11:14], "little"):06X}' != record['main']:
        raise ValueError('9C main address differs from the review')
    rooms = [f'{room:03X}' for room in sprite_rooms(donor, slot)]
    if rooms != record['rooms']:
        raise ValueError('9C room list differs from the review')
    return {'slot': record['slot'], 'raw': raw.hex(), 'init': record['init'],
            'main': record['main'], 'rooms': rooms,
            'constructor': f'{constructor:06X}', 'table': f'{table:06X}'}


def build_code(donor, base, recipe):
    code = recipe['code']
    first, native = int(code['source_address'], 16), int(code['native_address'], 16)
    if first != 0x228000 or native != 0xa28000 or code['size'] > 0x8000:
        raise ValueError('unreviewed executable mapping')
    payload = donor[lorom(first):lorom(first)+code['size']]
    verify(payload, code, 'source protected program')
    if (payload[:4] != b'STAR' or int.from_bytes(payload[4:6], 'little')+9 != len(payload)
            or int.from_bytes(payload[4:6], 'little') ^ int.from_bytes(payload[6:8], 'little') != 0xffff):
        raise ValueError('protected program bounds differ')
    audit = analyze(donor, recipe)
    adapted = bytearray(payload)
    changed = set()
    for patch in recipe['code_patches']:
        start = int(patch['address'], 16)-first
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if (len(before) != len(after) or start < 8 or start+len(before) > len(adapted)
                or adapted[start:start+len(before)] != before):
            raise ValueError('code adaptation bytes/bounds differ')
        if changed.intersection(range(start, start+len(before))):
            raise ValueError('overlapping code adaptations')
        changed.update(range(start, start+len(before)))
        adapted[start:start+len(before)] = after
    if sha(adapted) != code.get('adapted_sha256'):
        raise ValueError('adapted program hash differs from the review')
    for dependency in recipe.get('shared_dependencies', []):
        offset = lorom(int(dependency['address'], 16))
        for image in (donor, base):
            verify(image[offset:offset+dependency['size']], dependency, 'shared helper pin')
    return bytes(adapted), audit


def prepare(directory, recipe_path=RECIPE, manifest_path=MANIFEST):
    donor = prepare_donor(manifest_path)
    recipe = read_recipe(recipe_path)
    base = (ROOT / 'local/restoration' / recipe['base_restoration'] / 'rom.sfc').read_bytes()
    verify(base, recipe['base_output'], 'native base')
    record = check_record(donor, recipe)
    code, audit = build_code(donor, base, recipe)
    directory.mkdir(parents=True, exist_ok=True)
    paths = [Path(__file__), Path(recipe_path), ROOT / MANIFEST, ROOT / 'tools/prepare_seven_module.py',
             ROOT / 'tools/prepare_rom.py', ROOT / 'tools/restore_star_world_1.py',
             ROOT / 'tools/audit_star_boss_donors.py',
             ROOT / 'local/upstream/snesrecomp/recompiler/v2/decoder.py',
             ROOT / 'local/upstream/snesrecomp/recompiler/snes65816.py']
    receipt = {'scope': __doc__.strip(), 'recipe': recipe, 'audit': audit, 'record': record,
               'donor_manifest': str(Path(manifest_path).relative_to(ROOT)),
               'donor_sha256': sha(donor), 'base_sha256': sha(base),
               'adapted_code_sha256': sha(code),
               'input_files': {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in paths},
               'graphics': 'not prepared; the graphics review stays open'}
    for name, data in ((recipe['code']['pack_file'], code),
                       ('preparation-receipt.json',
                        (json.dumps(receipt, indent=2) + '\n').encode())):
        write_verified(directory / name, data)
    print(f'Prepared {len(code)} code bytes; no game ROM written')
    print('Receipt SHA-256:', sha((directory / 'preparation-receipt.json').read_bytes()))
    return code, receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'local/native-modules/mazo-9c-v1')
    parser.add_argument('--recipe', type=Path, default=RECIPE)
    args = parser.parse_args()
    prepare(args.output_dir, args.recipe)

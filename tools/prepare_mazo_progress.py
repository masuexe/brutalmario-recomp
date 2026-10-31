#!/usr/bin/env python3
"""Keep a donor corridor marker from clearing the recipient's unrelated course00D."""
import copy
import json
from pathlib import Path

from inspect_level_exits import stream
from native_sprite_gap import packs
from prepare_rom import verify
from qualify_forest_course_identity import sprite_list
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'demo11-native-mazo-primary-entry-v3'
TARGET = 'demo11-native-mazo-progress-v1'
RECIPE = ROOT / 'config/native-content/mazo-progress-v1.json'
VARIABLE = 'BM_SEVEN_CODE_PACK_MAZO_B0'


def course_identity(rom):
    body, pointer, size = stream(rom, 0x00d)
    sprites = sprite_list(rom, 0x00d)
    return dict(room='00D', pointer=f'{pointer:06X}', size=size, sha256=sha(body),
                sprites_sha256=sha(sprites))


def build(recipe=None):
    r = recipe if recipe is not None else json.loads(RECIPE.read_text())
    parent_path = ROOT / 'config/restorations' / (PARENT + '.json')
    if sha(parent_path.read_bytes()) != r['parent_config_sha256']:
        raise ValueError('parent configuration pin')
    cfg = json.loads(parent_path.read_text())
    if r['parent'] != PARENT or r['target'] != TARGET:
        raise ValueError('progress lineage')
    rom = (ROOT / 'local/restoration' / PARENT / 'rom.sfc').read_bytes()
    verify(rom, r['parent_output'], 'parent ROM')
    donor = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
    verify(donor, r['donor'], 'official Mazo ROM')
    if course_identity(donor) != r['source_course'] or course_identity(rom) != r['recipient_course']:
        raise ValueError('version-local course identity changed')
    if r['source_course']['sha256'] == r['recipient_course']['sha256']:
        raise ValueError('course mismatch was not established')
    selected = [p for p in packs(PARENT) if p['variable'] == VARIABLE]
    if len(selected) != 1 or selected[0]['address'] != 'A18989':
        raise ValueError('selected B0 module mapping differs')
    pack = selected[0]
    original = (ROOT / 'local/restoration' / PARENT / pack['pack_file']).read_bytes()
    verify(original, r['source_program'], 'installed official B0 program')
    source = donor[lorom(0x138989):lorom(0x138989) + len(original)]
    if original != source:
        raise ValueError('selected program no longer matches reviewed official source')
    if r['patch'] != dict(address='A189AE', offset=37, before='8daf1e', after='89ffea'):
        raise ValueError('progress patch extent')
    # LDA1EAF/ORA80 guarantees nonzero A in M=1. BIT#FF changes no flag;
    # BIT#FF+NOP replaces STA1EAF without changing addresses or CPU cycle count.
    if original[0x20:0x2d].hex() != 'adaf1e09808daf1ea9018d2614':
        raise ValueError('reviewed completion/message instruction window differs')
    result = bytearray(original)
    result[37:40] = bytes.fromhex(r['patch']['after'])
    verify(result, r['payload'], 'bounded progress adaptation')
    return r, cfg, rom, original, bytes(result)


def prepare():
    r, parent, rom, _, raw = build()
    source = 'local/native-modules/mazo-progress-v1'
    directory = ROOT / source
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'mazo-b0-code.bin', raw)
    cfg = copy.deepcopy(parent)
    cfg.update(id=TARGET, parent_restoration=PARENT, parent_output=parent['output'],
               scope='Preserve recipient00D completion; retain actual Mazo30 sphere-save path; experimental.')
    records = cfg['native_sprite_gap']['extra_packs']
    matches = [p for p in records if p['variable'] == VARIABLE]
    if len(matches) != 1:
        raise ValueError('ambiguous native B0 override')
    matches[0].update(source=source, sha256=sha(raw))
    cfg['native_adaptations'].append(dict(kind='version-scoped-mazo-progress',
        recipe=str(RECIPE.relative_to(ROOT)), recipe_sha256=sha(RECIPE.read_bytes()),
        note='Only A189AE STA1EAF is replaced. Unrelated recipient00D stays intact; actual sphere saves Mazo30.'))
    write_verified(ROOT / 'config/restorations' / (TARGET + '.json'),
                   (json.dumps(cfg, separators=(', ', ': ')) + '\n').encode())
    print(TARGET, sha(rom), 'B0', sha(raw))


if __name__ == '__main__':
    prepare()

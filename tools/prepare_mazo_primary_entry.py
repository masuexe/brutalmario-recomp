#!/usr/bin/env python3
"""Redirect the Mazo primary load without changing its map/save translevel."""
import argparse
import copy
import json
from pathlib import Path

from native_sprite_gap import packs
from prepare_mazo_messages import Code
from prepare_rom import verify
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'demo11-native-mazo-messages-v2'
TARGET = 'demo11-native-mazo-primary-entry-v3'
CONTROL = 'demo11-native-mazo-primary-control-v1'
RECIPE = ROOT / 'config/native-content/mazo-primary-entry-v3.json'


def legacy_program():
    c = Code()
    c.emit('c930')
    c.branch(0xd0, 'original')
    c.emit('0848')  # PHP/PHA8; checks below never modify hidden B or X/Y.
    for address, value in ((0x0dd6, 0), (0x1f11, 0), (0x1f17, 0),
                           (0x1f18, 1), (0x1f19, 0xf0), (0x1f1a, 0)):
        c.emit('ad' + address.to_bytes(2, 'little').hex() + 'c9' + f'{value:02x}')
        c.branch(0xd0, 'restore')
    c.emit('6828a9b4')  # Local load selector; original 13BF remains30.
    c.branch(0x80, 'original')
    c.label('restore')
    c.emit('6828')
    c.label('original')
    c.emit('c925')
    c.branch(0x90, 'low')
    c.emit('385ca7d805')  # Original SEC, then original SBC24.
    c.label('low')
    c.emit('5ca9d805')  # Original below25 branch.
    return c.finish()


def program_v2():
    c = Code()
    c.emit('850f0848')  # Original STA0F, then preserve A/P in M=1.
    for address, value in ((0x13bf, 0x30), (0x0dd6, 0), (0x1f11, 0), (0x1f17, 0),
                           (0x1f18, 1), (0x1f19, 0xf0), (0x1f1a, 0)):
        c.emit('ad' + address.to_bytes(2, 'little').hex() + 'c9' + f'{value:02x}')
        c.branch(0xd0, 'restore')
    c.emit('a9908dbb17850ea901850f')  # Local primary room0190 only.
    c.label('restore')
    c.emit('6828c2305cb9d805')  # Restore A/P; original REP30 and loader call.
    return c.finish()


def program():
    c = Code()
    c.emit('22a2ed130848')  # Call the existing helper, then save its A/P result.
    for address, value in ((0x13bf, 0x30), (0x0dd6, 0), (0x1f11, 0), (0x1f17, 0),
                           (0x1f18, 1), (0x1f19, 0xf0), (0x1f1a, 0)):
        c.emit('ad' + address.to_bytes(2, 'little').hex() + 'c9' + f'{value:02x}')
        c.branch(0xd0, 'restore')
    c.emit('a9908dbb17850e6828a9016b')  # Local0190; caller retains original STA0F.
    c.label('restore')
    c.emit('68286b')
    return c.finish()


def build(recipe=None):
    r = recipe if recipe is not None else json.loads(RECIPE.read_text())
    parent_path = ROOT / 'config/restorations' / (PARENT + '.json')
    if sha(parent_path.read_bytes()) != r['parent_config_sha256']:
        raise ValueError('parent configuration pin')
    parent = json.loads(parent_path.read_text())
    rom = (ROOT / 'local/restoration' / PARENT / 'rom.sfc').read_bytes()
    verify(rom, r['parent_output'], 'parent ROM')
    legacy = r['target'] == 'demo11-native-mazo-primary-entry-v1'
    v2 = r['target'] == 'demo11-native-mazo-primary-entry-v2'
    if r['target'] not in (TARGET, 'demo11-native-mazo-primary-entry-v1', 'demo11-native-mazo-primary-entry-v2') or r['parent'] != PARENT:
        raise ValueError('primary entry lineage')
    if r['scope'] != dict(map=0, player=0, x=256, y=240, translevel=48, room=400):
        raise ValueError('primary entry scope')
    if r['address'] != '888000' or any(int(p['address'], 16) >> 16 == 0x88 for p in packs(PARENT)):
        raise ValueError('native execution bank collision or mapping differs')
    raw = legacy_program() if legacy else program_v2() if v2 else program()
    verify(raw, r['payload'], 'primary adapter')
    patch = (dict(address='05D8A2', before='c925900338', after='5c008088ea') if legacy else
             dict(address='05D8B5', before='850fc230', after='5c008088') if v2 else
             dict(address='05D8B1', before='22a2ed13', after='22008088'))
    if r['patch'] != patch:
        raise ValueError('primary hook extent')
    # Pin the complete selector/load window, not just five overwritten bytes.
    window = rom[lorom(0x05d89b):lorom(0x05d8c0)]
    verify(window, r['selector_window'], 'recipient primary selector')
    out = bytearray(rom)
    at = lorom(int(patch['address'], 16))
    size = len(bytes.fromhex(patch['before']))
    if out[at:at+size].hex() != patch['before']:
        raise ValueError('primary hook preimage')
    out[at:at+size] = bytes.fromhex(patch['after'])
    return r, parent, bytes(out), raw


def prepare(control=False):
    r, parent, rom, raw = build()
    if control:
        cfg = copy.deepcopy(parent)
        cfg.update(id=CONTROL, parent_restoration=PARENT, parent_output=parent['output'],
                   scope='Frozen message-parent content rebuilt as an isolated current-runtime control; no primary-entry hook.')
        write_verified(ROOT / 'config/restorations' / (CONTROL + '.json'),
                       (json.dumps(cfg, separators=(', ', ': ')) + '\n').encode())
        print(CONTROL, parent['output']['sha256'])
        return
    target = r['target']
    source = 'local/native-modules/mazo-primary-entry-' + target.rsplit('-', 1)[1]
    directory = ROOT / source
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'primary-entry.bin', raw)
    cfg = copy.deepcopy(parent)
    cfg.update(id=target, parent_restoration=PARENT, parent_output=parent['output'],
               scope='Mazo map30 retains save identity and loads190 through a scoped primary selector; experimental.')
    cfg['output']['sha256'] = sha(rom)
    cfg['native_sprite_gap']['extra_packs'].append(dict(
        variable='BM_MAZO_PRIMARY_ENTRY_PACK', pack_file='primary-entry.bin',
        address=r['address'], size=len(raw), sha256=sha(raw), executable=True, source=source))
    p = r['patch']
    cfg['native_sprite_gap']['extra_patches'].append(dict(
        offset=lorom(int(p['address'], 16)), before=p['before'], after=p['after'],
        role='Redirect only Mazo primary load; retain original node and 13BF30'))
    cfg['native_adaptations'].append(dict(kind='mazo-primary-entry',
        recipe=str(RECIPE.relative_to(ROOT)), recipe_sha256=sha(RECIPE.read_bytes()),
        note='Scoped primary selector; generated capability suppresses legacy B4 node-table hook.'))
    write_verified(ROOT / 'config/restorations' / (target + '.json'),
                   (json.dumps(cfg, separators=(', ', ': ')) + '\n').encode())
    print(target, sha(rom), len(raw))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', action='store_true')
    prepare(parser.parse_args().control)

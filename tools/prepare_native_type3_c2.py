#!/usr/bin/env python3
"""Review and prepare the bounded official C2 shooter descendant."""
import json
from pathlib import Path

from audit_star_boss_donors import sprite_table
from native_sprite_gap import packs, prepare
from prepare_rom import verify
from qualify_world1_next_course import require
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-type3-c2-v2'
ADAPTER = ROOT / 'config/native-content/type3-shooters-c2-v2.json'
BLOCK = ROOT / 'config/native-content/type3-c2-boss-lowmirror.json'


def load(path):
    return json.loads(path.read_text())


def review(adapter=None, block=None):
    adapter = adapter if adapter is not None else load(ADAPTER)
    block = block if block is not None else load(BLOCK)
    cfg = load(ROOT / 'config/restorations' / (TARGET+'.json'))
    parent = (ROOT / 'local/restoration' / cfg['parent_restoration'] / 'rom.sfc').read_bytes()
    verify(parent, cfg['parent_output'], 'C0/C1 parent')
    require(cfg['parent_restoration'] == 'demo11-native-type3-shooters-v1', 'unexpected parent')
    original = load(ROOT / 'config/native-content/type3-shooters-v1.json')
    old = bytes.fromhex(original['code']['raw_payload'])
    require(old.count(bytes.fromhex('c9c2')) == 2 and old.count(bytes.fromhex('c932')) == 1,
            'parent threshold occurrences differ')
    expected = old.replace(bytes.fromhex('c9c2'), bytes.fromhex('c9c3')).replace(
        bytes.fromhex('c932'), bytes.fromhex('c933'))
    raw = bytes.fromhex(adapter['code']['raw_payload'])
    require(raw == expected, 'changes beyond three C2 admission thresholds')
    verify(raw, adapter['code'], 'extended adapter')
    for field in ('native_address', 'size', 'pack_file'):
        require(adapter['code'][field] == original['code'][field], 'adapter allocation changed')
    require([(p['offset'], p['before'], p['after']) for p in adapter['unapplied_rom_patches']] ==
            [(p['offset'], p['before'], p['after']) for p in original['unapplied_rom_patches']],
            'loader/store/dispatch hook changed')
    source_record = bytes.fromhex('03ffffffffffffff30dd1534dd15ffff')
    payload = bytes.fromhex(block['code']['raw_payload'])
    sources = {}
    for version in ('boss', '7hero'):
        manifest = load(ROOT / 'config' / (version+'-donor.json'))
        donor = (ROOT / 'local/content-versions' / version / 'rom.sfc').read_bytes()
        verify(donor, manifest['output'], 'official '+version)
        table = sprite_table(donor)[2]
        offset = lorom(table)+0xC2*16
        require(donor[offset:offset+16] == source_record, 'official C2 record differs')
        start = lorom(0x15DD21)
        require(donor[start:start+295] == payload and payload[:4] == b'STAR' and
                int.from_bytes(payload[4:6], 'little')+9 == len(payload) and
                int.from_bytes(payload[4:6], 'little') ^ int.from_bytes(payload[6:8], 'little') == 0xFFFF,
                'official protected C2 program differs')
        sources[version] = dict(rom_sha256=sha(donor), record=source_record.hex(), block_sha256=sha(payload))
    verify(payload, block['code'], 'unmodified C2 module')
    require(block['code']['native_address'] == '91DD21' and len(payload) == 295,
            'C2 low-mirror allocation differs')
    table = sprite_table(parent)[2]
    after = bytearray(source_record)
    after[10] = after[13] = 0x91
    require(block['unapplied_rom_patches'] == [dict(
        offset=lorom(table)+0xC2*16, before='0000ffffffffffff218001218001ffff',
        after=after.hex(), role='Install official C2 shooter record with low-mirror bank91 pointers')],
        'C2 record patch differs')
    patch = block['unapplied_rom_patches'][0]
    out = bytearray(parent)
    require(out[patch['offset']:patch['offset']+16].hex() == patch['before'], 'C2 parent preimage differs')
    out[patch['offset']:patch['offset']+16] = after
    verify(out, cfg['output'], 'C2 record-only ROM descendant')
    old_packs = packs(cfg['parent_restoration'])
    new_packs = packs(TARGET)
    adapted = []
    for pack in new_packs:
        if pack['pack_file'] == 'type3-c2.bin':
            require(pack['address'] == '91DD21' and pack['sha256'] == sha(payload) and pack['executable'],
                    'C2 descriptor differs')
            continue
        pack = dict(pack)
        if pack['pack_file'] == 'type3-shooters.bin':
            require(pack['sha256'] == sha(raw), 'adapter descriptor differs')
            pack['sha256'] = sha(old)
        adapted.append(pack)
    require(len(new_packs) == 50 and adapted == old_packs, 'unrelated pack changes')
    return dict(target=TARGET, rom_sha256=sha(out), sources=sources,
                adapter_changed_offsets=[i for i, (a, b) in enumerate(zip(old, raw)) if a != b],
                scope='One source C2 record and byte-identical program; three adapter threshold bytes only.')


def main():
    result = review()
    prepare(TARGET)
    paths = [Path(__file__), ADAPTER, BLOCK, ROOT / 'config/restorations' / (TARGET+'.json'),
             ROOT / 'config/boss-donor.json', ROOT / 'config/7hero-donor.json']
    result['files'] = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}
    destination = ROOT / 'local/restoration' / TARGET / 'type3-c2-review.json'
    write_verified(destination, (json.dumps(result, indent=2)+'\n').encode())
    print(destination, sha(destination.read_bytes()))


if __name__ == '__main__':
    main()

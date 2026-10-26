#!/usr/bin/env python3
"""Prepare the bounded Seven defeat music-stop descendant.

Keep the accepted child builder unchanged so its capture identities remain
reproducible. This builder inherits verified packs and changes one immediate.
"""
import json
from pathlib import Path

import native_seven_child as child
from prepare_rom import verify
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-seven-ending-stop'
PARENT = 'demo11-native-seven-child-fight-music'


def adapt(rom, master, donor, recipe):
    verify(rom, recipe['parent_output'], 'ending parent ROM')
    patch = recipe['ending_stop']
    verify(master, patch['parent_master'], 'ending parent master')
    if (patch['source_address'], patch['native_address'], patch['before'], patch['after']) != (
            '228383', 'A28383', 'a9ff8dfb1d', 'a9808dfb1d'):
        raise ValueError('unreviewed ending stop adaptation')
    before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
    if donor[lorom(0x228383):lorom(0x228383)+5] != before or master[0x383:0x388] != before:
        raise ValueError('source/parent defeat music write differs')
    handler = patch['modern_stop_handler']
    if handler['address'] != '0FC0D0' or handler['size'] != 30:
        raise ValueError('modern stop handler extent differs')
    offset = lorom(0x0fc0d0)
    verify(rom[offset:offset+handler['size']], handler, 'modern stop handler')
    result = bytearray(master)
    result[0x383:0x388] = after
    verify(result, recipe['master_payload'], 'ending master output')
    return bytes(result)


def prepare():
    cfg, recipe = child.settings(TARGET)
    if cfg['base_restoration'] != PARENT or recipe['parent_target'] != PARENT:
        raise ValueError('ending parent differs')
    source = ROOT / 'local/restoration' / PARENT
    receipt_path = source / 'input-manifest.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt['content'] != child.identity(PARENT):
        raise ValueError('ending parent receipt differs')
    for pack in child.packs(PARENT):
        verify((source / pack['pack_file']).read_bytes(), pack, 'ending inherited pack')
    donor_cfg = json.loads((ROOT / 'config/boss-donor.json').read_text())
    donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
    verify(donor, donor_cfg['output'], 'official Boss ending source')
    rom = (source / 'rom.sfc').read_bytes()
    master = adapt(rom, (source / 'seven-code.bin').read_bytes(), donor, recipe)
    verify(rom, cfg['output'], 'unchanged ending descendant ROM')
    directory = ROOT / 'local/restoration' / TARGET
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'rom.sfc', rom)
    for pack in child.packs(TARGET):
        data = master if pack['variable'] == 'BM_SEVEN_CODE_PACK' else (source / pack['pack_file']).read_bytes()
        verify(data, pack, 'ending descendant pack')
        write_verified(directory / pack['pack_file'], data)
    output = {'config': cfg, 'content': child.identity(TARGET),
              'builder_sha256': sha(Path(__file__).read_bytes()),
              'parent_receipt_sha256': sha(receipt_path.read_bytes()),
              'donor_sha256': sha(donor), 'adaptation': recipe['ending_stop'],
              'scope': 'One master-pack immediate changed; ROM and four other packs unchanged. '
                       'No earned defeat or saved-clear claim.'}
    write_verified(directory / 'input-manifest.json', (json.dumps(output, indent=2)+'\n').encode())
    print(TARGET, sha(rom), sha(master))


if __name__ == '__main__':
    prepare()

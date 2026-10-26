#!/usr/bin/env python3
"""Restore the official hidden green mushroom checkpoints only in room 17B."""
import json
from pathlib import Path

import native_seven_child as child
from prepare_rom import verify
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-seven-ending-1up'
PARENT = 'demo11-native-seven-ending-tiles'
SHIM = '0848ad0b01c97bd016ad0c01c901d00f6828cd2114d0045ca8f2005c99f20068285cbff200'


def adapt(rom, master, donor, recipe):
    verify(rom,recipe['parent_output'],'hidden mushroom parent ROM')
    route = recipe['ending_1up']
    verify(master,route['parent_master'],'hidden mushroom parent master')
    if (route['room'],route['source_address'],route['source_before'],route['recipient_before'],
            route['after'],route['shim_address'],route['shim']) != (
            '017B','00F294','cd2114f00f','602114f00f','5c00f1a2ea','A2F100',SHIM):
        raise ValueError('unreviewed hidden mushroom adaptation')
    for key,address,size in (('handler',0x00f28c,52),('spawn_helper',0x03c2d9,54)):
        pin = route[key]
        if (int(pin['address'],16),pin['size']) != (address,size):
            raise ValueError('hidden mushroom dependency extent differs')
        offset = lorom(address)
        source = donor[offset:offset+size]
        verify(source,pin,'official hidden mushroom '+key)
        expected = bytearray(source)
        if key == 'handler':
            expected[0xf294-0xf28c] = 0x60
        if rom[offset:offset+size] != expected:
            raise ValueError('recipient hidden mushroom dependency differs')
    offset = lorom(0x00f294)
    if donor[offset:offset+5] != bytes.fromhex(route['source_before']):
        raise ValueError('official checkpoint comparison differs')
    out = bytearray(rom)
    out[offset:offset+5] = bytes.fromhex(route['after'])
    if len(master) != 0x70d0:
        raise ValueError('hidden mushroom adapter allocation differs')
    payload = master+bytes(0x30)+bytes.fromhex(SHIM)
    verify(payload,recipe['master_payload'],'hidden mushroom master extension')
    return bytes(out),payload


def prepare():
    cfg,recipe = child.settings(TARGET)
    if cfg['base_restoration'] != PARENT or recipe['parent_target'] != PARENT:
        raise ValueError('hidden mushroom parent differs')
    source = ROOT/'local/restoration'/PARENT
    receipt_path = source/'input-manifest.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt['content'] != child.identity(PARENT):
        raise ValueError('hidden mushroom parent receipt differs')
    for pack in child.packs(PARENT):
        verify((source/pack['pack_file']).read_bytes(),pack,'inherited pack')
    donor = (ROOT/'local/content-versions/boss/rom.sfc').read_bytes()
    verify(donor,json.loads((ROOT/'config/boss-donor.json').read_text())['output'],'official Boss source')
    rom,master = adapt((source/'rom.sfc').read_bytes(),(source/'seven-code.bin').read_bytes(),donor,recipe)
    verify(rom,cfg['output'],'hidden mushroom descendant ROM')
    directory = ROOT/'local/restoration'/TARGET
    directory.mkdir(parents=True,exist_ok=True)
    write_verified(directory/'rom.sfc',rom)
    for pack in child.packs(TARGET):
        data = master if pack['variable'] == 'BM_SEVEN_CODE_PACK' else (source/pack['pack_file']).read_bytes()
        verify(data,pack,'hidden mushroom descendant pack')
        write_verified(directory/pack['pack_file'],data)
    output = {'config':cfg,'content':child.identity(TARGET),'builder_sha256':sha(Path(__file__).read_bytes()),
              'parent_receipt_sha256':sha(receipt_path.read_bytes()),'donor_sha256':sha(donor),
              'adaptation':recipe['ending_1up'],
              'scope':'Restore ordered checkpoint processing in room 17B; spawn an actual sprite 78, not a direct life increment.'}
    write_verified(directory/'input-manifest.json',(json.dumps(output,indent=2)+'\n').encode())
    print(TARGET,sha(rom),sha(master))


if __name__ == '__main__':
    prepare()

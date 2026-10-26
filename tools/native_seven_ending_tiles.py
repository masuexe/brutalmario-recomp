#!/usr/bin/env python3
"""Prepare a room-local FG2 clone for the official blank T-room pole tiles."""
import json
from pathlib import Path

import native_seven_child as child
from prepare_rom import verify
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-seven-ending-tiles'
PARENT = 'demo11-native-seven-ending-test'


def adapt(rom, graphics, donor, recipe):
    verify(rom, recipe['parent_output'], 'ending graphics parent ROM')
    route = recipe['ending_graphics']
    verify(graphics, route['parent_graphics'], 'ending graphics parent pack')
    tiles = [0xa4,0xa5,0xa6,0xa7,0xb4,0xb5,0xb6,0xb7]
    if (route['source_id'], route['source_address'], route['namespace_id'], route['room'],
            route['native_address'], route['blank_8x8_tiles']) != (
            '0017','0A97B6','FFC','017B','A6EA7D',[f'{t:04X}' for t in tiles]):
        raise ValueError('unreviewed room-local graphics adaptation')
    # Official Boss Map16 definitions intentionally make both pole blocks blank.
    if donor[lorom(0x0d8378):lorom(0x0d8388)] != bytes.fromhex('f810'*8):
        raise ValueError('official Boss blank tile definitions differ')
    if graphics_pointer(rom,0x17) != 0x0a97b6:
        raise ValueError('recipient FG2 source pointer differs')
    decoded, encoded = lz2(rom,0x0a97b6,limit=4096)
    verify(decoded,route['source_decoded'],'recipient FG2 source')
    verify(encoded,route['source_encoded'],'recipient encoded FG2 source')
    result = bytearray(decoded)
    for tile in tiles:
        offset = (tile-0x80)*32
        result[offset:offset+32] = bytes(32)
    verify(result,route['decoded'],'room-local FG2 tiles')
    stream = b''.join(bytes.fromhex('e3ff')+result[i:i+1024] for i in range(0,4096,1024))+b'\xff'
    verify(stream,route['encoded'],'bounded literal LC_LZ2 stream')
    if len(graphics) != 0x6a7d or len(graphics)+len(stream)>0x8000:
        raise ValueError('graphics allocation exceeds immutable A6 bank')
    # FFC is unassigned in every current room record and its pointer is empty.
    records = lorom(0x14ad08)
    if any(int.from_bytes(rom[records+i:records+i+2],'little') & 0xfff == 0xffc
           for i in range(0,512*32,2)):
        raise ValueError('graphics namespace FFC is already selected')
    if graphics_pointer(rom,0xffc) != 0xffffff:
        raise ValueError('graphics namespace FFC is already assigned')
    if [(p['address'],p['before'],p['after']) for p in route['rom_patches']] != [
            ('14DC68','0100ffffffffffffffffffffffffffffffff','018015001900fc0f14000200130001000000'),
            ('14ACFC','ffffff','7deaa6')]:
        raise ValueError('unreviewed ending graphics ROM patches')
    out = bytearray(rom)
    for patch in route['rom_patches']:
        offset = lorom(int(patch['address'],16))
        before,after = bytes.fromhex(patch['before']),bytes.fromhex(patch['after'])
        if out[offset:offset+len(before)] != before:
            raise ValueError('ending graphics patch site differs')
        out[offset:offset+len(before)] = after
    # No generic helper or Map16 ID/definition is edited.
    payload = graphics+stream
    verify(payload,recipe['font_lifecycle']['graphics_payload'],'ending graphics pack')
    return bytes(out),payload


def prepare():
    cfg,recipe = child.settings(TARGET)
    if cfg['base_restoration'] != PARENT or recipe['parent_target'] != PARENT:
        raise ValueError('ending graphics parent differs')
    source = ROOT/'local/restoration'/PARENT
    receipt_path = source/'input-manifest.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt['content'] != child.identity(PARENT):
        raise ValueError('ending graphics parent receipt differs')
    for pack in child.packs(PARENT):
        verify((source/pack['pack_file']).read_bytes(),pack,'inherited pack')
    donor = (ROOT/'local/content-versions/boss/rom.sfc').read_bytes()
    verify(donor,json.loads((ROOT/'config/boss-donor.json').read_text())['output'],'official Boss source')
    rom,graphics = adapt((source/'rom.sfc').read_bytes(),(source/'seven-graphics.bin').read_bytes(),donor,recipe)
    verify(rom,cfg['output'],'ending graphics descendant ROM')
    directory = ROOT/'local/restoration'/TARGET
    directory.mkdir(parents=True,exist_ok=True)
    write_verified(directory/'rom.sfc',rom)
    for pack in child.packs(TARGET):
        data = graphics if pack['variable'] == 'BM_SEVEN_GRAPHICS_PACK' else (source/pack['pack_file']).read_bytes()
        verify(data,pack,'ending graphics descendant pack')
        write_verified(directory/pack['pack_file'],data)
    output = {'config':cfg,'content':child.identity(TARGET),'builder_sha256':sha(Path(__file__).read_bytes()),
              'parent_receipt_sha256':sha(receipt_path.read_bytes()),'donor_sha256':sha(donor),
              'adaptation':recipe['ending_graphics'],
              'scope':'Only room 17B selects the adapted FG2 resource; no generic helper edits.'}
    write_verified(directory/'input-manifest.json',(json.dumps(output,indent=2)+'\n').encode())
    print(TARGET,sha(rom),sha(graphics))


if __name__ == '__main__':
    prepare()

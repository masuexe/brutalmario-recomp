#!/usr/bin/env python3
"""Room-local transparent patterns for mazo room 191; preserve actor logic."""
import argparse
import json
from pathlib import Path
from restore_star_world_1 import graphics_pointer, lz2, pointer_offset, sha
ROOT = Path(__file__).resolve().parents[1]

def prepare(restore_orb=False):
    base = ROOT/'config/restorations/demo11-native-product-r3.json'
    cfg=json.loads(base.read_text())
    rom=bytearray((ROOT/'local/restoration/demo11-native-product-r3/rom.sfc').read_bytes())
    assert sha(rom)==cfg['output']['sha256']=='3c36c27984e9660b2454c0ddf94a4a9b2881a0c78f5637462ef470cdb3b4f76d'
    pack=bytearray()
    patches=[]
    graphics = [(0x17,0xff9,[*range(0x24,0x28),*range(0x34,0x38)])]
    if not restore_orb:
        graphics.append((5,0xffa,[0xc,0xd,0x1c,0x1d]))
    for gfx, private, tiles in graphics:
        data,_=lz2(rom,graphics_pointer(rom,gfx));data=bytearray(data)
        assert len(data)==4096
        for tile in tiles:data[tile*32:(tile+1)*32]=bytes(32)
        stream=b''.join(b'\xe3\xff'+data[i:i+1024] for i in range(0,4096,1024))+b'\xff'
        address=0xd08000+len(pack);pack+=stream
        off=pointer_offset(private);assert rom[off:off+3]==b'\xff'*3
        patches.append(dict(offset=off,before='ffffff',after=address.to_bytes(3,'little').hex(),role=f'Private room191 transparent graphics {private:03X}'))
    off=679720
    record=bytes.fromhex('0180')+b''.join(x.to_bytes(2,'little') for x in [0x15,0x19,0xff9,0x14,(5 if restore_orb else 0xffa),0x13,1,0])+b'\xff'*14
    assert len(record)==32
    # Replace the existing reviewed room graphics record rather than overlap patches.
    found = False
    for p in cfg['native_sprite_gap']['extra_patches']:
        if p['offset']==off:
            found = True
            assert p['after']=='0100'+'ffff'*15
            p['after']=record.hex();p['role']='Room191 private foreground graphics; preserve orb' if restore_orb else 'Room191 private transparent foreground and control-marker graphics'
    assert found
    rom[off:off+32]=record
    for p in patches:rom[p['offset']:p['offset']+3]=bytes.fromhex(p['after'])
    cfg['native_sprite_gap']['extra_patches']+=patches
    source='local/native-modules/corridor-orb-v2' if restore_orb else 'local/native-modules/corridor-invisible-v1'
    directory=ROOT/source;directory.mkdir(parents=True,exist_ok=True)
    (directory/'corridor-invisible.bin').write_bytes(pack)
    cfg['native_sprite_gap']['extra_packs'].append(dict(variable='BM_CORRIDOR_INVISIBLE_PACK',pack_file='corridor-invisible.bin',address='D08000',size=len(pack),sha256=sha(pack),executable=False,source=source))
    cfg['id']='demo11-native-product-r6' if restore_orb else 'demo11-native-product-r5';cfg['output']['sha256']=sha(rom)
    (ROOT/('config/restorations/'+cfg['id']+'.json')).write_text(json.dumps(cfg,separators=(', ',': '))+'\n')
    print(cfg['output'],sha(pack))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore-orb', action='store_true', help='prepare r6 with unchanged SP4 instead of the r5 orb suppression')
    prepare(parser.parse_args().restore_orb)

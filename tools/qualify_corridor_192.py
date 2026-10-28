"""Check room192 foreground adaptation and unchanged accepted rooms."""
import json
from pathlib import Path
from restore_star_world_1 import sha,lz2,graphics_pointer
ROOT=Path(__file__).resolve().parents[1]
def qualify():
 r=(ROOT/'local/restoration/demo11-native-product-r7/rom.sfc').read_bytes()
 base=(ROOT/'local/restoration/demo11-native-product-r6/rom.sfc').read_bytes()
 expected=bytearray(base);expected[679752:679784]=base[679720:679752]
 assert r==expected
 cfg=json.loads((ROOT/'config/restorations/demo11-native-product-r7.json').read_text());assert sha(r)==cfg['output']['sha256']
 captures=ROOT/'local/captures'
 for tag in ('w1','w2','w3','w4','w5'):
  n=captures/'corridor-r7-192';i=captures/'corridor-r7-192-interp'
  ram=(n/(tag+'.wram.bin')).read_bytes();assert ram[0x100]==0x14 and ram[0x10b:0x10d]==bytes.fromhex('9201')
  for suffix in ('vram.bin','fb.bgrx','oam.bin','cgram.bin'):
   assert (n/(tag+'.'+suffix)).read_bytes()==(i/(tag+'.'+suffix)).read_bytes(),(tag,suffix)
  old=(captures/'corridor-r6-192'/(tag+'.wram.bin')).read_bytes()
  for lo,hi in [(0x14c8,0x14e0),(0xe4,0xf0),(0xd8,0xe4),(0x1ab9e,0x1abaa)]:assert ram[lo:hi]==old[lo:hi]
  v=(n/(tag+'.vram.bin')).read_bytes()
  for tile in (0xa4,0xa5,0xa6,0xa7,0xb4,0xb5,0xb6,0xb7):assert not any(v[tile*32:(tile+1)*32])
  original,_=lz2(r,graphics_pointer(r,5));assert v[0xf000:]==original
 for room,tags,baseline in [('191',['w1','w2','w3','w4','w5'],'invisible-r6-191'),('190',['q1'],'invisible-r6-190')]:
  for tag in tags:
   for suffix in ('wram.bin','vram.bin','fb.bgrx','oam.bin','cgram.bin'):
    assert (captures/f'corridor-r7-{room}'/(tag+'.'+suffix)).read_bytes()==(captures/baseline/(tag+'.'+suffix)).read_bytes(),(room,tag,suffix)
 identities={}
 for name in ['corridor-r7-192','corridor-r7-192-interp','corridor-r7-191','corridor-r7-190','corridor-r6-192']:
  identities[name]=json.loads((captures/name/'receipt.json').read_text())
 return dict(rom_sha256=sha(r),identities=identities,room192_samples=5,unchanged_files=30,scope='Assisted pipe entry/movement; graphics qualification only.')
if __name__=='__main__':
 result=qualify();p=ROOT/'local/reports/corridor-192-r7.json';p.write_text(json.dumps(result,indent=2)+'\n');print(p)

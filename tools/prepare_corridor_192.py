"""Extend the accepted room191 foreground adaptation to room192 only."""
import json
from pathlib import Path
from restore_star_world_1 import sha
ROOT=Path(__file__).resolve().parents[1]
def prepare():
 c=json.loads((ROOT/'config/restorations/demo11-native-product-r6.json').read_text())
 r=bytearray((ROOT/'local/restoration/demo11-native-product-r6/rom.sfc').read_bytes())
 assert sha(r)==c['output']['sha256']=='5ff22880ebd044930867b4e5eb2b637cf74c2cd57abb7c4ba348eb56c56926b7'
 patches=c['native_sprite_gap']['extra_patches']
 record=next(p['after'] for p in patches if p['offset']==679720)
 p=next(p for p in patches if p['offset']==679752)
 assert p['after']=='0100'+'ffff'*15
 p['after']=record;p['role']='Room192 private foreground graphics; preserve original sprites'
 r[679752:679784]=bytes.fromhex(record)
 c['id']='demo11-native-product-r7';c['output']['sha256']=sha(r)
 (ROOT/'config/restorations/demo11-native-product-r7.json').write_text(json.dumps(c,separators=(', ',': '))+'\n')
 print(sha(r))
if __name__=='__main__':prepare()

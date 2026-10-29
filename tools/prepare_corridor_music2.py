#!/usr/bin/env python3
"""Build demo11-native-product-r10: room 190 music override (native, slot 0x9E)."""
import json
from pathlib import Path
from restore_star_world_1 import sha
ROOT = Path(__file__).resolve().parents[1]
R9_SHA = 'd29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552'
def prepare():
    cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r9.json').read_text())
    rom = (ROOT / 'local/restoration/demo11-native-product-r9/rom.sfc').read_bytes()
    assert sha(rom) == cfg['output']['sha256'] == R9_SHA
    cfg['id'] = 'demo11-native-product-r10'
    cfg['output']['sha256'] = sha(rom)
    cfg.setdefault('native_adaptations', []).append(dict(
        kind='room-music-override', room='0x190', music_slot='0x9E',
        source='recomp/native_seven.c', note='Room 0x190 has no music object; force slot 0x9E.'))
    (ROOT / 'config/restorations/demo11-native-product-r10.json').write_text(json.dumps(cfg,separators=(', ',': '))+'\n')
    print('rom', sha(rom))
if __name__=='__main__': prepare()

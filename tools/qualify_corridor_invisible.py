#!/usr/bin/env python3
"""Assert room 191 transparent patterns and unchanged actor/room190 behavior."""
import json
from pathlib import Path
from restore_star_world_1 import lz2, graphics_pointer, sha
ROOT=Path(__file__).resolve().parents[1]

def qualify():
    base=ROOT/'local/captures/takeover-r3-191'
    native=ROOT/'local/captures/invisible-r5-191'
    interp=ROOT/'local/captures/invisible-r5-191-interp'
    rom=(ROOT/'local/restoration/demo11-native-product-r5/rom.sfc').read_bytes()
    cfg=json.loads((ROOT/'config/restorations/demo11-native-product-r5.json').read_text())
    assert sha(rom)==cfg['output']['sha256']
    pack=(ROOT/'local/native-modules/corridor-invisible-v1/corridor-invisible.bin').read_bytes()
    data=bytearray(rom);data[0x280000:0x280000+len(pack)]=pack
    for gfx in (0xff9,0xffa):
        decoded,_=lz2(data,graphics_pointer(rom,gfx))
        assert len(decoded)==4096
    for tag in ('w1','w2','w3','w4','w5'):
        a=(base/(tag+'.wram.bin')).read_bytes();b=(native/(tag+'.wram.bin')).read_bytes()
        assert b[0x100]==0x14 and b[0x10b:0x10d]==bytes.fromhex('9101')
        assert a[0x96:0x98]==b[0x96:0x98]
        assert abs(int.from_bytes(a[0x94:0x96],'little')-int.from_bytes(b[0x94:0x96],'little')) <= 2
        for lo,hi in [(0x9e,0xaa),(0xd8,0xf0),(0x14c8,0x14e0),(0x1ab9e,0x1abaa)]:
            assert a[lo:hi]==b[lo:hi],(tag,hex(lo))
        assert (base/(tag+'.oam.bin')).read_bytes()[444:448] == (native/(tag+'.oam.bin')).read_bytes()[444:448]
        for suffix in ('cgram.bin',):
            assert (base/(tag+'.'+suffix)).read_bytes()==(native/(tag+'.'+suffix)).read_bytes(),(tag,suffix)
        for suffix in ('vram.bin','fb.bgrx','oam.bin','cgram.bin'):
            assert (native/(tag+'.'+suffix)).read_bytes()==(interp/(tag+'.'+suffix)).read_bytes(),('interp',tag,suffix)
        v=(native/(tag+'.vram.bin')).read_bytes()
        for tile in [0xa4,0xa5,0xa6,0xa7,0xb4,0xb5,0xb6,0xb7]:
            assert not any(v[tile*32:(tile+1)*32])
        for tile in [0xc,0xd,0x1c,0x1d]:
            assert not any(v[0xf000+tile*32:0xf000+(tile+1)*32])
    # First sample: both foreground marker rectangles and the control sprite are transparent.
    f=(native/'w1.fb.bgrx').read_bytes();sky=f[:3]
    for x0,y0,x1,y1 in [(192,96,208,128),(176,176,192,191)]:
        for y in range(y0,y1):
            for x in range(x0,x1):
                assert f[(y*256+x)*4:(y*256+x)*4+3]==sky,(x,y)
    # Room 190 is unchanged, including the accepted smooth background.
    for suffix in ('wram.bin','vram.bin','fb.bgrx','oam.bin','cgram.bin'):
        assert (ROOT/f'local/captures/takeover-r3-190/q1.{suffix}').read_bytes()==(ROOT/f'local/captures/invisible-r5-190/q1.{suffix}').read_bytes(),('190',suffix)
    identities={}
    for directory in (base,native,interp,ROOT/'local/captures/invisible-r5-190',ROOT/'local/captures/takeover-r3-190'):
        identities[str(directory.relative_to(ROOT))]=json.loads((directory/'receipt.json').read_text())
    return dict(rom_sha256=sha(rom),pack_sha256=sha(pack),room191_samples=5,room190_equal_files=5,identities=identities,
                scope='User-directed room-local visual adaptation; assisted pipe entry and movement, not a course clear.')

if __name__=='__main__':
    report=qualify();out=ROOT/'local/reports/corridor-invisible-r5.json'
    out.write_text(json.dumps(report,indent=2)+'\n');print(out)

import struct, sys, zlib
from pathlib import Path
def png(path, w, h, pix):
    raw=b''.join(b'\x00'+bytes(pix[y*w:(y+1)*w]) for y in range(h))
    def chunk(t,d):
        c=struct.pack('>I',len(d))+t+d
        return c+struct.pack('>I', zlib.crc32(t+d)&0xffffffff)
    out=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,0,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
    Path(path).write_bytes(out)
v=Path(sys.argv[1]).read_bytes()
start=int(sys.argv[2],0) if len(sys.argv)>2 else 0x0000
nbytes=int(sys.argv[3],0) if len(sys.argv)>3 else 0x2000
tpr=32
tiles=nbytes//16
rows=(tiles+tpr-1)//tpr
W=tpr*8; H=rows*8
pix=[0]*(W*H)
for t in range(tiles):
    base=start+t*16
    for y in range(8):
        b0=v[base+y*2]; b1=v[base+y*2+1]
        for x in range(8):
            bit=7-x
            c=((b0>>bit)&1) | (((b1>>bit)&1)<<1)
            px=(t%tpr)*8+x; py=(t//tpr)*8+y
            pix[py*W+px]=c*85
out=sys.argv[4] if len(sys.argv)>4 else '/tmp/vram_tiles.png'
png(out,W,H,pix)
print('wrote',out,W,H)
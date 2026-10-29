"""Qualify the room 151 music retarget to recipient slot A4 (demo11-native-product-r9)."""
import array
import json
import math
import wave
from pathlib import Path
from restore_star_world_1 import graphics_pointer, lorom, lz2, sha

ROOT = Path(__file__).resolve().parents[1]
R8_SHA = '4a45955c65c30495940b69fbd4675ed41574e3ae37c4471ecc80c32adf2bd55f'
R9_SHA = 'd29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552'
PARAM = lorom(0x5BBCFF) + 0x3F4
OFFICIAL = ROOT / 'local/content-versions/demo-1-1/rom.sfc'


def music_block(rom, slot):
    o = lorom(0x0FE000) + slot * 3
    p = int.from_bytes(rom[o:o + 3], 'little')
    assert p not in (0, 0xFFFFFF), ('null slot', slot)
    return p, rom[lorom(p):lorom(p) + 2 + int.from_bytes(rom[lorom(p):lorom(p) + 2], 'little')]


def wav_rms(path):
    w = wave.open(str(path), 'rb')
    rate, ch = w.getframerate(), w.getnchannels()
    data = array.array('h')
    data.frombytes(w.readframes(w.getnframes()))

    def rms(seg):
        return math.sqrt(sum(x * x for x in seg) / len(seg)) if seg else 0.0

    windows = [rms(data[i * rate * ch:(i + 1) * rate * ch])
               for i in range(int(len(data) / (rate * ch)))]
    return rms(data), max(windows) if windows else 0.0, len(data) / rate


def qualify():
    r8 = (ROOT / 'local/restoration/demo11-native-product-r8/rom.sfc').read_bytes()
    r9 = (ROOT / 'local/restoration/demo11-native-product-r9/rom.sfc').read_bytes()
    assert sha(r8) == R8_SHA and sha(r9) == R9_SHA
    cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r9.json').read_text())
    assert cfg['id'] == 'demo11-native-product-r9' and sha(r9) == cfg['output']['sha256']

    # 1. r9 is r8 plus one music-object byte. No other byte moves.
    assert r8[PARAM - 2:PARAM] == b'\x40\x60' and r8[PARAM] == 0x61
    expected = bytearray(r8)
    expected[PARAM] = 0xA5
    assert bytes(expected) == r9
    assert r9[PARAM] == 0xA5

    # 2. Slot A4 is present and byte-identical to the official demo 1-1 song block.
    off = OFFICIAL.read_bytes()
    prod_ptr, prod_block = music_block(r9, 0xA4)
    off_ptr, off_block = music_block(off, 0xA4)
    assert prod_ptr == off_ptr and prod_block == off_block
    assert len(prod_block) > 10000, len(prod_block)

    # 3. In room 151 the current song record is A4, and gameplay is not stalled.
    native = ROOT / 'local/captures/corridor-music-r9-151'
    labels = sorted({p.name.split('.', 1)[0] for p in native.glob('*.wram.bin')})
    gameplay = 0
    last_room = None
    mazo = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
    g27d = lz2(mazo, graphics_pointer(mazo, 0x27D), limit=0x10000)[0]
    wave = 0
    for lbl in labels:
        b = (native / (lbl + '.wram.bin')).read_bytes()
        if (b[0x10B] | (b[0x10C] << 8)) != 0x151:
            continue
        assert b[0xDDA] == 0xA4, (lbl, b[0xDDA])
        assert b[0x100] != 0x12 or lbl in ('fight060',), ('stuck in Mario Start', lbl)
        last_room = lbl
        if b[0x100] == 0x14:
            gameplay += 1
        vram = (native / (lbl + '.vram.bin')).read_bytes()
        if b[0x100] == 0x14 and vram[0x8000:0x8000 + 4096] == g27d:
            wave += 1
    assert gameplay >= 20, gameplay
    assert wave >= 20, wave
    assert (native / (last_room + '.wram.bin')).read_bytes()[0x100] == 0x14, last_room

    # 4. The song is audible: the isolated audio capture is non-silent in room 151.
    audio = ROOT / 'local/captures/corridor-music-r9-151-audio'
    overall, loudest, seconds = wav_rms(audio / 'audio.wav')
    assert overall > 100 and loudest > 300, (overall, loudest)

    # 5. Rooms 190, 191 and 192 keep byte-identical dumps versus the accepted r8 captures.
    pairs = [('corridor-music-r9-190', 'corridor-wave-r8-190'),
             ('corridor-music-r9-191', 'corridor-wave-r8-191'),
             ('corridor-music-r9-192', 'corridor-wave-r8-192')]
    unchanged = 0
    for new, old in pairs:
        nd, od = ROOT / 'local/captures' / new, ROOT / 'local/captures' / old
        assert (sorted({p.name.split('.', 1)[0] for p in nd.glob('*.wram.bin')})
                == sorted({p.name.split('.', 1)[0] for p in od.glob('*.wram.bin')}))
        for lbl in sorted({p.name.split('.', 1)[0] for p in nd.glob('*.wram.bin')}):
            for suffix in ('wram.bin', 'vram.bin', 'fb.bgrx', 'oam.bin', 'cgram.bin'):
                assert ((nd / (lbl + '.' + suffix)).read_bytes()
                        == (od / (lbl + '.' + suffix)).read_bytes()), (new, lbl, suffix)
                unchanged += 1

    receipts = {name: json.loads((ROOT / 'local/captures' / name / 'receipt.json').read_text())
                for name in ('corridor-music-r9-151', 'corridor-music-r9-151-audio',
                             'corridor-music-r9-190', 'corridor-music-r9-191', 'corridor-music-r9-192')}
    return dict(rom_sha256=sha(r9), music_slot='A4', music_parameter='A5',
                music_param_offset=PARAM, a4_block_bytes=len(prod_block),
                a4_matches_official=True, room151_gameplay_samples=gameplay,
                room151_wave_samples=wave,
                audio={'rms': round(overall, 1), 'loudest_second_rms': round(loudest, 1),
                       'seconds': round(seconds, 2)},
                unchanged_files=unchanged, receipts=receipts,
                scope='Assisted pipe entry and stationary-Mario fixture; music selection plus graphics regression.')


if __name__ == '__main__':
    result = qualify()
    path = ROOT / 'local/reports/corridor-music-r9.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(path)
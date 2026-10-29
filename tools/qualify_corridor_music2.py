"""Qualify the room 190 music override (demo11-native-product-r10, native adaptation)."""
import array
import json
import math
import wave
from pathlib import Path
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
R9_SHA = 'd29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552'


def wav_rms(path):
    w = wave.open(str(path), 'rb'); rate, ch = w.getframerate(), w.getnchannels()
    data = array.array('h'); data.frombytes(w.readframes(w.getnframes()))
    def rms(seg): return math.sqrt(sum(x * x for x in seg) / len(seg)) if seg else 0.0
    return rms(data), max(rms(data[i*rate*ch:(i+1)*rate*ch])
                          for i in range(int(len(data)/(rate*ch))))


def room_music(cap, room):
    music, modes = set(), set()
    for f in (ROOT / 'local/captures' / cap).glob('*.wram.bin'):
        b = f.read_bytes()
        if (b[0x10B] | (b[0x10C] << 8)) == room:
            music.add(b[0xDDA]); modes.add(b[0x100])
    assert 0x14 in modes, ('stalled', cap, modes)
    return music


def qualify():
    r9 = (ROOT / 'local/restoration/demo11-native-product-r9/rom.sfc').read_bytes()
    r10 = (ROOT / 'local/restoration/demo11-native-product-r10/rom.sfc').read_bytes()
    assert sha(r9) == R9_SHA and sha(r10) == R9_SHA
    cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r10.json').read_text())
    assert cfg['id'] == 'demo11-native-product-r10' and sha(r10) == cfg['output']['sha256']
    assert any(a.get('kind') == 'room-music-override' and a.get('room') == '0x190'
               for a in cfg.get('native_adaptations', []))
    src = (ROOT / 'recomp/native_seven.c').read_bytes()
    assert b'bm_room_music_override' in src and b'g_ram[0x0dda] = 0x9e' in src

    # Room 190 now requests slot 9E; neighbours keep their accepted music.
    assert room_music('r10-190', 0x190) == {0x9E}
    assert room_music('r10-191', 0x191) == {0x02}
    assert room_music('r10-192', 0x192) == {0x02}
    assert room_music('r10-151', 0x151) == {0xA4}

    # Rooms 151/191/192 stay byte-identical to the accepted r9 captures.
    pairs = [('r10-191', 'corridor-music-r9-191'),
             ('r10-192', 'corridor-music-r9-192'),
             ('r10-151', 'corridor-music-r9-151')]
    unchanged = 0
    for new, old in pairs:
        nd, od = ROOT / 'local/captures' / new, ROOT / 'local/captures' / old
        labels = sorted({p.name.split('.', 1)[0] for p in nd.glob('*.wram.bin')})
        assert labels == sorted({p.name.split('.', 1)[0] for p in od.glob('*.wram.bin')})
        for lbl in labels:
            for suffix in ('wram.bin', 'vram.bin', 'fb.bgrx', 'oam.bin', 'cgram.bin'):
                assert ((nd / (lbl + '.' + suffix)).read_bytes()
                        == (od / (lbl + '.' + suffix)).read_bytes()), (new, lbl, suffix)
                unchanged += 1

    # The override is audible: isolated audio capture is non-silent in room 190.
    overall, loudest = wav_rms(ROOT / 'local/captures/r10-190-audio/audio.wav')
    assert overall > 100 and loudest > 300, (overall, loudest)

    receipts = {name: json.loads((ROOT / 'local/captures' / name / 'receipt.json').read_text())
                for name in ('r10-190', 'r10-190-audio', 'r10-191', 'r10-192', 'r10-151')}
    return dict(rom_sha256=sha(r10), room='0x190', music_slot='0x9E',
                native_adaptation='recomp/native_seven.c:bm_room_music_override',
                neighbours={'191': '0x02', '192': '0x02', '151': '0xA4'},
                unchanged_files=unchanged,
                audio={'rms': round(overall, 1), 'loudest_second_rms': round(loudest, 1)},
                receipts=receipts,
                scope='Assisted pipe entry fixture for room 190; music override, neighbours regressed.')


if __name__ == '__main__':
    result = qualify()
    path = ROOT / 'local/reports/corridor-music-r10.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(path)
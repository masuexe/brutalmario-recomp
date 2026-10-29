"""Qualify the room 151 tidal-wave graphics restoration (demo11-native-product-r8)."""
import json
from pathlib import Path
from restore_star_world_1 import graphics_pointer, lz2, pointer_offset, sha

ROOT = Path(__file__).resolve().parents[1]
GFX = 0x27D
MAZO = ROOT / 'local/content-versions/mazo/rom.sfc'
R7 = 'e18964c5b90e53eba2836f293dbb209ee4118af7649b1e7ecc6882a5892fe8b1'
R8 = '4a45955c65c30495940b69fbd4675ed41574e3ae37c4471ecc80c32adf2bd55f'


def decoded_gfx(rom, gid):
    return lz2(rom, graphics_pointer(rom, gid), limit=0x10000)[0]


def qualify():
    r7 = (ROOT / 'local/restoration/demo11-native-product-r7/rom.sfc').read_bytes()
    r8 = (ROOT / 'local/restoration/demo11-native-product-r8/rom.sfc').read_bytes()
    assert sha(r7) == R7 and sha(r8) == R8
    cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r8.json').read_text())
    assert sha(r8) == cfg['output']['sha256'] and cfg['id'] == 'demo11-native-product-r8'

    # 1. The r8 ROM is r7 plus one 3-byte extended-graphics pointer, and nothing else.
    off = pointer_offset(GFX)
    expected = bytearray(r7)
    expected[off:off + 3] = bytes.fromhex('0080d1')
    assert bytes(expected) == r8
    assert r7[off:off + 3] == b'\xff' * 3

    # 2. The mounted pack carries the exact mazo compressed stream for gfx 0x27D.
    mazo = MAZO.read_bytes()
    mazo_data, mazo_stream = lz2(mazo, graphics_pointer(mazo, GFX), limit=0x10000)
    assert len(mazo_data) == 4096
    pack = (ROOT / 'local/restoration/demo11-native-product-r8/corridor-wave.bin').read_bytes()
    assert pack == mazo_stream
    extra = next(p for p in cfg['native_sprite_gap']['extra_packs']
                 if p['variable'] == 'BM_CORRIDOR_WAVE_PACK')
    assert extra['address'] == 'D18000' and extra['size'] == len(pack)
    assert extra['sha256'] == sha(pack)

    # 3. In room 151 the boss tidal-wave background now equals the mazo graphics.
    native = ROOT / 'local/captures/corridor-wave-r8-151'
    interp = ROOT / 'local/captures/corridor-wave-r8-151-interp'
    labels = sorted({p.name.split('.', 1)[0] for p in native.glob('*.wram.bin')})
    gfx28 = decoded_gfx(r8, 0x28)
    checked = []
    for lbl in labels:
        wram = (native / (lbl + '.wram.bin')).read_bytes()
        if wram[0x100] != 0x14 or wram[0x10B:0x10D] != bytes.fromhex('5101'):
            continue
        vram = (native / (lbl + '.vram.bin')).read_bytes()
        # initial load (before the attack) still holds the room background
        if lbl == 'fight090':
            assert vram[0x8000:0x8000 + 2048] == gfx28, 'initial background changed'
        checked.append(lbl)
    # Every sample from the first wave onward must hold gfx 0x27D in both buffers.
    wave = [l for l in checked if int(l[5:]) >= 100]
    assert wave, 'no wave samples'
    for lbl in wave:
        wram = (native / (lbl + '.wram.bin')).read_bytes()
        vram = (native / (lbl + '.vram.bin')).read_bytes()
        assert wram[0xAD00:0xAD00 + 4096] == mazo_data, ('wram', lbl)
        assert vram[0x8000:0x8000 + 4096] == mazo_data, ('vram', lbl)

    # 4. Native and interpreter agree on graphics, palette and OAM for the wave frames.
    transient_fb = {'fight145', 'fight270'}
    ni_equal = 0
    for lbl in checked:
        for suffix in ('vram.bin', 'oam.bin', 'cgram.bin'):
            assert ((native / (lbl + '.' + suffix)).read_bytes()
                    == (interp / (lbl + '.' + suffix)).read_bytes()), (lbl, suffix)
        if lbl not in transient_fb:
            assert ((native / (lbl + '.fb.bgrx')).read_bytes()
                    == (interp / (lbl + '.fb.bgrx')).read_bytes()), (lbl, 'fb')
            ni_equal += 1

    # 5. The accepted rooms 190, 191 and 192 keep byte-identical dumps versus r7.
    pairs = [('corridor-wave-r8-190', 'corridor-r7-190'),
             ('corridor-wave-r8-191', 'corridor-r7-191'),
             ('corridor-wave-r8-192', 'corridor-r7-192')]
    unchanged = 0
    for new, old in pairs:
        new_dir, old_dir = ROOT / 'local/captures' / new, ROOT / 'local/captures' / old
        labels_new = sorted({p.name.split('.', 1)[0] for p in new_dir.glob('*.wram.bin')})
        labels_old = sorted({p.name.split('.', 1)[0] for p in old_dir.glob('*.wram.bin')})
        assert labels_new == labels_old, (new, labels_new, labels_old)
        for lbl in labels_new:
            for suffix in ('wram.bin', 'vram.bin', 'fb.bgrx', 'oam.bin', 'cgram.bin'):
                assert ((new_dir / (lbl + '.' + suffix)).read_bytes()
                        == (old_dir / (lbl + '.' + suffix)).read_bytes()), (new, lbl, suffix)
                unchanged += 1

    # 6. The donor reference really carries gfx 0x27D in the same buffer and VRAM.
    donor = ROOT / 'local/captures/mazo-9c-align-fine-v2-donor'
    d_wram = (donor / 'fight120.wram.bin').read_bytes()
    d_vram = (donor / 'fight120.vram.bin').read_bytes()
    assert d_wram[0xAD00:0xAD00 + 4096] == mazo_data
    assert d_vram[0x8000:0x8000 + 4096] == mazo_data

    receipts = {name: json.loads((ROOT / 'local/captures' / name / 'receipt.json').read_text())
                for name in ('corridor-wave-r8-151', 'corridor-wave-r8-151-interp',
                             'corridor-wave-r8-190', 'corridor-wave-r8-191', 'corridor-wave-r8-192')}
    return dict(rom_sha256=sha(r8), pack_sha256=sha(pack), pack_size=len(pack),
                pointer_file_offset=off, gfx='27D', wave_samples=wave,
                native_interpreter_samples=len(checked), unchanged_files=unchanged,
                receipts=receipts,
                scope='Assisted pipe entry and stationary-Mario attack fixture; graphics only.')


if __name__ == '__main__':
    result = qualify()
    path = ROOT / 'local/reports/corridor-wave-r8.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(path)

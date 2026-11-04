"""Render one song payload through the pinned reference host.

The Demo 1-1 engine reads an upload block, not a bare payload:

    +0  payload length, little-endian word
    +2  ARAM destination, little-endian word
    +4  payload bytes

The extraction tool renders a song by pointing the carrier slot at such a
block inside the Demo 1-1 image. This tool writes a new block for a payload
that comes from outside that image, so a song from a content pack can be
heard through the real engine.

Usage: render_song_payload.py <payload.bin> <out.wav> [seconds]
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import extract_demo11_music as music

ROM = music.ROM
WORK = ROOT / 'local/music-audit/render'
ARAM_DESTINATION = 0x5400


def block(payload):
    """Wrap a payload in the upload block that the engine expects."""
    return (len(payload).to_bytes(2, 'little') +
            ARAM_DESTINATION.to_bytes(2, 'little') + payload)


def render(payload, out, seconds=30, tail_frames=900):
    data = Path(payload).read_bytes()
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    rom = bytearray(ROM.read_bytes())
    offset = 0x2057B4   # largest zero run in the Demo 1-1 image
    blob = block(data)
    rom[offset:offset + len(blob)] = blob
    table = music.lorom(music.TABLE_ADDR)
    # A 3-byte LoROM pointer is bank, high byte, low byte of the block.
    bank = 0x80 | (offset >> 15)
    high = (offset & 0x7FFF) >> 8
    low = offset & 0xFF
    rom[table + music.CARRIER_SLOT * 3:table + music.CARRIER_SLOT * 3 + 3] = \
        bytes([bank, high, low])
    (WORK / 'rom.sfc').write_bytes(rom)
    route = music.ROUTE.replace('until 0100 == 14 480', 'until 0100 == 14 2400')
    (WORK / 'route.script').write_text(route.format(tail=tail_frames))
    env = dict(os.environ)
    env.update({
        'SNESREF_HEADLESS': '1',
        'SNESREF_WRAM_FILL': '0',
        'SNESREF_SCRIPT': str(WORK / 'route.script'),
        'SNESREF_DUMP_DIR': str(WORK),
        'SNESREF_TRACE_FILE': str(WORK / 'wram.jsonl'),
        'SNESREF_WAV': str(WORK / 'audio.wav'),
        'SNESREF_CORE_OPTIONS': music.CORE_OPTIONS,
    })
    with (WORK / 'run.log').open('w') as log:
        result = subprocess.run([str(music.SNESREF), str(music.CORE), str(WORK / 'rom.sfc')],
                                cwd=str(WORK), env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=300)
    if result.returncode:
        raise RuntimeError(f'reference run failed with {result.returncode}')
    samples, rate, total = music.read_wav(WORK / 'audio.wav')
    frame = music.read_request_frame(WORK / 'wram.jsonl')
    cut = music.find_cut(samples, rate, frame)
    if cut is None:
        cut = 0
    take = min(seconds * rate, total - cut)
    audio = samples[cut * 2:cut * 2 + take * 2]
    music.write_wav(Path(out), audio, rate)
    return music.analyse(audio, rate)


if __name__ == '__main__':
    stats = render(sys.argv[1], sys.argv[2])
    for key, value in stats.items():
        print(f'{key}: {value}')

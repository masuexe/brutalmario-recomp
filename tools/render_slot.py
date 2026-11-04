"""Render one existing song slot of the Demo 1-1 image through the reference host.

The extraction tool renders a song by pointing the carrier slot at the block
that the target slot already holds. This tool does the same for a single slot,
so a slot can be heard without rewriting its payload. The upload destination
comes from the block itself, which matters for the legacy songs that upload to
ARAM $6800 instead of $5400.

Usage: render_slot.py <slot-hex> <out.wav> [rom.sfc]
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import extract_demo11_music as music

WORK = ROOT / 'local/music-audit/render-slot'


def render(slot, out, rom_path=None, seconds=20, tail_frames=900):
    source = Path(rom_path) if rom_path else music.ROM
    rom = bytearray(source.read_bytes())
    table = music.lorom(music.TABLE_ADDR)
    pointer = rom[table + slot * 3:table + slot * 3 + 3]
    if pointer == b'\x00\x00\x00':
        raise SystemExit(f'slot {slot:02X} has no block')
    rom[table + music.CARRIER_SLOT * 3:table + music.CARRIER_SLOT * 3 + 3] = pointer
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
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
    slot = int(sys.argv[1], 16)
    rom = sys.argv[3] if len(sys.argv) > 3 else None
    stats = render(slot, sys.argv[2], rom)
    for key, value in stats.items():
        print(f'{key}: {value}')

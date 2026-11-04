"""Run one room probe script through the reference host and keep the audio.

The native runtime and the reference host run the same game code. A room that
plays in one and stays silent in the other isolates the fault to the runtime.

Usage: render_room_ref.py <room-hex> <rom.sfc> <out.wav>
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import extract_demo11_music as music

WORK = ROOT / 'local/music-audit/render-room'


def render(room, rom_path, out, script_path=None):
    work = WORK / f'room-{room:03X}'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    script = Path(script_path) if script_path else (
        ROOT / 'local/probes/music-audit' / f'room-{room:03X}.script')
    body = [line for line in script.read_text().splitlines()
            if not line.strip().startswith('turbo')]
    (work / 'route.script').write_text(chr(10).join(body) + chr(10))
    env = dict(os.environ)
    env.update({
        'SNESREF_HEADLESS': '1',
        'SNESREF_WRAM_FILL': '0',
        'SNESREF_SCRIPT': str(work / 'route.script'),
        'SNESREF_DUMP_DIR': str(work),
        'SNESREF_WAV': str(work / 'audio.wav'),
        'SNESREF_CORE_OPTIONS': music.CORE_OPTIONS,
    })
    rom_abs = str(Path(rom_path).resolve())
    with (work / 'run.log').open('w') as log:
        result = subprocess.run([str(music.SNESREF), str(music.CORE), rom_abs],
                                cwd=str(work), env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=300)
    print('exit', result.returncode)
    wav = work / 'audio.wav'
    if not wav.exists():
        raise SystemExit('no audio written')
    samples, rate, total = music.read_wav(wav)
    take = min(65536, total)
    audio = samples[total * 2 - take * 2:total * 2]
    music.write_wav(Path(out), audio, rate)
    return music.analyse(audio, rate)


if __name__ == '__main__':
    room = int(sys.argv[1], 16)
    script = sys.argv[4] if len(sys.argv) > 4 else None
    stats = render(room, sys.argv[2], sys.argv[3], script)
    for key, value in stats.items():
        print(f'{key}: {value}')

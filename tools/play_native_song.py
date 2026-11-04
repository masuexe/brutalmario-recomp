"""Play one Demo 1-1 song with the pinned DSP, without the SPC driver.

The SPC driver decides which song to start and writes the DSP registers. A
native player does that work itself: it reads the song stream, writes the same
registers, and lets the upstream DSP produce the samples. The sample set and
its directory come from a console capture of the same ROM.

This tool is a probe. It plays one song for a fixed number of frames and writes
a WAV file. It does not replace the game music engine.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/native_song_player.c'
STUBS = ROOT / 'tools/native_song_stubs.c'
ENGINE = ROOT / 'local/upstream/snesrecomp/runner/src'
BINARY = ROOT / 'local/music-audit/song-player'


def build():
    command = ['cc', '-std=c11', '-O2',
               '-I' + str(ENGINE), '-I' + str(ENGINE / 'snes'),
               str(SOURCE), str(STUBS),
               str(ENGINE / 'snes/dsp.c'), str(ENGINE / 'snes/dsp_shadow.c'),
               '-o', str(BINARY)]
    subprocess.run(command, check=True)
    return BINARY


def play(song, engine_aram, out, frames):
    binary = build()
    subprocess.run([str(binary), str(song), str(engine_aram), str(out), str(frames)],
                   check=True)
    return out


if __name__ == '__main__':
    play(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))

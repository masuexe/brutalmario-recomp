"""Play one Demo 1-1 song with the project's DSP, without the SPC driver.

The SPC driver decides which song to start and writes the DSP registers. A
native player can do that work in C: parse the song, run its command stream,
and write the same registers. The sample playback then comes from the pinned
DSP in the upstream runtime, so the audio path matches the console.

This tool is a probe. It plays one song for a fixed number of frames and
writes a WAV file. It does not replace the game's music engine.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import decode_song as D

RATE = 32040
TICK_FRAMES = 1


def registers(events):
    """Return the DSP register writes for one track, in order."""
    writes, ticks = [], 0
    for _, duration, pitch, command in events:
        if command:
            opcode = command[0]
            if opcode == 0xC6 or opcode == 0xC7:
                writes.append(('instrument', command[1], ticks))
            elif opcode == 0xDA:
                writes.append(('pan', command[1], ticks))
            elif opcode == 0xE0:
                writes.append(('volume', command[1], ticks))
            elif opcode == 0xE2:
                writes.append(('tuning', command[1], ticks))
        if duration:
            ticks += duration
            if pitch is not None:
                writes.append(('note', pitch, ticks, duration))
    return writes


def summary(path):
    rows = D.song(path)
    lines = []
    for pattern, track, events in rows:
        writes = registers(events)
        notes = [w for w in writes if w[0] == 'note']
        instruments = {w[1] for w in writes if w[0] == 'instrument'}
        lines.append(f'pattern {pattern:04X} track {track:04X}: '
                     f'{len(notes)} notes, instruments {sorted(instruments)[:6]}')
    return lines


if __name__ == '__main__':
    for line in summary(sys.argv[1]):
        print(line)

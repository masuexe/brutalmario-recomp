"""Render one decoded song to WAV with the project DSP.

The song stream sets the channel registers. This tool runs that stream and
writes the DSP register values the console driver would write, then advances
the pinned DSP to produce samples. The DSP comes from the upstream runtime, so
the sample path matches the console.
"""
import sys
from pathlib import Path
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import decode_song as D

RATE = 32040
# One tick is one frame of the engine tempo.
TICK_SECONDS = 1.0 / 60.0


def events_to_notes(events):
    """Return (start_tick, duration, pitch) for each timed note."""
    notes, tick = [], 0
    for _, duration, pitch, command in events:
        if duration:
            if pitch is not None:
                notes.append((tick, duration, pitch))
            tick += duration
    return notes


def render_timeline(notes, total_ticks):
    """Return a mono sample list from the note timeline."""
    total = int(total_ticks * TICK_SECONDS * RATE) + RATE
    samples = [0.0] * total
    for start, duration, pitch in notes:
        note = pitch - 0x80 if pitch >= 0x80 else pitch
        frequency = 440.0 * (2.0 ** ((note - 36) / 12.0))
        begin = int(start * TICK_SECONDS * RATE)
        span = int(duration * TICK_SECONDS * RATE)
        for index in range(span):
            at = begin + index
            if at >= total:
                break
            samples[at] += 3000.0 * (1.0 if (index * frequency / RATE) % 1.0 < 0.5 else -1.0)
    return samples


def write(path, samples):
    peak = max((abs(value) for value in samples), default=0) or 1.0
    scale = 20000.0 / peak
    with wave.open(path, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(b''.join(
            int(max(-32768, min(32767, value * scale))).to_bytes(2, 'little', signed=True)
            for value in samples))


def render(path, target, seconds=30):
    rows = D.song(path)
    notes = [note for _, _, events in rows for note in events_to_notes(events)]
    ticks = min(max((n[0] + n[1] for n in notes), default=0), seconds * 60)
    samples = render_timeline(notes, ticks)
    write(target, samples)
    return len(notes), ticks


if __name__ == '__main__':
    count, ticks = render(sys.argv[1], sys.argv[2])
    print(f'{sys.argv[2]}: {count} notes, {ticks} ticks')

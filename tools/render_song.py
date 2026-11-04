"""Render one decoded song to a WAV file as a note timeline.

This is a format probe, not a sample synthesiser. It writes one square tone
per timed note so a listener can compare the note order against the reference
render. The pitch comes from the note byte; the length comes from the duration
byte in ticks.
"""
import sys
from pathlib import Path
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import decode_song as D

RATE = 32040
TICK_SECONDS = 1.0 / 60.0  # One tick is one SPC frame at the engine tempo.


def render(rows):
    """Return a mono sample list for the decoded tracks."""
    longest = 0
    for _, _, events in rows:
        ticks = sum(e[1] for e in events if e[1])
        longest = max(longest, ticks)
    total = int(longest * TICK_SECONDS * RATE) + RATE
    samples = [0] * total
    for _, _, events in rows:
        position = 0
        for _, duration, pitch, _ in events:
            if not duration:
                continue
            span = int(duration * TICK_SECONDS * RATE)
            if pitch is not None and pitch != 0x80:
                # Pitch byte: 0x80 + (octave * 12 + semitone).
                note = pitch - 0x80
                frequency = 440.0 * (2.0 ** ((note - 36) / 12.0))
                for index in range(span):
                    at = position + index
                    if at >= total:
                        break
                    phase = (index * frequency / RATE) % 1.0
                    samples[at] += 6000 if phase < 0.5 else -6000
            position += span
    return samples


def write(path, samples):
    peak = max((abs(x) for x in samples), default=0) or 1
    scale = 24000 / peak
    with wave.open(path, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(b''.join(
            int(max(-32768, min(32767, x * scale))).to_bytes(2, 'little', signed=True)
            for x in samples))


if __name__ == '__main__':
    source, target = sys.argv[1], sys.argv[2]
    rows = D.song(source)
    samples = render(rows)
    write(target, samples)
    print(f'{target}: {len(samples)} samples, {len(samples)/RATE:.2f} s')

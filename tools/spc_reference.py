"""Reference data from the AddmusicK SPC engine.

Source: https://github.com/HertzDevil/AddmusicK, test/asm/main.asm and
test/asm/InstrumentData.asm. That project reimplements the Super Mario World
music engine, so its tables are the authority for the note-to-pitch
conversion this project needs.

PitchTable holds thirteen entries that span one octave. SetPitch indexes it by
the integer octave, then interpolates with the fractional part of the note, and
finally multiplies by the sample's own base pitch from $02f0.
"""
from pathlib import Path

PITCH_TABLE = (0x085F, 0x08DE, 0x0965, 0x09F4, 0x0A8C, 0x0B2C, 0x0BD6,
               0x0C8B, 0x0D4A, 0x0E14, 0x0EEA, 0x0FCD, 0x10BE)

# Five bytes per music instrument: sample, ADSR1/GAIN, ADSR2, GAIN, tuning.
# The sixth byte in the engine layout is a subtuning value.
INSTRUMENTS = (
    (0x00, 0xFE, 0x6A, 0xB8, 0x06),
    (0x01, 0xFA, 0x6A, 0xB8, 0x03),
    (0x02, 0xAE, 0x2F, 0xB8, 0x04),
    (0x03, 0xFE, 0x6A, 0xB8, 0x03),
    (0x04, 0xA9, 0x6A, 0xB8, 0x03),
    (0x07, 0xAE, 0x26, 0xB8, 0x07),
    (0x08, 0xFA, 0x6A, 0xB8, 0x03),
    (0x09, 0x9E, 0x1F, 0xB8, 0x03),
    (0x05, 0xAE, 0x26, 0xB8, 0x1E),
    (0x0A, 0xEE, 0x6A, 0xB8, 0x02),
    (0x0B, 0xFE, 0x6A, 0xB8, 0x08),
    (0x01, 0xF7, 0x6A, 0xB8, 0x03),
    (0x10, 0x0E, 0x6A, 0x7F, 0x04),
    (0x0C, 0xFE, 0x6A, 0xB8, 0x03),
    (0x0D, 0xAE, 0x26, 0xB8, 0x07),
    (0x12, 0x8E, 0xE0, 0xB8, 0x03),
    (0x0C, 0xFE, 0x70, 0xB8, 0x03),
    (0x11, 0xFE, 0x6A, 0xB8, 0x05),
    (0x01, 0xE9, 0x6A, 0xB8, 0x03),
    (0x0F, 0x0F, 0x6A, 0x7F, 0x03),
)


def instrument(index):
    """Return (sample, adsr1, adsr2, gain, tuning) for one instrument."""
    if not 0 <= index < len(INSTRUMENTS):
        raise ValueError(f'instrument {index} is outside the table')
    return INSTRUMENTS[index]


def pitch(note, tuning):
    """Return the DSP pitch register for one note.

    SetPitch divides the note high byte by 0x18 to pick the table entry, then
    interpolates with the low byte and multiplies by the sample base pitch.
    """
    if not 0 <= note < 0x60:
        raise ValueError(f'note {note} is outside the pitch table range')
    octave, remainder = divmod(note, 12)
    low = PITCH_TABLE[octave]
    if octave + 1 < len(PITCH_TABLE):
        high = PITCH_TABLE[octave + 1]
    else:
        high = low * 2
    # Interpolate across the semitone gap with the note remainder.
    value = low + (high - low) * remainder // 12
    # Scale by the sample base pitch, as SetPitch does with $02f0.
    return (value * (tuning + 1)) & 0xFFFF


if __name__ == '__main__':
    for note in (0, 12, 24, 36, 48, 60):
        print(f'note {note:02X}: pitch {pitch(note, 0x06):04X}')

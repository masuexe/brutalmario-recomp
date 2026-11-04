"""Decode a Demo 1-1 song payload into timed note events.

The format is the Nintendo/SPC "MML" stream. This module reads the structure
and produces one note list per track. It does not synthesise samples.

Command rules used here come from the observed streams of the 100 extracted
songs and from the reviewed adapt_music subset:

  0x00        end of the track
  0x01..0x7F  duration in ticks; an optional low byte adds volume or gate
  0xC6/0xC7   instrument select, one argument byte
  0xDA        pan or channel setup, one argument byte
  0xDB/0xDE/0xDF/0xE0/0xE2/0xE7  one argument byte
  0xE9/0xEF/0xF1/0xF2            three argument bytes
  0xF0        two argument bytes, channel or echo setup

A note is a duration byte followed by a pitch byte. The pitch is
0x80 + (octave * 12 + semitone), and 0x80 means rest.
"""
from pathlib import Path

BASE = 0x5400


def pattern_tables(payload):
    """Return the pattern addresses of one payload."""
    values = [int.from_bytes(payload[i:i + 2], 'little') for i in (0, 2)]
    return [value for value in values if value]


def tracks(payload, pattern_address):
    offset = pattern_address - BASE
    if not 0 <= offset < len(payload) - 15:
        raise ValueError('pattern pointer leaves the payload')
    return [int.from_bytes(payload[offset + i:offset + i + 2], 'little')
            for i in range(0, 16, 2)
            if int.from_bytes(payload[offset + i:offset + i + 2], 'little')]


# A duration byte (below 0x80) takes the next byte as its pitch. That pitch
# byte is in the range 0x80..0xFF and is consumed by the duration rule, so it
# never appears as a command. Only the bytes below can be commands.
# A duration byte is below 0x80 and takes the next byte as its pitch. Both
# halves can be below 0x80 for a low note, so a pair is always two bytes.
# A byte of 0x00 separates musical phrases. A phrase list continues until the
# caller's track stream reaches its terminator, so 0x00 does not end a track.
ONE_ARGUMENT = {0xC6, 0xC7, 0xDA, 0xDB, 0xDE, 0xDF, 0xE0, 0xE2, 0xE7}
TWO_ARGUMENT = {0xF0, 0xCB, 0xCC, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6,
                0xD7, 0xD8, 0xD9, 0xDC, 0xDD, 0xE1, 0xE3, 0xE6, 0xE8, 0xEA,
                0xEB, 0xEC, 0xED, 0xEE, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8,
                0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF}
THREE_ARGUMENT = {0xE9, 0xEF, 0xF1, 0xF2}


def decode_track(payload, address, limit=8192):
    """Return the events of one track as (address, duration, pitch, command).

    A 0x00 byte separates phrases and is reported as a break event. The
    stream ends when the cursor reaches the end of the payload or the limit.
    """
    events, cursor = [], address
    while len(events) < limit:
        offset = cursor - BASE
        if not 0 <= offset < len(payload):
            return events
        byte = payload[offset]
        if byte == 0:
            events.append((cursor, None, None, ('break',)))
            cursor += 1
            continue
        if byte < 0x80:
            pitch = payload[offset + 1] if offset + 1 < len(payload) else None
            events.append((cursor, byte, pitch, None))
            cursor += 2
            continue
        if byte in ONE_ARGUMENT:
            events.append((cursor, None, None, (byte, payload[offset + 1])))
            cursor += 2
            continue
        if byte in TWO_ARGUMENT:
            events.append((cursor, None, None,
                           (byte, payload[offset + 1], payload[offset + 2])))
            cursor += 3
            continue
        if byte in THREE_ARGUMENT:
            target = int.from_bytes(payload[offset + 1:offset + 3], 'little')
            events.append((cursor, None, None, (byte, target, payload[offset + 3])))
            cursor += 4
            continue
        events.append((cursor, None, None, (byte,)))
        cursor += 1
    return events


def song(path):
    payload = Path(path).read_bytes()
    addresses = sorted({value for pattern in pattern_tables(payload)
                        for value in tracks(payload, pattern)})
    out = []
    for pattern in pattern_tables(payload):
        for track in tracks(payload, pattern):
            events = decode_track(payload, track)
            out.append((pattern, track, events))
    return out


if __name__ == '__main__':
    import sys
    for pattern, track, events in song(sys.argv[1]):
        notes = [e for e in events if e[1]]
        print(f'pattern {pattern:04X} track {track:04X}: {len(events)} events, '
              f'{len(notes)} timed, {sum(e[1] for e in notes)} ticks')

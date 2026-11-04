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
  0xF0        one byte, channel or echo setup

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


ONE_ARGUMENT = {0xC6, 0xC7, 0xDA, 0xDB, 0xDE, 0xDF, 0xE0, 0xE2, 0xE7, 0xF0}
THREE_ARGUMENT = {0xE9, 0xEF, 0xF1, 0xF2}


def decode_track(payload, address, limit=8192):
    """Return the events of one track as (address, duration, pitch, command)."""
    events, cursor, ticks = [], address, 0
    while len(events) < limit:
        offset = cursor - BASE
        if not 0 <= offset < len(payload):
            raise ValueError(f'track cursor {cursor:04X} leaves the payload')
        byte = payload[offset]
        if byte == 0:
            return events
        if byte < 0x80:
            duration = byte
            cursor += 1
            offset += 1
            pitch = None
            # A duration byte takes the next byte as its pitch. The pitch is
            # 0x80 + (octave * 12 + semitone), so it can exceed 0x7F.
            if offset < len(payload):
                pitch = payload[offset]
                cursor += 1
                offset += 1
            events.append((cursor, duration, pitch, None))
            ticks += duration
            continue
        if byte in ONE_ARGUMENT:
            events.append((cursor, None, None, (byte, payload[offset + 1])))
            cursor += 2
            continue
        if byte in THREE_ARGUMENT:
            events.append((cursor, None, None, (byte, payload[offset + 1:offset + 4].hex())))
            cursor += 4
            continue
        events.append((cursor, None, None, (byte,)))
        cursor += 1
    return events


def song(path):
    payload = Path(path).read_bytes()
    out = []
    for pattern in pattern_tables(payload):
        for track in tracks(payload, pattern):
            out.append((pattern, track, decode_track(payload, track)))
    return out


if __name__ == '__main__':
    import sys
    for pattern, track, events in song(sys.argv[1]):
        notes = [e for e in events if e[1]]
        print(f'pattern {pattern:04X} track {track:04X}: {len(events)} events, '
              f'{len(notes)} timed, {sum(e[1] for e in notes)} ticks')

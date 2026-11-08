#!/usr/bin/env python3
"""Move a song upload block from the legacy ARAM base to the recipient base.

The product engine starts a song only when the upload block targets ARAM 5400.
The legacy donor family stores most group songs at 6800. The block has this
layout:

    +0  payload length, little-endian word
    +2  ARAM destination, little-endian word
    +4  payload bytes

The payload holds a sequence header, a pattern table and channel tracks. Only
these fields hold ARAM addresses:

- the two pattern pointers in the sequence header;
- the eight channel pointers of each pattern;
- the target of command e9;
- the sequence self-pointer.

Do not relocate every word in the source range. Note parameters can hold a
value in that range. A blanket pass corrupted 115 words of the room 0F5 song.

Usage: adapt_song_base.py <in.bin> <out.bin> [--to 5400] [--report]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

RECIPIENT_BASE = 0x5400

# Parameter byte count for each command at or above da (from ARAM $043E / $0F58).
# Commands below 80 are a duration. Commands 80 to d9 are a note value. The walk
# needs every other command to consume the correct number of bytes.
LENGTHS = {
    0xdf: 0, 0xf0: 0,
    0xda: 1, 0xdb: 1, 0xe0: 1, 0xe2: 1, 0xe4: 1, 0xe6: 1, 0xe7: 1, 0xea: 1, 0xee: 1,
    0xdc: 2, 0xe1: 2, 0xe3: 2, 0xe8: 2, 0xed: 2,
    0xdd: 3, 0xde: 3, 0xe5: 3, 0xe9: 3, 0xeb: 3, 0xec: 3, 0xef: 3, 0xf1: 3, 0xf2: 3,
}

VANILLA_BANK_OFFSET = 0x72EDA
VANILLA_BANK_LENGTH = 16893
VANILLA_BANK_BASE = 0x1360


class SongError(ValueError):
    """The block is not a song that this tool can move."""


def _walk(song, base):
    """Return the offsets of the pointer fields and the count of track bytes."""
    count = len(song)

    def relative(value):
        return value - base

    fields = set()
    patterns = []
    pos = 0
    while pos + 2 <= count:
        word = song[pos] | (song[pos + 1] << 8)
        if word == 0x00ff:
            if pos == 0 or pos + 4 > count:
                raise SongError('sequence marker not found')
            fields.add(pos + 2)
            pos += 4
            break
        if word < 0x0100:
            raise SongError('sequence marker not found')
        fields.add(pos)
        patterns.append(word)
        pos += 2
    else:
        raise SongError('sequence marker not found')

    min_cursor = pos

    def check(cursor):
        if cursor < min_cursor or cursor >= count:
            raise SongError('track cursor leaves the song: %d' % cursor)

    pending = []
    visited = set()
    for pat_addr in patterns:
        pattern = relative(pat_addr)
        if pattern < min_cursor or pattern + 16 > count:
            raise SongError('pattern table leaves the song')
        for k in range(pattern, pattern + 16, 2):
            address = song[k] | (song[k + 1] << 8)
            if address:
                pending.append(relative(address))
                fields.add(k)
    while pending:
        cursor = pending.pop()
        while cursor not in visited:
            check(cursor)
            visited.add(cursor)
            command = song[cursor]
            cursor += 1
            if command == 0:
                break
            if command < 0x80:
                check(cursor)
                if song[cursor] < 0x80:
                    cursor += 1
            elif command >= 0xda:
                if command not in LENGTHS:
                    raise SongError('unsupported command %02X' % command)
                size = LENGTHS[command]
                if cursor + size > count:
                    raise SongError('command parameter leaves the song')
                if command == 0xe9:
                    pending.append(relative(song[cursor] | (song[cursor + 1] << 8)))
                    fields.add(cursor)
                cursor += size
    return fields, len(visited)


def extract_vanilla_payload(bank, song_id, source=VANILLA_BANK_BASE, destination=RECIPIENT_BASE):
    """Extract a 1-based vanilla SMW song from its ARAM bank and pack at destination."""
    if len(bank) < song_id * 2 or song_id < 1:
        raise SongError('invalid vanilla song id %02X' % song_id)

    def r8(addr):
        off = addr - source
        if not 0 <= off < len(bank):
            raise SongError('address %04X outside vanilla bank' % addr)
        return bank[off]

    def r16(addr):
        off = addr - source
        if not 0 <= off < len(bank) - 1:
            raise SongError('word address %04X outside vanilla bank' % addr)
        return bank[off] | (bank[off + 1] << 8)

    seq_ptr = r16(source + (song_id - 1) * 2)
    cur = seq_ptr
    seq_words = []
    patterns = []
    while True:
        w = r16(cur)
        seq_words.append(w)
        cur += 2
        if w == 0x00ff:
            loop_target = r16(cur)
            seq_words.append(loop_target)
            cur += 2
            break
        if w < 0x0100:
            raise SongError('unexpected sequence control word %04X' % w)
        if w not in patterns:
            patterns.append(w)

    track_starts = []
    for p in patterns:
        for ch in range(8):
            tp = r16(p + ch * 2)
            if tp != 0 and tp not in track_starts:
                track_starts.append(tp)

    ranges = {}
    sub_ptr_addrs = set()
    queue = list(track_starts)
    visited = set()
    while queue:
        start = queue.pop(0)
        if start in visited:
            continue
        visited.add(start)
        c = start
        while True:
            cmd = r8(c)
            c += 1
            if cmd == 0x00:
                break
            if cmd < 0x80:
                if r8(c) < 0x80:
                    c += 1
            elif cmd >= 0xda:
                if cmd not in LENGTHS:
                    raise SongError('unsupported command %02X' % cmd)
                sz = LENGTHS[cmd]
                if cmd == 0xe9:
                    sub = r16(c)
                    sub_ptr_addrs.add(c)
                    if sub not in visited:
                        queue.append(sub)
                c += sz
        ranges[start] = c

    merged = []
    for s, e in sorted(ranges.items()):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    seq_len = len(seq_words) * 2
    pat_base = destination + seq_len
    pat_map = {p: pat_base + i * 16 for i, p in enumerate(patterns)}
    trk_base = pat_base + len(patterns) * 16

    seg_offsets = []
    cur_dst = trk_base
    for s, e in merged:
        seg_offsets.append((s, e, cur_dst))
        cur_dst += (e - s)

    def map_code_addr(addr):
        for s, e, dst in seg_offsets:
            if s <= addr < e:
                return dst + (addr - s)
        raise SongError('track address %04X outside merged ranges' % addr)

    out = bytearray()
    for i, w in enumerate(seq_words):
        if i == len(seq_words) - 2 and w == 0x00ff:
            out += (0x00ff).to_bytes(2, 'little')
        elif i == len(seq_words) - 1:
            loop_off = w - seq_ptr
            if not (0 <= loop_off < seq_len - 4 and loop_off % 2 == 0):
                raise SongError('invalid loop target %04X for sequence %04X' % (w, seq_ptr))
            out += (destination + loop_off).to_bytes(2, 'little')
        else:
            out += pat_map[w].to_bytes(2, 'little')

    for p in patterns:
        for ch in range(8):
            tp = r16(p + ch * 2)
            out += (map_code_addr(tp) if tp else 0).to_bytes(2, 'little')

    for s, e, _ in seg_offsets:
        seg = bytearray(bank[s - source:e - source])
        for addr in sorted(sub_ptr_addrs):
            if s <= addr < e:
                rel = addr - s
                seg[rel:rel + 2] = map_code_addr(r16(addr)).to_bytes(2, 'little')
        out += seg

    return bytes(out)


def wrap_upload_block(payload, destination=RECIPIENT_BASE):
    """Wrap a bare ARAM song payload in an upload block with a 4-byte zero trailer."""
    return (len(payload).to_bytes(2, 'little') +
            destination.to_bytes(2, 'little') +
            bytes(payload) +
            bytes(4))


def wrap_star_block(upload_block, pad_to=None):
    """Wrap an upload block in an 8-byte STAR header, optionally zero-padded."""
    count = len(upload_block) - 1
    star = (b'STAR' +
            count.to_bytes(2, 'little') +
            (count ^ 0xffff).to_bytes(2, 'little') +
            bytes(upload_block))
    if pad_to is not None:
        if len(star) > pad_to:
            raise SongError('STAR block (%d B) exceeds pad_to (%d B)' % (len(star), pad_to))
        star += bytes(pad_to - len(star))
    return star


def adapt(block, destination=RECIPIENT_BASE, report=None):
    """Return a block that targets the destination base."""
    if len(block) < 12:
        raise SongError('block is too short')
    count = block[0] | block[1] << 8
    source = block[2] | block[3] << 8
    if len(block) != count + 8:
        raise SongError('block length does not match its header')
    if source == destination:
        if report is not None:
            report.update({'moved': 0, 'fields': 0, 'track_bytes': 0, 'unchanged': True})
        return bytes(block)
    song = bytearray(block[4:4 + count])
    fields, walked = _walk(song, source)
    delta = source - destination
    lo, hi = destination, destination + count
    moved = 0
    for i in sorted(fields):
        word = song[i] | song[i + 1] << 8
        if not source <= word < source + count:
            raise SongError('pointer %04X outside the source range at %d' % (word, i))
        new = word - delta
        if not lo <= new < hi:
            raise SongError('relocated pointer %04X leaves the destination' % new)
        song[i] = new & 0xFF
        song[i + 1] = new >> 8
        moved += 1
    if report is not None:
        report.update({'moved': moved, 'fields': len(fields), 'track_bytes': walked,
                       'unchanged': False})
    out = count.to_bytes(2, 'little') + destination.to_bytes(2, 'little') + bytes(song)
    out += block[4 + count:]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--to', default='5400')
    parser.add_argument('--report', action='store_true')
    args = parser.parse_args()
    block = Path(args.source).read_bytes()
    report = {}
    out = adapt(block, int(args.to, 16), report)
    Path(args.output).write_bytes(out)
    if args.report:
        print('%s: %d bytes, base %04X to %s, %d pointer fields moved of %d walked bytes' % (
            args.source, len(out), block[2] | block[3] << 8, args.to,
            report['moved'], report['track_bytes']))
    else:
        print('%s: base %04X to %s, %d pointers relocated' % (
            args.source, block[2] | block[3] << 8, args.to, report['moved']))


if __name__ == '__main__':
    main()

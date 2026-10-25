#!/usr/bin/env python3
"""Extract every custom song from the Brutal Mario Demo 1-1 ROM.

The Demo 1-1 music engine keeps a 256-entry table of 3-byte LoROM pointers at
$0F:E000. Each non-null entry points at an upload block:

    +0  little-endian payload length
    +2  little-endian ARAM destination (always $5400 on this line)
    +4  payload bytes

The tool performs three jobs:

1. It writes every payload block to its own binary file.
2. It renders every payload to a WAV file through the pinned Snes9x reference
   host. The render changes one 3-byte pointer: the carrier level's song slot
   points at the target payload. The level load then starts the target song
   through the engine's normal upload path.
3. It writes a manifest, a checksum list, an M3U playlist and an HTML index.

All derived files stay under the gitignored local/ tree.
"""
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import wave
from array import array
from pathlib import Path

from prepare_rom import verify

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / 'local/roms/demo-1-1.sfc'
OUT = ROOT / 'local/music/demo-1-1'
SNESREF = ROOT / 'local/build/snesref/snesref'
CORE = ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so'
INPUTS = ROOT / 'config/inputs.json'
MAPPING = ROOT / 'config/music-mapping.json'

TABLE_ADDR = 0x0FE000
TABLE_ENTRIES = 256
ARAM_DESTINATION = 0x5400
CARRIER_SLOT = 0x30           # song requested by the level the capture route enters
CARRIER_FIRST_FRAME = 2100    # first frame that can hold the carrier request
CARRIER_LAST_FRAME = 2400     # last frame that can hold the carrier request
PREROLL_FRAMES = 35           # cut this many frames before the music request
REFERENCE_RATE = 32040
REFERENCE_FPS = 60.0988
SILENCE_RMS = 25.0
CORE_OPTIONS = 'snes9x_echo_buffer_hack=enabled'

ROUTE = '''# Demo 1-1 music extraction route.
# Enter the carrier level through the ordinary overworld, then let the song play.
wait 600
press start 2
wait 180
press start 2
wait 900
press b 30
wait 180
press a 30
wait 180
press y 30
wait 240
until 0100 == 14 480
wait {tail}
quit
'''


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def lorom(address):
    bank, low = address >> 16, address & 0xFFFF
    if not 0 <= bank <= 0xFF or bank in (0x7E, 0x7F) or low < 0x8000:
        raise ValueError('not a mapped LoROM address: %06X' % address)
    return (bank & 0x7F) * 0x8000 + (low & 0x7FFF)


def frame_to_sample(frame):
    return int(round(frame * REFERENCE_RATE / REFERENCE_FPS))


def read_rom():
    manifest = json.loads(INPUTS.read_text())
    data = ROM.read_bytes()
    verify(data, manifest['output'], 'Demo 1-1 ROM')
    return data


def read_table(rom):
    table = lorom(TABLE_ADDR)
    songs = []
    for slot in range(TABLE_ENTRIES):
        raw = rom[table + slot * 3:table + slot * 3 + 3]
        address = int.from_bytes(raw, 'big')
        if address == 0:
            continue
        offset = lorom(address)
        count = int.from_bytes(rom[offset:offset + 2], 'little')
        destination = int.from_bytes(rom[offset + 2:offset + 4], 'little')
        if count == 0 or destination != ARAM_DESTINATION:
            raise ValueError('slot %02X has an unexpected upload block' % slot)
        payload = rom[offset + 4:offset + 4 + count]
        if len(payload) != count:
            raise ValueError('slot %02X payload runs past the ROM end' % slot)
        songs.append({
            'slot': slot,
            'rom_address': address,
            'rom_offset': offset,
            'destination': destination,
            'size': count,
            'payload': payload,
            'sha256': sha256(payload),
        })
    return songs


def read_titles():
    data = json.loads(MAPPING.read_text())
    titles = {}
    for item in data['mappings']:
        slot = item.get('demo11_id')
        if slot:
            titles[int(slot, 16)] = {
                'title': item['title'],
                'origin_game': item['origin_game'],
                'levels': item.get('levels', []),
                'title_source': 'cross-version music mapping',
            }
    for item in data['new_family_additions']:
        slot = int(item['slot'], 16)
        titles.setdefault(slot, {
            'title': item['title'],
            'origin_game': item['origin_game'],
            'levels': [],
            'title_source': 'new-family addition',
        })
    return titles


def slug(text, limit=48):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text[:limit].strip('-')


def song_name(slot, title):
    if title:
        return 'song-%02X-%s' % (slot, slug(title['title']))
    return 'song-%02X' % slot


def read_request_frame(trace_path):
    frame = None
    pattern = re.compile(r'"adr":"0x01dfb","old":"0x[0-9a-f]+","val":"0x([0-9a-f]+)"')
    frame_pattern = re.compile(r'"f":(\d+)')
    with trace_path.open() as handle:
        for line in handle:
            match = pattern.search(line)
            if not match:
                continue
            value = int(match.group(1), 16)
            if value != CARRIER_SLOT:
                continue
            number = int(frame_pattern.search(line).group(1))
            if CARRIER_FIRST_FRAME <= number <= CARRIER_LAST_FRAME:
                frame = number
    return frame


def read_wav(path):
    with wave.open(str(path), 'rb') as handle:
        if handle.getnchannels() != 2 or handle.getsampwidth() != 2:
            raise ValueError('unexpected WAV format: %s' % path)
        rate = handle.getframerate()
        frames = handle.getnframes()
        handle.setpos(0)
        data = array('h')
        data.frombytes(handle.readframes(frames))
    return data, rate, frames


def find_cut(samples, rate, request_frame):
    """Return the first sample of the rendered excerpt, or None.

    The level load stops the map music about 30 frames before it requests the
    new song, and the request frame is deterministic. A sample 30 frames
    before the request is therefore inside the loading gap. The function
    verifies that the candidate is quiet and walks back if it is not.
    """
    if request_frame is None:
        return None
    first = frame_to_sample(max(0, request_frame - 60))
    candidate = frame_to_sample(request_frame - PREROLL_FRAMES)
    window = int(rate * 0.020)
    limit = len(samples) // 2
    position = candidate
    while position >= first and position + window <= limit:
        part = samples[position * 2:(position + window) * 2:2]
        if math.sqrt(sum(v * v for v in part) / window) < SILENCE_RMS:
            return position
        position -= int(rate * 0.005)
    return None


def content_end(samples, rate):
    """Return the end time of the last audible window, in seconds."""
    window = int(rate * 0.25)
    limit = len(samples) // 2
    position = 0
    end = 0.0
    while position + window <= limit:
        part = samples[position * 2:(position + window) * 2:2]
        if math.sqrt(sum(v * v for v in part) / window) >= 20.0:
            end = (position + window) / rate
        position += window
    return round(end, 3)


def analyse(samples, rate):
    count = len(samples) // 2
    if count == 0:
        return {'duration_seconds': 0.0, 'rms': 0.0, 'peak': 0, 'silent_fraction': 1.0,
                'leading_silence_seconds': 0.0}
    total = 0
    peak = 0
    for index in range(0, len(samples), 2):
        value = (samples[index] + samples[index + 1]) // 2
        total += value * value
        if abs(value) > peak:
            peak = abs(value)
    window = int(rate * 0.1)
    quiet = 0
    windows = 0
    leading = None
    position = 0
    while position + window <= count:
        part = samples[position * 2:(position + window) * 2:2]
        value = math.sqrt(sum(v * v for v in part) / window)
        if value < SILENCE_RMS:
            quiet += 1
        elif leading is None:
            leading = position / rate
        windows += 1
        position += window
    return {
        'duration_seconds': round(count / rate, 3),
        'rms': round(math.sqrt(total / count), 1),
        'peak': peak,
        'silent_fraction': round(quiet / windows, 3) if windows else 1.0,
        'leading_silence_seconds': round(leading or 0.0, 3),
    }


def write_wav(path, samples, rate):
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(samples.tobytes())


def capture_song(out, song, base_rom, seconds, tail_frames, title):
    """Render one payload to a WAV file and return its manifest entry."""
    slot = song['slot']
    name = song_name(slot, title)
    work = out / 'work' / ('song-%02X' % slot)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (out / 'payload').mkdir(parents=True, exist_ok=True)
    (out / 'wav').mkdir(parents=True, exist_ok=True)

    payload_path = out / 'payload' / ('song-%02X.bin' % slot)
    payload_path.write_bytes(song['payload'])

    rom = bytearray(base_rom)
    table = lorom(TABLE_ADDR)
    rom[table + CARRIER_SLOT * 3:table + CARRIER_SLOT * 3 + 3] = \
        base_rom[table + slot * 3:table + slot * 3 + 3]
    (work / 'rom.sfc').write_bytes(rom)
    (work / 'route.script').write_text(ROUTE.format(tail=tail_frames))

    env = dict(os.environ)
    env.update({
        'SNESREF_HEADLESS': '1',
        'SNESREF_WRAM_FILL': '0',
        'SNESREF_SCRIPT': str(work / 'route.script'),
        'SNESREF_DUMP_DIR': str(work),
        'SNESREF_TRACE_FILE': str(work / 'wram.jsonl'),
        'SNESREF_WAV': str(work / 'audio.wav'),
        'SNESREF_CORE_OPTIONS': CORE_OPTIONS,
    })
    with (work / 'run.log').open('w') as log:
        result = subprocess.run(
            [str(SNESREF), str(CORE), str(work / 'rom.sfc')],
            cwd=str(work), env=env, stdout=log, stderr=subprocess.STDOUT,
            timeout=300)
    if result.returncode:
        raise RuntimeError('slot %02X reference run failed with exit code %d'
                           % (slot, result.returncode))

    request_frame = read_request_frame(work / 'wram.jsonl')
    samples, rate, total_frames = read_wav(work / 'audio.wav')
    if rate != REFERENCE_RATE:
        raise ValueError('slot %02X rendered at unexpected rate %d' % (slot, rate))

    cut = find_cut(samples, rate, request_frame)
    cut_source = 'loading gap'
    if cut is None:
        if request_frame is None:
            raise ValueError('slot %02X has no carrier request and no silence gap' % slot)
        cut = max(0, frame_to_sample(request_frame - PREROLL_FRAMES))
        cut_source = 'request frame fallback'
    want = seconds * rate
    available = total_frames - cut
    take = min(want, available)
    if take < rate * 5:
        raise ValueError('slot %02X captured only %.1f seconds of audio'
                         % (slot, take / rate))
    audio = samples[cut * 2:cut * 2 + take * 2]
    if len(audio) > take * 2:
        audio = audio[:take * 2]
    end = content_end(audio, rate)
    stats = analyse(audio, rate)
    trimmed = None
    if end < 30.0 and stats['duration_seconds'] - end > 20.0:
        keep = int(round((end + 2.0) * rate))
        audio = audio[:keep * 2]
        stats = analyse(audio, rate)
        trimmed = stats['duration_seconds']
    wav_path = out / 'wav' / (name + '.wav')
    write_wav(wav_path, audio, rate)
    entry = {
        'slot': '%02X' % slot,
        'slot_value': slot,
        'title': title['title'] if title else None,
        'origin_game': title['origin_game'] if title else None,
        'levels': title['levels'] if title else [],
        'title_source': title['title_source'] if title else None,
        'payload': {
            'file': str(payload_path.relative_to(out)),
            'rom_address': '%06X' % song['rom_address'],
            'rom_file_offset': song['rom_offset'],
            'destination': '%04X' % song['destination'],
            'size': song['size'],
            'sha256': song['sha256'],
        },
        'audio': {
            'file': str(wav_path.relative_to(out)),
            'sample_rate': rate,
            'channels': 2,
            'sample_width_bytes': 2,
            **stats,
            'sha256': sha256(wav_path.read_bytes()),
            'carrier_slot': '%02X' % CARRIER_SLOT,
            'music_request_frame': request_frame,
            'cut_source': cut_source,
            'cut_frame': round(cut / rate * REFERENCE_FPS, 2),
            'content_end_seconds': end,
            'trimmed_seconds': trimmed,
            'core_options': CORE_OPTIONS,
        },
    }
    shutil.rmtree(work)
    return entry


def write_manifest(out, entries, base_rom, songs, args):
    document = {
        'schema': 1,
        'source': {
            'rom': str(ROM.relative_to(ROOT)),
            'rom_sha256': sha256(base_rom),
            'song_table_address': '%06X' % TABLE_ADDR,
            'song_table_entries': TABLE_ENTRIES,
            'payload_destination': '%04X' % ARAM_DESTINATION,
            'carrier_slot': '%02X' % CARRIER_SLOT,
            'capture_host': str(SNESREF.relative_to(ROOT)),
            'capture_host_sha256': sha256(SNESREF.read_bytes()),
            'reference_core': str(CORE.relative_to(ROOT)),
            'reference_core_sha256': sha256(CORE.read_bytes()),
            'core_options': CORE_OPTIONS,
            'route_tail_frames': args.tail,
            'render_seconds': args.seconds,
        },
        'song_count': len(entries),
        'table_entry_count': len(songs),
        'songs': entries,
        'limits': [
            'The audio render is a fixed-length excerpt from the song start.',
            'It is not loop-trimmed and not sample-identical to ZSNES 1.51.',
            'The carrier level is the Demo 1-1 overworld course used by the capture route.',
            'Titles come from config/music-mapping.json; unmapped slots stay untitled.',
        ],
    }
    (out / 'manifest.json').write_text(json.dumps(document, indent=2) + '\n')
    lines = []
    for entry in entries:
        lines.append('%s  %s' % (entry['payload']['sha256'], entry['payload']['file']))
        lines.append('%s  %s' % (entry['audio']['sha256'], entry['audio']['file']))
    (out / 'checksums.sha256').write_text('\n'.join(lines) + '\n')


def write_ids(out, entries):
    """Write the song id list as text and CSV."""
    text = ['# Demo 1-1 custom music ids. Level data music byte = slot id + 1.']
    rows = ['slot_hex,slot_dec,level_param_hex,payload_bytes,title,origin_game,wav']
    for entry in entries:
        slot = entry['slot_value']
        title = entry['title'] or ''
        origin = entry['origin_game'] or ''
        detail = title
        if origin:
            detail = '%s (%s)' % (title, origin) if title else origin
        text.append('%02X  dec %3d  level-byte %02X  %5d B  %s'
                    % (slot, slot, slot + 1, entry['payload']['size'], detail or '-'))
        rows.append('%02X,%d,%02X,%d,"%s","%s",%s'
                    % (slot, slot, slot + 1, entry['payload']['size'],
                       title.replace('"', '""'), origin.replace('"', '""'),
                       entry['audio']['file']))
    (out / 'music-ids.txt').write_text('\n'.join(text) + '\n')
    (out / 'music-ids.csv').write_text('\n'.join(rows) + '\n')


def write_playlist(out, entries):
    lines = ['#EXTM3U']
    for entry in entries:
        title = entry['title'] or ('Slot 0x%s' % entry['slot'])
        seconds = int(round(entry['audio']['duration_seconds']))
        lines.append('#EXTINF:%d,%02X - %s' % (seconds, entry['slot_value'], title))
        lines.append(entry['audio']['file'])
    (out / 'demo-1-1.m3u').write_text('\n'.join(lines) + '\n')


def write_index(out, entries):
    named = sum(1 for entry in entries if entry['title'])
    shortest = min(entry['audio']['duration_seconds'] for entry in entries)
    longest = max(entry['audio']['duration_seconds'] for entry in entries)
    hex_ids = ', '.join('0x%s' % entry['slot'] for entry in entries)
    detail = []
    rows = []
    for entry in entries:
        title = entry['title'] or ('Untitled slot 0x%s' % entry['slot'])
        origin = entry['origin_game'] or '-'
        level = '%02X' % (entry['slot_value'] + 1)
        detail.append('0x%s  song  ->  level byte 0x%s  %s' % (entry['slot'], level, title))
        rows.append(
            '<tr><td><b>0x%s</b></td><td>%d</td><td>0x%s</td><td>%s</td><td>%s</td>'
            '<td>%d</td><td>%.1f s</td>'
            '<td><audio controls preload="none" src="%s"></audio></td></tr>'
            % (entry['slot'], entry['slot_value'], level, title, origin,
               entry['payload']['size'], entry['audio']['duration_seconds'],
               entry['audio']['file']))
    html = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Brutal Mario Demo 1-1 music</title>
<style>
body{font-family:sans-serif;margin:2rem;background:#111;color:#ddd}
table{border-collapse:collapse;width:100%%}
td,th{border-bottom:1px solid #333;padding:.35rem .5rem;text-align:left;vertical-align:middle}
audio{height:2rem}
pre{background:#1b1b1b;padding:1rem;overflow:auto;max-height:16rem}
button{background:#2d2d2d;color:#ddd;border:1px solid #555;padding:.3rem .7rem;margin-right:.5rem}
.note{color:#aaa}
</style></head><body>
<h1>Brutal Mario Demo 1-1 music</h1>
<p>%d custom songs from the song table at $0F:E000. The level data music byte is
the song id plus one. Each file starts at the song introduction and runs for
%.1f to %.1f seconds.</p>
<h2>Music ids</h2>
<p class="note">Reference a song with the hex id: the music table index, the
$0DDA record or the $1DFB request. To set a level header music field, write the
level byte. The level byte is the hex id plus one. The level byte is not a song
id.</p>
<p><button onclick="copyBlock('ids-hex')">Copy id list</button>
<button onclick="copyBlock('ids-detail')">Copy ids, level bytes and names</button></p>
<pre id="ids-hex">%s</pre>
<h2>Ids with song names</h2>
<pre id="ids-detail">%s</pre>
<h2>Tracks</h2>
<table><thead><tr><th>Hex id</th><th>Dec</th><th>Level byte (id+1)</th><th>Title</th>
<th>Origin</th><th>Payload bytes</th><th>Length</th><th>Play</th></tr></thead><tbody>
%s
</tbody></table>
<script>
function copyBlock(id){var el=document.getElementById(id);var text=el.textContent;
if(navigator.clipboard){navigator.clipboard.writeText(text);return;}
var range=document.createRange();range.selectNodeContents(el);
var selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);
document.execCommand('copy');selection.removeAllRanges();}
</script></body></html>
''' % (len(entries), shortest, longest, hex_ids,
       '\n'.join(detail), '\n'.join(rows))
    (out / 'index.html').write_text(html)


def write_readme(out, entries, args):
    named = sum(1 for entry in entries if entry['title'])
    silent = [entry['slot'] for entry in entries if entry['audio']['rms'] < 1.0]
    text = '''# Demo 1-1 music extraction

This directory holds every custom song in the Brutal Mario Demo 1-1 ROM.
The tool that made it is tools/extract_demo11_music.py.

## Contents

| Path | Content |
| --- | --- |
| payload/ | Raw upload payload for each song slot. |
| wav/ | Rendered audio for each song slot. |
| manifest.json | Slot, payload, audio and identity records. |
| checksums.sha256 | SHA-256 values for every payload and WAV. |
| demo-1-1.m3u | Playlist for the WAV files. |
| music-ids.txt | Song id list with titles. |
| music-ids.csv | Song id list for spreadsheets. |
| index.html | Browser player for the WAV files. |

## Scope

The Demo 1-1 ROM keeps a 256-entry music pointer table at $0F:E000.
%d entries are not null. Each entry points at one upload block. The
destination address is $5400 for every entry.

The extraction covers these %d table entries. The engine also has
built-in songs for low ids. Those songs are not table entries and stay
outside this extraction.

## Method

1. The tool reads each upload block from the ROM.
2. It copies the Demo 1-1 ROM and changes one 3-byte pointer. The pointer
   for slot %02X points at the target song. Slot %02X is the song that the
   capture route course requests.
3. The pinned Snes9x reference host enters that course and records the
   audio output.
4. The tool cuts the WAV file at the level-load silence gap. The file then
   starts at the song introduction.
5. The tool writes the payload file and the manifest entry.

The reference host runs with snes9x_echo_buffer_hack=enabled. The legacy
music driver writes echo data outside the shared echo area. With the shared
area, the driver stops after about three seconds. The compatibility option
keeps the driver alive for the whole capture.

## Limits

- Each WAV file is a %d-second excerpt. It is not loop-trimmed. A short
  jingle that stops before the excerpt end is trimmed after its last note.
- The render uses one carrier course. A song that changes by course context
  would need a separate render.
- The titles come from config/music-mapping.json. %d of %d slots have a
  title. Unmapped slots keep the slot id.
- A WAV file is not proof of an audible match with ZSNES 1.51.
- The tool does not extract built-in engine songs or sound effects.

## Reproduce

    python3 tools/extract_demo11_music.py
''' % (len(entries), len(entries), CARRIER_SLOT, CARRIER_SLOT,
       args.seconds, named, len(entries))
    if silent:
        text += '\nSilent renders: %s\n' % ', '.join(silent)
    (out / 'README.md').write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=100,
                        help='WAV length after the cut, default 100')
    parser.add_argument('--jobs', type=int, default=6, help='parallel reference runs')
    parser.add_argument('--slots', help='comma-separated hex slots; default all')
    parser.add_argument('--out', type=Path, default=OUT, help='output directory')
    parser.add_argument('--force', action='store_true', help='replace an existing output tree')
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and not args.force:
        raise SystemExit('%s exists; pass --force to replace it' % out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for path in (SNESREF, CORE):
        if not path.is_file():
            raise SystemExit('missing capture dependency: %s' % path)

    base_rom = read_rom()
    songs = read_table(base_rom)
    titles = read_titles()
    if args.slots:
        wanted = {int(value, 16) for value in args.slots.split(',')}
        songs = [song for song in songs if song['slot'] in wanted]
        missing = wanted - {song['slot'] for song in songs}
        if missing:
            raise SystemExit('slots not in the table: %s'
                             % ', '.join('%02X' % slot for slot in sorted(missing)))

    args.tail = args.seconds * 60 + 200
    entries = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(capture_song, out, song, base_rom, args.seconds, args.tail,
                        titles.get(song['slot'])): song
            for song in songs
        }
        for future in concurrent.futures.as_completed(futures):
            song = futures[future]
            try:
                entry = future.result()
            except Exception as exc:
                raise SystemExit('slot %02X: %s' % (song['slot'], exc))
            entries.append(entry)
            print('slot %02X  %s  %s' % (
                song['slot'],
                entry['title'] or '-',
                '%.1f s rms %.0f' % (entry['audio']['duration_seconds'],
                                     entry['audio']['rms'])))
    entries.sort(key=lambda entry: entry['slot_value'])

    write_manifest(out, entries, base_rom, songs, args)
    write_playlist(out, entries)
    write_ids(out, entries)
    write_index(out, entries)
    write_readme(out, entries, args)
    print('wrote %d songs to %s' % (len(entries), out))


if __name__ == '__main__':
    main()

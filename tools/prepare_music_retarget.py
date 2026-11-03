#!/usr/bin/env python3
"""Prepare the Demo 1-1 level music retarget recipe, ROM and target.

The level data of the Demo 1-1 line came from the legacy demo family, so the
course music objects still request legacy-family song numbers.  The intended
Demo 1-1 slot for each course comes from config/music-level-targets.json.
This tool rewrites the one-byte music parameter of each reviewed music object
and installs the three legacy songs that Demo 1-1 does not carry.

The tool never invents a slot.  A target slot must already hold a song after
the installs, or the entry stays unchanged and is reported.

Actions:
  generate  Write config/restorations/demo11-music-retarget.json.
  prepare   Build local/restoration/demo11-music-retarget/rom.sfc.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from derive_legacy_song import walk
from prepare_rom import verify
from restore_star_world_1 import (apply_code_patches, check_allocation,
                                  lorom, restore_music, sha, write_verified)

BASE = 'demo11-overworld-music'
BASE_OUTPUT = {'size': 4194304,
               'sha256': '4ee6d47e0f3a6bfb5395d7531f683ab8aaedf6b29de15ab877341adbd0b71e8b'}
DONOR = 'cheap-demo'
DONOR_OUTPUT = {'size': 4194304,
                'sha256': 'f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822'}
TARGET = 'demo11-music-retarget'
TARGETS = ROOT / 'config/music-level-targets.json'
RECIPE = ROOT / 'config/restorations' / (TARGET + '.json')
RECORD_TABLE = 0x14AD08

# Legacy song -> Demo 1-1 slot.  (legacy id, group address, group slot, new slot)
PORTS = (
    (0x31, 0x2A8008, 1, 0x35),   # Go Red Team! (Treasure Hunter G)
    (0x49, 0x3FC008, 1, 0x3A),   # Sky Sands (Kirby Air Ride)
    (0x51, 0x448008, 1, 0x3D),   # Dr. Wily Stage 2 (Mega Man 3)
)


def pointer3(rom, offset):
    return int.from_bytes(rom[offset:offset + 3], 'little')


def level_block(rom, room):
    """Return (file offset, LoROM pointer, bytes) of the room layer 1 block."""
    pointer = pointer3(rom, lorom(0x05E000) + room * 3)
    if not pointer:
        return None
    try:
        start = lorom(pointer)
    except ValueError:
        return None
    if start < 8:
        return None
    header = rom[start - 8:start]
    if header[:4] != b'STAR':
        return None
    size = int.from_bytes(header[4:6], 'little') + 1
    if not 0 < size <= 0x8000 or start + size > len(rom):
        return None
    return start, pointer, rom[start:start + size]


def music_objects(block):
    """Return every level music object in one block.

    The object number is ((b0 >> 5) & 3) * 16 + (b1 >> 4), so music object
    0x26 has bits 7-5 of b0 equal to 0x40 and bits 7-4 of b1 equal to 0x60.
    The low bits carry the screen number and the vertical position.
    """
    return [{'index': index, 'param': block[index + 2]}
            for index in range(len(block) - 2)
            if (block[index] & 0xE0) == 0x40 and (block[index + 1] & 0xF0) == 0x60]


def choose_site(entry, objects):
    """Pick the music object that the user report identifies.

    The report gives the song id the build plays, so the matching parameter is
    the song id plus one.  A few rows give the raw parameter; accept that form
    as a second choice.  Never guess between two matches.  An object that
    matches neither form stays unchanged, because a false match would move an
    unrelated byte.
    """
    wrong = entry.get('wrong')
    if wrong is None:
        return None
    value = int(wrong, 16)
    for wanted in (value + 1, value):
        matches = [item for item in objects if item['param'] == wanted]
        if len(matches) == 1:
            return matches[0]
    return None


def free_segments(rom, minimum):
    """Return zeroed within-bank ranges that no RATS block protects."""
    coverage = bytearray(len(rom))
    cursor = 0
    while True:
        cursor = rom.find(b'STAR', cursor)
        if cursor < 0:
            break
        header = rom[cursor:cursor + 8]
        if len(header) == 8:
            count = int.from_bytes(header[4:6], 'little')
            complement = int.from_bytes(header[6:8], 'little')
            if count ^ complement == 0xffff and cursor + count + 9 <= len(rom):
                coverage[cursor:cursor + count + 9] = b'\x01' * (count + 9)
        cursor += 4
    segments, offset = [], 0
    while offset < len(rom):
        if rom[offset] == 0 and not coverage[offset]:
            end = offset
            limit = min(len(rom), (offset // 0x8000 + 1) * 0x8000)
            while end < limit and rom[end] == 0 and not coverage[end]:
                end += 1
            if end - offset >= minimum:
                segments.append((offset, end - offset))
            offset = end
        else:
            offset += 1
    return segments


def allocate(segments, sizes):
    """First-fit packing; every range stays inside one bank."""
    free, result = list(segments), []
    for size in sizes:
        for index, (start, length) in enumerate(free):
            if length >= size:
                result.append((start, size))
                free[index] = (start + size, length - size)
                break
        else:
            raise ValueError('no free within-bank range fits a song payload')
    return result


def free_graphics_record(rom):
    """Return a room graphics record that selects no graphics.

    A music-only recipe still reserves one room graphics record, as the other
    recipes do.  Bit 15 of the first word is the graphics-selection flag.
    """
    for room in range(512):
        offset = lorom(RECORD_TABLE) + room * 32
        if not int.from_bytes(rom[offset:offset + 2], 'little') & 0x8000:
            return room, offset
    raise ValueError('no free room graphics record')


def port_songs(donor, base):
    payloads = []
    for legacy_id, address, slot, new_slot in PORTS:
        group = donor[lorom(address):lorom(address) + 6136]
        config, payload = walk(group, slot, int.from_bytes(group[2:4], 'little'))
        config['id'] = f'{new_slot:02X}'
        config['source_address'] = f'{address:06X}'
        config['source_group'] = {'size': len(group), 'sha256': sha(group)}
        config['pointer_address'] = f'{0x0FE000 + new_slot * 3:06X}'
        config['before'] = '000000'
        config['adapted'] = {'size': len(payload), 'sha256': sha(payload)}
        payloads.append((legacy_id, config, payload))
    ranges = allocate(free_segments(base, 1024), [len(item[2]) + 8 for item in payloads])
    tracks = []
    for (_, config, _), (start, size) in zip(payloads, ranges):
        config['allocation'] = {'offset': start, 'size': size}
        tracks.append(config)
    return tracks


def plan(base, donor):
    """Return the reviewed recipe fields for one base image."""
    tracks = port_songs(donor, base)
    for track in tracks:
        check_allocation(base, track['allocation']['offset'], track['allocation']['size'])
    present = set()
    table = lorom(0x0FE000)
    for slot in range(256):
        if int.from_bytes(base[table + slot * 3:table + slot * 3 + 3], 'big'):
            present.add(slot)
    present.update(int(track['id'], 16) for track in tracks)

    targets = json.loads(TARGETS.read_text())
    patches, skipped = [], []
    for entry in targets['entries']:
        room = int(entry['room'], 16)
        found = level_block(base, room)
        if found is None:
            skipped.append((entry['room'], 'no level block'))
            continue
        _, pointer, block = found
        objects = music_objects(block)
        if not objects:
            skipped.append((entry['room'], 'no music object; the room inherits the parent song'))
            continue
        site = choose_site(entry, objects)
        if site is None:
            skipped.append((entry['room'], 'ambiguous music object'))
            continue
        target = entry['target']
        if target is None:
            skipped.append((entry['room'], 'no Demo 1-1 slot for the intended song'))
            continue
        wanted = int(target, 16)
        if wanted not in present:
            skipped.append((entry['room'], f'target slot {target} is null'))
            continue
        if site['param'] == wanted + 1:
            skipped.append((entry['room'], 'already correct'))
            continue
        # The level pointer keeps the bank form the game uses; a level in a
        # mirrored bank 0x80-0xFF stays in that form.
        patches.append({'address': f'{pointer + site["index"] + 2:06X}',
                        'before': f'{site["param"]:02x}',
                        'after': f'{wanted + 1:02x}',
                        'role': f'Room {entry["room"]} course music: '
                                f'{site["param"] - 1:02X} -> {wanted:02X}.'})
    room, record_offset = free_graphics_record(base)
    allocation = max(tracks, key=lambda item: item['allocation']['size'])['allocation']
    return {'tracks': tracks, 'patches': patches, 'skipped': skipped,
            'record_room': room, 'record_offset': record_offset,
            'allocation': allocation}


def recipe(base, result):
    record = result['record_offset']
    address = ((record // 0x8000) << 16) | 0x8000 | (record % 0x8000)
    return {
        'schema': 1,
        'id': TARGET,
        'target': 'Brutal Mario Demo11 Level Music Retarget',
        'recipient': 'demo-1-1',
        'donor': DONOR,
        'base_restoration': BASE,
        'base_output': BASE_OUTPUT,
        'music_retarget': {'tool': 'prepare_music_retarget.py',
                           'targets': 'config/music-level-targets.json'},
        'scope': 'Rewrite the course music parameter of every reviewed level music '
                 'object from the legacy-family song number to the intended Demo 1-1 '
                 'slot, and install the four legacy songs that Demo 1-1 does not carry. '
                 'No level layout, exit, sprite or engine code changes.',
        'gfx_record': {'address': f'{address:06X}',
                       'before': base[record:record + 32].hex()},
        'allocation': {'offset': result['allocation']['offset'],
                       'size': result['allocation']['size'], 'fill': 0},
        'assets': [],
        'music_tracks': result['tracks'],
        'code_patches': result['patches'],
    }


def base_recipe():
    return json.loads((ROOT / 'config/restorations' / (BASE + '.json')).read_text())


def song_pointer(track):
    """Return the 3-byte song table entry for one installed track.

    The cartridge reaches file banks 0x7E and 0x7F only through the
    0x80-0xFF mirror, the same way the level data pointers do.
    """
    start = track['allocation']['offset']
    bank = (start + 8) // 0x8000
    if bank >= 0x7E:
        bank |= 0x80
    address = (bank << 16) | 0x8000 | ((start + 8) & 0x7fff)
    return address.to_bytes(3, 'big')


def build(base, donor, config):
    out = bytearray(base)
    for track in config['music_tracks']:
        restore_music(donor, out, track)
        pointer = lorom(int(track['pointer_address'], 16))
        out[pointer:pointer + 3] = song_pointer(track)
    apply_code_patches(out, config)
    if config.get('level_music_objects'):
        import prepare_music_objects
        prepare_music_objects.apply(out, config)
    return bytes(out)


def generate():
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    verify(base, BASE_OUTPUT, 'base restoration')
    donor = (ROOT / 'local/content-versions' / DONOR / 'rom.sfc').read_bytes()
    verify(donor, DONOR_OUTPUT, DONOR)
    result = plan(base, donor)
    config = recipe(base, result)
    inherited = base_recipe().get('native_sprite_gap')
    if inherited:
        # The base ROM runs the base native content, so this target mounts the
        # same packs.  The pack files are data, not ROM-derived.
        config['native_sprite_gap'] = inherited
    # The object moves depend on the song installs and the selection patches,
    # so they are planned on the built image and recorded in the recipe.
    import prepare_music_objects
    config['level_music_objects'] = prepare_music_objects.plan(bytearray(build(base, donor, dict(config, level_music_objects=[]))))
    rom = build(base, donor, config)
    config['output'] = {'size': len(rom), 'sha256': sha(rom)}
    RECIPE.write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps({'target': TARGET, 'patches': len(config['code_patches']),
                      'skipped': len(result['skipped']),
                      'graphics_record_room': f'{result["record_room"]:03X}',
                      'allocations': [{'slot': t['id'],
                                       'offset': f'{t["allocation"]["offset"]:06X}',
                                       'size': t['allocation']['size']}
                                      for t in config['music_tracks']],
                      'rom': config['output']}, indent=1))
    for room, reason in result['skipped']:
        print(f'  skipped {room}: {reason}')
    return config


def prepare(target=TARGET):
    config = json.loads(RECIPE.read_text())
    if config['id'] != target:
        raise ValueError('music retarget config identity differs')
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    verify(base, config['base_output'], 'music retarget base')
    donor = (ROOT / 'local/content-versions' / config['donor'] / 'rom.sfc').read_bytes()
    verify(donor, DONOR_OUTPUT, config['donor'])
    rom = build(base, donor, config)
    verify(rom, config['output'], config['target'])
    directory = ROOT / 'local/restoration' / target
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'rom.sfc', rom)
    if config.get('native_sprite_gap'):
        import native_sprite_gap
        source = ROOT / 'local/restoration' / BASE
        for pack in native_sprite_gap.packs(target):
            data = (source / pack['pack_file']).read_bytes()
            verify(data, pack, pack['variable'])
            write_verified(directory / pack['pack_file'], data)
    manifest = dict(config, recipe_sha256=sha(Path(__file__).read_bytes()),
                    input_sha256={'base': sha(base), 'donor': sha(donor)})
    (directory / 'input-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{directory.relative_to(ROOT)}/rom.sfc: {sha(rom)}')
    return rom


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('generate', 'prepare', 'all'), nargs='?',
                        default='all')
    args = parser.parse_args()
    if args.action in ('generate', 'all'):
        generate()
    if args.action in ('prepare', 'all'):
        prepare()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Prepare isolated, hash-pinned Star World restoration candidates."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_rom import verify
from restoration_targets import RESTORATIONS

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lorom(address):
    bank, low = address >> 16, address & 0xffff
    if not 0 <= bank <= 0xff or bank in (0x7e, 0x7f) or low < 0x8000:
        raise ValueError(f'not mapped LoROM: {address:06X}')
    return (bank & 0x7f) * 0x8000 + (low & 0x7fff)


def lz2(rom, address, limit=4096):
    """Decode the game's LZ2 commands; reject overflow and invalid backreferences.

    Physical offsets remain contiguous across LoROM $FFFF -> next-bank $8000.
    The returned source slice includes the mandatory stream terminator.
    """
    start = cursor = lorom(address)
    out = bytearray()

    def fetch():
        nonlocal cursor
        if cursor >= len(rom):
            raise ValueError('truncated LZ2 stream')
        value = rom[cursor]
        cursor += 1
        return value

    while True:
        control = fetch()
        if control == 0xff:
            return bytes(out), rom[start:cursor]
        command, length = control >> 5, (control & 31) + 1
        if command == 7:
            command = (control >> 2) & 7
            length = ((control & 3) << 8 | fetch()) + 1
        if len(out) + length > limit:
            raise ValueError('LZ2 output exceeds graphics buffer')
        if command == 0:
            out.extend(fetch() for _ in range(length))
        elif command == 1:
            out.extend(bytes([fetch()]) * length)
        elif command == 2:
            first, second = fetch(), fetch()
            out.extend(first if i % 2 == 0 else second for i in range(length))
        elif command == 3:
            first = fetch()
            out.extend((first + i) & 255 for i in range(length))
        else:
            offset = fetch() << 8 | fetch()
            for _ in range(length):
                if offset >= len(out):
                    raise ValueError('LZ2 backreference outside decoded data')
                out.append(out[offset])
                offset += 1


def pointer_offset(gfx):
    if not 0x100 <= gfx <= 0xfff:
        raise ValueError('extended graphics ID outside table')
    return lorom(0x148008) + (gfx - 0x100) * 3


def graphics_pointer(rom, gfx):
    """Resolve the three verified LM graphics table formats; destinations stay extended."""
    if 0 <= gfx < 0x32:
        return sum(rom[lorom(address) + gfx] << shift for address, shift in
                   ((0x00B992, 0), (0x00B9C4, 8), (0x00B9F6, 16)))
    if 0x80 <= gfx < 0x100:
        offset = lorom(0x0FF600) + (gfx - 0x80) * 3
    else:
        offset = pointer_offset(gfx)
    return int.from_bytes(rom[offset:offset+3], 'little')


def check_allocation(recipient, start, size):
    end = start + size
    if (end > len(recipient) or start // 0x8000 != (end - 1) // 0x8000 or
            recipient[start:end] != bytes(size)):
        raise ValueError('allocation differs from the reviewed empty bank range')
    cursor = 0
    while (cursor := recipient.find(b'STAR', cursor)) >= 0:
        header = recipient[cursor:cursor+8]
        if len(header) == 8:
            count = int.from_bytes(header[4:6], 'little')
            complement = int.from_bytes(header[6:8], 'little')
            if count ^ complement == 0xffff and cursor < end and cursor + count + 9 > start:
                raise ValueError('allocation overlaps a protected RATS block')
        cursor += 4


def sprite_rooms(rom, sprite_id):
    """Audit the recipient's 512 three-byte sprite lists before enabling a slot."""
    rooms = []
    for room in range(512):
        word = lorom(0x05ec00) + room * 2
        address = (int.from_bytes(rom[word:word+2], 'little') |
                   rom[lorom(0x0ef100) + room] << 16)
        cursor = lorom(address) + 1  # Skip sprite-list header.
        for _ in range(1024):
            if cursor + 3 > len(rom):
                raise ValueError('truncated sprite list')
            if rom[cursor] == 0xff:
                break
            if rom[cursor] & 8 and rom[cursor+2] == sprite_id:
                rooms.append(room)
            cursor += 3
        else:
            raise ValueError('unterminated sprite list')
    return sorted(set(rooms))


def restore_sprite(recipient, donor, out, config):
    sprite_id = int(config['id'], 16)
    if sprite_rooms(recipient, sprite_id) != config['rooms']:
        raise ValueError('custom sprite has unexpected room dependencies')
    source = int(config['source_address'], 16)
    destination = int(config['destination_address'], 16)
    if source & 0xffff != destination & 0xffff:
        raise ValueError('custom sprite relocation changes bank-local addresses')
    if (destination >> 16 & 0x7f) >= 0x40:
        raise ValueError('custom sprite data bank must retain low WRAM mirrors')
    size = config['block']['size']
    block = donor[lorom(source):lorom(source)+size]
    verify(block, config['block'], 'custom sprite code')
    count = int.from_bytes(block[4:6], 'little')
    if (block[:4] != b'STAR' or count + 9 != size or
            count ^ int.from_bytes(block[6:8], 'little') != 0xffff):
        raise ValueError('invalid custom sprite RATS block')
    check_allocation(out, lorom(destination), size)
    for item in config['shared_dependencies']:
        offset = lorom(int(item['address'], 16))
        for data in (recipient, donor):
            verify(data[offset:offset+item['size']], item, 'custom sprite shared dependency')
    for item in config.get('versioned_dependencies', []):
        data = {'recipient': recipient, 'donor': donor}[item['role']]
        offset = lorom(int(item['address'], 16))
        verify(data[offset:offset+item['size']], item, 'custom sprite versioned dependency')
    source_record = lorom(int(config['source_record_address'], 16))
    record = bytearray(donor[source_record:source_record+16])
    if record.hex() != config['source_record']:
        raise ValueError('custom sprite donor record changed')
    for index in (8, 11):
        address = int.from_bytes(record[index:index+3], 'little')
        if not source + 8 <= address < source + size:
            raise ValueError('custom sprite entry is outside its code block')
        record[index+2] = destination >> 16
    offset = lorom(int(config['destination_record_address'], 16))
    if out[offset:offset+16].hex() != config['before']:
        raise ValueError('custom sprite destination slot is occupied')
    out[lorom(destination):lorom(destination)+size] = block
    out[offset:offset+16] = record


def adapt_music(group, config):
    """Extract one reviewed song from a donor's four-song group.

    Only this song's reviewed command subset and intro/loop header are
    supported. Walk reachable tracks/subroutines; never relocate raw matches
    inside note parameters or unused songs.
    """
    source, destination = config['source_base'], config['destination_base']
    count = int.from_bytes(group[:2], 'little')
    trailer_size = config.get('source_trailer_size', 4)
    sequence_offset = config.get('sequence_offset', 0)
    data_offset = config.get('source_data_offset', 64)
    data_size = config['song_size'] - 64
    if (trailer_size not in (2, 4) or len(group) != count + 4 + trailer_size or
            group[2:4] != source.to_bytes(2, 'little') or
            group[-trailer_size:] != bytes(trailer_size) or data_size <= 0 or sequence_offset < 0 or
            sequence_offset + 8 > data_offset or data_offset + data_size > count):
        raise ValueError('unexpected music upload group')
    sequence_source, data_source = source + sequence_offset, source + data_offset
    song = bytearray(group[4+sequence_offset:12+sequence_offset] + bytes(56) +
                     group[4+data_offset:4+data_offset+data_size])
    patterns = sorted({int.from_bytes(song[i:i+2], 'little') for i in (0, 2)})
    pattern_count = config.get('pattern_count', 1)
    if (pattern_count not in (1, 2) or len(patterns) != pattern_count or
            song[4:8] != b'\xff\x00' + (sequence_source+2).to_bytes(2, 'little')):
        raise ValueError('unsupported music sequence header')
    relocations = [0, 2, 6]

    def offset(address, size=1):
        if sequence_source <= address and address + size <= sequence_source + 8:
            return address - sequence_source
        if data_source <= address and address + size <= data_source + data_size:
            return 64 + address - data_source
        raise ValueError('music pointer escapes selected song')

    def check_track_cursor(cursor, size=1):
        if cursor < 64 or cursor + size > len(song):
            raise ValueError('music pointer escapes selected song')

    lengths = {0xda: 1, 0xdb: 1, 0xde: 1, 0xdf: 1, 0xe0: 1, 0xe2: 1, 0xe7: 1,
               0xe9: 3, 0xef: 3, 0xf0: 0, 0xf1: 3, 0xf2: 3}
    visited = set()
    pending = []
    for address in patterns:
        pattern = offset(address, 16)
        for i in range(pattern, pattern+16, 2):
            address = int.from_bytes(song[i:i+2], 'little')
            if address:
                pending.append(offset(address))
                relocations.append(i)
    while pending:
        cursor = pending.pop()
        while cursor not in visited:
            check_track_cursor(cursor)
            visited.add(cursor)
            command = song[cursor]
            cursor += 1
            if command == 0:
                break
            if command < 0x80:
                check_track_cursor(cursor)
                if song[cursor] < 0x80:
                    cursor += 1  # Optional note gate/volume after duration.
            elif command >= 0xda:
                if command not in lengths:
                    raise ValueError('unsupported music command')
                check_track_cursor(cursor, lengths[command])
                if command == 0xe9:
                    pending.append(offset(int.from_bytes(song[cursor:cursor+2], 'little')))
                    relocations.append(cursor)
                cursor += lengths[command]
    if sorted(relocations) != config['relocations']:
        raise ValueError('music pointer graph differs from reviewed relocations')
    for i in relocations:
        address = int.from_bytes(song[i:i+2], 'little')
        song[i:i+2] = (offset(address)+destination).to_bytes(2, 'little')
    return len(song).to_bytes(2, 'little') + destination.to_bytes(2, 'little') + song + bytes(4)


def raw_group_song(group, slot):
    """Build a song payload that keeps the group data at its own base.

    The donor group already stores a sequence header for each slot and a data
    area at source base + 64. When the destination base equals the source
    base, the pointers need no relocation. The payload keeps the data area
    unchanged. This bypasses the command-graph walk for songs that use
    commands outside the reviewed adapt_music subset.
    """
    count = int.from_bytes(group[:2], 'little')
    base = int.from_bytes(group[2:4], 'little')
    if len(group) != count + 8 or slot not in (0, 1, 2, 3):
        raise ValueError('unexpected raw music group')
    sequence = group[4 + 8 * slot:12 + 8 * slot]
    data = group[4 + 64:4 + count]
    song = sequence + bytes(56) + data
    return len(song).to_bytes(2, 'little') + base.to_bytes(2, 'little') + song + bytes(4)


def restore_music(donor, out, config):
    source = lorom(int(config['source_address'], 16))
    group = donor[source:source+config['source_group']['size']]
    verify(group, config['source_group'], 'donor music group')
    if config.get('raw'):
        payload = raw_group_song(group, config['sequence_offset'] // 8)
    else:
        payload = adapt_music(group, config)
    verify(payload, config['adapted'], 'adapted music')
    start, size = config['allocation']['offset'], config['allocation']['size']
    check_allocation(out, start, size)
    if len(payload) + 8 > size:
        raise ValueError('music exceeds reserved allocation')
    pointer = lorom(int(config['pointer_address'], 16))
    if out[pointer:pointer+3].hex() != config['before']:
        raise ValueError('music destination slot is occupied')
    count = len(payload) - 1
    out[start:start+len(payload)+8] = (b'STAR' + count.to_bytes(2, 'little') +
                                     (count ^ 0xffff).to_bytes(2, 'little') + payload)
    address = ((start+8) // 0x8000) << 16 | 0x8000 | ((start+8) & 0x7fff)
    # The recipient music table stores bank, high address, low address.
    out[pointer:pointer+3] = address.to_bytes(3, 'big')


def apply_code_patches(out, config):
    """Replace reviewed instruction bytes. The width stays the same."""
    for patch in config.get('code_patches', []):
        offset = lorom(int(patch['address'], 16))
        before = bytes.fromhex(patch['before'])
        after = bytes.fromhex(patch['after'])
        if len(before) != len(after) or not before:
            raise ValueError('code patch must keep the instruction width')
        if out[offset:offset+len(before)] != before:
            raise ValueError('code patch site changed')
        out[offset:offset+len(after)] = after


def restore_raw_blocks(donor, out, blocks):
    """Install pinned binary streams, including backgrounds with embedded FF.

    A full-bank clone may put its RATS header in the preceding bank. Both
    ranges must be empty and unprotected, and physically contiguous.
    """
    for item in blocks:
        if ('source_address' in item) == ('bytes' in item):
            raise ValueError('raw block requires exactly one source')
        if 'bytes' in item:
            blob = bytearray.fromhex(item['bytes'])
        else:
            source = lorom(int(item['source_address'], 16))
            blob = bytearray(donor[source:source+item['data']['size']])
        verify(blob, item['data'], 'raw source block')
        for patch in item.get('edits', []):
            offset = patch['offset']
            before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
            if (not before or len(before) != len(after) or offset < 0 or
                    blob[offset:offset+len(before)] != before):
                raise ValueError('raw block edit differs from reviewed bytes')
            blob[offset:offset+len(before)] = after
        if 'adapted' in item:
            verify(blob, item['adapted'], 'adapted raw block')
        start = lorom(int(item['destination_address'], 16))
        header = lorom(int(item['rats_address'], 16))
        if header + 8 != start or not 0 < len(blob) <= 0x8000:
            raise ValueError('raw block has invalid RATS geometry')
        check_allocation(out, header, 8)
        check_allocation(out, start, len(blob))
        count = len(blob)-1
        out[header:start] = b'STAR'+count.to_bytes(2, 'little')+(count ^ 0xffff).to_bytes(2, 'little')
        out[start:start+len(blob)] = blob



def file_to_lorom(offset):
    """Return the LoROM address that maps the given file offset."""
    if offset < 0 or offset >= 0x400000:
        raise ValueError('file offset outside the cartridge')
    bank = offset // 0x8000
    return (bank << 16) | 0x8000 | (offset % 0x8000)


def apply_relocations(out, config):
    """Move reviewed blocks and re-point their reviewed pointer slots."""
    for item in config.get('relocations', []):
        source = item['source_offset']
        destination = item['destination_offset']
        size = item['size']
        verify(bytes(out[source:source + size]), item, 'relocated block source')
        if destination // 0x8000 != (destination + size - 1) // 0x8000:
            raise ValueError('relocated block crosses a bank boundary')
        check_allocation(out, destination, size)
        slot = item.get('pointer_offset')
        if slot is not None:
            before = bytes.fromhex(item['pointer_before'])
            after = bytes.fromhex(item['pointer_after'])
            if out[slot:slot + len(before)] != before:
                raise ValueError('relocated pointer slot changed')
            out[slot:slot + len(after)] = after
        out[destination:destination + size] = out[source:source + size]
        if item.get('zero_source', True):
            out[source:source + size] = bytes(size)


def make_candidate(recipient, donor, config):
    start, size = config['allocation']['offset'], config['allocation']['size']
    end = start + size
    check_allocation(recipient, start, size)
    records = []
    for item in [config['gfx_record']] + config.get('additional_gfx_records', []):
        record = lorom(int(item['address'], 16))
        before = bytes.fromhex(item['before'])
        if recipient[record:record+len(before)] != before:
            raise ValueError('room graphics configuration changed')
        records.append(record)
    out, cursor, assets = bytearray(recipient), start, []
    apply_relocations(out, config)
    restore_raw_blocks(donor, out, config.get('raw_blocks', []))
    apply_code_patches(out, {'code_patches': config.get('pre_asset_patches', [])})
    for item in config['assets']:
        old_id, new_id = int(item['source_id'], 16), int(item['target_id'], 16)
        selected_rooms = []
        for room in range(512):
            header = lorom(0x14ad08) + room * 32
            if int.from_bytes(recipient[header:header+2], 'little') & 0x8000:
                words = [int.from_bytes(recipient[header+i:header+i+2], 'little')
                         for i in range(2, 20, 2)]
                if new_id in words:
                    selected_rooms.append(room)
        shared = item.get('global_pointer', False)
        if shared:
            if (old_id != new_id or selected_rooms != item['rooms'] or
                    'record_offset' in item or 'record_addresses' in item):
                raise ValueError('shared graphics have unexpected room dependencies or selection edits')
        elif selected_rooms:
            raise ValueError('destination graphics ID is selected by an existing room')
        source_pointer = graphics_pointer(donor, old_id)
        if source_pointer != int(item['source_address'], 16):
            raise ValueError('donor graphics pointer changed')
        decoded, compressed = lz2(donor, source_pointer)
        verify(decoded, item['decoded'], 'decoded graphics')
        verify(compressed, item['compressed'], 'compressed graphics')
        destination_pointer = pointer_offset(new_id)
        if out[destination_pointer:destination_pointer+3] != b'\xff' * 3:
            raise ValueError('destination graphics slot is occupied or repeated')
        chosen = [lorom(int(address, 16)) for address in item.get('record_addresses', [])]
        if 'record_addresses' in item and (not chosen or len(set(chosen)) != len(chosen) or
                                            any(record not in records for record in chosen)):
            raise ValueError('graphics asset selects an unreviewed room record')
        words = [] if shared else [record + item['record_offset'] for record in (chosen or records)]
        if any(int.from_bytes(out[word:word+2], 'little') != old_id for word in words):
            raise ValueError('room does not select the expected source ID')
        stop = cursor + len(compressed) + 8
        if stop > end:
            raise ValueError('graphics exceed reserved allocation')
        count = len(compressed) - 1
        out[cursor:stop] = (b'STAR' + count.to_bytes(2, 'little') +
                            (count ^ 0xffff).to_bytes(2, 'little') + compressed)
        address = ((cursor + 8) // 0x8000) << 16 | 0x8000 | ((cursor + 8) & 0x7fff)
        out[destination_pointer:destination_pointer+3] = address.to_bytes(3, 'little')
        for word in words:
            out[word:word+2] = new_id.to_bytes(2, 'little')
        check, stream = lz2(out, address)
        if check != decoded or stream != compressed:
            raise ValueError('relocated graphics differ from donor')
        assets.append(dict(item, destination_address=f'{address:06X}',
                           rats_offset=cursor, pointer_offset=destination_pointer,
                           room_word_offset=words[0] if words else None,
                           additional_room_word_offsets=words[1:]))
        cursor = stop
    for item in config.get('level_data', []):
        slot = lorom(int(item['table'], 16)) + int(item['room'], 16) * 3
        donor_ptr = int.from_bytes(donor[slot:slot+3], 'little')
        recip_ptr = int.from_bytes(recipient[slot:slot+3], 'little')
        if donor_ptr != int(item['source_address'], 16):
            raise ValueError('donor level pointer changed')
        if recip_ptr != int(item['current_address'], 16):
            raise ValueError('recipient level pointer changed')
        raw = donor[lorom(donor_ptr):lorom(donor_ptr) + 0x8000]
        term = raw.find(b'\xff')
        if term < 0:
            raise ValueError('level data has no terminator in its bank')
        blob = raw[:term + 1]
        verify(blob, item['data'], 'level data')
        stop = cursor + len(blob) + 8
        if stop > end:
            raise ValueError('level data exceeds reserved allocation')
        count = len(blob) - 1
        out[cursor:stop] = (b'STAR' + count.to_bytes(2, 'little') +
                            (count ^ 0xffff).to_bytes(2, 'little') + blob)
        address = ((cursor + 8) // 0x8000) << 16 | 0x8000 | ((cursor + 8) & 0x7fff)
        out[slot:slot+3] = address.to_bytes(3, 'little')
        cursor = stop
    if config.get('custom_sprite'):
        restore_sprite(recipient, donor, out, config['custom_sprite'])
    for item in config.get('custom_sprites', []):
        restore_sprite(recipient, donor, out, item)
    if config.get('music'):
        restore_music(donor, out, config['music'])
    for music in config.get('music_tracks', []):
        restore_music(donor, out, music)
    apply_code_patches(out, config)
    verify(out, config['output'], config['target'])
    return bytes(out), assets


def write_verified(path, data):
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f'refusing to replace a different file: {path}')
    path.write_bytes(data)


def prepare(target='star-world-1', ancestors=()):
    if target not in RESTORATIONS or target in ancestors:
        raise ValueError('unknown or cyclic restoration dependency')
    config_path = ROOT / 'config/restorations' / (target + '.json')
    config = json.loads(config_path.read_text())
    if config['id'] != target:
        raise ValueError('restoration config identity differs from target')
    versions = {v['id']: v for v in json.loads((ROOT / 'config/content-versions.json').read_text())['versions']}
    bodies = []
    for role in ('recipient', 'donor'):
        version = config[role]
        data = (ROOT / 'local/content-versions' / version / 'rom.sfc').read_bytes()
        verify(data, versions[version]['output'], role)
        bodies.append(data)
    input_sha256 = {role: sha(data) for role, data in zip(('recipient', 'donor'), bodies)}
    if config.get('base_restoration'):
        base = prepare(config['base_restoration'], ancestors + (target,))
        verify(base, config['base_output'], 'base restoration')
        bodies[0] = base
        input_sha256['base_restoration'] = sha(base)
    candidate, assets = make_candidate(*bodies, config)
    directory = ROOT / 'local/restoration' / target
    directory.mkdir(parents=True, exist_ok=True)
    manifest = dict(config, assets=assets, recipe_sha256=sha(Path(__file__).read_bytes()),
                    config_sha256=sha(config_path.read_bytes()), input_sha256=input_sha256)
    write_verified(directory / 'rom.sfc', candidate)
    # Receipts can change with recipe comments; the ROM is immutable by identity.
    (directory / 'input-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{directory.relative_to(ROOT)}/rom.sfc: {sha(candidate)}')
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=tuple(RESTORATIONS), default='star-world-1')
    args = parser.parse_args()
    prepare(args.target)


if __name__ == '__main__':
    main()

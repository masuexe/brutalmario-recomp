#!/usr/bin/env python3
"""Prepare the isolated, hash-pinned Star World 1 restoration candidate."""
import hashlib
import json
from pathlib import Path

from prepare_rom import verify

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/restorations/star-world-1.json'


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


def make_candidate(recipient, donor, config):
    start, size = config['allocation']['offset'], config['allocation']['size']
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
    record = lorom(int(config['gfx_record']['address'], 16))
    before = bytes.fromhex(config['gfx_record']['before'])
    if recipient[record:record+len(before)] != before:
        raise ValueError('room graphics configuration changed')
    out, cursor, assets = bytearray(recipient), start, []
    for item in config['assets']:
        old_id, new_id = int(item['source_id'], 16), int(item['target_id'], 16)
        for room in range(512):
            header = lorom(0x14ad08) + room * 32
            if int.from_bytes(recipient[header:header+2], 'little') & 0x8000:
                words = [int.from_bytes(recipient[header+i:header+i+2], 'little')
                         for i in range(2, 20, 2)]
                if new_id in words:
                    raise ValueError('destination graphics ID is selected by an existing room')
        source_pointer = int.from_bytes(donor[pointer_offset(old_id):pointer_offset(old_id)+3], 'little')
        if source_pointer != int(item['source_address'], 16):
            raise ValueError('donor graphics pointer changed')
        decoded, compressed = lz2(donor, source_pointer)
        verify(decoded, item['decoded'], 'decoded graphics')
        verify(compressed, item['compressed'], 'compressed graphics')
        destination_pointer = pointer_offset(new_id)
        if out[destination_pointer:destination_pointer+3] != b'\xff' * 3:
            raise ValueError('destination graphics slot is occupied or repeated')
        word = record + item['record_offset']
        if int.from_bytes(out[word:word+2], 'little') != old_id:
            raise ValueError('room does not select the expected source ID')
        stop = cursor + len(compressed) + 8
        if stop > end:
            raise ValueError('graphics exceed reserved allocation')
        count = len(compressed) - 1
        out[cursor:stop] = (b'STAR' + count.to_bytes(2, 'little') +
                            (count ^ 0xffff).to_bytes(2, 'little') + compressed)
        address = ((cursor + 8) // 0x8000) << 16 | 0x8000 | ((cursor + 8) & 0x7fff)
        out[destination_pointer:destination_pointer+3] = address.to_bytes(3, 'little')
        out[word:word+2] = new_id.to_bytes(2, 'little')
        check, stream = lz2(out, address)
        if check != decoded or stream != compressed:
            raise ValueError('relocated graphics differ from donor')
        assets.append(dict(item, destination_address=f'{address:06X}',
                           rats_offset=cursor, pointer_offset=destination_pointer,
                           room_word_offset=word))
        cursor = stop
    verify(out, config['output'], config['target'])
    return bytes(out), assets


def write_verified(path, data):
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f'refusing to replace a different file: {path}')
    path.write_bytes(data)


def main():
    config = json.loads(CONFIG.read_text())
    versions = {v['id']: v for v in json.loads((ROOT / 'config/content-versions.json').read_text())['versions']}
    bodies = []
    for role in ('recipient', 'donor'):
        version = config[role]
        data = (ROOT / 'local/content-versions' / version / 'rom.sfc').read_bytes()
        verify(data, versions[version]['output'], role)
        bodies.append(data)
    candidate, assets = make_candidate(*bodies, config)
    directory = ROOT / 'local/restoration/star-world-1'
    directory.mkdir(parents=True, exist_ok=True)
    manifest = dict(config, assets=assets, recipe_sha256=sha(Path(__file__).read_bytes()),
                    config_sha256=sha(CONFIG.read_bytes()),
                    input_sha256={role: sha(data) for role, data in zip(('recipient', 'donor'), bodies)})
    write_verified(directory / 'rom.sfc', candidate)
    # Receipts can change with recipe comments; the ROM is immutable by identity.
    (directory / 'input-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{directory.relative_to(ROOT)}/rom.sfc: {sha(candidate)}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Discover alternate Special Warp Star programs in prepared local donors.

The output is a structural inventory, not proof of playable room correspondence
or a completed boss. ROM, patch, archive and source inputs are read-only.
"""
import argparse
import bisect
import json
from pathlib import Path
import zipfile

from prepare_rom import verify
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
KNOWN_PROGRAM = 'd9ac74c7c0f05ba26dcfff5c2a09da94dff42d57cafe25361c4343fdcd1f448f'
MARKERS = {
    'boss_counter_load': bytes.fromhex('af28ff7f'),
    'boss_counter_store': bytes.fromhex('8f28ff7f'),
    'graphics_slot_1d4': bytes.fromhex('a9d4018f90ff7f'),
    'item_and_boss_room_init': bytes.fromhex('ad0b01c978'),
}


def rats_blocks(rom):
    blocks, cursor = [], 0
    while (cursor := rom.find(b'STAR', cursor)) >= 0:
        if cursor + 8 <= len(rom):
            count = int.from_bytes(rom[cursor+4:cursor+6], 'little')
            complement = int.from_bytes(rom[cursor+6:cursor+8], 'little')
            end = cursor + count + 9
            if count ^ complement == 0xffff and end <= len(rom):
                blocks.append((cursor, end))
        cursor += 4
    return blocks


def sprite_table(rom):
    """Derive the table from the installed constructor, not a fixed slot bank."""
    hook = rom[lorom(0x0187a7):lorom(0x0187a7)+4]
    if hook[0] != 0x5c:
        raise ValueError('unsupported SpriteTool constructor hook')
    constructor = int.from_bytes(hook[1:], 'little')
    body = rom[lorom(constructor):lorom(constructor)+160]
    store = body.index(bytes.fromhex('8f1cab7f'))
    if (store < 3 or body[store-3] != 0xb9 or
            bytes.fromhex('0a0a0a0a') not in body[:store] or
            bytes.fromhex('4bab') not in body[:store]):
        raise ValueError('unsupported constructor table or record stride')
    table = (constructor & 0xff0000) | int.from_bytes(body[store-2:store], 'little')
    if lorom(table) + 256 * 16 > len(rom):
        raise ValueError('SpriteTool table exceeds ROM')
    return constructor, body, table


def audit_version(version, rom=None):
    if rom is None:
        rom = (ROOT / 'local/content-versions' / version['id'] / 'rom.sfc').read_bytes()
        verify(rom, version['output'], version['id'])
    constructor, body, table = sprite_table(rom)
    blocks = rats_blocks(rom)
    starts = [start for start, _ in blocks]

    def owner(address):
        try:
            offset = lorom(address)
        except ValueError:
            return None
        # A nested valid header must not hide an enclosing code block.
        for index in range(bisect.bisect_right(starts, offset)-1, -1, -1):
            if offset < blocks[index][1]:
                return blocks[index]
        return None

    installed = []
    for slot in range(256):
        start = lorom(table) + slot * 16
        record = rom[start:start+16]
        if record[0] != 1:
            continue
        init = int.from_bytes(record[8:11], 'little')
        main = int.from_bytes(record[11:14], 'little')
        installed.append({'slot': f'{slot:02X}', 'init_block': owner(init),
                          'main_block': owner(main)})

    candidates = []
    for start, end in blocks:
        block = rom[start:end]
        matched = [name for name, pattern in MARKERS.items() if pattern in block]
        digest = sha(block)
        if digest != KNOWN_PROGRAM and len(matched) < 3:
            continue
        slots = [entry['slot'] for entry in installed
                 if (start, end) in (entry['init_block'], entry['main_block'])]
        candidates.append({
            'physical_offset': start, 'size': end-start, 'sha256': digest,
            'exact_accepted_star_program': digest == KNOWN_PROGRAM,
            'markers': matched, 'installed_slots': slots,
        })

    unprotected = {}
    for name, pattern in MARKERS.items():
        cursor, offsets = 0, []
        while (cursor := rom.find(pattern, cursor)) >= 0:
            if not any(start <= cursor < end for start, end in blocks):
                offsets.append(cursor)
            cursor += 1
        unprotected[name] = offsets

    return {
        'id': version['id'], 'rom_sha256': sha(rom),
        'constructor_address': f'{constructor:06X}', 'constructor_sha256': sha(body),
        'derived_table_address': f'{table:06X}', 'stride': 16,
        'installed_type1_records': len(installed), 'valid_rats_blocks': len(blocks),
        'candidate_programs': candidates, 'unprotected_marker_offsets': unprotected,
    }


def audit_sources():
    directory = ROOT.parent / 'references/brutalmario-data'
    sources, archive_entries = [], []
    for path in sorted(directory.rglob('star.asm')):
        raw = path.read_bytes()
        text = raw.decode('shift_jis', errors='replace')
        sources.append({
            'path': str(path.relative_to(directory)), 'sha256': sha(raw),
            'size': len(raw), 'has_boss_dispatch': 'MODE_DO' in text,
            'has_mode2_cycle': 'MODE2_4' in text, 'has_mode3_label': 'MODE3' in text,
            'mentions_goal_timer': '$1493' in text, 'mentions_stage_clear': '$13CE' in text,
        })
    for path in sorted(directory.glob('*.zip')):
        with zipfile.ZipFile(path) as archive:
            for entry in archive.namelist():
                if not entry.lower().endswith('/star.asm'):
                    continue
                raw = archive.read(entry)
                archive_entries.append({
                    'archive': path.name, 'entry': entry, 'size': len(raw),
                    'sha256': sha(raw),
                    'matches_extracted_source': any(source['sha256'] == sha(raw)
                                                    for source in sources),
                })
    return sources, archive_entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'local/reports/center-alternate-program-audit.json')
    parser.add_argument('--extra', action='append', default=[], metavar='ID=PATH',
                        help='also audit an unregistered ROM image; it is hashed but not '
                             'verified against a pinned patch receipt')
    args = parser.parse_args()
    metadata = json.loads((ROOT / 'config/content-versions.json').read_text())
    versions = []
    for version in metadata['versions']:
        result = audit_version(version)
        versions.append(result)
        print(f"{result['id']}: {result['installed_type1_records']} installed records, "
              f"{result['valid_rats_blocks']} valid RATS blocks, "
              f"{len(result['candidate_programs'])} candidate programs")
    for spec in args.extra:
        identifier, _, path = spec.partition('=')
        if not identifier or not path:
            raise SystemExit(f'malformed --extra (want ID=PATH): {spec}')
        image = Path(path).read_bytes()
        try:
            result = audit_version({'id': identifier}, rom=image)
        except ValueError as error:
            result = {'id': identifier, 'rom_sha256': sha(image),
                      'size': len(image), 'error': str(error),
                      'candidate_programs': []}
        result['unregistered'] = True
        versions.append(result)
        print(f"{result['id']} (unregistered): "
              f"{len(result['candidate_programs'])} candidate programs")
    sources, archives = audit_sources()
    report = {
        'scope': __doc__.strip(), 'candidate_rule':
        'Exact known code hash or at least three reviewed markers in one valid RATS block. '
        'All type-1 SpriteTool slots are mapped; unprotected marker hits are listed separately. '
        'A different implementation can evade this fingerprint.',
        'versions': versions, 'source_programs': sources, 'archive_entries': archives,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()

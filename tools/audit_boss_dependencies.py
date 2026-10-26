#!/usr/bin/env python3
"""Pin official Boss candidates and inventory their version-local dependencies.

This is a structural inventory, not an executable-module admission recipe or
proof of a complete fight. Only the explicitly selected official releases are
read; unrelated ROM collections and source trees are not searched.
"""
import argparse
import json
from pathlib import Path
import sys

from audit_star_boss_donors import rats_blocks, sprite_table
from prepare_rom import prepare_bytes, verify
from restore_star_world_1 import graphics_pointer, lorom, lz2, sha, sprite_rooms, write_verified

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ('cheap-demo', 'mazo', '7hero', 'boss', 'demo-only-1', 'demo-1-1')
SLOTS = (0x2a, 0x9b, 0x9c, 0xb0, 0xc0, 0xc1, 0xc2)
ROOMS = (0x00d, 0x0fe, 0x0ff, 0x10c, 0x151, 0x16b, 0x170, 0x190, 0x191, 0x192)
# Reviewed inline JSR tables selected by `LDA table,x|y; STA $00; JMP ($0000)`.
# The primary table for each candidate is the survey seed. Entries outside this
# review stay unresolved in the report.
REVIEWED_DISPATCH = {
    'boss': {'primary_dispatcher': 0x228115,
             'tables': ({'address': 0x228118, 'count': 23, 'dispatcher': 0x2281c8},
                        {'address': 0x22bb7b, 'count': 21, 'dispatcher': 0x22bbf7})},
    'mazo': {'primary_dispatcher': 0x2280a9,
             'tables': ({'address': 0x228923, 'count': 13, 'dispatcher': 0x22897e},
                        {'address': 0x228e49, 'count': 8, 'dispatcher': 0x228e7d})},
}


def survey_dispatch(rom, table, count, end, reviewed=None):
    """Explore explicit inline JSR tables; never infer their length from bytes."""
    sys.path.insert(0, str(ROOT / 'local/upstream/snesrecomp/recompiler'))
    from v2.decoder import decode_function
    from snes65816 import ABS, LONG, LONG_X
    reviewed = reviewed or {'primary_dispatcher': None, 'tables': ()}
    bank = table >> 16
    offset = lorom(table)
    targets = []
    for index in range(count):
        entry = rom[offset+index*3:offset+index*3+3]
        if len(entry) != 3 or entry[0] != 0x20:
            raise ValueError('reviewed inline JSR table differs')
        targets.append(int.from_bytes(entry[1:], 'little'))
    tables_out = []
    reviewed_sites = set()
    if reviewed['primary_dispatcher'] is not None:
        if rom[lorom(reviewed['primary_dispatcher']):
               lorom(reviewed['primary_dispatcher'])+3] != bytes.fromhex('6c0000'):
            raise ValueError('reviewed primary dispatcher differs')
        reviewed_sites.add(reviewed['primary_dispatcher'])
    for item in reviewed['tables']:
        address, entries = item['address'], item['count']
        data = rom[lorom(address):lorom(address)+entries*3]
        if len(data) != entries*3 or any(data[i*3] != 0x20 for i in range(entries)):
            raise ValueError('reviewed indirect JSR table differs')
        indirect_targets = [int.from_bytes(data[i*3+1:i*3+3], 'little') for i in range(entries)]
        if any(not 0x8008 <= target < end for target in indirect_targets):
            raise ValueError('reviewed indirect target escapes the module')
        if rom[lorom(item['dispatcher']):lorom(item['dispatcher'])+3] != bytes.fromhex('6c0000'):
            raise ValueError('reviewed indirect dispatcher differs')
        reviewed_sites.add(item['dispatcher'])
        tables_out.append({'table': f'{address:06X}', 'count': entries, 'sha256': sha(data),
                           'dispatcher': f'{item["dispatcher"]:06X}',
                           'targets': [f'{bank << 16 | target:06X}' for target in indirect_targets]})
        targets.extend(indirect_targets)
    observed = set()
    todo, entries, instructions, unresolved, outside = list(targets), set(), {}, [], []
    while todo:
        pc = todo.pop()
        if pc in entries:
            continue
        entries.add(pc)
        if not 0x8008 <= pc < end:
            outside.append(pc)
            continue
        graph = decode_function(rom, bank, pc, 1, 1, end=end)
        for item in graph.unresolved_indirects:
            site = getattr(item, 'site_pc24', None)
            if site in reviewed_sites:
                observed.add(site)
            else:
                unresolved.append(str(item))
        for item in graph.suppressed_indirect_calls:
            site = getattr(item, 'site_pc24', None)
            if site in reviewed_sites:
                observed.add(site)
            else:
                unresolved.append(str(item))
        for decoded in graph.insns.values():
            ins = decoded.insn
            instructions[(ins.addr, decoded.key.m, decoded.key.x)] = ins
            if ins.mnem == 'JSR' and ins.mode == ABS:
                todo.append(ins.operand)
    return {'scope': 'Exploratory 8-bit entry decode, local absolute JSR traversal only; '
                     'self-bank long calls and unresolved indirects are not expanded. '
                     'This is not a complete dependency closure or an admission check.',
            'table': f'{table:06X}', 'count': count,
            'table_sha256': sha(rom[offset:offset+count*3]),
            'targets': [f'{bank << 16 | pc:06X}' for pc in targets],
            'local_entries': len(entries), 'instruction_variants': len(instructions),
            'outside_local_entries': [f'{pc:04X}' for pc in sorted(outside)],
            'reviewed_indirect_tables': tables_out,
            'reviewed_dispatch_sites': [f'{site:06X}' for site in sorted(reviewed_sites)],
            'reviewed_dispatch_sites_observed': [f'{site:06X}' for site in sorted(observed)],
            'unresolved_indirects': sorted(set(unresolved)),
            'long_calls': [f'{pc:06X}' for pc in sorted({ins.operand for ins in instructions.values()
                                                       if ins.mnem in ('JSL', 'JML')})],
            'source_bank_long_reference_pcs': [f'{pc:06X}' for pc in sorted({ins.addr
                for ins in instructions.values() if ins.mode in (LONG, LONG_X)
                and ins.operand >> 16 == bank})]}


def prepare_boss(root=ROOT):
    manifest = json.loads((root / 'config/boss-donor.json').read_text())
    patch = manifest['authoritative_patch']
    patched = prepare_bytes((root / patch['base_path']).read_bytes(),
                            (root / patch['ips_path']).read_bytes(),
                            dict(patch, output=manifest['output']))
    bodies = []
    for source in manifest['inputs']:
        raw = (root / source['path']).read_bytes()
        verify(raw, source, source['path'])
        prefix = source['copier_prefix_bytes']
        if prefix not in (0, 512):
            raise ValueError('unreviewed copier prefix')
        body = raw[prefix:]
        verify(body, manifest['output'], 'Boss Demo body')
        bodies.append(body)
    if not bodies or any(body != patched for body in bodies):
        raise ValueError('supplied Boss Demo body differs from authoritative boss.ips output')
    directory = root / 'local/content-versions/boss'
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'rom.sfc', bodies[0])
    # Preserve earlier receipts that predate the authoritative IPS comparison.
    receipt = {'manifest_sha256': sha((root / 'config/boss-donor.json').read_bytes()),
               'manifest': manifest, 'operation': 'Apply pinned boss.ips, then compare normalized ROM bodies byte for byte',
               'comparisons': [{'path': source['path'], 'equal': True, 'different_bytes': 0}
                               for source in manifest['inputs']]}
    write_verified(directory / 'ips-verification-receipt.json',
                   (json.dumps(receipt, indent=2) + '\n').encode())
    return manifest


def code_owner(rom, blocks, address):
    offset = lorom(address)
    owners = [(start, end) for start, end in blocks if start <= offset < end]
    if not owners:
        return None
    start, end = min(owners, key=lambda span: span[1] - span[0])
    return {'offset': start, 'size': end-start, 'sha256': sha(rom[start:end]),
            'entry_in_payload': start+8 <= offset < end}


def room_inventory(rom, room):
    slot = lorom(0x05ec00) + room * 2
    address = (int.from_bytes(rom[slot:slot+2], 'little') |
               rom[lorom(0x0ef100) + room] << 16)
    start = lorom(address)
    cursor = start + 1
    placements = []
    for _ in range(1024):
        if cursor >= len(rom):
            raise ValueError('truncated sprite list')
        if rom[cursor] == 0xff:
            break
        entry = rom[cursor:cursor+3]
        if len(entry) != 3:
            raise ValueError('truncated sprite placement')
        if entry[0] & 8:
            placements.append({'slot': f'{entry[2]:02X}', 'raw': entry.hex()})
        cursor += 3
    else:
        raise ValueError('unterminated sprite list')
    offset = lorom(0x14ad08) + room * 32
    metadata = rom[offset:offset+32]
    graphics = []
    # Only the reviewed extended-graphics format enables these nine words.
    if metadata[:2] == bytes.fromhex('0180'):
        for index in range(9):
            gfx = int.from_bytes(metadata[2+index*2:4+index*2], 'little')
            resource = {'position': index, 'local_id': f'{gfx:03X}'}
            try:
                pointer = graphics_pointer(rom, gfx)
                resource['pointer'] = f'{pointer:06X}'
                decoded, encoded = lz2(rom, pointer, limit=0x10000)
                resource.update(pointer=f'{pointer:06X}', encoded_size=len(encoded),
                                encoded_sha256=sha(encoded), decoded_size=len(decoded),
                                decoded_sha256=sha(decoded))
            except (ValueError, IndexError) as error:
                resource['unresolved'] = str(error)
            graphics.append(resource)
    return {'sprite_pointer': f'{address:06X}',
            'sprite_list_size': cursor+1-start,
            'sprite_list_sha256': sha(rom[start:cursor+1]),
            'custom_placements': placements, 'graphics_metadata': metadata.hex(),
            'extended_graphics': graphics}


def inventory(rom, identifier):
    constructor, body, table = sprite_table(rom)
    blocks = rats_blocks(rom)
    records = {}
    for slot in SLOTS:
        offset = lorom(table) + slot*16
        raw = rom[offset:offset+16]
        record = {'raw': raw.hex(), 'type': raw[0],
                  'rooms': [f'{room:03X}' for room in sprite_rooms(rom, slot)]}
        if raw[0] == 1:
            for key, start in (('init', 8), ('main', 11)):
                address = int.from_bytes(raw[start:start+3], 'little')
                record[key] = {'address': f'{address:06X}',
                               'protected_block': code_owner(rom, blocks, address)}
        elif raw[0] == 3:
            record['dispatch'] = 'Type 3: not admitted through the type-1 constructor contract'
        records[f'{slot:02X}'] = record
    return {'id': identifier, 'rom_sha256': sha(rom),
            'constructor_address': f'{constructor:06X}', 'constructor_sha256': sha(body),
            'table_address': f'{table:06X}', 'records': records,
            'rooms': {f'{room:03X}': room_inventory(rom, room) for room in ROOMS}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'local/reports/boss-dependencies.json')
    args = parser.parse_args()
    boss = prepare_boss()
    metadata = json.loads((ROOT / 'config/content-versions.json').read_text())
    versions = {item['id']: item for item in metadata['versions']}
    versions['boss'] = boss
    results = []
    for identifier in VERSIONS:
        rom = (ROOT / 'local/content-versions' / identifier / 'rom.sfc').read_bytes()
        verify(rom, versions[identifier]['output'], identifier)
        results.append(inventory(rom, identifier))
    candidate = 'demo11-native-sprite9e'
    candidate_path = ROOT / 'config/restorations' / (candidate + '.json')
    candidate_cfg = json.loads(candidate_path.read_text())
    recipient = (ROOT / 'local/restoration' / candidate / 'rom.sfc').read_bytes()
    verify(recipient, candidate_cfg['output'], candidate)
    results.append(inventory(recipient, candidate))
    surveys = {}
    for identifier, table, count, end in (('boss', 0x228095, 35, 0xef3e),
                                          ('mazo', 0x228048, 25, 0xb07c)):
        rom = (ROOT / 'local/content-versions' / identifier / 'rom.sfc').read_bytes()
        surveys[identifier] = survey_dispatch(rom, table, count, end,
                                              REVIEWED_DISPATCH.get(identifier))
    decoder = ROOT / 'local/upstream/snesrecomp/recompiler'
    report = {'scope': __doc__.strip(), 'tool_sha256': sha(Path(__file__).read_bytes()),
              'boss_manifest_sha256': sha((ROOT / 'config/boss-donor.json').read_bytes()),
              'limitations': ['Room numbers, records and graphics IDs are version-local.',
                              'RATS ownership is not a call-graph dependency closure.',
                              'Music, dynamic graphics, shared helpers and ending flow need separate review.',
                              'No donor code, map or engine behavior is installed by this tool.'],
              'versions': results, 'dispatch_surveys': surveys,
              'decoder_files': {name: sha((decoder / name).read_bytes())
                                for name in ('v2/decoder.py', 'snes65816.py')}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_verified(args.output, (json.dumps(report, indent=2) + '\n').encode())
    print(args.output)
    print('report SHA-256:', sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()

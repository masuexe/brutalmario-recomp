#!/usr/bin/env python3
"""Inventory content differences between the Demo 1-1 and demoOnly1 baselines.

Read-only: compares level streams, room graphics records and music table targets
by content hash rather than by address, because the two builds relocate their data
independently. This is orientation for selective Demo 1-1 migration, not a
playability or dependency-closure claim.
"""
import hashlib, json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom

ROOT = Path(__file__).resolve().parents[1]


def sha(body):
    return hashlib.sha256(body).hexdigest()


def stream(rom, address, limit=0x8000):
    try:
        offset = lorom(address)
    except ValueError:
        return None
    if offset <= 0 or offset >= len(rom):
        return None
    blob = rom[offset:offset + limit]
    end = blob.find(b'\xff')
    return blob[:end + 1] if end >= 0 else blob


def song_block(rom, address):
    """Return the uploaded song block, which is count(2) + base(2) + data."""
    try:
        offset = lorom(address)
    except ValueError:
        return None
    if offset <= 0 or offset + 4 > len(rom):
        return None
    count = int.from_bytes(rom[offset:offset + 2], 'little')
    if count < 8 or offset + 4 + count > len(rom):
        return None
    return rom[offset:offset + 4 + count]


def level_pointers(rom, room):
    out = {}
    for table, name in ((0x05E000, 'layer1'), (0x05E600, 'layer2')):
        slot = lorom(table) + room * 3
        out[name] = int.from_bytes(rom[slot:slot + 3], 'little')
    slot = lorom(0x05EC00) + room * 2
    out['sprites'] = (int.from_bytes(rom[slot:slot + 2], 'little') |
                      rom[lorom(0x0EF100) + room] << 16)
    return out


def main():
    versions = {v['id']: v for v in json.loads((ROOT / 'config/content-versions.json').read_text())['versions']}
    bodies = {}
    for name in ('demo-1-1', 'demo-only-1'):
        body = (ROOT / 'local/content-versions' / name / 'rom.sfc').read_bytes()
        verify(body, versions[name]['output'], name)
        bodies[name] = body
    a, b = bodies['demo-1-1'], bodies['demo-only-1']

    levels = {}
    for room in range(512):
        pa, pb = level_pointers(a, room), level_pointers(b, room)
        entry = {}
        for kind in ('layer1', 'layer2', 'sprites'):
            sa = stream(a, pa[kind]) if pa[kind] else None
            sb = stream(b, pb[kind]) if pb[kind] else None
            if sa is None or sb is None:
                entry[kind] = {'demo11': len(sa) if sa else None, 'only1': len(sb) if sb else None,
                               'status': 'missing-in-' + ('demo11' if sa is None else 'only1')}
            else:
                entry[kind] = {'demo11': len(sa), 'only1': len(sb),
                               'same': sha(sa) == sha(sb),
                               'demo11_sha': sha(sa)[:16], 'only1_sha': sha(sb)[:16]}
        levels[f'{room:03X}'] = entry

    gfx = {}
    for room in range(512):
        off_a = lorom(0x14AD08) + room * 32
        off_b = lorom(0x14AD08) + room * 32
        ra, rb = a[off_a:off_a + 32], b[off_b:off_b + 32]
        if ra != rb:
            gfx[f'{room:03X}'] = {'demo11': ra.hex(), 'only1': rb.hex()}

    music = {}
    for song in range(256):
        slot = lorom(0x0FE000) + song * 3
        pa = int.from_bytes(a[slot:slot + 3], 'big')
        pb = int.from_bytes(b[slot:slot + 3], 'big')
        if not pa and not pb:
            continue
        ga = song_block(a, pa) if pa else None
        gb = song_block(b, pb) if pb else None
        if ga is None or gb is None or sha(ga) != sha(gb):
            music[f'{song:02X}'] = {
                'demo11': len(ga) if ga else None, 'only1': len(gb) if gb else None,
                'same_length': bool(ga and gb and len(ga) == len(gb)),
                'demo11_sha': sha(ga)[:16] if ga else None,
                'only1_sha': sha(gb)[:16] if gb else None}

    differing = {room: e for room, e in levels.items()
                 if any(not (v.get('same') or v.get('status')) for v in e.values())
                 or any(v.get('status') for v in e.values())}
    report = {
        'scope': __doc__.strip(),
        'demo_1_1_sha256': sha(a),
        'demo_only_1_sha256': sha(b),
        'levels_with_differing_content': sorted(differing),
        'level_count_differing': len(differing),
        'gfx_records_differing': sorted(gfx),
        'gfx_record_count': len(gfx),
        'music_slots_differing': sorted(music),
        'music_slot_count': len(music),
        'levels': levels,
        'gfx_records': gfx,
        'music': music,
        'limits': ['Content hashes only; no playability, dependency closure or',
                   'version-chronology claim. Relocated data can hash-differ while',
                   'being semantically equal, and vice versa.',
                   'Room graphics records are compared at the same offset because',
                   'both builds are recipients derived from the same base layout.']}
    out = ROOT / 'local/reports/demo11-additions-inventory.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('levels differing:', len(differing), 'of 512')
    print('gfx records differing:', len(gfx), 'of 512')
    print('music slots differing:', len(music), 'of 256')
    print('report:', out.relative_to(ROOT))


if __name__ == '__main__':
    main()
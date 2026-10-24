#!/usr/bin/env python3
"""Qualify the custom sprite 06 port on the Demo 1-1 line (castle room 10E).

Castle 10E's sprite list places the lineage-shared custom sprite 06 (room 6E
places it identically in every supplied version) at level x $B0. Demo 1-1's
record table 0x31:8272 holds the default record at id 06, so the runtime spawn
aborted silently at the record-enable gate before this port. The candidate
installs the reviewed cheap_demo block (byte-identical in demo8) and its
adapted record; entry captures on both hosts must show the slot alive with the
record's stock number, the custom flag and the decoded spawn position.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from restore_star_world_1 import lorom, sprite_rooms
from qualify_world1_next_course import require, sha

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-castle-sprite06'
TABLE = 0x318272
SID = 0x06


def slots(body):
    out = []
    for slot in range(12):
        if not body[0x14C8 + slot]:
            continue
        out.append((body[0x9E + slot], body[0x14C8 + slot],
                    body[0x1AB10 + slot], body[0x1AB9E + slot],
                    body[0xE4 + slot] | (body[0x14E0 + slot] << 8),
                    body[0xD8 + slot] | (body[0x14D4 + slot] << 8)))
    return out


def main():
    head = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    recipe = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(head, recipe['output'], HEAD)
    base = (ROOT / 'local/restoration' / recipe['base_restoration'] / 'rom.sfc').read_bytes()
    verify(base, recipe['base_output'], recipe['base_restoration'])
    version = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    donor_pin = next(v['output'] for v in version if v['id'] == 'cheap-demo')
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    verify(donor, donor_pin, 'cheap_demo')
    demo8 = (ROOT / 'local/content-versions/demo8/rom.sfc').read_bytes()

    sprite = recipe['custom_sprite']
    require(sprite_rooms(base, SID) == sprite['rooms'], 'room dependency changed')
    offset = lorom(TABLE + SID * 16)
    require(base[offset:offset + 16].hex() == sprite['before'], 'slot was not the default record')
    installed = head[offset:offset + 16]
    expected = bytearray(bytes.fromhex(sprite['source_record']))
    expected[10] = int(sprite['destination_address'], 16) >> 16
    expected[13] = int(sprite['destination_address'], 16) >> 16
    require(installed == bytes(expected), 'installed record differs from the adapted donor record')
    block = donor[lorom(int(sprite['source_address'], 16)):][:sprite['block']['size']]
    dest = head[lorom(int(sprite['destination_address'], 16)):][:sprite['block']['size']]
    require(dest == block, 'relocated block differs from the donor copy')
    demo8_block = demo8[lorom(int(sprite['source_address'], 16)):][:sprite['block']['size']]
    require(demo8_block == block, 'demo8 no longer carries the identical block')
    for item in sprite['shared_dependencies']:
        for data in (base, donor):
            require(sha(data[lorom(int(item['address'], 16)):lorom(int(item['address'], 16)) + item['size']]) == item['sha256'],
                    'shared dependency differs: ' + item['address'])
    diff = [i for i, (a, b) in enumerate(zip(base, head)) if a != b]
    allowed = set(range(lorom(int(sprite['destination_address'], 16)) - 8,
                        lorom(int(sprite['destination_address'], 16)) + sprite['block']['size']))
    allowed |= set(range(offset, offset + 16))
    require(all(i in allowed for i in diff), 'candidate differs outside the reviewed regions')

    report = {'scope': __doc__.strip(), 'head': HEAD, 'head_sha256': sha(head),
              'record_slot': '%06X' % (TABLE + SID * 16), 'block': sprite['destination_address'],
              'captures': {}}
    for host in ('ref', 'native'):
        capture_dir = ROOT / 'local/captures' / ('d11c06-entry-' + host)
        receipt = json.loads((capture_dir / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(head), 'capture ROM differs: ' + host)
        found = []
        for tag in ('e00', 'e01', 'e02', 'e03'):
            body = (capture_dir / (tag + '.wram.bin')).read_bytes()
            room = body[0x010B] | (body[0x010C] << 8)
            require(room == 0x10E, 'capture left the castle room: %s/%s' % (host, tag))
            hit = [s for s in slots(body)
                   if s[3] == SID and s[2] & 0x08 and s[1] == 0x08]
            require(len(hit) == 1, 'custom 06 slot state differs: %s/%s' % (host, tag))
            number, status, flags, custom, x, y = hit[0]
            require(number == installed[1], 'sprite number differs from record byte 1: %s/%s' % (host, tag))
            require(abs(x - 0x00B0) <= 8 and abs(y - 0x0140) <= 8,
                    'spawn position differs from the decoded entry site: %s/%s' % (host, tag))
            found.append({'slot_id': '%02X' % number, 'flags': '%02X' % flags,
                          'x': '%04X' % x, 'y': '%04X' % y})
        report['captures'][host] = found

    report['verified'] = [
        'the Demo 1-1 record slot 0x31:82D2 was the default record and now holds the',
        'reviewed cheap_demo record with only its code bank bytes adapted',
        'the relocated 270-byte STAR block equals the donor copy, which demo8 carries',
        'byte-identically at the same address',
        'the shared dependency regions are byte-identical between recipient and donor',
        'every changed byte lies inside the reviewed block and record regions',
        'castle entry captures on reference and native show exactly one custom-06 slot,',
        'status 08, custom flag set, sprite number from record byte 1, at x $B0 y $140',
    ]
    report['limits'] = [
        'The sprite looks correct in sampled framebuffers but its full in-level behaviour',
        '(interaction, animation, defeat) is not separately audited.',
        'Room 6E keeps placing the sprite; its playability on this line is not qualified.',
    ]
    output = ROOT / 'local/reports/demo11-castle-sprite06.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Castle sprite06 checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

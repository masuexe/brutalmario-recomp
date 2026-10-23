#!/usr/bin/env python3
"""Qualify the custom sprite 8D and 0B ports on the Demo 1-1 line.

Demo 1-1 keeps its custom sprite records in a different table from demoOnly1
(0x31:8272, file 0x188272). Writing the reviewed cheap_demo blocks and records there
restores the two sprites that 1-2 and room 138 place; both slots were default before.
"""
import hashlib, json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom, sprite_rooms

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-sprite0b'
BINARY = 'BrutalMarioDemo11Sprite0BSNESRecomp'
TABLE = 0x318272
PORTS = [
    ('demo11-sprite8d', 'BrutalMarioDemo11Sprite8DSNESRecomp', 0x8D,
     'd11s8d3-010', 'only1-010-route-ref', 'world1-next-course-entry.script',
     ('entry180', 'entry600', 'ability_walk')),
    ('demo11-sprite0b', 'BrutalMarioDemo11Sprite0BSNESRecomp', 0x0B,
     'd11s0b-138', 'only1-138-clear-ref', 'world1-room138-clear-save.script',
     ('entry600', 'fly150')),
]


def slots(body):
    out = []
    for slot in range(12):
        if not body[0x14C8 + slot]:
            continue
        out.append((body[0x161A + slot], body[0x14C8 + slot],
                    body[0xE4 + slot] | (body[0x14E0 + slot] << 8),
                    body[0xD8 + slot] | (body[0x14D4 + slot] << 8)))
    return sorted(out)


def main():
    head = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(head, cfg['output'], HEAD)
    version = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    donor_pin = next(v['output'] for v in version if v['id'] == 'cheap-demo')
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    verify(donor, donor_pin, 'cheap_demo')

    report = {'scope': __doc__.strip(), 'head': HEAD, 'head_sha256': sha(head),
              'table_lorom': '%06X' % TABLE, 'ports': {}}
    for target, binary_name, sid, capture, reference, script_name, tags in PORTS:
        recipe = json.loads((ROOT / 'config/restorations' / (target + '.json')).read_text())
        sprite = recipe['custom_sprite']
        base = (ROOT / 'local/restoration' / recipe['base_restoration'] / 'rom.sfc').read_bytes()
        verify(base, recipe['base_output'], recipe['base_restoration'])
        require(sprite['destination_record_address'].upper() == '%06X' % (TABLE + sid * 16),
                'record slot is not in the Demo 1-1 table: ' + target)
        slot = lorom(TABLE + sid * 16)
        require(base[slot:slot + 16].hex() == sprite['before'], 'slot was not the default record')
        installed = head[slot:slot + 16]
        source_record = bytes.fromhex(sprite['source_record'])
        expected = bytearray(source_record)
        expected[10] = int(sprite['destination_address'], 16) >> 16
        expected[13] = int(sprite['destination_address'], 16) >> 16
        require(installed == bytes(expected), 'installed record differs: ' + target)
        block = donor[lorom(int(sprite['source_address'], 16)):][:sprite['block']['size']]
        dest = head[lorom(int(sprite['destination_address'], 16)):][:sprite['block']['size']]
        require(dest == block, 'relocated block differs: ' + target)
        require(sprite_rooms(head, sid) == sprite['rooms'], 'room dependency changed: ' + target)
        build = json.loads((ROOT / 'local/build' / target / 'm1-build.json').read_text())
        binary = ROOT / 'local/build' / target / binary_name
        require(sha(binary.read_bytes()) == build['binary_sha256'], 'binary identity differs: ' + target)
        capture_dir = ROOT / 'local/captures' / capture
        reference_dir = ROOT / 'local/captures' / reference
        receipt = json.loads((capture_dir / 'receipt.json').read_text())
        require(receipt['rom_sha256'] in (sha(head), recipe['output']['sha256']),
                'capture ROM differs: ' + capture)
        entry = {'record_slot': '%06X' % (TABLE + sid * 16), 'block': sprite['destination_address'],
                 'samples': {}}
        for tag in tags:
            body = (capture_dir / (tag + '.wram.bin')).read_bytes()
            source = (reference_dir / (tag + '.wram.bin')).read_bytes()
            ours, theirs = slots(body), slots(source)
            require(len(ours) == len(theirs), 'active slot count differs: ' + capture + '/' + tag)
            by_id = {item[0]: item for item in theirs}
            require(len(by_id) == len(theirs), 'duplicate sprite id in reference: ' + reference + '/' + tag)
            for a_id, a_st, a_x, a_y in ours:
                match = by_id.pop(a_id, None)
                require(match is not None, 'unexpected sprite id %02X: %s/%s' % (a_id, capture, tag))
                _, b_st, b_x, b_y = match
                require(a_st == b_st, 'sprite %02X status differs: %s/%s' % (a_id, capture, tag))
                offscreen = a_y >= 0x8000 or b_y >= 0x8000
                if not offscreen:
                    require(abs(a_x - b_x) <= 8 and abs(a_y - b_y) <= 8,
                            'sprite %02X position differs: %s/%s' % (a_id, capture, tag))
            require(not by_id, 'missing sprite ids: ' + capture + '/' + tag)
            entry['samples'][tag] = len(ours)
        report['ports'][target] = entry

    report['verified'] = ['each record slot lives in the Demo 1-1 table 0x31:8272 and was default',
                          'the installed records adapt the reviewed cheap_demo pointers',
                          'the relocated code blocks equal the donor copies',
                          'the room dependencies still match the reviewed sets',
                          'the sprite slots on both courses match the demoOnly1 line within 8 px',
                          'each native build identity is pinned']
    report['limits'] = ['Position tolerance is 8 px; animation phase and the extra frame-level',
                        'differences are not part of this check.',
                        'The wider acceptance suite still pins the previous head and needs',
                        're-running against this one.']
    output = ROOT / 'local/reports/demo11-sprite-ports.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 sprite port checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
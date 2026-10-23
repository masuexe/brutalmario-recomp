#!/usr/bin/env python3
"""Qualify the room138 custom sprite 0B dependency recovery.

Entry and movement only: the sprite block, its record slot and two bank bytes
change. The settled sprite status array must match the cheap_demo donor, which
is exactly what fails without the definition. Full traversal, exits, collectibles
and audible output are not claimed here.
"""
import hashlib, json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, sprite_rooms
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / 'config/restorations/world1-room138-sprite.json').read_text())
    candidate = (ROOT / 'local/restoration/world1-room138-sprite/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/world1-room138-audio/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(base, cfg['base_output'], 'room138 audio base')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')

    sprite = cfg['custom_sprite']
    require(sprite_rooms(base, int(sprite['id'], 16)) == sprite['rooms'], 'sprite room dependencies differ')
    source = lorom(int(sprite['source_address'], 16))
    block = donor[source:source + sprite['block']['size']]
    verify(block, sprite['block'], 'donor sprite code')
    destination = lorom(int(sprite['destination_address'], 16))
    require(candidate[destination:destination + len(block)] == block, 'sprite code differs')
    record_offset = lorom(int(sprite['destination_record_address'], 16))
    record = candidate[record_offset:record_offset + 16]
    donor_record = bytearray(donor[lorom(int(sprite['source_record_address'], 16)):][:16])
    bank = int(sprite['destination_address'], 16) >> 16
    donor_record[10] = bank
    donor_record[13] = bank
    require(record.hex() == donor_record.hex(), 'sprite record differs beyond the relocated bank')
    changed = [i for i, (a, b) in enumerate(zip(base, candidate)) if a != b]
    allowed = set(range(destination, destination + len(block))) | set(range(record_offset, record_offset + 16))
    require(set(changed) <= allowed, 'unexpected changes outside the sprite regions')
    require(len(changed) > 0.9 * len(allowed), 'sprite regions were not actually installed')

    build = json.loads((ROOT / 'local/build/world1-room138-sprite/m1-build.json').read_text())
    binary = ROOT / 'local/build/world1-room138-sprite/BrutalMarioWorld1Room138SpriteSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')

    script = ROOT / 'recomp/inputs/world1-room138-entry.script'
    captures = {}
    states = {}
    for host in ('reference', 'native'):
        directory = ROOT / 'local/captures' / f'world1-138-sprite-qualified-{host}'
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script.read_bytes()),
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        log = (directory / 'run.log').read_bytes()
        require(b'quit' in log and b'timed out' not in log, 'route incomplete: ' + host)
        tags = ('title', 'files', 'intro', 'selected', 'entry180', 'entry600', 'settled', 'walk')
        states[host] = {}
        for tag in tags:
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, f'incomplete WRAM: {host}/{tag}')
            states[host][tag] = body
        captures[directory.name] = receipt
    donor_dir = ROOT / 'local/captures/world1-138-qualified-cheap'
    donor_receipt = json.loads((donor_dir / 'receipt.json').read_text())
    require(donor_receipt['rom_sha256'] == sha(donor), 'donor capture ROM differs')
    donor_settled = (donor_dir / 'settled.wram.bin').read_bytes()
    require(len(donor_settled) == 0x20000, 'incomplete donor WRAM')
    captures[donor_dir.name] = donor_receipt

    samples = {}
    cells = 19 * 0x1b0
    for host in ('reference', 'native'):
        samples[host] = {}
        for tag in ('settled', 'walk'):
            body = states[host][tag]
            require(body[0x100] == 0x14 and word(body, 0x10b) == 0x138, f'wrong room: {host}/{tag}')
            require(body[0x14c8:0x14d4] == donor_settled[0x14c8:0x14d4],
                    f'sprite statuses differ from donor: {host}/{tag}')
            require(body[0x161a:0x1626] == donor_settled[0x161a:0x1626],
                    f'sprite numbers differ from donor: {host}/{tag}')
            for base_address in (0xc800, 0x1c800):
                require(body[base_address:base_address + cells] == donor_settled[base_address:base_address + cells],
                        f'terrain differs from donor: {host}/{tag}/{base_address:x}')
            samples[host][tag] = {'x': word(body, 0x94), 'y': word(body, 0x96),
                                  'statuses': body[0x14c8:0x14d4].hex()}

    report = {
        'scope': __doc__.strip(),
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'donor_rom_sha256': sha(donor),
        'binary_sha256': build['binary_sha256'],
        'changed_bytes': len(changed),
        'sprite': {'id': sprite['id'], 'rooms': sprite['rooms'],
                   'block_size': sprite['block']['size'],
                   'block_sha256': sprite['block']['sha256'],
                   'destination_address': sprite['destination_address']},
        'verified': ['custom sprite code block and record installed',
                     'settled sprite status array matches the donor',
                     'settled sprite numbers match the donor',
                     'terrain matches the donor on both hosts'],
        'samples': samples,
        'captures': captures,
        'limits': ['Entry and movement scope only; full traversal, exits and',
                   'collectibles are not re-qualified on this candidate here.',
                   'Audible output is not claimed. Room106 music remains deferred.']}
    output = ROOT / 'local/reports/world1-room138-sprite-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Room138 sprite checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
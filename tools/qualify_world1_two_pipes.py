#!/usr/bin/env python3
"""Qualify assisted 1-2 pipe/ability/goal boundaries and onward room106 entry.

Position and movement fixtures skip traversal obstacles. This does not qualify
unassisted traversal, collectibles, or audible song identity.
"""
import json
from pathlib import Path

from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'recomp/inputs/world1-next-course-two-pipes.script'


def main():
    config = json.loads((ROOT / 'config/restorations/world1-next-course.json').read_text())
    candidate = (ROOT / 'local/restoration/world1-next-course/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/demo8/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, config['output'], 'candidate')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'demo8'), 'donor')
    build = json.loads((ROOT / 'local/build/world1-next-course/m1-build.json').read_text())
    binary = ROOT / 'local/build/world1-next-course/BrutalMarioWorld1NextCourseSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build changed')
    require(build['rom_sha256'] == sha(candidate), 'build ROM differs')

    # No script write may supply an exit, ability state, goal timer or progress.
    permitted = {0x0109, 0x1f11, 0x1f17, 0x1f1f, 0x0100,
                 0x1497, 0x94, 0x96, 0x7b, 0x7d, 0x1a, 0x1462, 0x85}
    for line in SCRIPT.read_text().splitlines():
        parts = line.split()
        if parts and parts[0] in ('poke', 'forcepoke', 'pokefor'):
            address = int(parts[1], 16)
            require(address in permitted, 'review new fixture write: ' + line)
            # Bound ranges too; an allowed start must not hide a forbidden write.
            limits = {0x1f11: 2, 0x1f17: 8, 0x1f1f: 8, 0x94: 4,
                      0x96: 2, 0x1a: 2, 0x1462: 2}
            require(len(bytes.fromhex(parts[-1])) <= limits.get(address, 1),
                    'review fixture write span: ' + line)

    states, receipts = {}, {}
    tags = ('selected', 'first_pipe', 'upward_entry', 'powerup',
            'exit_room', 'goal_contact', 'completed_map', 'next_course_entry')
    for host in ('reference', 'native', 'donor'):
        directory = ROOT / 'local/captures' / f'world1-two-pipes-qualified-v2-{host}'
        receipt = json.loads((directory / 'receipt.json').read_text())
        expected = sha(donor if host == 'donor' else candidate)
        require(receipt['rom_sha256'] == expected, 'wrong ROM: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(SCRIPT.read_bytes()),
                'wrong script: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'wrong native binary')
        log = (directory / 'run.log').read_bytes()
        require(b'quit' in log and b'timed out' not in log, 'route incomplete: ' + host)
        states[host] = {}
        for tag in tags:
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, f'truncated WRAM: {host}/{tag}')
            require((directory / (tag + '.sram.bin')).stat().st_size == (0x800 if host == 'donor' else 0x8000),
                    f'truncated SRAM: {host}/{tag}')
            states[host][tag] = body
        receipts[host] = receipt
        s = states[host]
        for tag, room in (('first_pipe', 0x10), ('upward_entry', 0x4a),
                          ('powerup', 0x4a), ('exit_room', 0x161),
                          ('goal_contact', 0x161), ('next_course_entry', 0x106)):
            require(s[tag][0x100] == 0x14 and word(s[tag], 0x10b) == room,
                    f'wrong room/mode: {host}/{tag}')
        require(s['first_pipe'][0x71] == 6, 'first pipe action missing: ' + host)
        require(s['upward_entry'][0x14af] == 0 and s['powerup'][0x14af] == 1,
                'extra-bit sprite not collected: ' + host)
        require(s['goal_contact'][0x1493] != 0, 'real goal not triggered: ' + host)
        initial, cleared = (0x00, 0x84) if host == 'donor' else (0x0c, 0x8c)
        require(s['selected'][0x1eb2] == initial and s['completed_map'][0x1eb2] == cleared,
                'normal clear state differs: ' + host)
        require(s['completed_map'][0x100] == 0x0e, 'no map return: ' + host)
        require(word(s['completed_map'], 0x1f17) == 0x58 and
                word(s['completed_map'], 0x1f19) == 0x1d8, 'onward node differs: ' + host)

    terrain = {}
    for tag, room, cells in (('upward_entry', 0x4a, 13 * 0x200),
                             ('exit_room', 0x161, 2 * 0x1b0)):
        for host in ('reference', 'native'):
            for base in (0xc800, 0x1c800):
                require(states[host][tag][base:base + cells] ==
                        states['donor'][tag][base:base + cells],
                        f'donor terrain differs: {host}/{tag}/{base:x}')
        terrain[tag] = {'room': f'{room:03X}', 'cells_per_buffer': cells}

    report = {
        'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate),
        'donor_rom_sha256': sha(donor), 'binary_sha256': build['binary_sha256'],
        'script_sha256': sha(SCRIPT.read_bytes()), 'receipts': receipts,
        'terrain': terrain,
        'verified': ['Up entry from room010 to room04A',
                     'actual extra-bit 8D power-up changes 14AF from 0 to 1',
                     'top pipe reaches room161', 'real goal and normal clear to map',
                     'map selects (058,1D8); entering it reaches room106'],
        'limits': ['Assisted movement skips traversal obstacles; no unassisted route claim.',
                   'No collectible or audible music qualification; room106 music remains deferred.'],
    }
    output = ROOT / 'local/reports/world1-two-pipes-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Assisted two-pipe checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

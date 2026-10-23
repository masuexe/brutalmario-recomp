#!/usr/bin/env python3
"""Qualify room106's assisted chase-Yoshi clear and real death/re-entry.

The clear uses invulnerability and one player-X/velocity alignment; the death
route uses only initial map fixtures. Neither writes riding, goal or progress.
Audible music and complete collectible coverage remain outside this scope.
"""
import json
from pathlib import Path

from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((ROOT / 'config/restorations/world1-next-course.json').read_text())
    candidate = (ROOT / 'local/restoration/world1-next-course/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, config['output'], 'candidate')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')
    build = json.loads((ROOT / 'local/build/world1-next-course/m1-build.json').read_text())
    executable = ROOT / 'local/build/world1-next-course/BrutalMarioWorld1NextCourseSNESRecomp'
    require(sha(executable.read_bytes()) == build['binary_sha256'], 'native binary differs')
    require(build['rom_sha256'] == sha(candidate), 'native ROM differs')
    # Shared chase script: initial mount, message, running Yoshi, re-mount success.
    program = candidate[0x171a90:0x171ad0]
    require(program == donor[0x171a90:0x171ad0], 'chase-script prefix differs')
    require(program.startswith(bytes.fromhex('a59df0016bad9314f0016baf06fd7f')),
            'review chase-script identification')

    captures, summary = {}, {}
    for route in ('clear', 'death'):
        script = ROOT / f'recomp/inputs/world1-room106-{route}.script'
        allowed = {0x109: 1, 0x1f11: 2, 0x1f17: 8, 0x1f1f: 8, 0x100: 1}
        if route == 'clear':
            allowed.update({0x1497: 1, 0x94: 2, 0x7b: 1})
        for line in script.read_text().splitlines():
            parts = line.split()
            if parts and parts[0] in ('poke', 'forcepoke', 'pokefor'):
                address = int(parts[1], 16)
                require(address in allowed and len(bytes.fromhex(parts[-1])) <= allowed[address],
                        'review fixture write: ' + line)
        for host in ('reference', 'native', 'cheap'):
            suffix = f'clear-qualified-v3-{host}' if route == 'clear' else f'death-qualified-{host}'
            directory = ROOT / 'local/captures' / ('world1-106-' + suffix)
            receipt = json.loads((directory / 'receipt.json').read_text())
            require(receipt['rom_sha256'] == sha(donor if host == 'cheap' else candidate),
                    'capture ROM differs: ' + directory.name)
            require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script.read_bytes()),
                    'capture script differs: ' + directory.name)
            if host == 'native':
                require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture build differs')
            log = (directory / 'run.log').read_bytes()
            require(b'quit' in log and b'timed out' not in log, 'route did not finish: ' + directory.name)

            def state(tag):
                body = (directory / (tag + '.wram.bin')).read_bytes()
                require(len(body) == 0x20000, 'truncated WRAM: ' + tag)
                require((directory / (tag + '.sram.bin')).stat().st_size == (0x800 if host == 'cheap' else 0x8000),
                        'truncated SRAM: ' + directory.name + '/' + tag)
                return body

            initial = state('settled')
            require(initial[0x100] == 0x14 and word(initial, 0x10b) == 0x106,
                    'initial room differs: ' + directory.name)
            require(initial[0x1ecc] == 4, 'course already cleared initially')
            if route == 'clear':
                catches = [state(f'catch{i:02}') for i in range(12)]
                caught = [i for i, b in enumerate(catches) if b[0x1fd06] == 1 and b[0x187a] == 1]
                require(caught, 'no actual Yoshi re-mount: ' + host)
                goal = state('goal')
                require(goal[0x1493] != 0 and goal[0x1fd06] == 1, 'no chase goal: ' + host)
                back = state('completed_map')
                require(back[0x100] == 0x0e and back[0x1ecc] == 0x84, 'no real clear: ' + host)
                require((back[0x1f02] & 0x10) != 0, 'normal exit event missing: ' + host)
                require(word(back, 0x1f17) == 0x88 and word(back, 0x1f19) == 0x1f8,
                        'onward node differs: ' + host)
                require(back[0xdbe] == initial[0xdbe], 'life lost in clear route: ' + host)
                summary[host] = {'first_caught_sample': caught[0], 'goal_timer': goal[0x1493],
                                 'clear_byte': back[0x1ecc], 'map': [0, 0x88, 0x1f8]}
                cells = 11 * 0x1b0
                for base in (0xc800, 0x1c800):
                    other = (ROOT / 'local/captures/world1-106-clear-qualified-v3-cheap/settled.wram.bin').read_bytes()
                    require(len(other) == 0x20000 and initial[base:base + cells] == other[base:base + cells],
                            'initial donor terrain differs: ' + host)
                standard_coins = sum(initial[0xc800+i] + 256 * initial[0x1c800+i] in (0x2d, 0x2e)
                                     for i in range(cells))
                require(standard_coins == 0, 'standard DK/dragon coins need qualification')
            else:
                dying = state('dying')
                require(dying[0x100] == 0x14 and dying[0x71] == 9, 'no real death: ' + host)
                back, reentry = state('returned_map'), state('reentry')
                require(back[0x100] == 0x0e and back[0xdbe] == initial[0xdbe] - 1,
                        'death did not return with one lost life: ' + host)
                require(back[0x1ecc] == 4, 'death spuriously cleared course: ' + host)
                require(reentry[0x100] == 0x14 and word(reentry, 0x10b) == 0x106,
                        're-entry failed: ' + host)
                require(reentry[0x1fd06] == 0, 'chase success state leaked through death: ' + host)
            captures[directory.name] = receipt

    report = {'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate),
              'donor_rom_sha256': sha(donor), 'binary_sha256': build['binary_sha256'],
              'chase_script_prefix': {'physical_offset': '171A90', 'size': 64, 'sha256': sha(program)},
              'clear_results': summary, 'captures': captures,
              'inventory': {'horizontal_screens': 11, 'standard_dragon_coin_cells': 0},
              'limits': ['Assisted clear; no unassisted traversal claim.',
                         'No full custom-block/collectible audit or save/reload qualification.',
                         'Room106 music remains incorrect and deferred.']}
    output = ROOT / 'local/reports/world1-room106-flow-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Room106 flow checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

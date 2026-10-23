#!/usr/bin/env python3
"""Qualify assisted room120 DK collection/normal clear and recipient persistence.

All three hosts cover natural entry after room106 and real pickups/goal.
Reset/File A persistence is qualified on recipient reference/native only;
the cheap_demo comparison intentionally ends at the normal clear.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'recomp/inputs/world1-room120-coins-save.script'
DONOR_SCRIPT = ROOT / 'local/probes/world1-survey/room120-donor-clear.script'


def donor_route():
    return SCRIPT.read_text().split('\nreset\n', 1)[0] + '\nquit\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-donor-script', action='store_true',
                        help='write the bounded donor prefix under ignored local storage')
    args = parser.parse_args()
    if args.prepare_donor_script:
        content = donor_route()
        require(not DONOR_SCRIPT.exists() or DONOR_SCRIPT.read_text() == content,
                'refusing to replace a different donor script')
        DONOR_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
        DONOR_SCRIPT.write_text(content)
        print(DONOR_SCRIPT.relative_to(ROOT))
        return

    config = json.loads((ROOT / 'config/restorations/world1-next-course.json').read_text())
    candidate = (ROOT / 'local/restoration/world1-next-course/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, config['output'], 'candidate')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')
    build = json.loads((ROOT / 'local/build/world1-next-course/m1-build.json').read_text())
    binary = ROOT / 'local/build/world1-next-course/BrutalMarioWorld1NextCourseSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native binary changed')
    require(build['rom_sha256'] == sha(candidate), 'build ROM differs')
    allowed = {0x109: 1, 0x1f11: 2, 0x1f17: 8, 0x1f1f: 8, 0x100: 1,
               0x1497: 1, 0x94: 4, 0x7b: 1, 0x7d: 1}
    for line in SCRIPT.read_text().splitlines():
        parts = line.split()
        if parts and parts[0] in ('poke', 'forcepoke', 'pokefor'):
            address = int(parts[1], 16)
            require(address in allowed and len(bytes.fromhex(parts[-1])) <= allowed[address],
                    'review new fixture write: ' + line)

    states, receipts = {}, {}
    for host in ('reference', 'native', 'cheap-clear'):
        directory = ROOT / 'local/captures' / f'world1-120-qualified-{host}'
        receipt = json.loads((directory / 'receipt.json').read_text())
        is_donor = host == 'cheap-clear'
        route = donor_route().encode() if is_donor else SCRIPT.read_bytes()
        require(receipt['rom_sha256'] == sha(donor if is_donor else candidate), 'wrong ROM: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(route), 'wrong route: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'wrong native binary')
        log = (directory / 'run.log').read_bytes()
        require(b'quit' in log and b'timed out' not in log, 'route incomplete: ' + host)
        tags = ['completed_map', 'cave_entry', 'coin1', 'coin2', 'coin3', 'coin4',
                'coin5', 'swim08', 'below_tape', 'cave_goal', 'cave_completed_map']
        if not is_donor:
            tags += ['file_reload', 'reload_node', 'reload_cave']
        states[host] = {}
        for tag in tags:
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, f'truncated WRAM: {host}/{tag}')
            require((directory / (tag + '.sram.bin')).stat().st_size == (0x800 if is_donor else 0x8000),
                    f'truncated SRAM: {host}/{tag}')
            states[host][tag] = body
        s = states[host]
        require(s['completed_map'][0x100] == 0x0e and s['completed_map'][0x1ecc] == 0x84,
                'preceding room106 clear missing: ' + host)
        entry = s['cave_entry']
        require(entry[0x100] == 0x14 and word(entry, 0x10b) == 0x120 and entry[0x13bf] == 0x44,
                'natural cave entry failed: ' + host)
        require(entry[0x85] == entry[0x75] == entry[0x187a] == 1,
                'water/Yoshi entry state differs: ' + host)
        require(entry[0x1ee6] == 0x0b and entry[0x1f37] == 0, 'already completed cave: ' + host)
        for i in range(1, 6):
            body = s[f'coin{i}']
            require(body[0x100] == 0x14 and word(body, 0x10b) == 0x120,
                    f'coin sample outside cave: {host}/{i}')
            require(body[0x1420] == body[0x1422] == i, f'coin pickup failed: {host}/{i}')
            require(body[0x1f37] == (8 if i == 5 else 0), f'DK bit differs: {host}/{i}')
        require(s['coin5'][0xdbe] == entry[0xdbe] + 1, 'fifth coin did not award life: ' + host)
        require(any(s['swim08'][0x14c8+i] and s['swim08'][0x9e+i] == 0x7b
                    for i in range(12)), 'goal tape not loaded: ' + host)
        require(s['cave_goal'][0x1493] != 0, 'no real tape contact: ' + host)
        back = s['cave_completed_map']
        require(back[0x100] == 0x0e and back[0x1ee6] == 0x8b and back[0x1f37] == 8,
                'normal clear/DK state differs: ' + host)
        require(word(back, 0x1f17) == 0xa8 and word(back, 0x1f19) == 0x1d8,
                'onward map node differs: ' + host)
        require(back[0xdbe] == s['coin5'][0xdbe], 'life lost before clear: ' + host)
        if not is_donor:
            for tag in ('file_reload', 'reload_node', 'reload_cave'):
                require(s[tag][0x1ee6] == 0x8b and s[tag][0x1f37] == 8,
                        f'clear/DK did not persist: {host}/{tag}')
            reload = s['reload_cave']
            require(reload[0x100] == 0x14 and word(reload, 0x10b) == 0x120, 'reload room differs: ' + host)
            require(all(reload[0xc800+i] + 256 * reload[0x1c800+i] not in (0x2d, 0x2e)
                        for i in range(14 * 0x1b0)), 'collected coins respawned: ' + host)
        receipts[host] = receipt

    cells = 14 * 0x1b0
    for host in ('reference', 'native'):
        for base in (0xc800, 0x1c800):
            require(states[host]['cave_entry'][base:base+cells] ==
                    states['cheap-clear']['cave_entry'][base:base+cells], 'donor terrain differs: ' + host)
    report = {'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate),
              'donor_rom_sha256': sha(donor), 'binary_sha256': build['binary_sha256'],
              'captures': receipts, 'terrain': {'screens': 14, 'cells_per_buffer': cells},
              'verified': ['natural room106 clear to room120 entry with Yoshi',
                           'five actual DK pickups, saved bit and extra life',
                           'real tape and normal clear to map0(0A8,1D8)',
                           'recipient File A clear/DK reload with coins removed'],
              'limits': ['Assisted route; no unassisted full-course or secret exit qualification.',
                         'cheap_demo persistence is not claimed; donor route stops before reset.',
                         'Audible music and room120 death/re-entry remain unqualified.']}
    output = ROOT / 'local/reports/world1-room120-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Room120 checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

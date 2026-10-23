#!/usr/bin/env python3
"""Qualify assisted room138 clear/save/onward entry and actual death/re-entry.

Air swimming, invulnerability and one final landing alignment bypass obstacles
and combat. This is not an unassisted run or every-enemy/custom-exit audit.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]
CLEAR = ROOT / 'recomp/inputs/world1-room138-clear-save.script'
DONOR = ROOT / 'local/probes/world1-survey/138-donor-flow.script'


def donor_route():
    return CLEAR.read_text().split('\nreset\n', 1)[0] + '\nquit\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-donor-script', action='store_true')
    args = parser.parse_args()
    if args.prepare_donor_script:
        content = donor_route()
        require(not DONOR.exists() or DONOR.read_text() == content, 'refusing to replace a different script')
        DONOR.parent.mkdir(parents=True, exist_ok=True)
        DONOR.write_text(content)
        print(DONOR.relative_to(ROOT))
        return
    cfg = json.loads((ROOT / 'config/restorations/world1-room138-audio.json').read_text())
    candidate = (ROOT / 'local/restoration/world1-room138-audio/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')
    build = json.loads((ROOT / 'local/build/world1-room138-audio/m1-build.json').read_text())
    binary = ROOT / 'local/build/world1-room138-audio/BrutalMarioWorld1Room138AudioSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')
    captures, states = {}, {}
    for route in ('flow', 'death'):
        script = CLEAR if route == 'flow' else ROOT / 'recomp/inputs/world1-room138-death.script'
        allowed = {0x109: 1, 0x100: 1, 0x1f11: 2, 0x1f17: 8, 0x1f1f: 8}
        if route == 'flow':
            allowed.update({0x1497: 1, 0x85: 1, 0x94: 4, 0x7b: 1, 0x7d: 1})
        for line in script.read_text().splitlines():
            parts = line.split()
            if parts and parts[0] in ('poke', 'forcepoke', 'pokefor'):
                address = int(parts[1], 16)
                require(address in allowed and len(bytes.fromhex(parts[-1])) <= allowed[address],
                        'review new fixture write: ' + line)
        for host in ('reference', 'native', 'cheap'):
            directory = ROOT / 'local/captures' / f'world1-138-{route}-qualified-{host}'
            receipt = json.loads((directory / 'receipt.json').read_text())
            expected_route = donor_route().encode() if route == 'flow' and host == 'cheap' else script.read_bytes()
            require(receipt['rom_sha256'] == sha(donor if host == 'cheap' else candidate), 'capture ROM differs')
            require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(expected_route),
                    'capture route differs: ' + directory.name)
            if host == 'native':
                require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
            log = (directory / 'run.log').read_bytes()
            require(b'quit' in log and b'timed out' not in log, 'route incomplete: ' + directory.name)
            tags = ['settled']
            if route == 'flow':
                tags += [f'fly{i:03}' for i in range(10, 161, 10)]
                tags += ['goal', 'completed_map', 'castle_entry']
                if host != 'cheap':
                    tags += ['file_reload', 'reload_node', 'reload_course']
            else:
                tags += ['dying', 'returned_map', 'reentry']
            s = {}
            for tag in tags:
                b = (directory / (tag + '.wram.bin')).read_bytes()
                require(len(b) == 0x20000, f'incomplete WRAM: {directory.name}/{tag}')
                require((directory / (tag + '.sram.bin')).stat().st_size == (0x800 if host == 'cheap' else 0x8000),
                        f'incomplete SRAM: {directory.name}/{tag}')
                s[tag] = b
            initial = s['settled']
            require(initial[0x100] == 0x14 and word(initial, 0x10b) == 0x138 and initial[0x1efe] == 0x0f,
                    'initial room/state differs')
            if route == 'flow':
                previous = word(initial, 0x94)
                for i in range(10, 161, 10):
                    b = s[f'fly{i:03}']
                    require(b[0x100] == 0x14 and word(b, 0x10b) == 0x138 and b[0x71] == 0,
                            'flight left active course: ' + host)
                    require(word(b, 0x94) > previous and b[0xdbe] == initial[0xdbe], 'flight did not advance safely')
                    previous = word(b, 0x94)
                require(previous >= 0x0f00, 'continuous assisted movement did not reach the late course')
                require(s['goal'][0x1493] != 0, 'real tape not triggered')
                back = s['completed_map']
                require(back[0x100] == 0x0e and back[0x1efe] == 0x8f, 'normal clear missing')
                require(word(back, 0x1f17) == 0xa8 and word(back, 0x1f19) == 0x1a8, 'onward node differs')
                require(back[0xdbe] == initial[0xdbe], 'life lost before clear')
                if host != 'cheap':
                    castle = s['castle_entry']
                    require(castle[0x100] == 0x14 and word(castle, 0x10b) == 0x10e, 'castle entry failed')
                    for tag in ('file_reload', 'reload_node', 'reload_course'):
                        require(s[tag][0x1efe] == 0x8f, 'clear did not persist: ' + tag)
                    require(s['reload_course'][0x100] == 0x14 and word(s['reload_course'], 0x10b) == 0x138,
                            'saved-course re-entry failed')
            else:
                require(s['dying'][0x100] == 0x14 and s['dying'][0x71] == 9, 'no actual death')
                require(s['returned_map'][0x100] == 0x0e and s['returned_map'][0xdbe] == initial[0xdbe] - 1,
                        'death did not return to map with one lost life')
                require(s['returned_map'][0x1efe] == 0x0f, 'death spuriously cleared course')
                require(s['reentry'][0x100] == 0x14 and word(s['reentry'], 0x10b) == 0x138, 'death re-entry failed')
            states[route, host] = s
            captures[directory.name] = receipt

    cells = 19 * 0x1b0
    for host in ('reference', 'native'):
        for tag in ('settled', 'fly080', 'fly160'):
            for base_address in (0xc800, 0x1c800):
                require(states['flow', host][tag][base_address:base_address+cells] ==
                        states['flow', 'cheap'][tag][base_address:base_address+cells], 'donor terrain differs')
    initial = states['flow', 'reference']['settled']
    require(all(initial[0xc800+i] + 256 * initial[0x1c800+i] not in (0x2d, 0x2e)
                for i in range(cells)), 'standard DK pickup route is needed')
    report = {'scope': __doc__.strip(), 'rom_sha256': sha(candidate), 'donor_rom_sha256': sha(donor),
              'binary_sha256': build['binary_sha256'], 'captures': captures,
              'verified': ['assisted continuous movement through late room138',
                           'real tape, normal clear and map0(0A8,1A8)',
                           'recipient natural room10E entry and File A clear persistence',
                           'three-host hazard death and room138 re-entry'],
              'standard_DK_cells_in_main_room': 0,
              'donor_castle_sample_mode': states['flow', 'cheap']['castle_entry'][0x100],
              'limits': ['No unassisted run or every-enemy behavior qualification.',
                         'Room0CB exit record exists; actual entry remains unproven in candidate and donor.',
                         'Donor castle entry and save persistence are not qualified.',
                         'Audible output and room106 music correction remain outside scope.']}
    output = ROOT / 'local/reports/world1-room138-flow-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Room138 flow checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

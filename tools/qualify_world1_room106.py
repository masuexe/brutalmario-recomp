#!/usr/bin/env python3
"""Check bounded room 106 graphics recovery and World 1 regression captures.

This does not qualify room 106's complete exit route or repair overworld
connectivity. Capture directories and the accepted forest baseline are read-only.
"""
import hashlib
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, lz2, pointer_offset

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def word(body, address):
    return int.from_bytes(body[address:address + 2], 'little')


def main():
    config = json.loads((ROOT / 'config/restorations/world1-room106.json').read_text())
    candidate = (ROOT / 'local/restoration/world1-room106/rom.sfc').read_bytes()
    baseline = (ROOT / 'local/restoration/star-world-forest/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    donor_pin = next(v['output'] for v in versions if v['id'] == 'cheap-demo')
    verify(candidate, config['output'], 'candidate')
    verify(baseline, config['base_output'], 'accepted forest baseline')
    verify(donor, donor_pin, 'cheap_demo donor')

    asset = config['assets'][0]
    decoded, compressed = lz2(donor, int(asset['source_address'], 16))
    verify(decoded, asset['decoded'], 'source graphics')
    verify(compressed, asset['compressed'], 'source compressed stream')
    destination = pointer_offset(int(asset['target_id'], 16))
    installed = int.from_bytes(candidate[destination:destination + 3], 'little')
    require(lz2(candidate, installed) == (decoded, compressed), 'relocated graphics differ')
    record_word = lorom(int(config['gfx_record']['address'], 16)) + asset['record_offset']
    start = config['allocation']['offset']
    stop = start + len(compressed) + 8
    allowed = set(range(start, stop)) | set(range(destination, destination + 3))
    allowed |= set(range(record_word, record_word + 2))
    differences = [i for i, (a, b) in enumerate(zip(baseline, candidate)) if a != b]
    require(set(differences) <= allowed, 'unexpected changes outside graphics relocation')
    require(word(candidate, record_word) == int(asset['target_id'], 16), 'selector differs')
    require(baseline[start:stop] == bytes(stop - start), 'allocation was not empty')
    count = len(compressed) - 1
    expected_header = b'STAR' + count.to_bytes(2, 'little') + (count ^ 0xffff).to_bytes(2, 'little')
    require(candidate[start:stop] == expected_header + compressed, 'protected payload differs')

    captures = {}
    build = json.loads((ROOT / 'local/build/world1-room106/m1-build.json').read_text())
    executable = ROOT / 'local/build/world1-room106/BrutalMarioWorld1Room106SNESRecomp'
    require(sha(executable.read_bytes()) == build['binary_sha256'], 'native binary changed')

    def capture(name, script, rom_sha, native=False):
        directory = ROOT / 'local/captures' / name
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == rom_sha, f'wrong ROM: {name}')
        script_sha = receipt.get('route_sha256', receipt.get('script_sha256'))
        require(script_sha == sha((ROOT / script).read_bytes()), f'wrong route: {name}')
        if native:
            require(receipt['host_binary_sha256'] == build['binary_sha256'], f'wrong binary: {name}')
        log = (directory / 'run.log').read_bytes()
        require(b'quit' in log and b'timed out' not in log, f'route did not finish: {name}')
        captures[name] = {'path': str(directory.relative_to(ROOT)), 'receipt': receipt}
        return directory

    def state(directory, tag):
        body = (directory / (tag + '.wram.bin')).read_bytes()
        require(len(body) == 0x20000, f'incomplete WRAM: {directory.name}/{tag}')
        return body

    entry_script = 'recomp/inputs/world1-room106-entry.script'
    entries = {
        'reference': capture('world1-106-qualified-entry-candidate', entry_script, sha(candidate)),
        'native': capture('world1-106-qualified-entry-native-v2', entry_script, sha(candidate), True),
        'donor': capture('world1-106-qualified-entry-cheap', entry_script, sha(donor)),
    }
    level_pointer = lorom(0x05e000) + 0x106 * 3
    source_level = lorom(int.from_bytes(donor[level_pointer:level_pointer + 3], 'little'))
    screens = (donor[source_level] & 0x1f) + 1
    active_tiles = screens * 0x1b0  # Horizontal room: 16 columns by 27 rows per screen.
    require(screens == 11, 'review room 106 level length before comparing terrain')
    samples = {}
    for tag in ('settled', 'walk', 'jump', 'landed'):
        states = {host: state(directory, tag) for host, directory in entries.items()}
        source = states['donor']
        samples[tag] = {}
        for host, body in states.items():
            require(body[0x100] == 0x14 and word(body, 0x10b) == 0x106, f'wrong room: {host}/{tag}')
            require(body[0x71] == 0, f'player is not active: {host}/{tag}')
            for address in (0xc800, 0x1c800):
                require(body[address:address + active_tiles] == source[address:address + active_tiles],
                        f'Map16 buffer mismatch: {host}/{tag}/{address:x}')
            require(abs(word(body, 0x94) - word(source, 0x94)) <= 2 and
                    abs(word(body, 0x96) - word(source, 0x96)) <= 2, f'movement differs: {host}/{tag}')
            unused_differences = [f'{i:05X}' for address in (0xc800, 0x1c800)
                                  for i in range(address + active_tiles, address + 0x3800)
                                  if body[i] != source[i]]
            samples[tag][host] = {'x': word(body, 0x94), 'y': word(body, 0x96),
                                   'unused_buffer_tail_differences': unused_differences}

    regressions = {}
    for host in ('reference', 'native'):
        is_native = host == 'native'
        goal = capture(f'world1-106-qualified-goal-{host}-v2',
                       'recomp/inputs/world1-first-goal-save.script', sha(candidate), is_native)
        contact = state(goal, 'at_edge')
        require(contact[0x1493] != 0 and contact[0x1ecb] == 0x0a, 'real goal/contact sample differs')
        for tag in ('completed_map', 'reloaded'):
            body = state(goal, tag)
            saved = (goal / (tag + '.sram.bin')).read_bytes()
            require(len(saved) == 32768, 'incomplete SRAM')
            require(body[0x100] == 0x0e and body[0x1ecb] == 0x8a, 'clear/reload differs')
            require(body[0x1f02] & 0x40, 'normal event not retained')
            require(saved[0x29] == saved[0x1d6] == 0x8a, 'both clear-save copies not retained')
            require((word(body, 0x1f17), word(body, 0x1f19)) == (0x18, 0x1b8),
                    'inherited automatic map destination changed')

        house = capture(f'world1-106-qualified-house-{host}-v2',
                        'recomp/inputs/world1-house-return.script', sha(candidate), is_native)
        require(word(state(house, 'entry600'), 0x10b) == 0x180, 'House subroom differs')
        require(state(house, 'moved')[0x100] == 0x0e, 'House exit did not return to map')
        returned = state(house, 'back_to_first')
        require(returned[0x100] == 0x0e and
                (word(returned, 0x1f17), word(returned, 0x1f19)) == (0x48, 0x198),
                'House walk back to first course differs')

        forest = capture(f'world1-106-qualified-forest-{host}-v2',
                         'recomp/inputs/star-world-forest-entry.script', sha(candidate), is_native)
        for tag in ('entry180', 'entry600', 'entry1200'):
            body = state(forest, tag)
            require(body[0x100] == 0x14 and word(body, 0x10b) == 3, 'forest regression')
            require(body[0x85] == body[0x75] == 0, 'forest water-state regression')
        regressions[host] = {'first_course_goal_and_both_save_copies': True,
                             'inherited_next_node': 'map 0 / 018,1B8; connectivity NOT repaired',
                             'house_entry_exit_and_walk_back': True, 'forest_dry_entry': True}

    report = {
        'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate),
        'baseline_rom_sha256': sha(baseline), 'binary_sha256': build['binary_sha256'],
        'changed_bytes': len(differences), 'changed_footprint': {
            'graphics_rats_physical': [start, stop], 'graphics_pointer_physical': destination,
            'room_selector_physical': record_word},
        'source_graphics': asset, 'terrain_comparison': {
            'horizontal_screens': screens, 'active_cells_per_buffer': active_tiles,
            'buffer_bases': ['0C800', '1C800'],
            'boundary': 'Unused buffer tail differences are reported, not full-WRAM equivalence.'},
        'samples': samples, 'regressions': regressions,
        'captures': captures, 'limits': [
            'Room 106 complete exits, collectibles, death/re-entry and audible output remain unqualified.',
            'Overworld normal-exit connectivity and Demo 1-1 content migration remain open.',
            'This is an isolated resource-recovery candidate, not a new manually accepted baseline.'],
    }
    output = ROOT / 'local/reports/world1-room106-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Bounded graphics and regression checks passed: {output.relative_to(ROOT)}')


if __name__ == '__main__':
    main()

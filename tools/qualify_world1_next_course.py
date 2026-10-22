#!/usr/bin/env python3
"""Check the World 1 next-course graphics/music candidate and its captures.

This qualifies a bounded resource recovery: room 010 loads with donor terrain,
the first course normal exit reaches it, and death/subroom entry work on both
hosts. It does not qualify a complete World 1 route, collectibles, or audible
output. Captures and the accepted base ROM are read-only.
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
    config = json.loads((ROOT / 'config/restorations/world1-next-course.json').read_text())
    candidate = (ROOT / 'local/restoration/world1-next-course/rom.sfc').read_bytes()
    baseline = (ROOT / 'local/restoration/world1-room106/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/demo8/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    donor_pin = next(v['output'] for v in versions if v['id'] == 'demo8')
    verify(candidate, config['output'], 'candidate')
    verify(baseline, config['base_output'], 'accepted room106 base')
    verify(donor, donor_pin, 'demo8 donor')

    allowed = set()
    start = config['allocation']['offset']
    cursor = start
    graphics = []
    for asset in config['assets']:
        decoded, compressed = lz2(donor, int(asset['source_address'], 16))
        verify(decoded, asset['decoded'], 'source graphics')
        verify(compressed, asset['compressed'], 'source compressed stream')
        pointer = pointer_offset(int(asset['target_id'], 16))
        allowed |= set(range(pointer, pointer + 3))
        installed = int.from_bytes(candidate[pointer:pointer + 3], 'little')
        require(lz2(candidate, installed) == (decoded, compressed),
                'relocated graphics differ for ' + asset['target_id'])
        require(lz2(candidate, int.from_bytes(
            candidate[pointer:pointer + 3], 'little')) == (decoded, compressed),
            'relocated graphics differ for ' + asset['target_id'])
        for record_address in asset.get('record_addresses', [config['gfx_record']['address']]):
            record_word = lorom(int(record_address, 16)) + asset['record_offset']
            allowed |= set(range(record_word, record_word + 2))
            require(word(candidate, record_word) == int(asset['target_id'], 16),
                    'graphics selector differs for ' + asset['target_id'])
        graphics.append({'source_id': asset['source_id'], 'target_id': asset['target_id'],
                         'pointer': pointer})
    stop = start + sum(len(lz2(donor, int(a['source_address'], 16))[1]) + 8
                       for a in config['assets'])
    allowed |= set(range(start, stop))
    for item in config.get('additional_gfx_records', []):
        off = lorom(int(item['address'], 16))
        allowed |= set(range(off, off + len(bytes.fromhex(item['before']))))
    for patch in config.get('code_patches', []):
        off = lorom(int(patch['address'], 16))
        allowed |= set(range(off, off + len(bytes.fromhex(patch['before']))))
    music = config['music']
    mstart = music['allocation']['offset']
    allowed |= set(range(mstart, mstart + music['adapted']['size'] + 8))
    mpointer = lorom(int(music['pointer_address'], 16))
    allowed |= set(range(mpointer, mpointer + 3))
    sprite = config['custom_sprite']
    sdest = lorom(int(sprite['destination_address'], 16))
    allowed |= set(range(sdest, sdest + sprite['block']['size']))
    srecord = lorom(int(sprite['destination_record_address'], 16))
    allowed |= set(range(srecord, srecord + len(bytes.fromhex(sprite['before']))))
    differences = [i for i, (a, b) in enumerate(zip(baseline, candidate)) if a != b]
    require(set(differences) <= allowed, 'unexpected changes outside reviewed regions')
    require(baseline[start:stop] == bytes(stop - start), 'graphics allocation was not empty')
    position = start
    for asset in config['assets']:
        compressed = lz2(donor, int(asset['source_address'], 16))[1]
        count = len(compressed) - 1
        header = b'STAR' + count.to_bytes(2, 'little') + (count ^ 0xffff).to_bytes(2, 'little')
        end = position + len(header) + len(compressed)
        require(candidate[position:end] == header + compressed,
                'protected graphics payload differs for ' + asset['target_id'])
        position = end

    build = json.loads((ROOT / 'local/build/world1-next-course/m1-build.json').read_text())
    executable = ROOT / 'local/build/world1-next-course/BrutalMarioWorld1NextCourseSNESRecomp'
    require(sha(executable.read_bytes()) == build['binary_sha256'], 'native binary changed')
    require(build['rom_sha256'] == sha(candidate), 'build receipt ROM differs')

    captures = {}

    def capture(name, script, rom_sha, native=False):
        directory = ROOT / 'local/captures' / name
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == rom_sha, f'wrong ROM: {name}')
        route = receipt.get('route_sha256', receipt.get('script_sha256'))
        require(route == sha((ROOT / script).read_bytes()), f'wrong route: {name}')
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

    entry_script = 'recomp/inputs/world1-next-course-entry.script'
    entries = {
        'reference': capture('world1-next-qualified-entry-v2-reference', entry_script, sha(candidate)),
        'native': capture('world1-next-qualified-entry-native', entry_script, sha(candidate), True),
        'donor': capture('world1-next-qualified-entry-donor-v2-reference', entry_script, sha(donor)),
    }
    level_table = lorom(0x05e000) + 0x010 * 3
    source_level = lorom(int.from_bytes(donor[level_table:level_table + 3], 'little'))
    screens = (donor[source_level] & 0x1f) + 1
    active = screens * 0x1b0
    require(screens == 9, 'review room 010 level length before comparing terrain')
    terrain = {}
    for tag in ('entry600', 'ability_walk'):
        bodies = {host: state(directory, tag) for host, directory in entries.items()}
        donor_body = bodies['donor']
        terrain[tag] = {}
        for host, body in bodies.items():
            require(body[0x100] == 0x14 and word(body, 0x10b) == 0x010, f'wrong room: {host}/{tag}')
            for base_address in (0xc800, 0x1c800):
                require(body[base_address:base_address + active] == donor_body[base_address:base_address + active],
                        f'Map16 buffer differs from donor: {host}/{tag}/{base_address:x}')
            terrain[tag][host] = {'x': word(body, 0x94), 'y': word(body, 0x96)}

    death_script = 'recomp/inputs/world1-next-course-death.script'
    for host in ('reference', 'native'):
        directory = capture(f'world1-next-qualified-death-{host}', death_script,
                           sha(candidate), host == 'native')
        require(state(directory, 'falling')[0x100] == 0x14, f'no pit death sample: {host}')
        back = state(directory, 'reentry')
        require(back[0x100] == 0x14 and word(back, 0x10b) == 0x010, f'no re-entry: {host}')

    progression_script = 'recomp/inputs/world1-next-course-progression.script'
    for host in ('reference', 'native'):
        suffix = 'v2-reference' if host == 'reference' else 'native'
        directory = capture(f'world1-next-qualified-progression-{suffix}', progression_script,
                           sha(candidate), host == 'native')
        tape = state(directory, 'at_tape')
        require(tape[0x100] == 0x14 and word(tape, 0x10b) == 0x105, f'goal not reached: {host}')
        require(state(directory, 'completed_map')[0x100] == 0x0e, f'no map return: {host}')
        for tag in ('next_entry', 'next_walk'):
            body = state(directory, tag)
            require(body[0x100] == 0x14 and word(body, 0x10b) == 0x010,
                    f'normal exit did not reach room 010: {host}/{tag}')

    subroom_script = 'recomp/inputs/world1-next-course-subroom.script'
    for host in ('reference', 'native'):
        directory = capture(f'world1-next-qualified-subroom-{host}', subroom_script,
                           sha(candidate), host == 'native')
        body = state(directory, 'subroom')
        require(body[0x100] == 0x14 and word(body, 0x10b) == 0x04a, f'subroom differs: {host}')

    report = {
        'scope': __doc__.strip(),
        'candidate_rom_sha256': sha(candidate),
        'baseline_rom_sha256': sha(baseline),
        'donor_rom_sha256': sha(donor),
        'binary_sha256': build['binary_sha256'],
        'changed_bytes': len(differences),
        'terrain': {'horizontal_screens': screens, 'active_cells_per_buffer': active,
                    'buffer_bases': ['0C800', '1C800'], 'samples': terrain},
        'verified': {'room010_loads_with_donor_terrain': True,
                     'first_course_normal_exit_reaches_room010': True,
                     'pit_death_and_reentry': True,
                     'existing_subroom_reachable': True,
                     'music_and_sprite_installed': True},
        'captures': captures,
        'limits': [
            'A complete World 1 route, collectibles and audible output remain unqualified.',
            'Intended course numbering for room 010 is not established; it is not labelled 1-2.',
            'Overworld normal-exit connectivity beyond the first course is not claimed.',
            'This is a bounded resource-recovery candidate pending user playtesting.'],
    }
    output = ROOT / 'local/reports/world1-next-course-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Bounded next-course checks passed: {output.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
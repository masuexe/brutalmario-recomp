#!/usr/bin/env python3
"""Check the Demo 1-1 port of the accepted demoOnly1 Forest Star course.

The fixtures teleport to the map-6 middle-left entrance and use explicit camera
and player-position shortcuts. No fixture writes an exit destination, completion
flag, carried key state, event or SRAM value. Reference and native captures must
agree with fresh demoOnly1-line forest captures under the same scripts.
"""
import json
from pathlib import Path

from audit_demo11_line import allowed_regions
from m1 import ROOT
from prepare_rom import verify
from qualify_demo11_lower_inner_music import capture
from qualify_demo11_star_sprites_safe import state
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom, make_candidate, pointer_offset, sprite_rooms

ROOT = Path(ROOT)
HEAD = 'demo11-star-forest'
BASE = 'demo11-center-route'
DONOR = 'star-world-forest'
SCRIPTS = {
    'entry': 'star-world-forest-entry.script',
    'attack': 'demo11-forest-attack.script',
    'normal': 'star-world-forest-normal.script',
    'secret': 'star-world-forest-secret.script',
    'death': 'star-world-forest-death.script',
}
DUMPS = {
    'entry': ('entry180', 'entry600', 'entry1200', 'shot_spawn', 'shot_flight', 'movement'),
    'attack': ('enemies', 'shot', 'hit', 'resolved', 'shot2', 'hit2', 'resolved2',
               'shot3', 'hit3', 'resolved3'),
    'normal': ('goal_room', 'tape', 'normal_map', 'reloaded'),
    'secret': ('aftergoal', 'destination', 'reloaded'),
    'death': ('death_map', 'reentry'),
}
COURSE_SEGMENTS = ((0xAD01, 0xC100), (0xC800, 0xE000), (0x1C8D9, 0x1D57C))
KEY_LEVEL = 0x0C
NORMAL_KEY = 0x8C
SECRET_KEY = 0x8E
PARROT, PROJECTILE, VINE = 0xB0, 0xB1, 0xB2
SPRITE_RECORDS = {'B0': 0x318D72, 'B1': 0x318D82, 'B2': 0x318D92}
SECONDARY = {'05F003': 0x0B, '05F203': 0x05, '05F403': 0xEA, '05F603': 0x00}
LEVEL_POINTERS = {'003': '80a850', '04E': '7db751'}


def read_json(path):
    return json.loads(path.read_text())


def image(target):
    cfg = read_json(ROOT / 'config/restorations' / (target + '.json'))
    rom = (ROOT / 'local/restoration' / target / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], target)
    return rom, cfg


def split_star(rom, address):
    header = lorom(address)
    require(rom[header:header + 4] == b'STAR', 'block header missing at ' + hex(address))
    count = int.from_bytes(rom[header + 4:header + 6], 'little')
    require(count < 0x8000 and
            int.from_bytes(rom[header + 6:header + 8], 'little') == count ^ 0xFFFF,
            'block header complement differs at ' + hex(address))
    return rom[header + 8:header + 8 + count + 1]


def slots(body, number):
    return [(i, body[0x14C8 + i]) for i in range(12) if body[0x1AB9E + i] == number]


def position(body, index):
    return (body[0xE4 + index] | (body[0x14E0 + index] << 8),
            body[0xD8 + index] | (body[0x14D4 + index] << 8))


def summary(directory, tag):
    body = state(directory, tag)
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    return dict(mode=body[0x100], room=word(body, 0x10B), x=word(body, 0x94), y=word(body, 0x96),
                water=body[0x85], in_water=body[0x75], lives=body[0x0DBE],
                flag=body[0x1EA5], sram=[saved[3], saved[0x1B0]], map=body[0x1F11],
                map_x=word(body, 0x1F17), map_y=word(body, 0x1F19))


def route_states(captures):
    return {route: {tag: summary(captures[route], tag) for tag in DUMPS[route]}
            for route in SCRIPTS}


def verify_recipe():
    base, base_cfg = image(BASE)
    final, cfg = image(HEAD)
    versions = read_json(ROOT / 'config/content-versions.json')['versions']
    pins = {version['id']: version['output'] for version in versions}
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    verify(donor, pins[cfg['donor']], cfg['donor'])
    recipient = (ROOT / 'local/content-versions' / cfg['recipient'] / 'rom.sfc').read_bytes()
    verify(recipient, pins[cfg['recipient']], cfg['recipient'])
    verify(base, cfg['base_output'], 'intact parent')

    replay, _ = make_candidate(base, donor, cfg)
    require(replay == final, 'recipe does not reproduce the candidate')
    changed = {i for i, (a, b) in enumerate(zip(base, final)) if a != b}
    require(changed <= allowed_regions(cfg), 'unexpected byte outside the reviewed regions')

    water = lorom(0x05DE03)
    require(base[water] == 0x40 and final[water] == 0x00,
            'room 003 water setting is not 40 -> 00')
    for address, value in SECONDARY.items():
        require(final[lorom(int(address, 16))] == value,
                'room 003 secondary setting differs: ' + address)

    clone = bytes(donor[lorom(0x128000):lorom(0x128000) + 0x8000])
    require(split_star(final, 0x40FFF8) == clone, 'private Map16 block differs')
    require(base[lorom(0x40FFF8):lorom(0x40FFF8) + 0x8008] == bytes(0x8008),
            'parent clone range is not empty')

    old = read_json(ROOT / 'config/restorations/star-world-forest.json')
    shim = bytes.fromhex(old['raw_blocks'][5]['bytes'])
    shim = shim.replace(bytes.fromhex('a90044'), bytes.fromhex('a90041'))
    shim = shim.replace(bytes.fromhex('bf00e044'), bytes.fromhex('bf00e041'))
    require(split_star(final, 0x49E900) == shim, 'relocated Map16 shims differ')
    require(base[lorom(0x49E900):lorom(0x49E900) + 108] == bytes(108),
            'parent shim range is not empty')
    require(final[lorom(0x06F540):lorom(0x06F540) + 4] == bytes.fromhex('5c08e949'),
            'graphics hook does not target the relocated shim')
    require(final[lorom(0x06F623):lorom(0x06F623) + 4] == bytes.fromhex('2244e949'),
            'ActsLike hook does not target the relocated shim')

    for item in cfg['level_data']:
        source = lorom(int(item['source_address'], 16))
        blob = donor[source:source + item['data']['size']]
        verify(blob, item['data'], 'donor level room ' + item['room'])
        slot = lorom(int(item['table'], 16)) + int(item['room'], 16) * 3
        require(base[slot:slot + 3].hex() == LEVEL_POINTERS[item['room']],
                'parent level pointer changed: ' + item['room'])
        pointer = int.from_bytes(final[slot:slot + 3], 'little')
        require(split_star(final, pointer - 8) == blob,
                'stored level room differs: ' + item['room'])

    for sprite in cfg['custom_sprites']:
        address = SPRITE_RECORDS[sprite['id']]
        require(int(sprite['destination_record_address'], 16) == address,
                'sprite record address differs: ' + sprite['id'])
        require(base[lorom(address):lorom(address) + 16].hex() == sprite['before'],
                'sprite record slot changed: ' + sprite['id'])
        require(sprite_rooms(base, int(sprite['id'], 16)) == [],
                'sprite slot is placed in a room: ' + sprite['id'])
        source = lorom(int(sprite['source_address'], 16))
        block = donor[source:source + sprite['block']['size']]
        destination = lorom(int(sprite['destination_address'], 16))
        require(final[destination:destination + sprite['block']['size']] == block,
                'sprite code block differs: ' + sprite['id'])

    for asset in cfg['assets']:
        pointer = pointer_offset(int(asset['target_id'], 16))
        target = int.from_bytes(final[pointer:pointer + 3], 'little')
        source = lorom(int(asset['source_address'], 16))
        require(split_star(final, target - 8) ==
                donor[source:source + asset['compressed']['size']],
                'isolated ExGFX payload differs: ' + asset['target_id'])
    require(final[lorom(0x14AD68) + 2:lorom(0x14AD68) + 4] == bytes.fromhex('c00f'),
            'room 003 graphics selection differs')
    require(final[lorom(0x14B6C8) + 4:lorom(0x14B6C8) + 8] == bytes.fromhex('be0fbf0f'),
            'goal-room graphics selection differs')
    return base, final, cfg, donor, changed


def check_host(host, native):
    captures, directories = {}, {}
    directory, receipt = capture('d11-forest-entry-' + host, HEAD, SCRIPTS['entry'], native)
    captures[directory.name] = receipt
    directories['entry'] = directory
    for tag in DUMPS['entry'][:3]:
        body = summary(directory, tag)
        require(body['mode'] == 0x14 and body['room'] == 3 and body['x'] == 112 and body['y'] == 352,
                'forest entry differs: ' + host + '/' + tag)
        require(body['water'] == 0 and body['in_water'] == 0, 'water flag survived: ' + host)
        require(body['lives'] == 4 and body['flag'] == KEY_LEVEL and
                body['sram'] == [KEY_LEVEL, KEY_LEVEL], 'entry save state differs: ' + host)
        require(body['map'] == 6 and body['map_x'] == 344 and body['map_y'] == 424,
                'entry map state differs: ' + host)
    live_parrots = slots(state(directory, 'entry1200'), PARROT)
    require(live_parrots and all(status == 8 for _, status in live_parrots),
            'donor parrot is not live on entry: ' + host)
    spawn = state(directory, 'shot_spawn')
    launched = [(i, status) for i, status in slots(spawn, PROJECTILE) if status == 8]
    require(len(launched) == 1, 'parrot projectile did not spawn: ' + host)
    index = launched[0][0]
    flight = state(directory, 'shot_flight')
    require(flight[0x14C8 + index] == 8 and position(flight, index)[0] > position(spawn, index)[0] + 0x40,
            'projectile did not fly: ' + host)
    moved = state(directory, 'movement')
    require(word(moved, 0x94) == 0x89 and abs(word(moved, 0x96) - 0x152) <= 3,
            'player did not move on the parrot: ' + host)
    require(any(status == 8 for _, status in slots(moved, PARROT)), 'parrot was lost: ' + host)

    directory, receipt = capture('d11-forest-attack-' + host, HEAD, SCRIPTS['attack'], native)
    captures[directory.name] = receipt
    directories['attack'] = directory
    bodies = {tag: state(directory, tag) for tag in DUMPS['attack']}
    live = {i for i, status in slots(bodies['enemies'], VINE) if status == 8}
    require(len(live) == 2, 'both live vine enemies are not present: ' + host)
    defeated = set()
    for tag in DUMPS['attack'][1:]:
        for index, status in slots(bodies[tag], VINE):
            if status == 2:
                defeated.add(index)
    require(defeated == live, 'real projectiles did not defeat every vine enemy: ' + host)
    require(not any(status == 8 for _, status in slots(bodies['resolved3'], VINE)),
            'a vine enemy is still alive at the end: ' + host)
    require(any(status == 8 for _, status in slots(bodies['resolved3'], PARROT)),
            'parrot died during the attack: ' + host)

    directory, receipt = capture('d11-forest-normal-' + host, HEAD, SCRIPTS['normal'], native)
    captures[directory.name] = receipt
    directories['normal'] = directory
    goal, tape = state(directory, 'goal_room'), state(directory, 'tape')
    require(word(goal, 0x10B) == 0x4E and word(tape, 0x10B) == 0x4E and word(tape, 0x94) > 0x160,
            'normal exit did not reach the goal room: ' + host)
    normal = summary(directory, 'normal_map')
    require(normal['mode'] == 0x0E and normal['room'] == 0x4E and
            normal['flag'] == NORMAL_KEY and normal['sram'] == [NORMAL_KEY, NORMAL_KEY],
            'normal clear is not saved: ' + host)
    require(normal['map'] == 6 and normal['map_x'] == 296 and normal['map_y'] == 360,
            'normal return position differs: ' + host)
    reloaded = summary(directory, 'reloaded')
    require(reloaded['mode'] == 0x0E and reloaded['room'] == 0xC7 and
            reloaded['flag'] == NORMAL_KEY and reloaded['sram'] == [NORMAL_KEY, NORMAL_KEY],
            'normal reload differs: ' + host)

    directory, receipt = capture('d11-forest-secret-' + host, HEAD, SCRIPTS['secret'], native)
    captures[directory.name] = receipt
    directories['secret'] = directory
    after = summary(directory, 'aftergoal')
    require(after['mode'] == 0x0E and after['flag'] == SECRET_KEY and
            after['sram'] == [SECRET_KEY, SECRET_KEY], 'secret exit is not saved: ' + host)
    destination = summary(directory, 'destination')
    require(destination['map'] == 0 and destination['map_x'] == 440 and
            destination['map_y'] == 488 and destination['room'] == 0xC7,
            'secret portal destination differs: ' + host)
    require(summary(directory, 'reloaded')['flag'] == SECRET_KEY,
            'secret save did not reload: ' + host)

    directory, receipt = capture('d11-forest-death-' + host, HEAD, SCRIPTS['death'], native)
    captures[directory.name] = receipt
    directories['death'] = directory
    death, reentry = summary(directory, 'death_map'), summary(directory, 'reentry')
    require(death['mode'] == 0x0E and death['room'] == 3 and death['lives'] == 3 and
            death['flag'] == KEY_LEVEL, 'death did not return to the hub: ' + host)
    require(reentry['mode'] == 0x14 and reentry['room'] == 3 and reentry['lives'] == 3,
            're-entry after death differs: ' + host)
    return captures, route_states(directories)


def check_donor():
    captures, directories = {}, {}
    for route, script in SCRIPTS.items():
        directory, receipt = capture('d11-forest-only1-' + route + '-ref', DONOR, script)
        captures[directory.name] = receipt
        directories[route] = directory
    return captures, route_states(directories)


def compare_with_donor(reference, donor):
    require(set(reference) == set(donor), 'donor comparison is missing a route')
    for route, dumps in DUMPS.items():
        for tag in dumps:
            expected, actual = donor[route][tag], reference[route][tag]
            for key, value in expected.items():
                if actual[key] == value:
                    continue
                if route == 'entry' and tag == 'movement' and key == 'y' and abs(actual[key] - value) <= 3:
                    continue
                raise ValueError(f'route differs from demoOnly1 forest: {route}/{tag}/{key}')


def main():
    base, final, cfg, donor, changed = verify_recipe()
    captures = {}
    reference_captures, reference_states = check_host('ref', False)
    captures.update(reference_captures)
    native_captures, native_states = check_host('native', True)
    captures.update(native_captures)
    donor_captures, donor_states = check_donor()
    captures.update(donor_captures)
    compare_with_donor(reference_states, donor_states)

    new_body = state(Path(ROOT / 'local/captures/d11-forest-entry-ref'), 'entry1200')
    donor_body = state(Path(ROOT / 'local/captures/d11-forest-only1-entry-ref'), 'entry1200')
    for start, stop in COURSE_SEGMENTS:
        require(new_body[start:stop] == donor_body[start:stop],
                'loaded course buffer differs: ' + hex(start))

    report = dict(scope=__doc__.strip(), target=HEAD, rom_sha256=sha(final),
                  base_sha256=sha(base), donor_sha256=sha(donor), donor_target=DONOR,
                  changed_bytes_from_base=len(changed),
                  forest_cell=dict(room='003', goal_room='04E', entrance='map 6 0158/01A8',
                                   map16_clone='418000', shims='49E908'),
                  captures=captures,
                  results=dict(reference=reference_states, native=native_states,
                               donor=donor_states),
                  limits=['The fixtures teleport to the entrance and use camera/player position shortcuts; they do not qualify an unassisted whole-course traversal.',
                          'The single-shot attack of the earlier fixture is host-phase sensitive on this line; the tracked attack script uses three real shots and requires every live vine enemy to be defeated on both hosts.',
                          'The course-buffer comparison covers the initialized level tilemap, Map16/level buffer and sprite data regions against fresh demoOnly1-line captures.',
                          'No listening acceptance is inferred; the course uses existing recipient song selections.',
                          'The center Boss ending, other full-course/DK/death coverage and the broader restoration remain open.'])
    output = ROOT / 'local/reports/demo11-star-forest.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Forest Star checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

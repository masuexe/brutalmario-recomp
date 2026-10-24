#!/usr/bin/env python3
"""Check the restored Star World center node, route and center-course entry.

The fixture teleports to the lower-inner node with map-coordinate pokes (explicit
shortcut), walks Up with real input, samples the center special-warp-star display
twice and presses Y. The parent control keeps the same fixture on the accepted
head; the demoOnly1 predecessor control runs it on the donor line. This is bounded
qualification of the reported route and missing center display, not a full
lower-inner clear or an unassisted route.
"""
import json
from pathlib import Path

from audit_demo11_line import allowed_regions
from m1 import ROOT
from prepare_rom import verify
from qualify_demo11_lower_inner_music import capture
from qualify_demo11_star_sprites_safe import state
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom, lz2, make_candidate

ROOT = Path(ROOT)
HEAD = 'demo11-center-route'
BASE = 'demo11-star-visuals-flame'
DONOR = 'star-world-forest'
SCRIPT = 'demo11-star-center-route.script'
LEVEL_MAP = 0x10BEDF
NODE_CELL = 0x7A7
NODE_TILE = 0x5A
CENTER_LEVEL = 0x0A
MAP_WIDTH = 256
INTERIOR = (20, 60, 236, 200)
TAGS = ('lower_node', 'moving_up', 'center_arrival', 'center_anim', 'entry_attempt')


def read_json(path):
    return json.loads(path.read_text())


def image(target, path=None):
    cfg = read_json(ROOT / 'config/restorations' / (target + '.json'))
    rom = (ROOT / 'local/restoration' / (path or target) / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], target)
    return rom, cfg


def encode_literal(decoded):
    """Reproduce the recipe's reference-free LZ2 stream: literal chunks then FF."""
    encoded = bytearray()
    for offset in range(0, len(decoded), 1024):
        chunk = decoded[offset:offset + 1024]
        count = len(chunk) - 1
        encoded.extend((0xE0 | (count >> 8), count & 0xFF))
        encoded.extend(chunk)
    encoded.append(0xFF)
    return bytes(encoded)


def frame(directory, tag):
    return (directory / (tag + '.fb.bgrx')).read_bytes()


def display(directory, tag):
    body = frame(directory, tag)
    colours, opaque = set(), 0
    for y in range(INTERIOR[1], INTERIOR[3]):
        for x in range(INTERIOR[0], INTERIOR[2]):
            i = (y * MAP_WIDTH + x) * 4
            pixel = body[i:i + 3]
            if pixel != bytes(3):
                opaque += 1
            colours.add(pixel)
    colours.discard(bytes(3))
    return dict(colours=len(colours), opaque=opaque)


def frame_difference(a, b):
    return sum(1 for i in range(0, len(a), 4) if a[i:i + 3] != b[i:i + 3])


def verify_recipe():
    base, base_cfg = image(BASE)
    final, cfg = image(HEAD)
    require(final != base, 'candidate equals its parent')
    versions = read_json(ROOT / 'config/content-versions.json')['versions']
    pins = {version['id']: version['output'] for version in versions}
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    verify(donor, pins[cfg['donor']], cfg['donor'])
    verify(base, cfg['base_output'], 'intact parent')

    replay, _ = make_candidate(base, donor, cfg)
    require(replay == final, 'recipe does not reproduce the candidate')
    changed = {i for i, (a, b) in enumerate(zip(base, final)) if a != b}
    require(changed <= allowed_regions(cfg), 'unexpected byte outside the reviewed regions')

    decoded, compressed = lz2(base, LEVEL_MAP)
    pin = cfg['overworld_level_map']
    verify(decoded, pin['source_decoded'], 'recipient level map')
    verify(compressed, pin['source_compressed'], 'recipient level map stream')
    adapted = bytearray(decoded)
    for edit in pin['decoded_edits']:
        offset = edit['offset']
        require(adapted[offset:offset + 1].hex() == edit['before'], 'level map edit site changed')
        adapted[offset:offset + 1] = bytes.fromhex(edit['after'])
    verify(bytes(adapted), pin['adapted_decoded'], 'adapted level map')
    require({i for i in range(len(decoded)) if decoded[i] != adapted[i]} == {NODE_CELL},
            'level map adaptation is not the single center cell')
    require(decoded[NODE_CELL] == 0x00 and adapted[NODE_CELL] == CENTER_LEVEL,
            'center level assignment is not 00 -> 0A')

    block = cfg['raw_blocks'][0]
    data = bytes.fromhex(block['bytes'])
    verify(data, block['data'], 'stored level map block')
    require(encode_literal(adapted) == data, 'reference-free LZ2 stream differs from the pin')
    header = lorom(int(block['rats_address'], 16))
    start = lorom(int(block['destination_address'], 16))
    require(base[header:start + len(data)] == bytes(len(data) + 8),
            'parent block range is no longer empty')
    require(final[header:header + 4] == b'STAR' and header + 8 == start,
            'level map block header geometry changed')
    count = int.from_bytes(final[header + 4:header + 6], 'little')
    require(count == len(data) - 1 and
            int.from_bytes(final[header + 6:header + 8], 'little') == count ^ 0xFFFF,
            'level map block header fields changed')
    require(final[start:start + len(data)] == data, 'stored level map block differs')

    require(int(block['destination_address'], 16) == 0x37C008, 'loader pointer destination moved')
    require(final[lorom(0x04D803):lorom(0x04D803) + 2] == bytes.fromhex('08c0'),
            'loader low word is not the private stream')
    require(final[lorom(0x04D808)] == 0x37, 'loader source bank is not the private stream')
    require(base[lorom(0x04D803):lorom(0x04D803) + 2] == bytes.fromhex('dfbe') and
            base[lorom(0x04D808)] == 0x10, 'parent loader pointer changed')
    node = lorom(0x0CFF86)
    require(base[node] == 0x00 and final[node] == NODE_TILE, 'center node tile is not 00 -> 5A')
    require(donor[node] == NODE_TILE, 'restored node byte differs from the pinned donor')
    require(final[lorom(0x04D802)] == 0xA2 and final[lorom(0x04D807)] == 0xA9,
            'loader instruction bytes changed')
    return base, final, cfg, donor, changed


def check_states(directory, label, reference=None):
    bodies = {tag: state(directory, tag) for tag in TAGS}
    lower, moving = bodies['lower_node'], bodies['moving_up']
    center, anim = bodies['center_arrival'], bodies['center_anim']
    entry = bodies['entry_attempt']
    require(word(lower, 0x1F17) == 0x178 and word(lower, 0x1F19) == 0x1C8,
            'lower-inner start position differs: ' + label)
    require(word(lower, 0x13C1) == NODE_TILE, 'lower-inner node tile is absent: ' + label)
    require(word(moving, 0x1F19) == 0x01AD, 'Up movement from the lower node diverges: ' + label)
    require(word(center, 0x1F17) == 0x178 and word(center, 0x1F19) == 0x01A8,
            'center node was not reached: ' + label)
    require(word(center, 0x13C1) == NODE_TILE,
            'tile under the player at the center is not the special star tile: ' + label)
    for tag in TAGS[:4]:
        require(bodies[tag][0xCFA7] == NODE_TILE and bodies[tag][0xD7A7] == CENTER_LEVEL,
                'center map cell is not restored: ' + label + '/' + tag)
    require(entry[0x100] == 0x14, 'center entry did not reach level mode: ' + label)
    require(word(entry, 0x10B) == CENTER_LEVEL and word(entry, 0x13BF) == CENTER_LEVEL,
            'center entry does not load room 00A / translevel 0A: ' + label)
    if reference is not None:
        for tag in TAGS[:4]:
            other = reference[tag]
            require(word(bodies[tag], 0x1F17) == word(other, 0x1F17) and
                    word(bodies[tag], 0x1F19) == word(other, 0x1F19),
                    'route position differs from the donor predecessor: ' + label + '/' + tag)
            require(bodies[tag][0x13C1] == other[0x13C1] and
                    bodies[tag][0xCFA7] == other[0xCFA7] and bodies[tag][0xD7A7] == other[0xD7A7],
                    'center map cell differs from the donor predecessor: ' + label + '/' + tag)
        require(word(entry, 0x10B) == word(reference['entry_attempt'], 0x10B),
                'entry room differs from the donor predecessor: ' + label)
    return bodies


def main():
    base, final, cfg, donor, changed = verify_recipe()
    captures, results = {}, {}

    directory, receipt = capture('d11-center-ref', HEAD, SCRIPT)
    reference_bodies = check_states(directory, 'reference')
    captures[directory.name] = receipt
    first, second = display(directory, 'center_arrival'), display(directory, 'center_anim')
    animation = frame_difference(frame(directory, 'center_arrival'), frame(directory, 'center_anim'))
    require(first['colours'] >= 50 and first['opaque'] >= 5000,
            'reference center special-warp-star display is dark')
    require(second['colours'] >= 50 and second['opaque'] >= 5000,
            'reference center display lost its colours in the second sample')
    require(animation >= 4000, 'reference center display is not animated')
    results['reference'] = dict(first, second=second, animation_pixels=animation)

    directory, receipt = capture('d11-center-native', HEAD, SCRIPT, native=True)
    check_states(directory, 'native', reference_bodies)
    captures[directory.name] = receipt
    native_first = display(directory, 'center_arrival')
    native_animation = frame_difference(frame(directory, 'center_arrival'),
                                        frame(directory, 'center_anim'))
    require(native_first['colours'] >= 50 and native_first['opaque'] >= 5000,
            'native center special-warp-star display is dark')
    require(native_animation >= 4000, 'native center display is not animated')
    results['native'] = dict(native_first, animation_pixels=native_animation)

    directory, receipt = capture('d11-center-only1-ref', DONOR, SCRIPT)
    donor_bodies = check_states(directory, 'demoOnly1 predecessor', reference_bodies)
    captures[directory.name] = receipt
    donor_first = display(directory, 'center_arrival')
    require(donor_first['colours'] >= 50, 'demoOnly1 center display is unexpectedly dark')
    require(frame(directory, 'entry_attempt') == frame(ROOT / 'local/captures/d11-center-ref',
                                                       'entry_attempt'),
            'loaded center-course frame differs from the demoOnly1 predecessor')
    results['donor'] = donor_first

    directory, receipt = capture('d11-center-parent-ref', BASE, SCRIPT)
    captures[directory.name] = receipt
    parent = {tag: state(directory, tag) for tag in TAGS}
    require(word(parent['moving_up'], 0x1F19) == 0x01B2 and
            word(parent['center_arrival'], 0x1F17) == 0x17C and
            word(parent['center_arrival'], 0x1F19) == 0x01D0,
            'parent control no longer reproduces the route deviation')
    require(parent['center_arrival'][0x13C1] == 0x5D and
            parent['center_arrival'][0xCFA7] == 0x00 and
            parent['center_arrival'][0xD7A7] == 0x00,
            'parent control no longer reproduces the erased center cell')
    require(word(parent['entry_attempt'], 0x10B) == 0x0000,
            'parent control no longer loads room 000')
    dark = display(directory, 'center_arrival')
    dark_animation = frame_difference(frame(directory, 'center_arrival'),
                                      frame(directory, 'center_anim'))
    require(dark['colours'] <= 30 and dark['opaque'] <= 3000,
            'parent center display is unexpectedly lit')
    require(dark_animation <= 3000, 'parent center display is unexpectedly animated')
    results['parent'] = dict(dark, animation_pixels=dark_animation)

    report = dict(scope=__doc__.strip(), target=HEAD, rom_sha256=sha(final),
                  base_sha256=sha(base), donor_sha256=sha(donor),
                  changed_bytes_from_base=len(changed),
                  center_cell=dict(tile='%02X' % NODE_TILE, level='%02X' % CENTER_LEVEL,
                                   map_source='10BEDF', decoded_edit=hex(NODE_CELL)),
                  captures=captures, results=results,
                  limits=['The fixture teleports to the lower-inner node; it does not replay an unassisted course exit or traversal.',
                          'The center special-warp-star display is sampled as two animated frames; its colour phase is not compared pixel by pixel with the donor.',
                          'The center course is entered at room 00A on both hosts; its accepted unfinished boss ending is unchanged and no clear is claimed.',
                          'The center node/level restoration does not qualify the other full-course, DK or death coverage.'])
    output = ROOT / 'local/reports/demo11-center-route.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Center-route warp-star checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

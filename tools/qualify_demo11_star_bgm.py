#!/usr/bin/env python3
"""Qualify the Star World course BGM selections on the Demo 1-1 line.

The restored Star World courses still carried legacy-family BGM numbers. The
Brutal Mario wiki Star Road table and the individual star pages give the songs;
config/music-mapping.json gives the new-family slot IDs. Six one-byte level-data
parameters move to the new-family IDs. Both hosts must request the intended
slot and the native ARAM must hold that uploaded track.

Forest Star keeps the accepted demoOnly1-line substitute track. The wiki lists
vanilla BGM 02, but demo 1-1 has no custom upload for it and a request of 02
stalls the level load.
"""
import json
from pathlib import Path

from audit_demo11_line import allowed_regions
from m1 import ROOT
from prepare_rom import verify
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom, make_candidate

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
BASE = 'demo11-node-music'
APPLICATION_BASE = 0x5400
PIECES = {
    'lower-left': dict(slot=0x38, room=0x005, script='star-world-1-entry.script',
                       wiki='Grassland Star',
                       title='Town Where the West Wind Blows (Wild ARMs 2)'),
    'middle-left': dict(slot=0x5D, room=0x003, script='star-world-forest-entry.script',
                        wiki='Forest Star',
                        title='accepted demoOnly1-line substitute (wiki lists vanilla BGM 02)'),
    'upper-left': dict(slot=0x49, room=0x004, script='star-world-upper-left-entry.script',
                      wiki='Bay Star', title='Podol / Boundaries (Romancing SaGa 3)'),
    'upper-inner': dict(slot=0x51, room=0x007, script='star-world-upper-inner-entry.script',
                        wiki='Cave Star', title='Fear Factory (Donkey Kong Country)'),
    'upper-right': dict(slot=0x32, room=0x002, script='star-world-upper-right-entry.script',
                        wiki='Plains Star', title='Freiluftmusik (SaGa Frontier 2)'),
    'middle-right': dict(slot=0x58, room=0x009, script='star-world-middle-right-entry.script',
                         wiki='Sky Star', title="Grape Garden (Kirby's Adventure)"),
    'lower-right': dict(slot=0x54, room=0x008, script='star-world-lower-right-entry.script',
                        wiki='Snow Star', title='Jingle Bells'),
    'lower-inner': dict(slot=0x60, room=0x117, script='star-world-lower-inner-music.script',
                        wiki='Valley Star', title='Iceberg Ocean (Kirby\'s Dream Course)'),
    'center': dict(slot=0x7A, room=0x00A, script='star-world-center-entry.script',
                   wiki='Special Warp Star', title='Slide (Super Mario 64)'),
}
FOREST_SLOT = 0x5D
LEGACY_REJECTS = {
    'lower-left': (0x4A,),
    'upper-left': (0x28,),
    'upper-inner': (0x24,),
    'upper-right': (0x5D,),
    'middle-right': (0x2E,),
    'center': (0x30,),
}
UPPER_INNER_EXTRA = ('d11-bgm-upper-inner-ref2', 'd11-bgm-upper-inner-native2',
                     'demo11-star-bgm-upper-inner.script')


def song(rom, number):
    pointer = lorom(0x0FE000) + number * 3
    address = int.from_bytes(rom[pointer:pointer + 3], 'big')
    if address == 0:
        return None
    offset = lorom(address)
    count = int.from_bytes(rom[offset:offset + 2], 'little')
    if rom[offset + 2:offset + 4] != APPLICATION_BASE.to_bytes(2, 'little'):
        return None
    return rom[offset + 4:offset + 4 + count]


def requests(capture_name):
    events = [json.loads(line) for line in
              (ROOT / 'local/captures' / capture_name / 'wram.jsonl').read_text().splitlines()]
    return [int(event['val'], 16) for event in events
            if event['f'] >= 2000 and event['adr'] == '0x01dfb'
            and int(event['val'], 16) not in (0, 0x20, 0x80)]


def in_course(directory, room, slot):
    for path in sorted(directory.glob('*.wram.bin')):
        body = path.read_bytes()
        if body[0x100] == 0x14 and word(body, 0x10B) == room and body[0x0DDA] == slot:
            return path.name
    return None


def final_aram(directory):
    ram = (directory / 'apu-ram.bin').read_bytes()
    for number in range(256):
        body = song(final_rom, number)
        if body and len(body) > 32 and ram[APPLICATION_BASE:APPLICATION_BASE + len(body)] == body:
            return number, len(body)
    return None


def verify_recipe():
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    final = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    parent = json.loads((ROOT / 'config/restorations' / (BASE + '.json')).read_text())
    verify(base, parent['output'], 'intact parent')
    verify(final, cfg['output'], HEAD)
    donor_pin = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    pins = {version['id']: version['output'] for version in donor_pin}
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    verify(donor, pins[cfg['donor']], cfg['donor'])
    replay, _ = make_candidate(base, donor, cfg)
    require(replay == final, 'recipe does not reproduce the candidate')
    changed = {i for i, (a, b) in enumerate(zip(base, final)) if a != b}
    require(changed <= allowed_regions(cfg), 'unexpected byte outside the reviewed regions')
    require(len(changed) == 6, 'change is not the reviewed six music parameters: %d' % len(changed))
    patches = cfg['code_patches']
    require(len(patches) == 6, 'patch list differs')
    expected = [('3DA32B', '4b', '39'), ('58FBF1', '29', '4a'), ('198491', '25', '52'),
                ('1EEC26', '5e', '33'), ('5D9FBC', '2f', '59'), ('6D8EA6', '31', '7b')]
    require([(p['address'], p['before'], p['after']) for p in patches] == expected,
            'music parameter patches differ')
    require(final[lorom(0x38E1D6)] == 0x5E, 'Forest substitute music parameter changed')
    return base, final, cfg


def main():
    global final_rom
    base, final, cfg = verify_recipe()
    final_rom = final
    donor_rom = (ROOT / 'local/content-versions/demo-only-1/rom.sfc').read_bytes()
    captures, results = {}, {}
    for name, piece in PIECES.items():
        directory, receipt = capture('d11-bgm-' + name + '-ref', HEAD, piece['script'], False)
        captures[directory.name] = receipt
        sequence = requests(directory.name)
        require(piece['slot'] in sequence,
                'reference does not request the intended slot: %s %r' % (name, sequence))
        for legacy in LEGACY_REJECTS.get(name, ()):
            require(legacy not in sequence, 'legacy BGM still requested: %s' % name)
        directory, receipt = capture('d11-bgm-' + name + '-native', HEAD, piece['script'], True)
        captures[directory.name] = receipt
        tag = in_course(directory, piece['room'], piece['slot'])
        require(tag is not None, 'native course state missing the intended slot: ' + name)
        if name == 'upper-inner':
            ref2, native2, script = UPPER_INNER_EXTRA
            reference_directory, receipt = capture(ref2, HEAD, script, False)
            captures[ref2] = receipt
            native_directory, receipt = capture(native2, HEAD, script, True)
            captures[native2] = receipt
            tag = in_course(native_directory, piece['room'], piece['slot'])
            require(tag is not None, 'native playing state missing the intended slot: ' + name)
            require(in_course(reference_directory, piece['room'], piece['slot']) is not None,
                    'reference playing state missing the intended slot: ' + name)
            directory = native_directory
        match = final_aram(directory)
        require(match is not None and match[0] == piece['slot'],
                'native ARAM does not hold the intended upload: %s %r' % (name, match))
        results[name] = dict(wiki=piece['wiki'], title=piece['title'], slot='%04X' % piece['slot'],
                             reference_requests=['%02X' % value for value in sequence],
                             native_in_course=tag, native_aram_slot='%04X' % match[0],
                             native_aram_bytes=match[1])
    require(results['middle-left']['native_aram_slot'] == '%04X' % FOREST_SLOT,
            'Forest substitute track changed')

    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11StarWorldBgmSNESRecomp'
    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    require(build['rom_sha256'] == sha(final) and
            build['binary_sha256'] == sha(binary.read_bytes()), 'native build identity differs')

    report = dict(scope=__doc__.strip(), target=HEAD, base_target=BASE,
                  rom_sha256=sha(final), base_sha256=sha(base), binary_sha256=build['binary_sha256'],
                  changed_bytes=6, captures=captures, results=results,
                  wiki_sources=['https://brutalmario.fandom.com/wiki/Music',
                                'https://brutalmario.fandom.com/wiki/Star_World',
                                'https://brutalmario.fandom.com/wiki/Grassland_Star',
                                'https://brutalmario.fandom.com/wiki/Forest_Star',
                                'https://brutalmario.fandom.com/wiki/Bay_Star',
                                'https://brutalmario.fandom.com/wiki/Cave_Star',
                                'https://brutalmario.fandom.com/wiki/Plains_Star',
                                'https://brutalmario.fandom.com/wiki/Sky_Star',
                                'https://brutalmario.fandom.com/wiki/Snow_Star',
                                'https://brutalmario.fandom.com/wiki/Valley_Star',
                                'https://brutalmario.fandom.com/wiki/Special_Warp_Star'],
                  limits=['The node fixtures use explicit map teleports; this checks course music selection, not route completion.',
                          'The wiki numbers are legacy-family BGM numbers. This change applies the new-family IDs from config/music-mapping.json.',
                          'Forest Star keeps the accepted demoOnly1-line substitute; vanilla BGM 02 has no upload in demo 1-1 and stalls the load.',
                          'The Star-9 boss cue 98, the hub map BGM and other worlds stay outside this check.'])
    output = ROOT / 'local/reports/demo11-star-bgm.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Star World BGM checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

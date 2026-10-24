#!/usr/bin/env python3
"""Qualify the Star World lower-right Snow Star routes on the Demo 1-1 line.

The tracked lower-right scripts cover the ice cave on the current head: entry
and ordinary controls, the loaded ice Ptooie and penguin sprites, five real DK
coins with the real end-wall transfer and known goal-point match plus save and
console-reset reload, the real Santa reward key/keyhole secret exit, and a real
fall/death/re-entry. Reference and native runs must match fresh demoOnly1-line
captures under the same scripts.

The wiki describes the Snow Star as a seal cave with Santa's gift reward and
three matching goal-point blocks. The secret route stomps the seal to freeze
the water and reach the icy alcove with the key.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
DONOR = 'star-world-lower-right'
ROUTES = {
    'entry': 'star-world-lower-right-entry.script',
    'enemies': 'star-world-lower-right-enemies.script',
    'coins-save': 'star-world-lower-right-coins-save.script',
    'secret': 'star-world-lower-right-secret.script',
    'death': 'star-world-lower-right-death.script',
}
CLEAR_FLAG = 0x1EAA
DK_SAVED = 0x1F30
COUNTERS = (0x1420, 0x1422)
KEY_HELD = 0x1470
CUSTOM_ID = 0x1AB9E
SRAM_FLAG = 8
SRAM_FLAG_MIRROR = 0x1B5
SRAM_DK = 0x7D1
SRAM_CHECKSUM = 0x7DC
SNOW_SLOT = 0x54
PRE_ENTRY = {'title', 'files', 'intro', 'selected'}
ROUTE_SAMPLES = {
    'entry': {'layout', 'graphics', 'active', 'early', 'entry180', 'entry600', 'move', 'later'},
    'enemies': {'plants_loaded', 'plants_active', 'penguins_loaded', 'penguins_active'},
    'coins-save': {'active', 'coin1', 'coin2', 'coin3', 'coin4', 'coin5', 'end_ready',
                   'destination', 'slot1', 'slot2', 'slot3', 'slots_stopped', 'reward',
                   'saved_map', 'file_reload', 'reload_node', 'reload_reentry'},
    'secret': {'key_held', 'secret_reward', 'secret_map', 'secret_warp'},
    'death': {'active', 'death_return', 'reentry'},
}


def blob(capture_name, tag, suffix='wram.bin'):
    return (ROOT / 'local/captures' / capture_name / (tag + '.' + suffix)).read_bytes()


def state(capture_name, tag):
    body = blob(capture_name, tag)
    return dict(mode=body[0x100], room=word(body, 0x10B), x=word(body, 0x94),
                y=word(body, 0x96), life=body[0x0DBE], clear=body[CLEAR_FLAG],
                dk=body[DK_SAVED], counts=tuple(body[address] for address in COUNTERS),
                map=body[0x1F11], mapxy=body[0x1F17:0x1F1B].hex(),
                key=body[KEY_HELD])


def sprites(capture_name, tag):
    body = blob(capture_name, tag)
    return [dict(slot=index, custom=body[CUSTOM_ID + index], id=body[0x9E + index],
                 status=body[0x14C8 + index], c2=body[0xC2 + index],
                 stopped=body[0x1528 + index], tile=body[0x151C + index])
            for index in range(12) if body[0x14C8 + index]]


def music_requests(capture_name):
    events = [json.loads(line) for line in
              (ROOT / 'local/captures' / capture_name / 'wram.jsonl').read_text().splitlines()]
    return [int(event['val'], 16) for event in events
            if event['f'] >= 2000 and event['adr'] == '0x01dfb'
            and int(event['val'], 16) not in (0, 0x20, 0x80)]


def check_route(host, route, script, native):
    tag = 'native' if native else 'ref'
    name = 'd11-lr-' + route + '-' + tag
    directory, receipt = capture(name, HEAD, script, native)
    require(receipt['rom_sha256'] == sha(head_rom), 'capture ROM differs: ' + name)
    if route == 'entry':
        require(blob(name, 'layout')[0xC800:0x10000] == blob(name, 'graphics')[0xC800:0x10000],
                'low Map16 buffer was corrupted: ' + host)
        for sample in ('early', 'entry180', 'entry600'):
            body = state(name, sample)
            require(body['mode'] == 0x14 and body['room'] == 0x008 and body['life'] == 4,
                    'entry sample differs: ' + host + '/' + sample)
        require(state(name, 'move')['x'] != state(name, 'entry600')['x'],
                'ordinary movement changed nothing: ' + host)
        if not native:
            sequence = music_requests(name)
            require(SNOW_SLOT in sequence, 'Snow Star slot 54 is not requested: ' + str(sequence))
    if route == 'enemies':
        plants = sprites(name, 'plants_loaded')
        require(all(any(sprite['custom'] == 0x57 and sprite['c2'] == value for sprite in plants)
                    for value in (0, 1)),
                'ice Ptooie and projectile are missing: ' + host)
        require(any(sprite['custom'] == 0x58 for sprite in sprites(name, 'penguins_loaded')),
                'penguin sprite is missing: ' + host)
    if route == 'coins-save':
        for number in range(1, 5):
            require(state(name, 'coin%d' % number)['counts'] == (number, number),
                    'real coin counter differs: ' + host + '/%d' % number)
        coin5 = state(name, 'coin5')
        require(coin5['counts'] == (5, 5) and coin5['dk'] == 0x80 and coin5['life'] == 5,
                'coin 5 DK/1-up result differs: ' + host)
        require(state(name, 'destination')['mode'] == 0x14 and
                state(name, 'destination')['room'] == 0x026,
                'end-wall transfer differs: ' + host)
        stopped = [sprite for sprite in sprites(name, 'slots_stopped') if sprite['custom'] == 9]
        require(len([sprite for sprite in stopped
                     if sprite['stopped'] == 1 and sprite['tile'] == 0x8C]) == 3,
                'three matching goal-point symbols differ: ' + host)
        require(any(sprite['id'] == 0x4A for sprite in sprites(name, 'reward')),
                'goal sphere sprite is missing: ' + host)
        saved = state(name, 'saved_map')
        require(saved['mode'] == 0x0E and saved['clear'] == 0x8A and saved['life'] == 5,
                'normal clear state differs: ' + host)
        for sample in ('saved_map', 'file_reload', 'reload_reentry'):
            body = state(name, sample)
            require(body['clear'] == 0x8A and body['dk'] == 0x80,
                    'saved progress differs: ' + host + '/' + sample)
        for sample in ('saved_map', 'file_reload', 'reload_reentry'):
            saved_ram = blob(name, sample, 'sram.bin')
            require(saved_ram[SRAM_FLAG] == 0x8A and saved_ram[SRAM_FLAG_MIRROR] == 0x8A,
                    'saved SRAM flag differs: ' + host + '/' + sample)
            require(saved_ram[SRAM_DK] == 0x80 and
                    saved_ram[SRAM_CHECKSUM:SRAM_CHECKSUM + 2] == bytes.fromhex('da59'),
                    'saved SRAM DK/checksum differs: ' + host + '/' + sample)
    if route == 'secret':
        require(state(name, 'key_held')['key'] == 1, 'the key is not carried: ' + host)
        secret = state(name, 'secret_map')
        require(secret['mode'] == 0x0E and secret['clear'] == 0x8B,
                'secret clear flag differs: ' + host)
        warp = state(name, 'secret_warp')
        require(warp['mode'] == 0x0E and warp['map'] == 0 and warp['mapxy'] == '28014800',
                'Warp Star destination differs: ' + host)
        saved_ram = blob(name, 'secret_map', 'sram.bin')
        require(saved_ram[SRAM_FLAG] == 0x8B and saved_ram[SRAM_FLAG_MIRROR] == 0x8B and
                saved_ram[SRAM_DK] == 0x80, 'secret SRAM differs: ' + host)
    if route == 'death':
        require(state(name, 'death_return')['mode'] == 0x0E and
                state(name, 'death_return')['life'] == 3, 'death return differs: ' + host)
        reentry = state(name, 'reentry')
        require(reentry['mode'] == 0x14 and reentry['room'] == 0x008 and reentry['life'] == 3,
                'death re-entry differs: ' + host)
    return name, receipt


def compare_samples(a, b, samples):
    for sample in samples:
        left, right = state(a, sample), state(b, sample)
        require(left == right, f'sample differs: {sample}: {left} != {right}')


def main():
    global head_rom
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    head_rom = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    require(sha(head_rom) == cfg['output']['sha256'], 'head ROM identity differs')
    captures = {}
    for route, script in ROUTES.items():
        name, receipt = check_route('reference', route, script, False)
        captures[name] = receipt
        native_name, receipt = check_route('native', route, script, True)
        captures[native_name] = receipt
        compare_samples(native_name, name, ROUTE_SAMPLES[route])
    for route, script in ROUTES.items():
        name = 'd11-lr-only1-' + route + '-ref'
        directory, receipt = capture(name, DONOR, script, False)
        captures[name] = receipt
        compare_samples(name, 'd11-lr-' + route + '-ref', ROUTE_SAMPLES[route])

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11StarWorldBgmSNESRecomp'
    require(build['rom_sha256'] == sha(head_rom) and
            build['binary_sha256'] == sha(binary.read_bytes()), 'native build identity differs')

    report = dict(scope=__doc__.strip(), head=HEAD, donor_target=DONOR,
                  rom_sha256=sha(head_rom), binary_sha256=build['binary_sha256'],
                  captures=captures,
                  wiki_sources=['https://brutalmario.fandom.com/wiki/Snow_Star',
                                'https://brutalmario.fandom.com/wiki/Music',
                                'https://wikiwiki.jp/kitikumario/',
                                'docs/walkthrough-reference.md'],
                  limits=['The scripts use labelled coordinate shortcuts and damage immunity; the coins, end-wall transfer, slots, goal sphere, Santa reward, keyhole and deaths are real guest actions.',
                          'The normal clear is qualified. The user previously accepted normal and key exits on the demoOnly1 line; this run re-qualifies both on the Demo 1-1 head.',
                          'An unassisted full traversal and listening acceptance are not claimed.',
                          'The save flag, DK bit and SRAM constants are recipient-local. The demoOnly1 line matches them on these scripts.'])
    output = ROOT / 'local/reports/demo11-star-lower-right-route.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Lower-right Snow Star route checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

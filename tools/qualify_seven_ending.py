#!/usr/bin/env python3
"""Qualify assisted fight phases, the injected defeat boundary and T-room pit.

No earned fight clear or saved completion is inferred from the ending fixture.
Captures and preparation receipts remain immutable; reports use fresh paths.
"""
import argparse
import json
from pathlib import Path
import re

import native_seven_ending as stop
import native_seven_ending_test as ending
import native_seven_ending_tiles as graphics
import native_seven_ending_1up as mushroom
from native_seven_child import ROOT, settings, identity, packs, parent_identity
from prepare_rom import verify
from qualify_seven_child import SUFFIXES, body, room, require, read
from restoration_targets import RESTORATIONS
from restore_star_world_1 import lorom, sha, write_verified
from runtime_patches import patch_plan
from seven_fight_route import route

def native_capture(directory, target, script, *, executes_master=False):
    receipt = read(directory/'receipt.json')
    cfg = read(ROOT/'config/restorations'/(target+'.json'))
    build = read(ROOT/'local/build'/target/'m1-build.json')
    require(receipt['stage'] == 'native' and receipt['target'] == target, 'native role differs')
    require(receipt['rom_sha256'] == build['rom_sha256'] == cfg['output']['sha256'], 'native ROM differs')
    require(receipt['native_content'] == build['native_content'] == parent_identity(target), 'native packs differ')
    require(receipt['host_binary_sha256'] == build['binary_sha256'] ==
            sha((ROOT/'local/build'/target/RESTORATIONS[target]['binary']).read_bytes()), 'native binary differs')
    require(receipt['analysis'] == build['analysis'] and receipt['runtime_patches'] ==
            build['runtime_patches'] == patch_plan(), 'native analysis/runtime differs')
    require(receipt['route_sha256'] == sha(script) and
            (directory/'input.script').read_bytes() == b'turbo on\n'+script, 'native executed input differs')
    program = read(directory/'program-manifest.json')
    forbidden = (0x1e, 0x9e, 0x22, 0xa2, 0x25, 0xa5, 0x26, 0xa6, 0x36, 0xb6)
    require(not any(int(key.split(':')[0], 16) >> 16 in forbidden for key in program['nodes']),
            'AOT overlaps an immutable split bank')
    log = (directory/'run.log').read_text()
    require('exit: script quit after' in log and 'TIMEOUT' not in log, 'native route incomplete')
    if executes_master:
        require(re.search(r'bank=A2 resolutions=\d+ executed_page_instructions=[1-9]\d*', log),
                'immutable master was not executed')
    return receipt


def reference_capture(directory, script):
    receipt = read(directory/'receipt.json')
    donor = read(ROOT/'config/boss-donor.json')['output']
    verify((ROOT/'local/content-versions/boss/rom.sfc').read_bytes(), donor, 'official Boss image')
    require(receipt['rom_sha256'] == donor['sha256'] and receipt['script_sha256'] == sha(script)
            and (directory/'input.script').read_bytes() == script, 'source ROM/input differs')
    for field, path in (('frontend_sha256', 'local/build/snesref/snesref'),
                        ('core_sha256', 'local/upstream/snes9x/libretro/snes9x_libretro.so')):
        require(receipt[field] == sha((ROOT/path).read_bytes()), 'reference binary differs')
    require(receipt['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled' and
            ' quit' in (directory/'run.log').read_text() and
            'TIMEOUT' not in (directory/'run.log').read_text(), 'source route/config incomplete')
    return receipt


def samples(directory):
    result = {}
    tags = sorted(p.name.removesuffix('.wram.bin') for p in directory.glob('*.wram.bin'))
    require(tags, 'capture has no dumps')
    reference = read(directory/'receipt.json').get('stage') != 'native'
    suffixes = ({key: SUFFIXES[key] for key in ('wram.bin','vram.bin','sram.bin','fb.bgrx')}
                if reference else SUFFIXES)
    if reference:
        suffixes['sram.bin'] = 2048  # Official Boss header: 2 KiB SRAM, versus recipient 32 KiB.
    for tag in tags:
        result[tag] = {}
        for suffix, size in suffixes.items():
            data = (directory/(tag+'.'+suffix)).read_bytes()
            require(data and (size is None or len(data) == size), 'dump empty/size differs')
            result[tag][suffix] = sha(data)
    return result


def position(data):
    return [int.from_bytes(data[x:x+2], 'little') for x in (0x94, 0x96)]


def qualify(args):
    target = args.target
    modules = [stop, ending, graphics]
    if target == mushroom.TARGET:
        modules.append(mushroom)
    preparation = []
    for module in modules:
        cfg, recipe = settings(module.TARGET)
        parent = ROOT/'local/restoration'/module.PARENT
        directory = ROOT/'local/restoration'/module.TARGET
        source = (ROOT/'local/content-versions/boss/rom.sfc').read_bytes()
        parent_rom = (parent/'rom.sfc').read_bytes()
        payload_name = 'seven-graphics.bin' if module is graphics else 'seven-code.bin'
        payload = (parent/payload_name).read_bytes()
        adapted = module.adapt(parent_rom, payload, source, recipe)
        rom, code = (parent_rom, adapted) if module is stop else adapted
        require(rom == (directory/'rom.sfc').read_bytes() and code == (directory/payload_name).read_bytes(),
                'prepared output does not reproduce')
        verify(rom, cfg['output'], 'ending descendant ROM')
        for pack in packs(module.TARGET):
            verify((directory/pack['pack_file']).read_bytes(), pack, 'ending descendant pack')
        receipt = read(directory/'input-manifest.json')
        require(receipt['config'] == cfg and receipt['content'] == identity(module.TARGET) and
                receipt['builder_sha256'] == sha(Path(module.__file__).read_bytes()) and
                receipt['parent_receipt_sha256'] == sha((parent/'input-manifest.json').read_bytes()) and
                receipt['donor_sha256'] == sha(source), 'preparation receipt differs')
        preparation.append({'target': module.TARGET, 'rom': cfg['output'], 'master': recipe['master_payload'],
                            'graphics': recipe['font_lifecycle']['graphics_payload'],
                            'receipt_sha256': sha((directory/'input-manifest.json').read_bytes())})
    source = ROOT/'local/captures'/args.donor_ending
    native = ROOT/'local/captures'/(args.ending+'-native')
    captures = []
    source_script = (ROOT/'recomp/inputs/seven-ending-donor-fixture.script').read_bytes()
    native_script = (ROOT/'recomp/inputs/seven-ending-native-fixture.script').read_bytes()
    reference_capture(source, source_script); native_capture(native, target, native_script, executes_master=True)
    graphics_payload = (ROOT/'local/restoration'/target/'seven-graphics.bin').read_bytes()
    english, japanese = graphics_payload[0x627d:0x6a7d], graphics_payload[0x5a7d:0x627d]
    require(len(english) == len(japanese) == 2048, 'font pack slices differ')
    walking = []
    for directory, expected_room in ((source, 0x174), (native, 0x17b)):
        queued, late = body(directory, 'ending_queued'), body(directory, 'ending_late')
        require(queued[0xcb] == 0x15 and room(queued) == 0xff, 'ending threshold not reached')
        require(late[0x100] == 0x14 and room(late) == expected_room and position(late) == [16,352],
                'T-room ending not reached')
        death, returned = body(directory, 'test_right10'), body(directory, 'test_after_death')
        require(death[0x71] == 9 and position(death) == [744,456], 'right pit death not reached')
        require(returned[0x100] == 0x0e and returned[0xdbe]+1 == death[0xdbe], 'life loss/map return differs')
        require(body(directory, 'test_right09')[0x71] == 0, 'walk was already dying before pit')
        captures.append(directory)
    for i in range(1,11):
        tag = f'test_right{i:02}'
        a,b = body(source,tag),body(native,tag)
        require(position(a) == position(b), 'pre-death traversal coordinates differ')
        walking.append({'tag':tag,'position':position(b),'action':b[0x71],
                        'donor_lives':a[0xdbe],'native_lives':b[0xdbe]})
    for tag in ('ending_late','test_after_death'):
        require((native/(tag+'.vram.bin')).read_bytes()[0x9000:0x9800] == english, 'English font not restored')
    require((source/'ending_late.vram.bin').read_bytes()[0x9000:0x9800] == japanese, 'source font differs')
    # Normalize only the eight reviewed pole tile words to the official blank.
    # Check their actual pattern pixels are blank; keep all Map16 IDs/physics.
    av = (source/'ending_late.vram.bin').read_bytes()
    bv = (native/'ending_late.vram.bin').read_bytes()
    normalized = bytearray(bv[0x4000:0x6000])
    graphics_words = (0x04a4,0x04a5,0x04a6,0x04a7,0x18b4,0x18b5,0x18b6,0x18b7)
    normalized_tiles = 0
    for offset in range(0,len(normalized),2):
        word = int.from_bytes(normalized[offset:offset+2],'little')
        if word in graphics_words:
            tile = word & 0x3ff
            require(bv[tile*32:(tile+1)*32] == bytes(32), 'adapted pole graphics are not blank')
            require(av[0x4000+offset:0x4002+offset] == bytes.fromhex('f810'), 'source pole is not blank')
            normalized[offset:offset+2] = bytes.fromhex('f810')
            normalized_tiles += 1
    # The loaded foreground map contains two copies of the eight blank pole subtiles.
    require(normalized_tiles == 16 and av[0x4000:0x6000] == normalized, 'T-room foreground differs outside adapted pole')
    foreground_tiles = {int.from_bytes(av[i:i+2],'little') & 0x3ff for i in range(0x4000,0x6000,2)}
    require(all(av[t*32:(t+1)*32] == bv[t*32:(t+1)*32] for t in foreground_tiles),
            'retained foreground character pixels differ')
    a,b = body(source,'ending_late'),body(native,'ending_late')
    for start in (0xc800,0x1c800):
        require(a[start:start+0x510] == b[start:start+0x510], 'T-room Map16/collision IDs differ')
    phases = []
    for host, name in (('donor',args.donor_phases),('native',args.native_phases)):
        directory = ROOT/'local/captures'/name
        script = route(host).encode()
        if host == 'native': native_capture(directory,target,script,executes_master=True)
        else: reference_capture(directory,script)
        observed = []
        for path in sorted(directory.glob('phase*.wram.bin')):
            data = body(directory,path.name.removesuffix('.wram.bin'))
            require(data[0x100] == 0x14 and room(data) == 0xff and data[0x1531] <= 6 and
                    data[0x14c8+9] == 8 and data[0x1ab9e+9] == 0x2a,
                    'assisted phase sample escaped fight')
            observed.append({'tag':path.name.removesuffix('.wram.bin'),'tier':data[0x1531],
                             'damage':int.from_bytes(data[0x1ff00:0x1ff02],'little')})
        require({x['tier'] for x in observed} == set(range(7)), 'not all seven joined-part tiers sampled')
        phases.append({'host':host,'samples':observed})
        captures.append(directory)
    mushroom_evidence = None
    if target == mushroom.TARGET:
        donor_script = (ROOT/'recomp/inputs/seven-ending-mushroom-donor.script').read_bytes()
        native_script = (ROOT/'recomp/inputs/seven-ending-mushroom-native.script').read_bytes()
        donor_capture = ROOT/'local/captures'/args.mushroom_donor
        native_mushroom = ROOT/'local/captures'/args.mushroom
        reference_capture(donor_capture, donor_script)
        native_capture(native_mushroom, target, native_script, executes_master=True)
        records, events = [], {}
        for directory, expected_room, host in ((donor_capture, 0x174, 'donor'),
                                               (native_mushroom, 0x17b, 'native')):
            start = body(directory, 'ending_late')
            before = body(directory, 'mushroom_before')
            require(before[0x100] == 0x14 and room(before) == expected_room,
                    'mushroom walk did not reach the T room')
            require(before[0xdbe] == start[0xdbe], 'life changed before the hidden checkpoints')
            first_spawn = first_life = None
            for index in range(1, 81):
                sample = body(directory, f'mushroom{index:03d}')
                require(sample[0x100] == 0x14 and room(sample) == expected_room,
                        'mushroom sample escaped the T room')
                if first_spawn is None and any(sample[0x9e+slot] == 0x78 and
                                               sample[0x14c8+slot] == 8 for slot in range(12)):
                    first_spawn = index
                if first_life is None and sample[0xdbe] == before[0xdbe]+1:
                    first_life = index
                require(sample[0xdbe] in (before[0xdbe], before[0xdbe]+1),
                        'life count left the reviewed range')
            require(first_spawn is not None and first_life is not None,
                    'hidden checkpoint did not spawn or award the mushroom')
            require(first_life > first_spawn, 'life award preceded the mushroom spawn')
            returned = body(directory, 'mushroom_map')
            require(returned[0x100] == 0x0e and returned[0xdbe] == before[0xdbe],
                    'post-mushroom pit did not consume the awarded life')
            events[host] = {'first_spawn': first_spawn, 'first_life': first_life}
            records.append({'host': host, 'capture': str(directory.relative_to(ROOT)),
                            'first_spawn': first_spawn, 'first_life': first_life,
                            'lives': [before[0xdbe], before[0xdbe]+1, returned[0xdbe]]})
        require(events['donor'] == events['native'],
                'hidden checkpoint timing differs between hosts')
        donor_rom = (ROOT/'local/content-versions/boss/rom.sfc').read_bytes()
        target_rom = (ROOT/'local/restoration'/target/'rom.sfc').read_bytes()
        def property_byte(image):
            return image[lorom(0x07f4c7)+0x78]
        spawn_tag = f"mushroom{events['donor']['first_spawn']:03d}"
        donor_spawn = body(donor_capture, spawn_tag)
        native_spawn = body(native_mushroom, spawn_tag)
        require(donor_spawn[0x9e+11] == native_spawn[0x9e+11] == 0x78,
                'spawned sprite id differs')
        require(donor_spawn[0x1685] == property_byte(donor_rom) == 0xc2 and
                native_spawn[0x1685] == property_byte(target_rom) == 0xd2,
                'sprite property provenance differs')
        captures.extend((donor_capture, native_mushroom))
        mushroom_evidence = {
            'samples': records,
            'sprite_property': 'Sprite 78 property byte $167A/$1685 comes from the image sprite '
                               'database: official C2, recipient D2 (table $07F4C7). The '
                               'recipient value is retained; spawn id, state and life award match.',
            'scope': 'Ordered hidden checkpoints in the T room spawn a real sprite 78 in both '
                     'hosts. Both hosts award one life at the same sample index, and the pit '
                     'death consumes that life. Neither host writes the life count.'}
    completion = None
    if target == mushroom.TARGET:
        save_ranges = ((0x1ea2,0x1f02),(0x1f02,0x1f11),(0x1f27,0x1f2b),
                       (0x1f2e,0x1f2f),(0x1f2f,0x1f3b),(0x182c,0x1844))
        starts = {}
        for directory, label in ((source,'donor'),(native,'native')):
            start, end = body(directory,'fight180'), body(directory,'test_after_death')
            for low, high in save_ranges:
                require(start[low:high] == end[low:high],
                        f'{label} ending wrote saved progress at {low:05X}')
            require(start[0x1febe] == end[0x1febe] == 0, 'master flag changed')
            starts[label] = start
        differing = [f'{index:05X}' for low, high in save_ranges for index in range(low,high)
                     if starts['donor'][index] != starts['native'][index]]
        completion = {
            'save_progress_written': False,
            'master_flag_7FEBE': 0,
            'preexisting_level_status_differences': differing,
            'scope': 'Neither host changes saved level status, events, switches, completion '
                     'counter, DK bits, midway masks or $7FEBE across the ending path. The listed '
                     'level-status differences exist before the fight and are version-local '
                     'starting progress. The fixture does not prove an earned defeat.'}
    comparisons = []
    routes = [('star1','recomp/inputs/demo11-star1-entry.script'),
              ('boss','recomp/inputs/demo11-hp-boss-bc.script'),
              ('lifts','recomp/inputs/native-sprite9e-room146.script')]
    routes += [(x,f'recomp/inputs/seven-child-existing-{x}.script') for x in ('0d8','0e2','0e3','0e4')]
    for name, script_path in routes:
        oldname = 'seven-regression-v1-'+name if not name.startswith('0') else 'seven-child-existing-v1-parent-'+name
        old, new = ROOT/'local/captures'/oldname, ROOT/'local/captures'/(args.regression+'-'+name)
        script = (ROOT/script_path).read_bytes()
        native_capture(old,'demo11-native-seven-font-entry',script)
        native_capture(new,target,script)
        old_samples, new_samples = samples(old),samples(new)
        require(old_samples == new_samples, 'unchanged regression differs: '+name)
        comparisons.append({'route':name,'files':sum(len(s) for s in new_samples.values()),'samples':new_samples})
        captures.extend((old,new))
    evidence = [{'directory':str(d.relative_to(ROOT)), 'receipt_sha256':sha((d/'receipt.json').read_bytes()),
                 'script_sha256':sha((d/'input.script').read_bytes()),
                 'log_sha256':sha((d/'run.log').read_bytes()),'samples':samples(d)} for d in captures]
    scope = ('Assisted real-damage tiers 0..6; injected defeat boundary; original T ending, '
             'ordinary rightward pit death, English font and map return. No earned full-fight '
             'or saved-clear proof.')
    deferred = ['Full earned defeat and saved completion remain open.']
    if target == mushroom.TARGET:
        scope += (' The hidden ordered checkpoints are restored only in room 17B and spawn a '
                  'real sprite 78 at the same sample index in both hosts.')
        deferred.append('Hidden checkpoints outside room 17B keep the recipient early return.')
    else:
        deferred.append('Source gains one life during the walk; recipient retains its own life-award behavior.')
    deferred.append('Post-death timing/map coordinates and status/font graphics are version-specific.')
    report = {'target':target,'preparation':preparation,'walking':walking,'assisted_phases':phases,
              'regressions':comparisons,'evidence':evidence,
              'scope':scope,'deferred':deferred}
    if mushroom_evidence is not None:
        report['mushroom'] = mushroom_evidence
    if completion is not None:
        report['completion'] = completion
    write_verified(ROOT/args.output,(json.dumps(report,indent=2)+'\n').encode())
    print(args.output,sha((ROOT/args.output).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ending',default='seven-ending-tiles-v1')
    parser.add_argument('--donor-ending',default='seven-ending-visuals-v1-donor')
    parser.add_argument('--native-phases',default='seven-ending-tiles-phases-v1-native')
    parser.add_argument('--donor-phases',default='seven-ending-test-phases-v1-donor')
    parser.add_argument('--regression',default='seven-ending-tiles-v1')
    parser.add_argument('--target',default=graphics.TARGET)
    parser.add_argument('--mushroom',default='seven-ending-mushroom-v1-native')
    parser.add_argument('--mushroom-donor',default='seven-ending-mushroom-v1-donor')
    parser.add_argument('--output',required=True)
    qualify(parser.parse_args())

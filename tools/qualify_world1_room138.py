#!/usr/bin/env python3
"""Qualify the room138 missing-song recovery, entry and earlier course regression.

Exact musical graphs and upload images are checked; audible output and the
complete room138 course, exits and collectibles remain unqualified.
"""
import csv
import json
from pathlib import Path

from audit_lower_inner_music import song_graph
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import adapt_music, lorom

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / 'config/restorations/world1-room138-audio.json').read_text())
    sequence_cfg = json.loads((ROOT / 'config/restorations/world1-room138.json').read_text())
    intermediate = (ROOT / 'local/restoration/world1-room138/rom.sfc').read_bytes()
    candidate = (ROOT / 'local/restoration/world1-room138-audio/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/world1-next-course/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(intermediate, cfg['base_output'], 'sequence intermediate')
    verify(base, sequence_cfg['base_output'], 'accepted cumulative base')
    require({i for i, (a, b) in enumerate(zip(intermediate, candidate)) if a != b} == {lorom(0x0fcf7e)},
            'unexpected intermediate-to-final change')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')
    music = sequence_cfg['music']
    start = lorom(int(music['source_address'], 16))
    group = donor[start:start + music['source_group']['size']]
    verify(group, music['source_group'], 'source bank')
    payload = adapt_music(group, music)
    verify(payload, music['adapted'], 'relocated song')
    source_graph = song_graph(group[4:-4], music['source_base'], music['source_base'] + music['sequence_offset'])
    target_graph = song_graph(payload[4:-4], 0x5400, 0x5400)
    require(source_graph == target_graph, 'donor musical graph differs')
    parsed, matches = 0, []
    for song_id in range(256):
        entry = lorom(0x0fe000) + song_id * 3
        try:
            position = lorom(int.from_bytes(base[entry:entry+3], 'big'))
            count = word(base, position)
            if word(base, position+2) != 0x5400 or count < 64:
                continue
            graph = song_graph(base[position+4:position+4+count], 0x5400, 0x5400)
        except (ValueError, IndexError):
            continue
        parsed += 1
        if graph == source_graph:
            matches.append(song_id)
    require(parsed == 53 and not matches, 'review existing-song comparison')
    allocation = music['allocation']['offset']
    size = len(payload) - 1
    protected = b'STAR' + size.to_bytes(2, 'little') + (size ^ 0xffff).to_bytes(2, 'little') + payload
    require(candidate[allocation:allocation + len(protected)] == protected, 'music RATS block differs')
    require(base[allocation:allocation + music['allocation']['size']] == bytes(music['allocation']['size']),
            'music allocation was occupied')
    slot = lorom(int(music['pointer_address'], 16))
    require(base[slot:slot+3] == bytes(3) and candidate[slot:slot+3] == bytes.fromhex('508008'),
            'private song pointer differs')
    missing = lorom(0x0fe063)
    require(candidate[missing:missing+3] == base[missing:missing+3] == bytes(3), 'global21 changed')
    control = lorom(0x5cfbe5)
    require(base[control-2:control+2] == bytes.fromhex('406022ff'), 'music object changed')
    require(candidate[control-2:control+2] == bytes.fromhex('40607fff'), 'private music selection differs')
    aliases = [r for r in range(512) if base[lorom(0x05e000)+r*3:lorom(0x05e000)+r*3+3] == bytes.fromhex('e5eb5c')]
    require(aliases == [0x138], 'music object stream has other room aliases')
    allowed = set(range(allocation, allocation + len(protected))) | set(range(slot, slot+3)) | {control, lorom(0x0fcf7e)}
    require(candidate[lorom(0x0fcf7e)] == base[lorom(0x0fcf21)] == 2, 'sample-bank dependency differs')
    changed = {i for i, (a, b) in enumerate(zip(base, candidate)) if a != b}
    require(len(candidate) == len(base) and changed <= allowed, 'unreviewed ROM difference')

    build = json.loads((ROOT / 'local/build/world1-room138-audio/m1-build.json').read_text())
    binary = ROOT / 'local/build/world1-room138-audio/BrutalMarioWorld1Room138AudioSNESRecomp'
    require(build['rom_sha256'] == sha(candidate) and sha(binary.read_bytes()) == build['binary_sha256'],
            'native build identity differs')
    for filename in ('world1-room138-entry.script', 'world1-room138-natural-entry.script'):
        allowed_writes = {0x109: 1, 0x100: 1, 0x1f11: 2, 0x1f17: 8,
                          0x1f1f: 8, 0x1497: 1, 0x94: 4, 0x7b: 1, 0x7d: 1}
        for line in (ROOT / 'recomp/inputs' / filename).read_text().splitlines():
            parts = line.split()
            if parts and parts[0] in ('poke', 'forcepoke', 'pokefor'):
                address = int(parts[1], 16)
                require(address in allowed_writes and len(bytes.fromhex(parts[-1])) <= allowed_writes[address],
                        'review new fixture write: ' + line)
    captures = {}

    def capture(name, script, rom, tags, native=False):
        directory = ROOT / 'local/captures' / name
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(rom), 'wrong capture ROM: ' + name)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha((ROOT / script).read_bytes()),
                'wrong input: ' + name)
        if native:
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'wrong binary: ' + name)
        log = (directory / 'run.log').read_bytes()
        require(b'quit' in log and b'timed out' not in log, 'route incomplete: ' + name)
        states = {}
        for tag in tags:
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, f'truncated WRAM: {name}/{tag}')
            require((directory / (tag + '.sram.bin')).stat().st_size == (0x800 if rom == donor else 0x8000),
                    f'truncated SRAM: {name}/{tag}')
            states[tag] = body
        captures[name] = receipt
        return states

    script = 'recomp/inputs/world1-room138-entry.script'
    entries = {}
    for host in ('reference', 'native', 'cheap'):
        entries[host] = capture(('world1-138-qualified-cheap' if host == 'cheap' else 'world1-138-audio-qualified-' + host), script,
                                donor if host == 'cheap' else candidate,
                                ('entry600', 'late', 'walk'), host == 'native')
        for tag, body in entries[host].items():
            require(body[0x100] == 0x14 and word(body, 0x10b) == 0x138 and body[0x71] == 0,
                    f'room138 not playable: {host}/{tag}')
        require(word(entries[host]['walk'], 0x94) > word(entries[host]['entry600'], 0x94),
                'no ordinary movement: ' + host)
    cells = 19 * 0x1b0
    for host in ('reference', 'native'):
        for tag in ('entry600', 'walk'):
            require(entries[host][tag][0xdda] == 0x7e and entries[host][tag][0xc112] == 2,
                    'private song/sample bank not selected')
            for address in (0xc800, 0x1c800):
                require(entries[host][tag][address:address+cells] == entries['cheap'][tag][address:address+cells],
                        f'donor terrain differs: {host}/{tag}/{address:x}')
    natural = 'recomp/inputs/world1-room138-natural-entry.script'
    for host in ('reference', 'native'):
        s = capture('world1-138-audio-natural-qualified-' + host, natural, candidate,
                    ('cave_completed_map', 'next_course', 'next_late'), host == 'native')
        require(s['cave_completed_map'][0x100] == 0x0e and s['cave_completed_map'][0x1ee6] == 0x8b,
                'preceding normal clear missing')
        for tag in ('next_course', 'next_late'):
            require(s[tag][0x100] == 0x14 and word(s[tag], 0x10b) == 0x138, 'natural entry failed: ' + host)
    for host, rom in (('reference', base), ('cheap', donor)):
        s = capture('world1-after-120-late-' + host, natural, rom, ('next_course', 'next_late'))
        require(all(body[0x100] == (0x12 if host == 'reference' else 0x14) for body in s.values()),
                'baseline/donor outcome differs')

    saved = capture('world1-138-audio-regression-room120-native', 'recomp/inputs/world1-room120-coins-save.script',
                    candidate, ('cave_completed_map', 'file_reload', 'reload_cave'), True)
    for tag, body in saved.items():
        require(body[0x1ee6] == 0x8b and body[0x1f37] == 8, 'prior clear/DK regression: ' + tag)
    require(saved['reload_cave'][0x100] == 0x14 and word(saved['reload_cave'], 0x10b) == 0x120,
            'prior course reload regression')
    source_aram = (ROOT / 'local/probes/world1-survey/room138-donor-aram.bin').read_bytes()
    target_aram = (ROOT / 'local/probes/world1-survey/room138-final-aram.bin').read_bytes()
    native_aram = (ROOT / 'local/captures/world1-138-audio-qualified-native/apu-ram.bin').read_bytes()
    require(len(source_aram) == len(target_aram) == len(native_aram) == 65536, 'incomplete ARAM')
    require(source_aram[0x6800:0x6800+len(group)-8] == group[4:-4], 'donor upload differs')
    require(word(source_aram, 0x40) == 0x680a, 'donor is not playing the second bank-local sequence')
    for body in (target_aram, native_aram):
        require(body[0x5400:0x5400+len(payload)-8] == payload[4:-4], 'relocated upload differs')
    trace = ROOT / 'local/probes/world1-survey/room138-pc.csv'
    with trace.open() as f:
        rows = list(csv.DictReader(f))
    require(len(rows) > 1000 and all(int(row['pc']) in (0x0fc347, 0x0fc34a) and int(row['mode']) == 0x12
                                   for row in rows), 'baseline SPC wait not established')
    report = {'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate), 'base_rom_sha256': sha(base),
              'donor_rom_sha256': sha(donor), 'binary_sha256': build['binary_sha256'],
              'sequence_intermediate_sha256': sha(intermediate), 'sample_bank': 2,
              'changed_bytes': len(changed), 'music_graph_sha256': sha(json.dumps(target_graph, separators=(',', ':')).encode()),
              'source_and_relocated_graphs_equal': True, 'actual_uploads_match': True,
              'existing_song_audit': {'parsed': parsed, 'exact_matches': matches},
              'baseline_stall_trace_sha256': sha(trace.read_bytes()), 'captures': captures,
              'limits': ['Room138 full course, exits, collectibles and audible output remain unqualified.',
                         'Room106 incorrect music remains deferred.']}
    output = ROOT / 'local/reports/world1-room138-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Room138 recovery checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Build a room-scoped Japanese message adapter without changing course/save IDs."""
import argparse
import copy
import json
from pathlib import Path

from native_sprite_gap import packs
from prepare_rom import verify
from restore_star_world_1 import graphics_pointer, lorom, lz2, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'demo11-native-mazo-cumulative-v1'
TARGET = 'demo11-native-mazo-messages-v2'
LEGACY_TARGET = 'demo11-native-mazo-messages-v1'
RECIPE = ROOT/'config/native-content/mazo-messages-v2.json'
LEGACY_RECIPE = ROOT/'config/native-content/mazo-messages.json'


class Code:
    def __init__(self):
        self.data = bytearray()
        self.labels = {}
        self.branches = []

    def emit(self, text):
        self.data.extend(bytes.fromhex(text))

    def label(self, name):
        self.labels[name] = len(self.data)

    def branch(self, opcode, label):
        self.data.extend((opcode, 0))
        self.branches.append((len(self.data)-1, label))

    def finish(self):
        for at, label in self.branches:
            delta = self.labels[label]-at-1
            if not -128 <= delta <= 127:
                raise ValueError('branch exceeds reviewed short range')
            self.data[at] = delta & 255
        return bytes(self.data)


def upload(address, full=True):
    # Preserve A/P, use DMA2 to VRAM9000, and return within the private bank.
    # No game-state writes such as Seven's original STZ14AF are included.
    prefix = '08c22048e220' if full else '0848'
    suffix = 'c220682860' if full else '682860'
    return bytes.fromhex(prefix+'a9808d1521c220a900488d1621a901188d2043a9') + \
        (address & 65535).to_bytes(2, 'little') + bytes.fromhex('8d2243a900088d2543e220a9') + \
        bytes([address >> 16]) + bytes.fromhex('8d2443a9048d0b42'+suffix)


def routing():
    c = Code()
    c.emit('0848ad0c01c901')  # PHP/PHA, exact room high byte.
    c.branch(0xd0, 'fallback')
    c.emit('ad0b01c991')
    c.branch(0xf0, 'room191')
    c.emit('c992')
    c.branch(0xd0, 'fallback')
    c.emit('ad2614c901')
    c.branch(0xf0, 'local')
    c.branch(0x80, 'fallback')
    c.label('room191')
    c.emit('ad2614c902')
    c.branch(0xf0, 'local')
    c.label('fallback')
    c.emit('68285ca6b610')  # Restore A/P; original recipient selector.
    c.label('local')
    c.emit('68282000b2a200ac2614885cc9bb89')  # Upload JP, X=0, Y=message-1.
    return c.finish()


def closing():
    c = Code()
    c.emit('0848ad0c01c901')
    c.branch(0xd0, 'original')
    c.emit('ad0b01c991')
    c.branch(0xf0, 'restore')
    c.emit('c992')
    c.branch(0xd0, 'original')
    c.label('restore')
    c.emit('2040b2')
    c.label('original')
    c.emit('68289c26149c881b5c23b105')  # Original STZs, original continuation.
    return c.finish()


def build(recipe=None):
    r = recipe if recipe is not None else json.loads(RECIPE.read_text())
    if (r['schema'], r['id'], r['parent']) != (1, 'mazo-room-messages', PARENT) or r['target'] not in (TARGET, LEGACY_TARGET):
        raise ValueError('unreviewed message lineage')
    full = r['target'] == TARGET
    if full and r.get('accumulator_save') != 'full-16-bit-A-and-P':
        raise ValueError('message DMA must preserve hidden accumulator B')
    if r['allocations'] != [dict(address='89B000', size=0xe84, executable=True),
                             dict(address='D38000', size=0x1100, executable=False)]:
        raise ValueError('unreviewed allocation or data-bank semantics')
    if r['helper']['address'] != '03BBC9' or r['stripe_rows']['address'] != '03BC7F':
        raise ValueError('unreviewed official renderer range')
    if set(r['sources']) != {'mazo', '7hero', 'boss', 'demo-only-1', 'demo-1-1'}:
        raise ValueError('official source audit differs')
    if (r['fonts']['japanese']['version'], r['fonts']['english']['version']) != ('boss', 'demo-1-1'):
        raise ValueError('font version selection differs')
    cfg_path = ROOT/'config/restorations'/(PARENT+'.json')
    verify(cfg_path.read_bytes(), r['parent_config'], 'cumulative parent config')
    cfg = json.loads(cfg_path.read_text())
    parent = (ROOT/'local/restoration'/PARENT/'rom.sfc').read_bytes()
    verify(parent, r['parent_output'], 'cumulative parent ROM')
    parent_font, _ = lz2(parent, graphics_pointer(parent, 0x2a), limit=0x10000)
    verify(parent_font, r['fonts']['english'], 'retained recipient font')
    versions = {}
    for name, pin in r['sources'].items():
        versions[name] = (ROOT/'local/content-versions'/name/'rom.sfc').read_bytes()
        verify(versions[name], pin, 'official '+name)
    require_banks = {0x89, 0xd3}
    if require_banks & {int(p['address'], 16) >> 16 for p in packs(PARENT)}:
        raise ValueError('message adapter bank occupied')
    data = bytearray(0x1100)
    cursor = 0
    for index, message in enumerate(r['messages']):
        if message['room'] != ('192' if index == 0 else '191') or message['request'] != index+1:
            raise ValueError('unreviewed room/message identity')
        at = lorom(int(message['source_address'], 16))
        raw = versions['mazo'][at:at+message['size']]
        verify(raw, message, 'official message')
        if raw[-1] != 0xfe or 0xfe in raw[:-1] or len(raw) > 144:
            raise ValueError('message exceeds original eight-row extent')
        if any(raw in versions[name] for name in ('7hero', 'boss', 'demo-only-1', 'demo-1-1')):
            raise ValueError('newer official matching message needs review')
        pointer = lorom(0x03be80)+0x30*4+index*2
        old_offset = int.from_bytes(versions['mazo'][pointer:pointer+2], 'little')
        if 0x53d0d4+old_offset != int(message['source_address'], 16):
            raise ValueError('official message context differs')
        message['native_offset'] = cursor
        data[cursor:cursor+len(raw)] = raw
        cursor += len(raw)
    if cursor > 0x100:
        raise ValueError('message payload exceeds bounded allocation')
    for name, at in [('japanese', 0x100), ('english', 0x900)]:
        font = r['fonts'][name]
        rom = versions[font['version']]
        decoded, _ = lz2(rom, graphics_pointer(rom, 0x2a), limit=0x10000)
        verify(decoded, font, 'decoded '+name+' font')
        data[at:at+0x800] = decoded
    # Latest official rendering loop, unchanged except its explicit text source.
    helper = versions['demo-1-1'][lorom(0x03bbc9):lorom(0x03bc49)]
    verify(helper, r['helper'], 'latest official message renderer')
    if parent[lorom(0x03bbc9):lorom(0x03bc49)] != helper:
        raise ValueError('recipient rendering loop differs')
    helper = bytearray(helper)
    if helper[0x41:0x45] != bytes.fromhex('bf27c92f'):
        raise ValueError('text-source operand differs')
    helper[0x42:0x45] = bytes.fromhex('0080d3')
    rows = versions['demo-1-1'][lorom(0x03bc7f):lorom(0x03bc8f)]
    verify(rows, r['stripe_rows'], 'latest official stripe rows')
    code = bytearray(0xe84)  # 89B000..89BE83, including private pointer table.
    regions = [(0xb000, routing()), (0xb100, closing()),
               (0xb200, upload(0xd38100, full)), (0xb240, upload(0xd38900, full)),
               (0xbbc9, helper), (0xbc7f, rows),
               (0xbe80, b''.join(m['native_offset'].to_bytes(2, 'little') for m in r['messages']))]
    for at, raw in regions:
        code[at-0xb000:at-0xb000+len(raw)] = raw
    expected = [(0x03bb90, '5ca6b610', '5c00b089'),
                (0x05b11d, '9c26149c881b', '5c00b189eaea')]
    if [(int(p['address'], 16), p['before'], p['after']) for p in r['patches']] != expected:
        raise ValueError('unreviewed hook extent')
    out = bytearray(parent)
    for patch in r['patches']:
        at = lorom(int(patch['address'], 16))
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if parent[at:at+len(before)] != before or len(before) != len(after):
            raise ValueError('message hook preimage differs')
        out[at:at+len(after)] = after
    return r, cfg, bytes(out), bytes(code), bytes(data)


def prepare(legacy=False):
    recipe_path = LEGACY_RECIPE if legacy else RECIPE
    r, parent, rom, code, data = build(json.loads(recipe_path.read_text()))
    target = r['target']
    source = 'local/native-modules/mazo-messages-'+('v1' if legacy else 'v2')
    directory = ROOT/source
    directory.mkdir(parents=True, exist_ok=True)
    cfg = copy.deepcopy(parent)
    cfg.update(id=target, parent_restoration=PARENT, parent_output=parent['output'],
               scope='Restore official Mazo room191/192 messages and local font lifecycle; retain cumulative modules; experimental.')
    cfg['output']['sha256'] = sha(rom)
    for file, raw, address, executable, variable in [
        ('message-code.bin', code, '89B000', True, 'BM_MAZO_MESSAGE_CODE_PACK'),
        ('message-data.bin', data, 'D38000', False, 'BM_MAZO_MESSAGE_DATA_PACK')]:
        write_verified(directory/file, raw)
        cfg['native_sprite_gap']['extra_packs'].append(dict(
            variable=variable, pack_file=file, address=address, size=len(raw), sha256=sha(raw),
            executable=executable, source=source))
    for patch in r['patches']:
        cfg['native_sprite_gap']['extra_patches'].append(dict(offset=lorom(int(patch['address'], 16)),
            before=patch['before'], after=patch['after'], role=patch['role']))
    cfg['native_adaptations'].append(dict(kind='room-scoped-mazo-messages', recipe=str(recipe_path.relative_to(ROOT)),
                                        recipe_sha256=sha(recipe_path.read_bytes()),
                                        note='191 message2 and192 message1 use official text and Japanese font; close restores English font; course/save IDs unchanged.'))
    path = ROOT/'config/restorations'/(target+'.json')
    write_verified(path, (json.dumps(cfg, separators=(', ', ': '))+'\n').encode())
    print(target, sha(rom), 'code', len(code), 'data', len(data))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--legacy-probe', action='store_true', help='reproduce the superseded V1 low-byte-only accumulator prototype')
    prepare(p.parse_args().legacy_probe)

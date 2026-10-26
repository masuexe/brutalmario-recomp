#!/usr/bin/env python3
"""Build the isolated Seven Koopalings child-6A namespace descendant."""
import json
from pathlib import Path
import subprocess
import sys

from audit_boss_dependencies import prepare_boss
from audit_star_boss_donors import sprite_table
import native_seven as parent
from prepare_rom import verify
from restore_star_world_1 import graphics_pointer, lorom, lz2, sha, sprite_rooms, write_verified

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-seven-child-font-cycle'


def settings(target):
    path = ROOT / 'config/restorations' / (target+'.json')
    if not path.is_file():
        return None
    cfg = json.loads(path.read_text())
    if 'native_seven_child' not in cfg:
        return None
    recipe = json.loads((ROOT / cfg['native_seven_child']['manifest']).read_text())
    if cfg['schema'] != 1 or recipe['schema'] != 1 or cfg['id'] != target:
        raise ValueError('Seven child schema or target differs')
    return cfg, recipe


def analyze(donor, recipe):
    sys.path.insert(0, str(ROOT / 'local/upstream/snesrecomp/recompiler'))
    from v2.decoder import decode_function
    from snes65816 import ABS, ABS_X, ABS_Y, LONG, LONG_X, IMM
    code = recipe['code']
    first = int(code['source_address'], 16)
    last = first+code['size']
    bank = first >> 16
    todo = [(int(code[name], 16) & 0xffff, 1, 1) for name in ('init', 'main')]
    entries, instructions = set(), {}
    while todo:
        pc, m, x = todo.pop()
        if (pc, m, x) in entries:
            continue
        entries.add((pc, m, x))
        if not first+8 <= bank << 16 | pc < last:
            raise ValueError('child entry escapes protected code')
        graph = decode_function(donor, bank, pc, m, x, end=last & 0xffff)
        if graph.unresolved_indirects or graph.suppressed_indirect_calls:
            raise ValueError('child has an unreviewed indirect transfer')
        for decoded in graph.insns.values():
            ins = decoded.insn
            if not first+8 <= ins.addr < last or ins.addr+ins.length > last:
                raise ValueError('child instruction escapes protected code')
            instructions[(ins.addr, decoded.key.m, decoded.key.x)] = ins
            if ins.mode in (ABS, ABS_X, ABS_Y) and ins.operand >= 0x8000:
                if not first <= bank << 16 | ins.operand < last:
                    raise ValueError('child bank-local reference escapes code')
            if ins.mode in (LONG, LONG_X) and ins.operand >> 16 == bank:
                raise ValueError('child needs an unreviewed source-bank adaptation')
            if ins.mode == IMM and ins.operand == 0x6a:
                raise ValueError('child has an unreviewed literal self ID')
            if ins.mnem == 'JSR' and ins.mode == ABS:
                todo.append((ins.operand, decoded.key.m, decoded.key.x))
    calls = sorted({f'{ins.operand:06X}' for ins in instructions.values()
                    if ins.mnem in ('JSL', 'JML')})
    if calls != recipe['external_calls']:
        raise ValueError('child shared call set differs')
    return {'entry_states': sorted(entries), 'instruction_variants': len(instructions),
            'external_calls': calls, 'source_bank_long_references': [],
            'scope': 'Init/main and local absolute JSR traversal with decoded M/X. '
                     'No indirect transfer or hard-coded 6A self ID admitted. '
                     'Outside helper closure and fight progression require runtime evidence.'}


def build(donor, base, master, recipe):
    verify(base, recipe['parent_output'], 'Seven child parent')
    code, record = recipe['code'], recipe['record']
    source, native = int(code['source_address'], 16), int(code['native_address'], 16)
    if source != 0x1ec20e or native != 0x9ec20e or (source & 0xffff)+code['size'] > 0x10000:
        raise ValueError('unreviewed child mapping')
    payload = donor[lorom(source):lorom(source)+code['size']]
    verify(payload, code, 'newest official child code')
    if (payload[:4] != b'STAR' or int.from_bytes(payload[4:6], 'little')+9 != len(payload) or
            int.from_bytes(payload[4:6], 'little') ^ int.from_bytes(payload[6:8], 'little') != 0xffff):
        raise ValueError('child protected extent differs')
    audit = analyze(donor, recipe)
    namespace = int(record['namespace_slot'], 16)
    if namespace != 0xe0 or sprite_rooms(base, namespace):
        raise ValueError('child namespace has existing placements')
    _, _, source_table = sprite_table(donor)
    _, _, destination_table = sprite_table(base)
    if (record['source_offset'] != lorom(source_table)+0x6a*16 or
            record['destination_offset'] != lorom(destination_table)+namespace*16):
        raise ValueError('child constructor-derived record offset differs')
    slot = record['destination_offset']
    if (donor[record['source_offset']:record['source_offset']+16].hex() != record['source'] or
            base[slot:slot+16].hex() != record['before']):
        raise ValueError('child record/namespace identity differs')
    after = bytearray(bytes.fromhex(record['source']))
    after[10] = after[13] = native >> 16
    if after.hex() != record['after']:
        raise ValueError('child record adaptation differs')
    kept = recipe['preserved_recipient_6a']
    off = kept['record_offset']
    if base[off:off+16].hex() != kept['record'] or sprite_rooms(base, 0x6a) != kept['rooms']:
        raise ValueError('existing recipient 6A differs')
    verify(base[kept['code_offset']:kept['code_offset']+kept['size']], kept, 'preserved recipient 6A')
    for dependency in recipe['shared_dependencies']:
        offset = lorom(int(dependency['address'], 16))
        for image in (base, donor):
            verify(image[offset:offset+dependency['size']], dependency, 'child shared dependency')
    # The engine-visible normal ID and custom dispatch ID are separate contracts.
    # Preserve the normal class; change only the custom dispatch store.
    sites = {int(patch['source_address'], 16) for patch in recipe['master_patches']}
    custom_only = recipe.get('namespace_strategy') == 'custom-only'
    if sites != ({0x2284d9} if custom_only else {0x2284d5, 0x22a168}):
        raise ValueError('child namespace adaptation site set differs')
    adapted = bytearray(master)
    for patch in recipe['master_patches']:
        address = int(patch['source_address'], 16)
        native_pc = int(patch['native_address'], 16)
        before, replacement = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        offset = (native_pc & 0xffff)-0x8000
        if native_pc != address | 0x800000 or adapted[offset:offset+len(before)] != before:
            raise ValueError('child master call-site identity differs')
        if custom_only:
            if before.hex() != '9f9eab7f' or replacement.hex() != '2040f0ea':
                raise ValueError('child custom-ID store adaptation differs')
        elif len(before) != 2 or before[1] != 0x6a or replacement != bytes([before[0], namespace]):
            raise ValueError('child namespace operand adaptation differs')
        adapted[offset:offset+len(before)] = replacement
    if custom_only:
        for site in recipe['preserved_master_sites']:
            offset = (int(site['address'], 16) & 0xffff)-0x8000
            raw = bytes.fromhex(site['bytes'])
            if adapted[offset:offset+len(raw)] != raw:
                raise ValueError('preserved normal-ID contract differs')
        adapter = recipe['master_adapter']
        offset = (int(adapter['address'], 16) & 0xffff)-0x8000
        raw = bytes.fromhex(adapter['bytes'])
        if adapter['address'] != 'A2F040' or offset < len(adapted) or offset+len(raw) > 0x8000:
            raise ValueError('custom-ID adapter mapping differs')
        adapted.extend(bytes(offset-len(adapted)))
        adapted.extend(raw)
    lifecycle = recipe.get('font_lifecycle')
    if lifecycle:
        font = lifecycle['recipient_font']
        decoded, encoded = lz2(base, graphics_pointer(base, 0x2a), limit=0x800)
        verify(decoded, font['decoded'], 'recipient font lifecycle bytes')
        verify(encoded, font['encoded'], 'recipient font encoded bytes')
        hook = lifecycle['main_hook']
        offset = (int(hook['address'], 16) & 0xffff)-0x8000
        before, hook_after = bytes.fromhex(hook['before']), bytes.fromhex(hook['after'])
        if hook['address'] != 'A28090' or adapted[offset:offset+len(before)] != before or len(before) != len(hook_after):
            raise ValueError('font lifecycle main hook differs')
        adapted[offset:offset+len(hook_after)] = hook_after
        for name, address in (('wrapper', 'A2F060'), ('callback', 'A2F0A0')):
            adapter = lifecycle[name]
            raw = bytes.fromhex(adapter['bytes'])
            offset = (int(adapter['address'], 16) & 0xffff)-0x8000
            if adapter['address'] != address or offset < len(adapted) or offset+len(raw) > 0x8000:
                raise ValueError('font lifecycle adapter mapping differs')
            adapted.extend(bytes(offset-len(adapted)))
            adapted.extend(raw)
        audit['font_lifecycle'] = lifecycle['scope']
    verify(adapted, recipe['master_payload'], 'namespaced Seven master')
    out = bytearray(base)
    out[slot:slot+16] = after
    return bytes(out), bytes(adapted), payload, audit


def packs(target):
    cfg, recipe = settings(target)
    data = parent.packs(cfg['base_restoration'])
    data[0] = dict(data[0], size=recipe['master_payload']['size'], sha256=recipe['master_payload']['sha256'])
    if 'font_lifecycle' in recipe:
        data[1] = dict(data[1], **recipe['font_lifecycle']['graphics_payload'])
    code = recipe['code']
    data.append(dict(variable='BM_SEVEN_CHILD_PACK', pack_file=code['pack_file'],
                     address=code['native_address'], size=code['size'], sha256=code['sha256'], executable=True))
    return data


def header(target):
    cfg, _ = settings(target)
    data = packs(target)
    digest = lambda value: '{'+','.join(str(n) for n in bytes.fromhex(value))+'}'
    text = ('/* Generated cumulative child-module descriptors. */\n#include <stdint.h>\n'
            f'#define BM_SEVEN_ROM_SIZE {cfg["output"]["size"]}u\n'
            f'#define BM_SEVEN_PACKS {len(data)}u\n'
            'typedef struct { const char *variable; unsigned bank, offset, size, executable, '
            'first_page, last_page; uint8_t sha256[32]; } BmSevenPack;\n'
            'static const uint8_t bm_seven_rom_sha[32] = '+digest(cfg['output']['sha256'])+';\n'
            'static const BmSevenPack bm_seven_packs[BM_SEVEN_PACKS] = {\n')
    for pack in data:
        address = int(pack['address'], 16)
        text += ('{"'+pack['variable']+'",'+','.join(str(n)+'u' for n in
                 (address >> 16, lorom(address), pack['size'], int(pack['executable']),
                  address >> 8, (address+pack['size']-1) >> 8))+','+digest(pack['sha256'])+'},\n')
    return text+'};\n'


def identity(target):
    pair = settings(target)
    if pair is None:
        return None
    cfg, recipe = pair
    feature = parent.identity(cfg['base_restoration'])
    paths = [ROOT / 'config/restorations' / (target+'.json'),
             ROOT / cfg['native_seven_child']['manifest'], Path(__file__),
             ROOT / 'recomp/native_seven.c', ROOT / 'recomp/native_content.h',
             ROOT / 'local/upstream/snesrecomp/recompiler/v2/decoder.py',
             ROOT / 'local/upstream/snesrecomp/recompiler/snes65816.py']
    return {'kind': 'immutable-seven-child', 'parent_feature': feature,
            'files': {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in paths},
            'packs': packs(target), 'generated_header_sha256': sha(header(target).encode()),
            'runtime_source_sha256': feature['runtime_source_sha256'],
            'runtime_result_sha256': feature['runtime_result_sha256']}


def prepare(target=TARGET):
    cfg, recipe = settings(target)
    donor_manifest = prepare_boss()
    donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
    verify(donor, donor_manifest['output'], 'authoritative Boss Demo child donor')
    source_dir = ROOT / 'local/restoration' / cfg['base_restoration']
    receipt = json.loads((source_dir / 'input-manifest.json').read_text())
    if receipt['content'] != parent.identity(cfg['base_restoration']):
        raise ValueError('parent content receipt is stale')
    for pack in parent.packs(cfg['base_restoration']):
        verify((source_dir / pack['pack_file']).read_bytes(), pack, 'parent cumulative pack')
    rom, master, child, audit = build(donor, (source_dir / 'rom.sfc').read_bytes(),
                                    (source_dir / 'seven-code.bin').read_bytes(), recipe)
    verify(rom, cfg['output'], 'namespaced Seven child descendant')
    graphics = graphics_payload(recipe, source_dir)
    directory = ROOT / 'local/restoration' / target
    directory.mkdir(parents=True, exist_ok=True)
    write_verified(directory / 'rom.sfc', rom)
    for pack in packs(target):
        data = (child if pack['variable'] == 'BM_SEVEN_CHILD_PACK' else
                master if pack['variable'] == 'BM_SEVEN_CODE_PACK' else
                graphics if pack['variable'] == 'BM_SEVEN_GRAPHICS_PACK' else
                (source_dir / pack['pack_file']).read_bytes())
        verify(data, pack, 'cumulative child pack')
        write_verified(directory / pack['pack_file'], data)
    receipt = {'config': cfg, 'content': identity(target), 'child_audit': audit,
               'donor_sha256': sha(donor),
               'parent_receipt_sha256': sha((source_dir / 'input-manifest.json').read_bytes())}
    write_verified(directory / 'input-manifest.json', (json.dumps(receipt, indent=2)+'\n').encode())
    print(target, sha(rom), f'{len(child)} external child bytes; {len(audit["entry_states"])} entry states')
    return rom


def graphics_payload(recipe, parent_dir):
    graphics = (parent_dir / 'seven-graphics.bin').read_bytes()
    if 'font_lifecycle' not in recipe:
        return graphics
    lifecycle = recipe['font_lifecycle']
    font = lifecycle['recipient_font']
    official = (ROOT / 'local/content-versions' / font['source_version'] / 'rom.sfc').read_bytes()
    verify(official, font['source_rom'], 'official recipient font source')
    pointer = graphics_pointer(official, int(font['source_id'], 16))
    if pointer != int(font['source_address'], 16) or int(font['native_address'], 16) != 0xa68000+len(graphics):
        raise ValueError('recipient font source/native pointer differs')
    decoded, encoded = lz2(official, pointer, limit=0x800)
    verify(decoded, font['decoded'], 'official English font')
    verify(encoded, font['encoded'], 'official encoded English font')
    graphics += decoded
    verify(graphics, lifecycle['graphics_payload'], 'font lifecycle graphics pack')
    return graphics


def environment(target, env):
    for pack in packs(target):
        path = ROOT / 'local/restoration' / target / pack['pack_file']
        verify(path.read_bytes(), pack, pack['variable'])
        env[pack['variable']] = str(path)


def configure(experiment, binary, target):
    if settings(target) is None:
        return
    feature = identity(target)
    program = json.loads((experiment / 'src/gen/program_manifest.json').read_text())
    forbidden = (0x1e, 0x9e, 0x22, 0xa2, 0x25, 0xa5, 0x26, 0xa6, 0x36, 0xb6)
    if any(int(key.split(':')[0], 16) >> 16 in forbidden for key in program['nodes']):
        raise ValueError('Seven child forbids AOT in split banks and aliases')
    directory = ROOT / 'local/native-content-runtime' / target
    cart = directory / 'runner/src/snes/cart.c'
    cart.parent.mkdir(parents=True, exist_ok=True)
    if not cart.exists():
        cart.write_bytes((ROOT / 'local/upstream/snesrecomp/runner/src/snes/cart.c').read_bytes())
    previous = json.loads((ROOT / 'config/native-content/sprite9e.json').read_text())
    if sha(cart.read_bytes()) == feature['runtime_source_sha256']:
        subprocess.run(['git', 'apply', '--directory='+str(directory.relative_to(ROOT)),
                       str(ROOT / previous['runtime_patch'])], cwd=ROOT, check=True)
    if sha(cart.read_bytes()) != feature['runtime_result_sha256']:
        raise ValueError('Seven child cartridge override differs')
    write_verified(directory / 'native_seven_manifest.h', header(target).encode())
    cmake = experiment / 'CMakeLists.txt'
    text = cmake.read_text()
    begin, end = '# BEGIN native seven child', '# END native seven child'
    block = '\n'.join([begin, f'get_target_property(_child_sources {binary} SOURCES)',
        'list(REMOVE_ITEM _child_sources "${SNESRECOMP_ROOT}/runner/src/snes/cart.c")',
        f'set_property(TARGET {binary} PROPERTY SOURCES ${{_child_sources}})',
        f'target_sources({binary} PRIVATE "{cart}" "{ROOT / "recomp/native_seven.c"}")',
        f'target_include_directories({binary} PRIVATE "{directory}" "{ROOT / "recomp"}" "{ROOT / "local/upstream/snesrecomp/runner/src/snes"}")', end])
    if begin in text:
        text = text[:text.index(begin)]+block+text[text.index(end)+len(end):]
    else:
        text += '\n'+block+'\n'
    cmake.write_text(text)


if __name__ == '__main__':
    prepare()

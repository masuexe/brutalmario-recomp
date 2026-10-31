#!/usr/bin/env python3
"""Reject unsafe message mappings, scope changes and modifications to guest state hooks."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from prepare_mazo_messages import RECIPE, build
from restore_star_world_1 import lorom


class MazoMessageConfigTests(unittest.TestCase):
    def test_candidate_lineage_and_scope(self):
        cfg = json.loads((ROOT/'config/restorations/demo11-native-mazo-messages-v2.json').read_text())
        self.assertEqual(cfg['base_restoration'], 'demo11-native-sprite9e')
        self.assertEqual(cfg['parent_restoration'], 'demo11-native-mazo-cumulative-v1')
        packs = cfg['native_sprite_gap']['extra_packs']
        self.assertEqual([p['variable'] for p in packs[-2:]],
                         ['BM_MAZO_MESSAGE_CODE_PACK', 'BM_MAZO_MESSAGE_DATA_PACK'])
        recipe = json.loads(RECIPE.read_text())
        self.assertEqual([m['room'] for m in recipe['messages']], ['192', '191'])
        self.assertEqual(set(recipe['fonts']), {'japanese', 'english'})


@unittest.skipUnless((ROOT/'local/restoration/demo11-native-mazo-cumulative-v1/rom.sfc').exists(),
                     'requires the pinned cumulative parent and official assets')
class MazoMessageTests(unittest.TestCase):
    def setUp(self):
        self.recipe = json.loads(RECIPE.read_text())

    def test_rom_changes_only_the_two_reviewed_hooks(self):
        _, _, rom, _, _ = build(copy.deepcopy(self.recipe))
        parent = (ROOT/'local/restoration/demo11-native-mazo-cumulative-v1/rom.sfc').read_bytes()
        allowed = set()
        for patch in self.recipe['patches']:
            at = lorom(int(patch['address'], 16))
            after = bytes.fromhex(patch['after'])
            self.assertEqual(rom[at:at+len(after)], after)
            allowed.update(range(at, at+len(after)))
        self.assertEqual(len(rom), len(parent))
        self.assertTrue(all(i in allowed for i, (a, b) in enumerate(zip(parent, rom)) if a != b))

    def test_unmirrored_execution_mapping_rejected(self):
        self.recipe['allocations'][0]['address'] = 'D4B000'
        with self.assertRaisesRegex(ValueError, 'data-bank semantics'):
            build(self.recipe)

    def test_unrelated_room_rejected(self):
        self.recipe['messages'][0]['room'] = '190'
        with self.assertRaisesRegex(ValueError, 'room/message identity'):
            build(self.recipe)

    def test_extra_hook_rejected(self):
        self.recipe['patches'].append(dict(address='001234', before='00', after='80', role='unreviewed'))
        with self.assertRaisesRegex(ValueError, 'hook extent'):
            build(self.recipe)

    def test_english_font_as_japanese_source_rejected(self):
        self.recipe['fonts']['japanese']['version'] = 'demo-1-1'
        with self.assertRaisesRegex(ValueError, 'font version'):
            build(self.recipe)

    def test_dma_pushes_and_pulls_full_accumulator(self):
        _, _, rom, code, _ = build(copy.deepcopy(self.recipe))
        mapped = bytearray(rom)
        at = lorom(0x89b000)
        mapped[at:at+len(code)] = code
        sys.path.insert(0, str(ROOT/'local/upstream/snesrecomp/recompiler'))
        from v2.decoder import decode_function
        for entry in (0xb200, 0xb240):
            graph = decode_function(mapped, 0x89, entry, 1, 1, end=entry+0x40)
            pushes = [d for d in graph.insns.values() if d.insn.mnem == 'PHA']
            pulls = [d for d in graph.insns.values() if d.insn.mnem == 'PLA']
            self.assertEqual(len(pushes), 1)
            self.assertEqual(len(pulls), 1)
            self.assertEqual(pushes[0].key.m, 0)
            self.assertEqual(pulls[0].key.m, 0)
            writes = {d.insn.operand for d in graph.insns.values() if d.insn.mnem in ('STA', 'STZ')}
            self.assertEqual(writes, {0x2115, 0x2116, 0x4320, 0x4322, 0x4324, 0x4325, 0x420b})


if __name__ == '__main__':
    unittest.main()

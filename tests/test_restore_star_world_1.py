"""Bounded graphics decoding and immutable restoration-output safeguards."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from restore_star_world_1 import apply_code_patches, lorom, lz2, write_verified
import restore_star_world_1 as restoration
from m1 import verify_scaffold_rom


class RestorationSafetyTests(unittest.TestCase):
    def test_overflow_is_rejected_before_a_write_outside_the_graphics_buffer(self):
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            lz2(bytes.fromhex('e7ff00ff'), 0x008000, limit=100)

    def test_invalid_backreference_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'backreference'):
            lz2(bytes.fromhex('800100ff'), 0x008000)

    def test_stream_crosses_a_lorom_bank_without_consumption_gaps(self):
        rom = bytearray(0x8002)
        rom[0x7ffe:] = bytes.fromhex('010102ff')
        decoded, source = lz2(rom, 0x00fffe)
        self.assertEqual(decoded, b'\x01\x02')
        self.assertEqual(source, bytes.fromhex('010102ff'))

    def test_code_patch_replaces_the_pinned_site_and_rejects_a_mismatch(self):
        rom = bytearray(0x8000)
        # Synthetic byte site: this checks patch validation, not gameplay semantics.
        rom[0x10:0x12] = bytes.fromhex('d006')
        apply_code_patches(rom, {'code_patches': [{
            'address': '008010', 'before': 'd006', 'after': '8006'}]})
        self.assertEqual(rom[0x10:0x12].hex(), '8006')
        with self.assertRaisesRegex(ValueError, 'code patch site changed'):
            apply_code_patches(rom, {'code_patches': [{
                'address': '008010', 'before': 'd006', 'after': '8006'}]})
        with self.assertRaisesRegex(ValueError, 'instruction width'):
            apply_code_patches(bytearray(0x8000), {'code_patches': [{
                'address': '008010', 'before': '80', 'after': '8006'}]})

    def test_rom_mirrors_are_distinct_from_wram_banks(self):
        self.assertEqual(lorom(0xff8000), 0x3f8000)
        self.assertEqual(lorom(0xf0aa50), 0x382a50)
        with self.assertRaises(ValueError):
            lorom(0x7f8000)

    def test_existing_conflicting_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rom.sfc'
            write_verified(path, b'original')
            write_verified(path, b'original')
            with self.assertRaisesRegex(ValueError, 'refusing'):
                write_verified(path, b'different')
            self.assertEqual(path.read_bytes(), b'original')

    def test_wrong_pinned_base_cannot_produce_a_cumulative_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare_chain_fixture(root)
            base = b'base candidate'
            with patch.object(restoration, 'ROOT', root), patch.object(
                    restoration, 'make_candidate', return_value=(base, [])) as build:
                with self.assertRaisesRegex(ValueError, 'base restoration'):
                    restoration.prepare('star-world-upper-left')
            self.assertEqual(build.call_count, 1)
            self.assertFalse((root / 'local/restoration/star-world-upper-left/rom.sfc').exists())

    def test_cyclic_recipe_stops_before_writing_any_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare_chain_fixture(root)
            path = root / 'config/restorations/star-world-1.json'
            config = json.loads(path.read_text())
            config['base_restoration'] = 'star-world-upper-left'
            path.write_text(json.dumps(config))
            with patch.object(restoration, 'ROOT', root), patch.object(
                    restoration, 'make_candidate') as build:
                with self.assertRaisesRegex(ValueError, 'cyclic'):
                    restoration.prepare('star-world-upper-left')
            build.assert_not_called()
            self.assertFalse((root / 'local/restoration').exists())

    def test_sprite_used_in_an_unreviewed_room_is_rejected(self):
        with patch.object(restoration, 'sprite_rooms', return_value=[4, 5]):
            with self.assertRaisesRegex(ValueError, 'room dependencies'):
                restoration.restore_sprite(b'', b'', bytearray(), {'id': '7A', 'rooms': [4]})

    def test_sprite_relocation_must_preserve_bank_local_addresses(self):
        config = {'id': '7A', 'rooms': [4], 'source_address': '248B77',
                  'destination_address': '3D8B78'}
        with patch.object(restoration, 'sprite_rooms', return_value=[4]):
            with self.assertRaisesRegex(ValueError, 'bank-local'):
                restoration.restore_sprite(b'', b'', bytearray(), config)

    def test_nonzero_or_protected_space_cannot_be_used_for_code(self):
        with self.assertRaisesRegex(ValueError, 'empty bank range'):
            restoration.check_allocation(b'occupied', 0, 8)
        rom = b'STAR' + bytes.fromhex('0f00f0ff') + bytes(16)
        with self.assertRaisesRegex(ValueError, 'protected RATS'):
            restoration.check_allocation(rom, 8, 8)

    def test_shared_missing_graphics_preserve_selectors_and_fill_the_original_slot(self):
        recipient, donor, config = self.shared_graphics_fixture()
        result, assets = restoration.make_candidate(recipient, donor, config)
        record = lorom(0x14ad08)
        self.assertEqual(result[record:record+32], recipient[record:record+32])
        self.assertIsNone(assets[0]['room_word_offset'])
        self.assertEqual(lz2(result, 0x00a008)[0], b'\x01\x02')

    def test_shared_graphics_cannot_enable_an_unreviewed_room(self):
        recipient, donor, config = self.shared_graphics_fixture()
        config['assets'][0]['rooms'] = []
        with self.assertRaisesRegex(ValueError, 'shared graphics'):
            restoration.make_candidate(recipient, donor, config)

    @staticmethod
    def shared_graphics_fixture():
        recipient = bytearray(0xa7000)
        donor = bytearray(recipient)
        pointer = restoration.pointer_offset(0x100)
        record = lorom(0x14ad08)
        recipient[pointer:pointer+3] = b'\xff' * 3
        recipient[record:record+4] = bytes.fromhex('01800001')
        donor[pointer:pointer+3] = bytes.fromhex('008100')
        donor[0x100:0x104] = bytes.fromhex('010102ff')
        expected = bytearray(recipient)
        expected[pointer:pointer+3] = bytes.fromhex('08a000')
        expected[0x2000:0x200c] = bytes.fromhex('535441520300fcff010102ff')
        identity = lambda b: dict(size=len(b), sha256=hashlib.sha256(b).hexdigest())
        config = dict(target='shared-graphics-fixture',
                      gfx_record=dict(address='14AD08', before=recipient[record:record+32].hex()),
                      allocation=dict(offset=0x2000, size=0x100),
                      assets=[dict(source_id='100', target_id='100', global_pointer=True,
                                   rooms=[0], source_address='008100',
                                   compressed=identity(bytes.fromhex('010102ff')),
                                   decoded=identity(b'\x01\x02'))], output=identity(expected))
        return recipient, donor, config

    def test_old_embedded_rom_identity_is_rejected_even_with_new_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / 'rom.sfc'
            rom.write_bytes(b'new candidate')
            (root / 'rom_identity.txt').write_text('expected_sha256 = ' + '0' * 64 + '\n')
            with self.assertRaisesRegex(ValueError, 'scaffold ROM identity is stale'):
                verify_scaffold_rom(root, rom)
            (root / 'rom_identity.txt').write_text(
                'expected_sha256 = ' + hashlib.sha256(rom.read_bytes()).hexdigest() + '\n')
            verify_scaffold_rom(root, rom)

    @staticmethod
    def prepare_chain_fixture(root):
        def identity(data):
            return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        versions = []
        for name in ('recipient', 'donor'):
            data = name.encode()
            path = root / 'local/content-versions' / name / 'rom.sfc'
            path.parent.mkdir(parents=True)
            path.write_bytes(data)
            versions.append({'id': name, 'output': identity(data)})
        configs = root / 'config/restorations'
        configs.mkdir(parents=True)
        (root / 'config/content-versions.json').write_text(json.dumps({'versions': versions}))
        for target in ('star-world-1', 'star-world-upper-left'):
            config = {'id': target, 'target': target, 'recipient': 'recipient', 'donor': 'donor'}
            if target == 'star-world-upper-left':
                config.update(base_restoration='star-world-1', base_output=identity(b'other base'))
            (configs / (target + '.json')).write_text(json.dumps(config))


class MusicMigrationTests(unittest.TestCase):
    @staticmethod
    def fixture():
        song = bytearray(128)
        song[:8] = bytes.fromhex('70687068ff000268')
        song[8:64] = b'\xee' * 56  # Unused group headers must not survive extraction.
        song[0x70:0x72] = bytes.fromhex('4068')
        # An E9 echo parameter is data; only the following E9 is a call.
        song[0x40:0x49] = bytes.fromhex('efe90000e950680100')
        song[0x50:0x56] = bytes.fromhex('da10187fb700')
        config = {'source_base': 0x6800, 'destination_base': 0x5400,
                  'song_size': 128, 'relocations': [0, 2, 6, 0x45, 0x70]}
        return bytearray(bytes.fromhex('80000068') + song + bytes(4)), config

    def test_reachable_calls_relocate_and_echo_parameters_remain_data(self):
        group, config = self.fixture()
        result = restoration.adapt_music(group, config)
        self.assertEqual(result[:12], bytes.fromhex('8000005470547054ff000254'))
        self.assertEqual(result[4+8:4+64], bytes(56))
        self.assertEqual(result[4+0x40:4+0x49], bytes.fromhex('efe90000e950540100'))
        self.assertEqual(result[4+0x70:4+0x72], bytes.fromhex('4054'))
        self.assertEqual(result[-4:], bytes(4))

    def test_call_into_another_song_cannot_escape_the_reviewed_slice(self):
        group, config = self.fixture()
        group[4+0x45:4+0x47] = bytes.fromhex('8068')
        with self.assertRaisesRegex(ValueError, 'escapes selected song'):
            restoration.adapt_music(group, config)

    def test_unreviewed_music_command_is_rejected(self):
        group, config = self.fixture()
        group[4+0x50] = 0xff
        with self.assertRaisesRegex(ValueError, 'unsupported music command'):
            restoration.adapt_music(group, config)

    def test_changed_pointer_graph_cannot_be_silently_accepted(self):
        group, config = self.fixture()
        config['relocations'] = [0, 2, 6, 0x70]
        with self.assertRaisesRegex(ValueError, 'pointer graph'):
            restoration.adapt_music(group, config)

    def test_truncated_upload_group_is_rejected(self):
        group, config = self.fixture()
        with self.assertRaisesRegex(ValueError, 'upload group'):
            restoration.adapt_music(group[:-1], config)

    def test_unreviewed_sequence_layout_is_rejected(self):
        group, config = self.fixture()
        group[4+2] = 0x71
        with self.assertRaisesRegex(ValueError, 'sequence header'):
            restoration.adapt_music(group, config)

    def test_second_group_song_compacts_its_data_and_preserves_zero_operand_f0(self):
        group, config = self.fixture()
        group[4+0x50:4+0x57] = bytes.fromhex('f0da10187fb700')
        expected = restoration.adapt_music(group, config)
        body = bytearray(0x140)
        body[8:16] = bytes.fromhex('30693069ff000a68')
        body[0x100:0x140] = group[4+64:4+128]
        body[0x105:0x107] = bytes.fromhex('1069')
        body[0x130:0x132] = bytes.fromhex('0069')
        config.update(sequence_offset=8, source_data_offset=0x100)
        compact_group = bytes.fromhex('40010068') + body + bytes(4)
        self.assertEqual(restoration.adapt_music(compact_group, config), expected)
        self.assertEqual(expected[4+0x50:4+0x53], bytes.fromhex('f0da10'))

    def test_compact_data_window_cannot_extend_past_the_upload(self):
        group, config = self.fixture()
        config['source_data_offset'] = 0x100
        with self.assertRaisesRegex(ValueError, 'upload group'):
            restoration.adapt_music(group, config)

    def test_call_into_another_song_header_is_rejected(self):
        group, config = self.fixture()
        group[4+0x45:4+0x47] = bytes.fromhex('1068')
        with self.assertRaisesRegex(ValueError, 'escapes selected song'):
            restoration.adapt_music(group, config)

    def test_distinct_intro_and_loop_patterns_relocate_all_channels(self):
        group, config = self.fixture()
        body = bytearray(group[4:-4]) + bytearray(16)
        body[2:4] = bytes.fromhex('8068')
        body[0x80:0x82] = bytes.fromhex('5068')
        config.update(song_size=144, pattern_count=2,
                      relocations=[0, 2, 6, 0x45, 0x70, 0x80])
        group = bytes.fromhex('90000068') + body + bytes(4)
        result = restoration.adapt_music(group, config)
        self.assertEqual(result[4:12], bytes.fromhex('70548054ff000254'))
        self.assertEqual(result[4+0x70:4+0x72], bytes.fromhex('4054'))
        self.assertEqual(result[4+0x80:4+0x82], bytes.fromhex('5054'))

    def test_two_pattern_recipe_cannot_silently_collapse_to_one(self):
        group, config = self.fixture()
        config['pattern_count'] = 2
        with self.assertRaisesRegex(ValueError, 'sequence header'):
            restoration.adapt_music(group, config)

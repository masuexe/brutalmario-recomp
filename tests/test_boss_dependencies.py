"""Negative and boundary cases for the read-only Boss inventory."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_boss_dependencies import code_owner, prepare_boss, room_inventory
from restore_star_world_1 import lorom, sha


class BossDependencyTests(unittest.TestCase):
    def test_nested_rats_owner_uses_smallest_span(self):
        rom = bytes(range(256)) * 256
        owner = code_owner(rom, [(0, 1024), (100, 200)], 0x008080)
        self.assertEqual((owner['offset'], owner['size']), (100, 100))
        self.assertTrue(owner['entry_in_payload'])
        self.assertFalse(code_owner(rom, [(100, 200)], 0x008064)['entry_in_payload'])
        self.assertIsNone(code_owner(rom, [(100, 200)], 0x008200))

    def test_sprite_terminator_is_checked_at_entry_boundary(self):
        rom = bytearray(0x100000)
        rom[lorom(0x05ec00):lorom(0x05ec00)+2] = bytes.fromhex('0080')
        rom[lorom(0x0ef100)] = 0x10
        # FF is a legal sprite ID within a three-byte entry, not a terminator.
        rom[lorom(0x108000):lorom(0x108000)+8] = bytes.fromhex('002950ff39602aff')
        room = room_inventory(rom, 0)
        self.assertEqual([p['slot'] for p in room['custom_placements']], ['FF', '2A'])
        self.assertEqual(room['sprite_list_size'], 8)
        self.assertEqual(room['extended_graphics'], [])

    def test_unterminated_list_is_rejected(self):
        rom = bytearray(0x100000)
        rom[lorom(0x05ec00):lorom(0x05ec00)+2] = bytes.fromhex('0080')
        rom[lorom(0x0ef100)] = 0x10
        with self.assertRaisesRegex(ValueError, 'unterminated'):
            room_inventory(rom, 0)

    def test_prepare_rejects_bad_body_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir()
            raw = bytes(512) + b'body'
            (root / 'input.smc').write_bytes(raw)
            base, ips = b'base', b'PATCH' + bytes.fromhex('0002000004') + b'body' + b'EOF'
            (root / 'base.sfc').write_bytes(base)
            (root / 'boss.ips').write_bytes(ips)
            manifest = {'inputs': [{'path': 'input.smc', 'size': len(raw),
                'sha256': sha(raw), 'copier_prefix_bytes': 512}],
                'authoritative_patch': {'base_path': 'base.sfc',
                    'base': {'size': len(base), 'sha256': sha(base)},
                    'ips_path': 'boss.ips', 'ips': {'size': len(ips), 'sha256': sha(ips)},
                    'copier_prefix_bytes': 512},
                'output': {'size': 4, 'sha256': sha(b'body')}}
            path = root / 'config/boss-donor.json'
            path.write_text(json.dumps(manifest))
            prepare_boss(root)
            target = root / 'local/content-versions/boss/rom.sfc'
            self.assertEqual(target.read_bytes(), b'body')
            target.write_bytes(b'keep')
            with self.assertRaisesRegex(ValueError, 'refusing to replace'):
                prepare_boss(root)
            self.assertEqual(target.read_bytes(), b'keep')
            manifest['inputs'][0]['copier_prefix_bytes'] = 0
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                prepare_boss(root)
            self.assertEqual((root / 'input.smc').read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()

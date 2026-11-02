"""Product identity and release gate regressions, using synthetic assets."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import product


class ProductTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'product.json'
        self.config.write_text(json.dumps(dict(target='fixture', features={'console': True},
            platforms={'linux': {'binary': 'game', 'output_method': 'SDL-Software'}})))
        data = self.root / 'local/restoration/fixture'
        data.mkdir(parents=True)
        (data / 'rom.sfc').write_bytes(b'synthetic ROM')
        digest = product.sha(data / 'rom.sfc')
        recipes = self.root / 'config/restorations'
        recipes.mkdir(parents=True)
        (recipes / 'fixture.json').write_text(json.dumps({'output': {'sha256': digest}}))
        (data / 'pack.bin').write_bytes(b'pack')
        assets = [dict(variable='TEST_PACK', pack_file='pack.bin', size=4,
                       sha256=product.sha(data / 'pack.bin'))]
        self.binary = self.root / 'game'
        self.binary.write_bytes(b'\x7fELF' + digest.encode() + b'PRACTICE CHEAT CONSOLE')
        self.addCleanup(patch.stopall)
        patch.object(product, 'ROOT', self.root).start()
        patch.object(product, 'packs', return_value=assets).start()
        (self.root / 'recomp').mkdir()
        (self.root / 'recomp/m1-config.ini').write_text('OutputMethod=SDL-Software\n')
        self.receipt = self.root / 'verification.json'
        *_, identity = product.inputs(self.config, 'linux', self.binary)
        self.receipt.write_text(json.dumps(dict(passed=True, identity=identity)))

    def test_rejects_changed_pack(self):
        (self.root / 'local/restoration/fixture/pack.bin').write_bytes(b'evil')
        with self.assertRaisesRegex(ValueError, 'pack differs'):
            product.inputs(self.config, 'linux', self.binary)

    def test_rejects_wrong_binary_rom(self):
        self.binary.write_bytes(b'\x7fELFwrong')
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            product.inputs(self.config, 'linux', self.binary)

    def test_changed_binary_invalidates_verification(self):
        self.binary.write_bytes(self.binary.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'verification does not match'):
            product.package(self.config, 'linux', self.binary, self.receipt, self.root / 'release')
        self.assertFalse((self.root / 'release').exists())

    def test_failed_verification_cannot_package(self):
        value = json.loads(self.receipt.read_text()); value['passed'] = False
        self.receipt.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'verification does not match'):
            product.package(self.config, 'linux', self.binary, self.receipt, self.root / 'release')

    def test_archive_is_complete_and_preserved_on_repeat(self):
        output = self.root / 'release'
        archive = product.package(self.config, 'linux', self.binary, self.receipt, output)
        original = archive.read_bytes()
        manifest = json.loads((output / 'files.json').read_text())
        for name, digest in manifest.items():
            self.assertEqual(product.sha(output / name), digest)
        self.assertTrue((output / 'saves').is_dir())
        self.assertFalse(list((output / 'saves').iterdir()))
        with self.assertRaisesRegex(ValueError, 'exists'):
            product.package(self.config, 'linux', self.binary, self.receipt, output)
        self.assertEqual(archive.read_bytes(), original)

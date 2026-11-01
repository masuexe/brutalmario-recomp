#!/usr/bin/env python3
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CheatConsoleTests(unittest.TestCase):
    def test_runtime_patch_is_installed(self):
        manifest = json.loads((ROOT / 'config/runtime-patches.json').read_text())
        item = next(x for x in manifest['patches'] if x['id'] == 'builtin-cheat-console')
        self.assertEqual(item['source'], 'runner/src/desktop/host_main.c')
        patch = (ROOT / item['patch']).read_text()
        for token in ('CheatExecute', 'RunCheatConsoleLoop', 'TickCheatHolds',
                      'CHEAT_CONSOLE_COMMANDS', 'teleport ROOM'):
            self.assertIn(token, patch)

    def test_console_document_exists(self):
        text = (ROOT / 'docs/native-cheat-console.md').read_text()
        self.assertIn('backquote', text)
        self.assertIn('invincible', text)
        self.assertIn('teleport ROOM', text)


if __name__ == '__main__':
    unittest.main()

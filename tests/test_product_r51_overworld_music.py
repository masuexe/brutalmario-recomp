#!/usr/bin/env python3
"""Verify demo11-native-product-r51 World 4 & World 6 Overworld map BGM restoration."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import native_sprite_gap
import package_public_beta as ppb
import prepare_product_r51 as r51
from restore_star_world_1 import lorom

TARGET = "demo11-native-product-r51"
BINARY = ROOT / "local/build" / TARGET / "BrutalMarioDemo11ProductR51SNESRecomp"
ROM_PATH = ROOT / "local/restoration" / TARGET / "rom.sfc"
CAPTURE_ROOT = ROOT / "local/captures/r51-overworld-music-verify"

EXPECTED_TABLE = bytes.fromhex("1e232225292726")
TABLE_A_OFF = lorom(0x048D8A)
TABLE_B_OFF = lorom(0x04DBC8)
SONG_TABLE_OFF = lorom(0x0FE000)

SUBMAP_CASES = [
    (1, 0x23, "World 6 Sky"),
    (2, 0x22, "World 4 Cave"),
    (3, 0x25, "World 7"),
    (4, 0x29, "Star World"),
    (5, 0x27, "Special Zone"),
    (6, 0x26, "World 5"),
]

BOOT_TO_OVERWORLD = (
    "turbo on\n"
    "until 0100 == 07 4000\n"
    "wait 10\n"
    "press start 2\n"
    "until 0100 == 08 900\n"
    "wait 180\n"
    "press start 2\n"
    "until16 010b == 01c5 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "press a 2\n"
    "until16 010b == 014b 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "press b 2\n"
    "until16 010b == 014c 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "press a 2\n"
    "until16 010b == 014d 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "press b 2\n"
    "until 0100 == 0e 2400\n"
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_song_payload(rom: bytes, slot: int) -> tuple[int, int, bytes]:
    ptr_off = SONG_TABLE_OFF + slot * 3
    snes_addr = int.from_bytes(rom[ptr_off : ptr_off + 3], "big")
    file_off = lorom(snes_addr)
    size, dest = struct.unpack_from("<HH", rom, file_off)
    payload = rom[file_off + 4 : file_off + 4 + size]
    return snes_addr, dest, payload


def _run_submap_session(session_dir: Path, submap: int) -> dict:
    """Boot native r51 to Overworld, transfer to `submap`, and capture 1DFB + APU RAM."""
    if session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True)
    (session_dir / "saves").mkdir()

    cfg_path = session_dir / "config.ini"
    cfg_path.write_text(ppb.format_config_ini("linux"), encoding="utf-8")

    probe_lines = "".join(f"wait 3\ndump d{i:02d}\n" for i in range(30))
    script_text = (
        BOOT_TO_OVERWORLD
        + f"poke 1f11 {submap:02x}{submap:02x}\n"
        + "poke 0100 0b\n"
        + "until 0100 == 0c 600\n"
        + probe_lines
        + "until 0100 == 0e 600\n"
        + "wait 30\n"
        + "dump settled\n"
        + "quit\n"
    )
    script_path = session_dir / "route.script"
    script_path.write_text(script_text, encoding="utf-8")

    apu_dump_path = session_dir / "apu-ram.bin"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BM_", "SNESRECOMP_", "M1_"))}
    env.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        SNESRECOMP_REWIND="0",
        BM_LANG="en",
        SNESRECOMP_DUMP_DIR=str(session_dir),
        M1_APU_DUMP=str(apu_dump_path),
    )
    native_sprite_gap.environment(TARGET, env)

    res = subprocess.run(
        [
            str(BINARY),
            "--no-launcher",
            "--config",
            str(cfg_path),
            "--rom",
            str(ROM_PATH),
            "--script",
            str(script_path),
        ],
        cwd=session_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    (session_dir / "run.log").write_text(res.stdout + res.stderr, encoding="utf-8")
    if res.returncode != 0:
        raise AssertionError(
            f"submap {submap} session failed (rc={res.returncode}):\n{res.stderr}\n{res.stdout}"
        )
    if "exit: script quit" not in res.stderr:
        raise AssertionError(f"submap {submap} missing script quit exit marker")
    if not apu_dump_path.is_file():
        raise AssertionError(f"submap {submap} missing apu-ram.bin dump")

    requests = []
    for i in range(30):
        wram = (session_dir / f"d{i:02d}.wram.bin").read_bytes()
        if wram[0x1DFB] != 0:
            requests.append(wram[0x1DFB])
    settled_wram = (session_dir / "settled.wram.bin").read_bytes()
    apu_ram = apu_dump_path.read_bytes()
    return {
        "submap": submap,
        "requests": requests,
        "unique_requests": sorted(set(requests)),
        "settled_mode": settled_wram[0x0100],
        "settled_map": settled_wram[0x1F11],
        "apu_ram": apu_ram,
        "script_sha256": _sha256(script_path.read_bytes()),
    }


class ProductR51OverworldMusicTests(unittest.TestCase):
    _captures: dict[int, dict] | None = None

    @classmethod
    def _ensure_captures(cls) -> dict[int, dict]:
        if cls._captures is not None:
            return cls._captures
        if not BINARY.is_file() or not ROM_PATH.is_file():
            raise unittest.SkipTest("demo11-native-product-r51 binary or ROM not built yet")

        CAPTURE_ROOT.mkdir(parents=True, exist_ok=True)
        rom = ROM_PATH.read_bytes()
        results: dict[int, dict] = {}
        receipt_submaps = []

        for submap, expected_slot, label in SUBMAP_CASES:
            session_dir = CAPTURE_ROOT / f"submap{submap}_{expected_slot:02x}"
            res = _run_submap_session(session_dir, submap)
            results[submap] = res

            _, _, expected_payload = _extract_song_payload(rom, expected_slot)
            aram_slice = res["apu_ram"][0x5400 : 0x5400 + len(expected_payload)]
            receipt_submaps.append(
                {
                    "submap": submap,
                    "label": label,
                    "expected_slot": f"0x{expected_slot:02x}",
                    "observed_1dfb_requests": [f"0x{x:02x}" for x in res["unique_requests"]],
                    "settled_mode": f"0x{res['settled_mode']:02x}",
                    "settled_map": f"0x{res['settled_map']:02x}",
                    "expected_payload_bytes": len(expected_payload),
                    "expected_payload_sha256": _sha256(expected_payload),
                    "aram_5400_sha256": _sha256(aram_slice),
                    "aram_5400_match": aram_slice == expected_payload,
                    "script_sha256": res["script_sha256"],
                }
            )

        receipt = {
            "target": TARGET,
            "rom_sha256": _sha256(rom),
            "binary_sha256": _sha256(BINARY.read_bytes()),
            "submaps": receipt_submaps,
        }
        (CAPTURE_ROOT / "receipt.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        cls._captures = results
        return cls._captures

    def test_rom_diff_tables_payloads_and_active_target_guard(self):
        r50_rom_path = ROOT / "local/restoration/demo11-native-product-r50/rom.sfc"
        do1_rom_path = ROOT / "local/content-versions/demo-only-1/rom.sfc"
        if not ROM_PATH.is_file() or not r50_rom_path.is_file() or not do1_rom_path.is_file():
            self.skipTest("required r50/r51/demo-only-1 ROMs not present")

        r50_rom = r50_rom_path.read_bytes()
        r51_rom = ROM_PATH.read_bytes()
        do1_rom = do1_rom_path.read_bytes()

        self.assertEqual(_sha256(r51_rom), r51.EXPECTED_R51_ROM_SHA)
        diffs = [i for i, (a, b) in enumerate(zip(r50_rom, r51_rom)) if a != b]
        self.assertEqual(diffs, [0x20D8B, 0x20D8C, 0x25BC9, 0x25BCA])
        self.assertEqual((r50_rom[0x20D8B], r51_rom[0x20D8B]), (0x22, 0x23))
        self.assertEqual((r50_rom[0x20D8C], r51_rom[0x20D8C]), (0x27, 0x22))
        self.assertEqual((r50_rom[0x25BC9], r51_rom[0x25BC9]), (0x22, 0x23))
        self.assertEqual((r50_rom[0x25BCA], r51_rom[0x25BCA]), (0x27, 0x22))

        self.assertEqual(r51_rom[TABLE_A_OFF : TABLE_A_OFF + 7], EXPECTED_TABLE)
        self.assertEqual(r51_rom[TABLE_B_OFF : TABLE_B_OFF + 7], EXPECTED_TABLE)
        self.assertEqual(r51_rom[TABLE_A_OFF : TABLE_A_OFF + 7], do1_rom[TABLE_A_OFF : TABLE_A_OFF + 7])
        self.assertEqual(r51_rom[TABLE_B_OFF : TABLE_B_OFF + 7], do1_rom[TABLE_B_OFF : TABLE_B_OFF + 7])

        # Verify r50 Yoshi's House InitialSaveData remains preserved.
        self.assertEqual(
            r51_rom[0x1EF0 : 0x1EF0 + 22],
            r51.EXPECTED_R50_INITIAL_SAVE_DATA,
        )

        # Verify intact $0F:E000 upload headers and payloads for all 7 Overworld slots.
        for slot in (0x1E, 0x22, 0x23, 0x25, 0x26, 0x27, 0x29):
            snes_addr, dest, payload = _extract_song_payload(r51_rom, slot)
            self.assertNotEqual(snes_addr, 0, f"slot {slot:#04x} pointer is zero")
            self.assertEqual(dest, 0x5400, f"slot {slot:#04x} dest != 0x5400")
            self.assertGreater(len(payload), 0, f"slot {slot:#04x} empty payload")
            self.assertEqual(
                (snes_addr, dest, payload),
                _extract_song_payload(r50_rom, slot),
                f"slot {slot:#04x} payload drifted from r50",
            )

        # Permanent active-target regression guard so future r52+ merges cannot lose this fix.
        launch_text = (ROOT / "tools/launch_native.py").read_text(encoding="utf-8")
        m = re.search(r'--target",\s*default="([^"]+)"', launch_text)
        self.assertIsNotNone(m, "could not parse default --target from tools/launch_native.py")
        active_target = m.group(1)
        active_rom_path = ROOT / "local/restoration" / active_target / "rom.sfc"
        if active_rom_path.is_file():
            active_rom = active_rom_path.read_bytes()
            self.assertEqual(
                active_rom[TABLE_A_OFF : TABLE_A_OFF + 7],
                EXPECTED_TABLE,
                f"active target {active_target} regressed OverworldMusic ($04:8D8A)",
            )
            self.assertEqual(
                active_rom[TABLE_B_OFF : TABLE_B_OFF + 7],
                EXPECTED_TABLE,
                f"active target {active_target} regressed OverworldMusic2 ($04:DBC8)",
            )

    def test_native_overworld_submaps_1dfb_and_aram_5400(self):
        captures = self._ensure_captures()
        rom = ROM_PATH.read_bytes()

        for submap, expected_slot, label in SUBMAP_CASES:
            res = captures[submap]
            self.assertEqual(
                res["settled_mode"],
                0x0E,
                f"submap {submap} ({label}) did not settle to Overworld mode 0x0E",
            )
            self.assertEqual(
                res["settled_map"],
                submap,
                f"submap {submap} ({label}) settled on wrong submap",
            )
            self.assertEqual(
                res["unique_requests"],
                [expected_slot],
                f"submap {submap} ({label}) $1DFB={res['unique_requests']}, expected {[expected_slot]}",
            )

            _, _, expected_payload = _extract_song_payload(rom, expected_slot)
            aram = res["apu_ram"]
            self.assertEqual(len(aram), 65536)
            self.assertEqual(
                aram[0x5400 : 0x5400 + len(expected_payload)],
                expected_payload,
                f"submap {submap} ({label}) ARAM $5400 did not match slot {expected_slot:#04x}",
            )


if __name__ == "__main__":
    unittest.main()

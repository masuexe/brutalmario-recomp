#!/usr/bin/env python3
"""Prepare demo11-native-product-r52: cumulative r51 + native mod runtime & 16:9 widescreen."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import native_sprite_gap
from restore_star_world_1 import sha, write_verified

PARENT = "demo11-native-product-r51"
TARGET = "demo11-native-product-r52"
R51_SHA = "be82cf49edd22a975fbce35ac7d570260494fc7812715fd2862f497504ce5948"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"


def write_symbols_toml() -> None:
    """Copy r51 symbols.toml to r52 with updated header comment."""
    r51_sym = ROOT / "recomp/targets" / PARENT / "symbols.toml"
    r52_sym = ROOT / "recomp/targets" / TARGET / "symbols.toml"
    r52_sym.parent.mkdir(parents=True, exist_ok=True)
    text = r51_sym.read_text(encoding="utf-8")
    old_hdr = "# Symbol map for Brutal Mario Demo11 Product R51."
    new_hdr = "# Symbol map for Brutal Mario Demo11 Product R52."
    assert old_hdr in text, "unexpected r51 symbols.toml header"
    r52_sym.write_text(text.replace(old_hdr, new_hdr, 1), encoding="utf-8")


def prepare() -> None:
    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text(encoding="utf-8"))
    r51_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r51_rom = r51_rom_path.read_bytes()
    assert len(r51_rom) == 4194304, len(r51_rom)
    assert sha(r51_rom) == R51_SHA, f"r51 ROM SHA-256 mismatch: {sha(r51_rom)}"
    assert parent_cfg["output"]["sha256"] == R51_SHA

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["target"] = "Brutal Mario Demo11 Product R52"
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R51_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["native_enhancements"] = True
    cfg["scope"] = (
        "Cumulative r51 (all 71 BM_* packs, bilingual EN/JA localization, Demo 7 English OW names, "
        "Room 0x116 countdown fix, Yoshi's House InitialSaveData, World 4 & 6 OW map BGM) + "
        "native SNESRecomp mod runtime mounting (mods/preloaded catalog, Trusted Plugins, "
        "non-executable pack/localization overrides) and opt-in native 16:9 widescreen PPU rendering "
        "(400x224 scrolling courses with dynamic edge clamping, BG3 HUD clamping, and centered Overworld/cutscenes/bosses)."
    )
    cfg["native_sprite_gap"]["frozen_manifests"] = list(
        parent_cfg["native_sprite_gap"]["frozen_manifests"]
    )
    cfg["native_sprite_gap"]["extra_patches"] = []
    cfg["code_patches"] = []
    cfg["output"] = {"size": 4194304, "sha256": R51_SHA}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    write_symbols_toml()
    native_sprite_gap.prepare(TARGET)

    r51_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r51_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r52_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r52_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 71, f"expected 71 packs, got {len(collected)}"
    print(f"Prepared {TARGET}: rom_sha256={R51_SHA}, packs={len(collected)}")


if __name__ == "__main__":
    prepare()

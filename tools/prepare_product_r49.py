#!/usr/bin/env python3
"""Prepare demo11-native-product-r49: cumulative r48 + Demo 7 English Overworld names."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import audit_localization
import build_smw_delta
import native_sprite_gap
import prepare_product_r47 as r47
from restore_star_world_1 import sha, write_verified

PARENT = "demo11-native-product-r48"
TARGET = "demo11-native-product-r49"
R48_SHA = "bbd52ff43fe86e872ee2c55da7adf40ca0eb52e117d529bc5449f3aae5b1bc52"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"

AUDIT_JSON = ROOT / "config/native-content/localization-audit-r49.json"
PACK_SOURCE = "local/native-modules/lang-r47-v2"
EXPECTED_BMLG_SHA = "1fe91ec2d233cb300251461b93ca869fe3a6f5a641e32894f92e6c026a7cca3f"
EXPECTED_BMLG_SIZE = 30814
EXPECTED_CODE_SHA = "ea1c8cef78d1f32b68fa9db0dfdc5767f11d3ad36fa9f94aff9df75555e0deb8"
EXPECTED_CODE_SIZE = 4096


def build_data_pack() -> bytes:
    """Build deterministic BMLG v1 pack (81 EN OW names) for $D5:8000 from pinned r49 audit."""
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    pack = audit_localization.build_bmlg_pack(audit, local_dir=ROOT / "local")
    assert len(pack) == EXPECTED_BMLG_SIZE <= 32768, len(pack)
    assert sha(pack) == EXPECTED_BMLG_SHA, sha(pack)
    return pack


def write_symbols_toml() -> None:
    """Copy r48 symbols.toml to r49 with updated header comment."""
    r48_sym = ROOT / "recomp/targets" / PARENT / "symbols.toml"
    r49_sym = ROOT / "recomp/targets" / TARGET / "symbols.toml"
    r49_sym.parent.mkdir(parents=True, exist_ok=True)
    text = r48_sym.read_text(encoding="utf-8")
    old_hdr = "# Symbol map for Brutal Mario Demo11 Product R48."
    new_hdr = "# Symbol map for Brutal Mario Demo11 Product R49."
    assert old_hdr in text, "unexpected r48 symbols.toml header"
    r49_sym.write_text(text.replace(old_hdr, new_hdr, 1), encoding="utf-8")


def prepare() -> None:
    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text(encoding="utf-8"))
    r48_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r48_rom = r48_rom_path.read_bytes()
    assert len(r48_rom) == 4194304, len(r48_rom)
    assert sha(r48_rom) == R48_SHA, f"r48 ROM SHA-256 mismatch: {sha(r48_rom)}"
    assert parent_cfg["output"]["sha256"] == R48_SHA

    data_bytes = build_data_pack()
    code_bytes, _entrypoints = r47.build_code_pack_and_entrypoints()
    data_sha = sha(data_bytes)
    code_sha = sha(code_bytes)
    assert data_sha == EXPECTED_BMLG_SHA and len(data_bytes) == EXPECTED_BMLG_SIZE
    assert code_sha == EXPECTED_CODE_SHA and len(code_bytes) == EXPECTED_CODE_SIZE

    pack_dir = ROOT / PACK_SOURCE
    pack_dir.mkdir(parents=True, exist_ok=True)
    for fname, blob in ((r47.DATA_PACK_FILE, data_bytes), (r47.CODE_PACK_FILE, code_bytes)):
        write_verified(pack_dir / fname, blob)

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["target"] = "Brutal Mario Demo11 Product R49"
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R48_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["scope"] = (
        "Cumulative r48 (Room 0x116 countdown ExGFX 0x12A + Super GFX Bypass SP2 protection) "
        "+ Demo 7 English Overworld level names: upgrade BM_LANG_R47_DATA_PACK ($D5:8000, 30814B) "
        "to lang-r47-v2 (81 EN / 3 blank / 12 post-demo7 JP auto-fallback Overworld names) "
        "while preserving r47/r48 historical baselines intact."
    )
    cfg["native_sprite_gap"]["frozen_manifests"] = list(
        cfg["native_sprite_gap"]["manifests"]
    )
    updated_data_pack = False
    updated_code_pack = False
    for pack in cfg["native_sprite_gap"]["extra_packs"]:
        if pack["variable"] == r47.DATA_PACK_VAR:
            pack["size"] = len(data_bytes)
            pack["sha256"] = data_sha
            pack["source"] = PACK_SOURCE
            updated_data_pack = True
        elif pack["variable"] == r47.CODE_PACK_VAR:
            pack["size"] = len(code_bytes)
            pack["sha256"] = code_sha
            pack["source"] = PACK_SOURCE
            updated_code_pack = True
    assert updated_data_pack and updated_code_pack, "missing r47 lang packs in parent config"
    cfg["native_sprite_gap"]["extra_patches"] = []
    cfg["code_patches"] = []
    cfg["output"] = {"size": 4194304, "sha256": R48_SHA}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    write_symbols_toml()
    native_sprite_gap.prepare(TARGET)

    r48_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r48_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r49_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r49_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 71, f"expected 71 packs, got {len(collected)}"
    print(
        f"Prepared {TARGET}: rom_sha256={R48_SHA}, "
        f"data_pack=({len(data_bytes)}B, {data_sha}), "
        f"code_pack=({len(code_bytes)}B, {code_sha}), packs={len(collected)}"
    )


if __name__ == "__main__":
    prepare()

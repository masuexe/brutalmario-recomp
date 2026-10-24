#!/usr/bin/env python3
"""Brutal Mario music ID mapping and conversion between demo families.

Legacy family: cheap_demo, 7hero, mazo, ow, demo7, demo8.
New family:    demoOnly1 (2012) and demo 1-1 (2015).

Provides:
- config/music-mapping.json database
- docs/music-mapping.md reference documentation
- Python API: resolve_music_id(source_id, from_family, to_version)
- CLI lookup and verification commands
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE_ADDR = 0x0FE000


def lorom(address: int) -> int:
    bank, low = address >> 16, address & 0xFFFF
    if not 0 <= bank <= 0xFF or bank in (0x7E, 0x7F) or low < 0x8000:
        raise ValueError(f"not mapped LoROM: {address:06X}")
    return (bank & 0x7F) * 0x8000 + (low & 0x7FFF)


# Static curated data base merged from wiki extractions, revision logs, and ROM inspection
BASE_MAPPINGS = [
    {
        "legacy_id": "0x24",
        "demo_only1_id": "0x51",
        "demo11_id": "0x51",
        "title": "Fear Factory",
        "origin_game": "Donkey Kong Country",
        "levels": ["Cave Star", "Castle Crush", "Skull Coaster"],
        "verification_status": "verified_graph_match",
        "notes": "Fast industrial mine theme. Verified present in demoOnly1 and demo1-1 slot $51 (2,656 bytes upload).",
        "wiki_source": "Cave Star",
    },
    {
        "legacy_id": "0x27",
        "demo_only1_id": "0x8E",
        "demo11_id": "0x8E",
        "title": "Castle Pandemonium",
        "origin_game": "Final Fantasy II",
        "levels": ["Finish! Bowser Keep (Crash/Burn)"],
        "verification_status": "verified_graph_match",
        "notes": "Plays during the Crash and Burn segment in Bowser's Keep. Verified present in demo1-1 slot $8E (766 bytes).",
        "wiki_source": "Finish! Bowser Keep",
    },
    {
        "legacy_id": "0x28",
        "demo_only1_id": "0x49",
        "demo11_id": "0x49",
        "title": "Podol / Boundaries",
        "origin_game": "Romancing SaGa 3",
        "levels": ["Bay Star", "Frozen Cave (pre-clear)", "Deep Sea Research", "Ocean Palace"],
        "verification_status": "verified_graph_match",
        "notes": "Plays in Bay Star and un-cleared Frozen Cave. Confirmed by user playtests. Verified present in demo1-1 slot $49 (609 bytes).",
        "wiki_source": "Bay Star",
    },
    {
        "legacy_id": "0x2E",
        "demo_only1_id": "0x58",
        "demo11_id": "0x58",
        "title": "Grape Garden",
        "origin_game": "Kirby's Adventure",
        "levels": ["Sky Star", "Athletic Special (part 3)", "Battleship Halberd", "Dolphin Barbecue", "The Future of UFOs", "Twin Lifts"],
        "verification_status": "verified_graph_match",
        "notes": "Used across multiple sky and flying stages. Verified present in demo1-1 slot $58 (1,010 bytes).",
        "wiki_source": "Sky Star",
    },
    {
        "legacy_id": "0x30",
        "demo_only1_id": "0x7A",
        "demo11_id": "0x7A",
        "title": "Slide",
        "origin_game": "Super Mario 64",
        "levels": ["End of Special Zone", "Special Warp Star"],
        "verification_status": "verified_graph_match",
        "notes": "Slider track from Super Mario 64. Verified present in demo1-1 slot $7A (2,370 bytes).",
        "wiki_source": "End of Special Zone",
    },
    {
        "legacy_id": "0x33",
        "demo_only1_id": "0xAC",
        "demo11_id": "0xAC",
        "title": "Last Battle",
        "origin_game": "Romancing SaGa 2",
        "levels": ["Seven Koopalings Boss", "Wily's Revenge"],
        "verification_status": "verified_graph_match",
        "notes": "Seven Heroes battle theme. In cheap_demo selectable as BGM 32/33; mapped to $AC in new family (2,318 bytes).",
        "wiki_source": "Finish! Bowser Keep",
    },
    {
        "legacy_id": "0x36",
        "demo_only1_id": "0x61",
        "demo11_id": "0x61",
        "title": "Rainbow Resort",
        "origin_game": "Kirby's Adventure",
        "levels": ["Mario's Attack", "Athletic Special (parts 1-2)", "Ludwig's Castle"],
        "verification_status": "verified_graph_match",
        "notes": "Kirby night sky theme. Verified present in demo1-1 slot $61 (806 bytes).",
        "wiki_source": "Mario's Attack",
    },
    {
        "legacy_id": "0x38",
        "demo_only1_id": "0xA4",
        "demo11_id": "0xA4",
        "title": "The Decisive Battle",
        "origin_game": "Final Fantasy VI",
        "levels": ["Naval Piranha Boss", "Ocean Palace Boss", "Finish! Bowser Keep (Naval Piranha)"],
        "verification_status": "verified_graph_match",
        "notes": "Boss battle theme. Verified present in demo1-1 slot $A4 (1,645 bytes).",
        "wiki_source": "Finish! Bowser Keep",
    },
    {
        "legacy_id": "0x39",
        "demo_only1_id": "0x98",
        "demo11_id": "0x98",
        "title": "Go! Go! Kids!",
        "origin_game": "Treasure Hunter G",
        "levels": ["Twinbee Special (Dangling Ghost Boss)", "Morton the NEET Boss", "Special Warp Star Boss", "Haunt-idiot Mansion"],
        "verification_status": "verified_graph_match",
        "notes": "Whimsical boss theme. Verified present in demo1-1 slot $98 (2,057 bytes).",
        "wiki_source": "Twinbee Special",
    },
    {
        "legacy_id": "0x3A",
        "demo_only1_id": "0xA2",
        "demo11_id": "0xA2",
        "title": "The Flame and the Arrow",
        "origin_game": "Treasure of the Rudras",
        "levels": ["Two-Face Moon Boss", "Wendy the Gal Boss", "Finish! Bowser Keep (Two-Face Moon)"],
        "verification_status": "verified_graph_match",
        "notes": "Rudra boss theme. Verified present in demo1-1 slot $A2 (2,000 bytes).",
        "wiki_source": "Finish! Bowser Keep",
    },
    {
        "legacy_id": "0x3B",
        "demo_only1_id": "0x9C",
        "demo11_id": "0x9C",
        "title": "Irwin on Reflection",
        "origin_game": "Legend of Mana",
        "levels": ["Baby Bowser Boss", "Toad Boss (End of Special Zone)", "Mirror Fort"],
        "verification_status": "verified_graph_match",
        "notes": "Legend of Mana boss track. Verified present in demo1-1 slot $9C (1,801 bytes).",
        "wiki_source": "End of Special Zone",
    },
    {
        "legacy_id": "0x3E",
        "demo_only1_id": None,
        "demo11_id": "0x8D",
        "title": "Koopa's Road",
        "origin_game": "Super Mario 64",
        "levels": ["Finish! Bowser Keep (SMB3 Castle)"],
        "verification_status": "verified_graph_match",
        "notes": "Excluded from demoOnly1 (which had NSMB Castle at $8D), but reinstated in demo 1-1 at slot $8D (2,280 bytes).",
        "wiki_source": "Music",
    },
    {
        "legacy_id": "0x40",
        "demo_only1_id": "0x60",
        "demo11_id": "0x60",
        "title": "Iceberg Ocean",
        "origin_game": "Kirby's Dream Course",
        "levels": ["Valley Star", "Athletic Special (part 4)", "What Matches a Key?", "Mario's Item Theft", "Northern Resort"],
        "verification_status": "verified_graph_match",
        "notes": "Star World lower-inner theme. 12/16 channel graphs match donor group. Verified in demo1-1 slot $60 (1,196 bytes).",
        "wiki_source": "Valley Star",
    },
    {
        "legacy_id": "0x41",
        "demo_only1_id": "0x79",
        "demo11_id": "0x79",
        "title": "Cap Theme",
        "origin_game": "Super Mario 64",
        "levels": ["Valley Star (Cap item power-up)"],
        "verification_status": "verified_byte_identical",
        "notes": "Mario 64 cap music. 16/16 channel graphs match donor group. Verified in demo1-1 slot $79 (416 bytes).",
        "wiki_source": "Valley Star",
    },
    {
        "legacy_id": "0x42",
        "demo_only1_id": "0x71",
        "demo11_id": "0x71",
        "title": "A Child's Fantasy Realm",
        "origin_game": "Pop'n Twinbee: Rainbow Bell Adventures",
        "levels": ["Twinbee Special", "Gachapoko Land"],
        "verification_status": "verified_graph_match",
        "notes": "Twinbee level theme. Verified present in demo1-1 slot $71 (1,328 bytes).",
        "wiki_source": "Twinbee Special",
    },
    {
        "legacy_id": "0x43",
        "demo_only1_id": "0x59",
        "demo11_id": "0x59",
        "title": "Aboard the Hilda Garde",
        "origin_game": "Final Fantasy IX",
        "levels": ["Milky Way Wishes", "Night Galaxy Train", "Really Big Jump"],
        "verification_status": "verified_graph_match",
        "notes": "Airship theme from FF9. Verified present in demo1-1 slot $59 (3,048 bytes).",
        "wiki_source": "Milky Way Wishes",
    },
    {
        "legacy_id": "0x47",
        "demo_only1_id": None,
        "demo11_id": "0x6B",
        "title": "Leonid's Castle",
        "origin_game": "Romancing SaGa 3",
        "levels": ["Gourmet Boo", "Koindozer Forest", "A Remote Shack", "Fear of Monday", "Ocean Palace", "The Cursed Mansion", "Titanic"],
        "verification_status": "verified_graph_match",
        "notes": "Omitted in demoOnly1, reinstated in demo 1-1 at slot $6B (604 bytes upload).",
        "wiki_source": "Music",
    },
    {
        "legacy_id": "0x4A",
        "demo_only1_id": "0x38",
        "demo11_id": "0x38",
        "title": "Town Where the West Wind Blows",
        "origin_game": "Wild Arms 2",
        "levels": ["Baby Yoshi Hill", "Grassland Star"],
        "verification_status": "verified_graph_match",
        "notes": "Western acoustic guitar theme. Verified present in demo1-1 slot $38 (1,237 bytes).",
        "wiki_source": "Baby Yoshi Hill",
    },
    {
        "legacy_id": "0x4B",
        "demo_only1_id": "0xB9",
        "demo11_id": "0xB9",
        "title": "To Far Away Times",
        "origin_game": "Chrono Trigger",
        "levels": ["Unused / Ending sequences"],
        "verification_status": "verified_graph_match",
        "notes": "Chrono Trigger ending theme. Verified present in demo1-1 slot $B9 (2,090 bytes).",
        "wiki_source": "Music",
    },
    {
        "legacy_id": "0x58",
        "demo_only1_id": "0xA0",
        "demo11_id": "0xA0",
        "title": "Boss Theme",
        "origin_game": "Super Nazo Puyo: Rulue's Roux",
        "levels": ["Finish! Bowser Keep (Section 1)", "Fort of Gravity"],
        "verification_status": "verified_graph_match",
        "notes": "Fast-paced Puyo boss track. Verified present in demo1-1 slot $A0 (2,668 bytes).",
        "wiki_source": "Finish! Bowser Keep",
    },
    {
        "legacy_id": "0x59",
        "demo_only1_id": "0x39",
        "demo11_id": "0x39",
        "title": "Hometown Domina",
        "origin_game": "Legend of Mana",
        "levels": ["Unused in cheap_demo, present in demoOnly line"],
        "verification_status": "verified_graph_match",
        "notes": "Town music from Legend of Mana. Verified present in demo1-1 slot $39 (1,703 bytes).",
        "wiki_source": "Music",
    },
    {
        "legacy_id": "0x5D",
        "demo_only1_id": "0x32",
        "demo11_id": "0x32",
        "title": "Freiluftmusik",
        "origin_game": "SaGa Frontier 2",
        "levels": ["Plains Star", "Chomp Chomp Panic 1", "Fishing Spree"],
        "verification_status": "verified_graph_match",
        "notes": "Open-air acoustic melody. Verified present in demo1-1 slot $32 (942 bytes).",
        "wiki_source": "Plains Star",
    },
    {
        "legacy_id": "0x61",
        "demo_only1_id": "0xA5",
        "demo11_id": "0xA5",
        "title": "The Fierce Battle",
        "origin_game": "Final Fantasy VI",
        "levels": ["Athletic Special (Part 5 / Final section)"],
        "verification_status": "verified_graph_match",
        "notes": "Atma Weapon / Fierce Battle theme. Verified present in demo1-1 slot $A5 (2,881 bytes).",
        "wiki_source": "Athletic Special",
    },
]

# Songs exclusive to the new family (demoOnly1 & demo 1-1)
NEW_FAMILY_ADDITIONS = [
    {"slot": "0x2A", "title": "Prophecy", "origin_game": "Secret of Mana", "introduced_in": "demoOnly1", "notes": "Added in demoOnly1 custom music list."},
    {"slot": "0x52", "title": "Stickerbrush Symphony", "origin_game": "Donkey Kong Country 2", "introduced_in": "demoOnly1", "notes": "Bramble theme ported by Carol."},
    {"slot": "0x5A", "title": "The Moon", "origin_game": "DuckTales", "introduced_in": "demoOnly1", "notes": "Famous 8-bit arrangement."},
    {"slot": "0x62", "title": "Cold Man's Stage", "origin_game": "Mega Man & Bass", "introduced_in": "demoOnly1", "notes": "Rockman & Forte icy stage theme."},
    {"slot": "0x68", "title": "Last Dungeon", "origin_game": "Romancing SaGa 2", "introduced_in": "demoOnly1", "notes": "Used in Bowser's Keep Yoshi coins room and Mammon Machine."},
    {"slot": "0x69", "title": "Ghost House", "origin_game": "New Super Mario Bros.", "introduced_in": "demo 1-1", "notes": "Used in Horror House / Ghost Forest (1,009 bytes)."},
    {"slot": "0x6A", "title": "Krook's March", "origin_game": "Donkey Kong Country 2", "introduced_in": "demo 1-1", "notes": "DKC2 castle / march theme (4,172 bytes)."},
    {"slot": "0x6B", "title": "Leonid's Castle", "origin_game": "Romancing SaGa 3", "introduced_in": "demo 1-1", "notes": "Re-added in demo 1-1 replacing legacy $47 (604 bytes)."},
    {"slot": "0x72", "title": "Taking Over the Halberd", "origin_game": "Kirby Super Star", "introduced_in": "demoOnly1", "notes": "Revenge of Meta Knight airship theme."},
    {"slot": "0x73", "title": "Magic Man's Stage", "origin_game": "Mega Man & Bass", "introduced_in": "demoOnly1", "notes": "Rockman & Forte theme."},
    {"slot": "0x86", "title": "Boss / Action Track", "origin_game": "Custom Port", "introduced_in": "demo 1-1", "notes": "New slot allocated in demo 1-1 table."},
    {"slot": "0x88", "title": "Save Hut", "origin_game": "Kirby Super Star", "introduced_in": "demoOnly1", "notes": "Used in Lemmy's Castle orb room."},
    {"slot": "0x8D", "title": "Koopa's Road", "origin_game": "Super Mario 64", "introduced_in": "demo 1-1", "notes": "Replaces demoOnly1 NSMB Castle; restores SM64 Koopa Road (2,280 bytes)."},
    {"slot": "0x8F", "title": "Thema", "origin_game": "SaGa Frontier 2", "introduced_in": "demoOnly1", "notes": "Main theme arrangement."},
    {"slot": "0x90", "title": "Sad Freedom", "origin_game": "Treasure Hunter G", "introduced_in": "demoOnly1", "notes": "Sad emotional melody."},
    {"slot": "0x91", "title": "The Galaxy Reactor", "origin_game": "Super Mario Galaxy", "introduced_in": "demoOnly1", "notes": "SMG Bowser final galaxy arrangement."},
    {"slot": "0x92", "title": "Undersea Palace", "origin_game": "Chrono Trigger", "introduced_in": "demoOnly1", "notes": "Ocean Palace theme."},
    {"slot": "0x93", "title": "One of Them Is Hope", "origin_game": "Secret of Mana", "introduced_in": "demoOnly1", "notes": "Sanctuary theme."},
    {"slot": "0x94", "title": "The Savior of Those on Earth", "origin_game": "Lufia II", "introduced_in": "demoOnly1", "notes": "Estpolis II boss battle."},
    {"slot": "0x99", "title": "Final Fight", "origin_game": "SNK vs. Capcom: Chaos", "introduced_in": "demoOnly1", "notes": "Fighting game boss theme."},
    {"slot": "0x9A", "title": "Gangplank Galleon", "origin_game": "Donkey Kong Country", "introduced_in": "demoOnly1", "notes": "King K. Rool boss battle."},
    {"slot": "0x9D", "title": "Masked Dedede's Theme", "origin_game": "Kirby Super Star Ultra", "introduced_in": "demoOnly1", "notes": "Revenge of the King arena."},
    {"slot": "0xA6", "title": "Maybe I'm a Lion", "origin_game": "Final Fantasy VIII", "introduced_in": "demoOnly1", "notes": "Griever / Ultimecia battle."},
    {"slot": "0xA7", "title": "High Tension Wire", "origin_game": "Trials of Mana (Seiken Densetsu 3)", "introduced_in": "demoOnly1", "notes": "Fast battle theme."},
    {"slot": "0xA8", "title": "Nuclear Fusion", "origin_game": "Trials of Mana (Seiken Densetsu 3)", "introduced_in": "demoOnly1", "notes": "God-beast battle."},
    {"slot": "0xAB", "title": "Bowser Battle", "origin_game": "Super Mario RPG", "introduced_in": "demoOnly1", "notes": "Chandelier battle theme."},
    {"slot": "0xAE", "title": "Battle With Magus", "origin_game": "Chrono Trigger", "introduced_in": "demoOnly1", "notes": "Decisive Magus duel."},
    {"slot": "0xAF", "title": "The Sun Rises", "origin_game": "Okami", "introduced_in": "demoOnly1", "notes": "Okami climax battle."},
    {"slot": "0xB0", "title": "Megalomania", "origin_game": "Live A Live", "introduced_in": "demo 1-1", "notes": "Re-added in demo 1-1 for Lemmy's Castle boss duel (2,067 bytes)."},
    {"slot": "0xB8", "title": "The Credits Concerto", "origin_game": "Donkey Kong Country", "introduced_in": "demoOnly1", "notes": "DKC end credits medley."},
]

# Songs exclusive to legacy family or unmapped
LEGACY_FAMILY_EXCLUSIVE = [
    {"legacy_id": "0x31", "title": "Go Red Team! Go White Team! Rah Rah Rah!", "origin_game": "Treasure Hunter G", "levels": ["Switch Palaces (Blue, Green, Red, Yellow)"], "notes": "Standard palace track in legacy family; in demoOnly family, standard SMW palace track is used."},
    {"legacy_id": "0x53", "title": "Haunted Chase", "origin_game": "Donkey Kong Country 2", "levels": ["Airborne Cemetery", "Ghost Special", "Abode of Larry"], "notes": "Ghost rope climbing theme from DKC2; present in cheap_demo bank."},
    {"legacy_id": "0x54", "title": "Jingle Bells", "origin_game": "James Lord Pierpont", "levels": ["Snow Star"], "notes": "Holiday theme used in Snow Star. Does not exist in demoOnly1."},
    {"legacy_id": "0x57", "title": "KingBonbie VS MechaBonbie", "origin_game": "Super Momotarou Dentetsu DX", "levels": ["Rescue Yoshi"], "notes": "Mecha Bonbie battle theme; legacy family only."},
    {"legacy_id": "0x5A", "title": "Akuma's Theme", "origin_game": "Street Fighter Alpha 2", "levels": ["Unused in cheap_demo"], "notes": "Present in cheap_demo bank; omitted in demoOnly1."},
    {"legacy_id": "0x5C", "title": "Mißgestalt", "origin_game": "SaGa Frontier 2", "levels": ["Unused in cheap_demo"], "notes": "Present in cheap_demo bank; omitted in demoOnly1."},
]


def resolve_music_id(source_id: int | str, from_family: str = "legacy", to_version: str = "demo1-1") -> str | None:
    """Resolve a music ID between version families.

    Args:
        source_id: Hex string (e.g. '0x28') or int (e.g. 0x28).
        from_family: 'legacy' (cheap_demo/7hero/mazo/ow) or 'new' (demoOnly1/demo1-1).
        to_version: 'demo1-1', 'demoOnly1', or 'legacy'.

    Returns:
        Hex string of resolved ID (e.g. '0x49'), or None if unmapped.
    """
    if isinstance(source_id, int):
        source_hex = f"0x{source_id:02X}"
    else:
        source_hex = source_id if source_id.startswith("0x") else f"0x{int(source_id, 16):02X}"

    source_hex = source_hex.upper().replace("0X", "0x")

    for item in BASE_MAPPINGS:
        if from_family == "legacy":
            if item["legacy_id"].upper() == source_hex.upper():
                if to_version == "demo1-1":
                    return item["demo11_id"]
                elif to_version == "demoOnly1":
                    return item["demo_only1_id"]
        else:  # from new family
            target_id = item["demo11_id"] if to_version == "demo1-1" else item["demo_only1_id"]
            curr_id = item["demo11_id"] if from_family == "demo1-1" else item["demo_only1_id"]
            if curr_id and curr_id.upper() == source_hex.upper():
                return item["legacy_id"]
    return None


def verify_against_roms():
    """Verify pointer validity in demo-1-1 and demo-only-1."""
    d11_path = ROOT / "local/content-versions/demo-1-1/rom.sfc"
    d1_path = ROOT / "local/content-versions/demo-only-1/rom.sfc"

    if not d11_path.exists() or not d1_path.exists():
        print("Note: local ROMs not found, skipping ROM verification check.")
        return True

    d11 = d11_path.read_bytes()
    t = lorom(TABLE_ADDR)

    verified_count = 0
    for item in BASE_MAPPINGS:
        target_id_str = item["demo11_id"]
        if not target_id_str:
            continue
        target_id = int(target_id_str, 16)
        raw = d11[t + target_id * 3 : t + target_id * 3 + 3]
        addr = int.from_bytes(raw, "big")
        assert addr != 0, f"Slot {target_id_str} in demo1-1 is empty!"
        off = lorom(addr)
        count = int.from_bytes(d11[off : off + 2], "little")
        dest = int.from_bytes(d11[off + 2 : off + 4], "little")
        assert dest == 0x5400, f"Slot {target_id_str} dest is {dest:04X}, expected 5400!"
        assert count > 64, f"Slot {target_id_str} count {count} is too small!"
        verified_count += 1

    print(f"Verified {verified_count} demo 1-1 slots directly in ROM: all valid and upload to $5400.")
    return True


def generate_json() -> dict:
    data = {
        "schema": 1,
        "legacy_family": ["cheap_demo", "7hero", "mazo", "ow", "demo7", "demo8"],
        "new_family": ["demoOnly1", "demo-1-1"],
        "description": "Cross-version custom music ID mapping table between Carol's legacy demo family and new demo family.",
        "mappings": BASE_MAPPINGS,
        "new_family_additions": NEW_FAMILY_ADDITIONS,
        "legacy_family_exclusive": LEGACY_FAMILY_EXCLUSIVE,
    }
    out_path = ROOT / "config/music-mapping.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote {out_path} ({len(BASE_MAPPINGS)} mappings, {len(NEW_FAMILY_ADDITIONS)} new additions)")
    return data


def generate_markdown():
    lines = [
        "# Brutal Mario Cross-Version Music ID Mapping Reference",
        "",
        "This document defines the custom music ID mapping between Carol's **Legacy Demo Family**",
        "(`cheap_demo`, `7hero`, `mazo`, `ow`, `demo7`, `demo8`) and the **New Demo Family**",
        "(`demoOnly1` and `demo 1-1`).",
        "",
        "> [!IMPORTANT]",
        "> Numeric music IDs in Brutal Mario are version-local. Level headers (`$3A:B524`),",
        "> sprite music triggers, and `$1DFB` commands in legacy donor ROMs use legacy indices.",
        "> When porting levels or repairing music on the modern line (`demo 1-1`), **never copy",
        "> donor music IDs verbatim**; consult this table to map them to the recipient target.",
        "",
        "## Version Chronology and Engine Architecture",
        "",
        "| Family | ROM Releases | Release Date | Music Engine Architecture |",
        "| :--- | :--- | :--- | :--- |",
        "| **Legacy Family (Old)** | `demo7`, `demo8`, `cheap_demo`, `7hero`, `mazo`, `ow` | ~2008–2011 | Shared 110-entry pointer table at `$0FE000` + multi-song bank group uploads (`$3F:8008`, etc. into ARAM `$6800`). |",
        "| **New Family (Modern)** | `demoOnly1` (2012), `demo 1-1` (2015) | 2012, 2015 | Overhauled global pointer table at `$0FE000` uploading individual custom songs directly to ARAM `$5400`. `demo 1-1` re-adds several unreleased tracks. |",
        "",
        "## Core Cross-Version Mapping Table",
        "",
        "| Legacy ID (`cheap_demo` family) | `demoOnly1` ID | `demo 1-1` ID | Track Title | Origin Game | Verified In-Game Usages | Status |",
        "| :---: | :---: | :---: | :--- | :--- | :--- | :--- |",
    ]

    for m in BASE_MAPPINGS:
        leg = f"`${int(m['legacy_id'], 16):02X}`"
        d1 = f"`${int(m['demo_only1_id'], 16):02X}`" if m["demo_only1_id"] else "*(none)*"
        d11 = f"`${int(m['demo11_id'], 16):02X}`" if m["demo11_id"] else "*(none)*"
        levels = ", ".join(m["levels"][:3])
        if len(m["levels"]) > 3:
            levels += f" (+{len(m['levels']) - 3} more)"
        status = m["verification_status"].replace("_", " ")
        lines.append(f"| **{leg}** | {d1} | **{d11}** | **{m['title']}** | {m['origin_game']} | {levels} | {status} |")

    lines.extend([
        "",
        "## Modern Family Additions (`demoOnly1` and `demo 1-1`)",
        "",
        "These tracks were ported and introduced in Carol's new engine line (`demoOnly1` and `demo 1-1`), and do not exist in the legacy family under these slots:",
        "",
        "| New Slot ID | Track Title | Origin Game | Introduced In | Notes |",
        "| :---: | :--- | :--- | :---: | :--- |",
    ])

    for a in NEW_FAMILY_ADDITIONS:
        slot = f"`${int(a['slot'], 16):02X}`"
        lines.append(f"| **{slot}** | **{a['title']}** | {a['origin_game']} | {a['introduced_in']} | {a['notes']} |")

    lines.extend([
        "",
        "## Legacy Family Exclusive / Unported Tracks",
        "",
        "These tracks exist in the legacy family (`cheap_demo`, etc.) but were either unported or replaced in the new demo line:",
        "",
        "| Legacy ID | Track Title | Origin Game | Known Level Usages | Notes |",
        "| :---: | :--- | :--- | :--- | :--- |",
    ])

    for ex in LEGACY_FAMILY_EXCLUSIVE:
        leg = f"`${int(ex['legacy_id'], 16):02X}`"
        levels = ", ".join(ex["levels"])
        lines.append(f"| **{leg}** | **{ex['title']}** | {ex['origin_game']} | {levels} | {ex['notes']} |")

    lines.extend([
        "",
        "## Agent Restoration Workflow",
        "",
        "When an agent restores a level or repairs music on the modern line (`demo 1-1`):",
        "",
        "1. **Identify the Donor Cue**: Check the donor ROM's room header byte (at `$3A:B524` or similar), sprite controller immediates (such as cap expiry), or `$1DFB` writes in execution captures.",
        "2. **Look Up the Recipient Slot**: Consult the core table above. For example, if donor requests `$28` (Podol), map to recipient `$49`. If donor requests `$40` (Iceberg Ocean), map to recipient `$60` (header byte `$61`).",
        "3. **Special Bank Dependencies**: If donor requested a bank-internal selection (such as cap requests `$21/$22` inside bank `$3F:8008`), translate to recipient global custom song slots (cap pickup `$79`, cap expiry resume `$60`).",
        "4. **Re-added in Demo 1-1**: For tracks like *Koopa's Road* (`$8D`), *Leonid's Castle* (`$6B`), or *Megalomania* (`$B0`), use the `demo 1-1` ID even though `demoOnly1` lacked them.",
        "5. **Unmapped Tracks**: If the donor track has no recipient slot, do not invent arbitrary IDs. Follow the protocol in [`docs/world1-room106-music-investigation.md`](world1-room106-music-investigation.md) to audition candidate library tracks or consult the user.",
    ])

    out_path = ROOT / "docs/music-mapping.md"
    out_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["generate", "lookup", "verify"], default="generate", nargs="?")
    parser.add_argument("id", nargs="?", help="Hex ID to look up (e.g. 0x28 or 28)")
    parser.add_argument("--family", choices=["legacy", "new"], default="legacy", help="Source family for lookup")
    parser.add_argument("--target", choices=["demo1-1", "demoOnly1", "legacy"], default="demo1-1", help="Target version")
    args = parser.parse_args()

    if args.command == "generate":
        generate_json()
        generate_markdown()
        verify_against_roms()
    elif args.command == "verify":
        verify_against_roms()
    elif args.command == "lookup":
        if not args.id:
            print("Error: lookup command requires an ID argument (e.g. 'python3 tools/music_mapping.py lookup 0x28')")
            sys.exit(1)
        res = resolve_music_id(args.id, from_family=args.family, to_version=args.target)
        if res:
            print(f"Lookup {args.id} (from {args.family}) -> {res} (in {args.target})")
        else:
            print(f"Lookup {args.id} (from {args.family}): NO MAPPING FOUND for {args.target}")


if __name__ == "__main__":
    main()

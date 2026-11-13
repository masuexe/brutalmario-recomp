#!/usr/bin/env python3
"""Prepare demo11-native-product-r47: bilingual EN/JA native product target."""
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import audit_localization
import build_smw_delta
import native_sprite_gap
from restore_star_world_1 import lorom, sha, write_verified

PARENT = "demo11-native-product-r46"
TARGET = "demo11-native-product-r47"
R46_SHA = "142ee768d1d5cd436a17d459719b30a02ba5dafaa79271b9d3c37da4965a0b7e"
MUSIC_PACK_SHA = "b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47"
AUDIT_JSON = ROOT / "config/native-content/localization-audit-r47.json"
EXPECTED_BMLG_SHA = "dc88751479e1342c31da4fd292a8c371b4c792179de547439b258ee24f7b819a"
EXPECTED_BMLG_SIZE = 30814

PACK_SOURCE = "local/native-modules/lang-r47-v1"

DATA_PACK_ADDRESS = 0xD58000
DATA_PACK_FILE = "lang-r47-data.bin"
DATA_PACK_VAR = "BM_LANG_R47_DATA_PACK"

CODE_PACK_ADDRESS = 0x908000
CODE_PACK_SIZE = 0x1000
CODE_PACK_FILE = "lang-r47-code.bin"
CODE_PACK_VAR = "BM_LANG_R47_CODE_PACK"

CONTROL_BLOCK_OFFSET = 0x0FF0  # $90:8FF0..8FFF (16 bytes, zero on disk)
CONTROL_BLOCK_SIZE = 16
EFFECTIVE_LANG_ADDR = CODE_PACK_ADDRESS + CONTROL_BLOCK_OFFSET  # $90:8FF0


class Asm65816:
    """Minimal two-pass 65816 assembler anchored at a LoROM base address."""

    def __init__(self, base_addr: int) -> None:
        self.base_addr = base_addr
        self.buf = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str, str]] = []

    @property
    def pc(self) -> int:
        return self.base_addr + len(self.buf)

    def label(self, name: str) -> None:
        assert name not in self.labels, f"duplicate label: {name}"
        self.labels[name] = self.pc

    def emit(self, *bytes_or_hex: int | str) -> None:
        for item in bytes_or_hex:
            if isinstance(item, str):
                self.buf.extend(bytes.fromhex(item))
            else:
                self.buf.append(item & 0xFF)

    def u16(self, val: int) -> None:
        self.buf.extend(struct.pack("<H", val & 0xFFFF))

    def u24(self, addr: int) -> None:
        self.buf.extend((addr & 0xFF, (addr >> 8) & 0xFF, (addr >> 16) & 0xFF))

    def branch(self, opcode: int, target: str) -> None:
        self.emit(opcode)
        self.fixups.append((len(self.buf), "rel8", target))
        self.emit(0x00)

    def jmp(self, target: str) -> None:
        self.emit(0x4C)
        self.fixups.append((len(self.buf), "abs16", target))
        self.u16(0)

    def jsr(self, target: str) -> None:
        self.emit(0x20)
        self.fixups.append((len(self.buf), "abs16", target))
        self.u16(0)

    def jsl_local(self, target: str) -> None:
        self.emit(0x22)
        self.fixups.append((len(self.buf), "abs24", target))
        self.u24(0)

    def jml_local(self, target: str) -> None:
        self.emit(0x5C)
        self.fixups.append((len(self.buf), "abs24", target))
        self.u24(0)

    def resolve(self) -> bytes:
        for pos, kind, target in self.fixups:
            assert target in self.labels, f"unknown label: {target}"
            addr = self.labels[target]
            if kind == "rel8":
                origin = self.base_addr + pos + 1
                delta = addr - origin
                assert -128 <= delta <= 127, (target, delta)
                self.buf[pos] = delta & 0xFF
            elif kind == "abs16":
                assert (addr >> 16) == (self.base_addr >> 16), (target, hex(addr))
                self.buf[pos : pos + 2] = struct.pack("<H", addr & 0xFFFF)
            elif kind == "abs24":
                self.buf[pos : pos + 3] = bytes((addr & 0xFF, (addr >> 8) & 0xFF, (addr >> 16) & 0xFF))
            else:
                raise ValueError(kind)
        return bytes(self.buf)


def build_code_pack_and_entrypoints() -> tuple[bytes, dict[str, int]]:
    """Assemble BM_LANG_R47_CODE_PACK ($90:8000, 4096 B) and return (blob, entrypoints)."""
    a = Asm65816(CODE_PACK_ADDRESS)
    d5_hdr = DATA_PACK_ADDRESS  # $D5:8000

    def lda_long(addr: int) -> None:
        a.emit(0xAF)
        a.u24(addr)

    def adc_long(addr: int) -> None:
        a.emit(0x6F)
        a.u24(addr)

    # ------------------------------------------------------------------
    # NMI/VBlank callbacks invoked via JSL $7E:C130 ($10:821E) with M=1, X=1.
    # Safe host/SFC VBlank DMA of GFX 0x2A (2048 B) to VRAM word $4800.
    # ------------------------------------------------------------------
    a.label("nmi_upload_ja_gfx02a")
    a.emit("08 c2 20")  # PHP; REP #$20
    lda_long(d5_hdr + 0x0E)  # ja_gfx02a_off
    a.branch(0x80, "nmi_upload_gfx02a_common")

    a.label("nmi_upload_en_gfx02a")
    a.emit("08 c2 20")  # PHP; REP #$20
    lda_long(d5_hdr + 0x14)  # en_gfx02a_off

    a.label("nmi_upload_gfx02a_common")
    a.emit("18 69 00 80")      # CLC; ADC #$8000
    a.emit("8d 22 43")         # STA $4322 (DMA2 src lo16)
    a.emit("a9 01 18 8d 20 43")  # LDA #$1801; STA $4320
    a.emit("a9 00 48 8d 16 21")  # LDA #$4800; STA $2116
    a.emit("a9 00 08 8d 25 43")  # LDA #$0800; STA $4325
    a.emit("e2 20")            # SEP #$20
    a.emit("a9 80 8d 15 21")   # LDA #$80; STA $2115
    a.emit("a9 d5 8d 24 43")   # LDA #$D5; STA $4324
    a.emit("a9 04 8d 0b 42")   # LDA #$04; STA $420B (safe VBlank DMA)
    a.emit("28 6b")            # PLP; RTL

    # Helpers to queue NMI VBlank upload via $10:D8D0 (M=1, X=1, preserves A/X/Y/$0A..$0E).
    for qlabel, cb_label in (
        ("queue_nmi_ja_gfx02a", "nmi_upload_ja_gfx02a"),
        ("queue_nmi_en_gfx02a", "nmi_upload_en_gfx02a"),
    ):
        a.label(qlabel)
        a.emit("48 da")                          # PHA; PHX
        a.emit("a5 0a 48 a5 0b 48 a5 0c 48 a5 0d 48 a5 0e 48")  # save $0A..$0E
        a.emit("22 d0 d8 10")                    # JSL $10D8D0
        a.jsl_local(cb_label)                    # inline 4-byte JSL target consumed by $10:D8D0
        a.emit("68 85 0e 68 85 0d 68 85 0c 68 85 0b 68 85 0a")  # restore $0E..$0A
        a.emit("fa 68 60")                       # PLX; PLA; RTS

    # ------------------------------------------------------------------
    # Hook 1: Overworld Level Names ($03:BB20 -> JML hook_ow_level_name).
    # Entry: M=0, X=0, A = translevel (0..0x5F). Exit: M=0, X=0, DB restored, RTL.
    # ------------------------------------------------------------------
    a.label("hook_ow_level_name")
    a.emit("29 ff 00")         # AND #$00FF
    a.emit("c9 60 00")         # CMP #$0060
    a.branch(0x90, "ow_idx_ok")
    a.emit("a9 00 00")         # LDA #$0000
    a.label("ow_idx_ok")
    a.emit("85 02")            # STA $02 (T)
    a.emit("0a 0a 0a 0a 85 00")  # ASL x4; STA $00 (16*T)
    a.emit("a5 02 0a 18 65 02 18 65 00 85 00")  # $00 = 19*T
    a.emit("e2 30")            # SEP #$30
    lda_long(EFFECTIVE_LANG_ADDR)
    a.branch(0xF0, "ow_en_mode")
    # JA mode: queue ja_gfx02a safely and select ja_ow_names
    a.jsr("queue_nmi_ja_gfx02a")
    a.emit("c2 30")            # REP #$30
    lda_long(d5_hdr + 0x18)    # ja_ow_names_off
    a.branch(0x80, "ow_render")
    a.label("ow_en_mode")
    a.emit("c2 30")            # REP #$30
    lda_long(d5_hdr + 0x1C)    # ow_needs_jp_font_off
    a.emit("18 69 00 80")      # CLC; ADC #$8000
    a.emit("18 65 02 aa")      # CLC; ADC $02; TAX
    a.emit("e2 20")            # SEP #$20 (keep X=0 16-bit for $D50000,X!)
    a.emit("bf 00 00 d5")      # LDA $D50000,X (ow_needs_jp_font[T])
    a.branch(0xF0, "ow_use_en_font")
    a.emit("e2 10")            # SEP #$10 (M=1, X=1 for queue_nmi_ja_gfx02a)
    a.jsr("queue_nmi_ja_gfx02a")
    a.branch(0x80, "ow_load_en_names")
    a.label("ow_use_en_font")
    a.emit("e2 10")            # SEP #$10 (M=1, X=1 for queue_nmi_en_gfx02a)
    a.jsr("queue_nmi_en_gfx02a")
    a.label("ow_load_en_names")
    a.emit("c2 30")            # REP #$30
    lda_long(d5_hdr + 0x1A)    # en_ow_names_off
    a.label("ow_render")
    a.emit("18 69 00 80")      # CLC; ADC #$8000
    a.emit("18 65 00 aa")      # CLC; ADC $00; TAX ($D5 lo16 name ptr)
    a.emit("8b f4 7f 7f ab ab")  # PHB; PEA $7F7F; PLB; PLB
    a.emit("ad 7b 83 a8")      # LDA $837B; TAY
    a.emit("18 69 26 00 85 02")  # CLC; ADC #$0026; STA $02
    a.emit("18 69 04 00 8d 7b 83")  # CLC; ADC #$0004; STA $837B
    a.emit("a9 00 25 99 7f 83")  # LDA #$2500; STA $837F,Y
    a.emit("a9 50 8b 99 7d 83")  # LDA #$8B50; STA $837D,Y
    a.emit("e2 20")            # SEP #$20
    a.label("ow_loop")
    a.emit("bf 00 00 d5")      # LDA $D50000,X
    a.emit("99 81 83")         # STA $8381,Y
    a.emit("a9 39 99 82 83")   # LDA #$39; STA $8382,Y
    a.emit("c8 c8 e8")         # INY; INY; INX
    a.emit("c4 02")            # CPY $02
    a.branch(0x90, "ow_loop")
    a.emit("a9 ff 99 81 83")   # LDA #$FF; STA $8381,Y
    a.emit("c2 20 ab 6b")      # REP #$20; PLB; RTL

    # ------------------------------------------------------------------
    # Hook 2a: Message Box Entry ($03:BB90 -> JML hook_msg_entry).
    # Handles Mazo 0x191 ($1426==2) and 0x192 ($1426==1) before $10:B6A6.
    # ------------------------------------------------------------------
    a.label("hook_msg_entry")
    a.emit("08 c2 20 48")      # PHP; REP #$20; PHA
    a.emit("ad 0b 01 29 ff 01")  # LDA $010B; AND #$01FF
    a.emit("c9 91 01")         # CMP #$0191
    a.branch(0xF0, "msg_chk_191")
    a.emit("c9 92 01")         # CMP #$0192
    a.branch(0xF0, "msg_chk_192")
    a.label("msg_entry_fallback")
    a.emit("c2 20 68 28")      # REP #$20; PLA; PLP
    a.emit("5c a6 b6 10")      # JML $10B6A6

    a.label("msg_chk_191")
    a.emit("e2 20 ad 26 14 c9 02")  # SEP #$20; LDA $1426; CMP #$02
    a.branch(0xD0, "msg_entry_fallback")
    a.emit("c2 20 68 28")      # REP #$20; PLA; PLP
    a.emit("e2 30")            # SEP #$30
    a.jsr("queue_nmi_ja_gfx02a")
    a.emit("c2 30")            # REP #$30
    lda_long(d5_hdr + 0x2E)    # mazo_msg_191_off
    a.emit("18 69 00 80 aa")   # CLC; ADC #$8000; TAX
    a.jmp("shared_msg_stripe_render")

    a.label("msg_chk_192")
    a.emit("e2 20 ad 26 14 c9 01")  # SEP #$20; LDA $1426; CMP #$01
    a.branch(0xD0, "msg_entry_fallback")
    a.emit("c2 20 68 28")      # REP #$20; PLA; PLP
    a.emit("e2 30")            # SEP #$30
    a.jsr("queue_nmi_ja_gfx02a")
    a.emit("c2 30")            # REP #$30
    lda_long(d5_hdr + 0x2C)    # mazo_msg_192_off
    a.emit("18 69 00 80 aa")   # CLC; ADC #$8000; TAX
    a.jmp("shared_msg_stripe_render")

    # ------------------------------------------------------------------
    # Hook 2b: Message Box Render ($03:BBC9 -> JML hook_msg_render).
    # Entry: M=1, X=1, X = level (0..0x47), Y = msg sub-index (0 or 1).
    # ------------------------------------------------------------------
    a.label("hook_msg_render")
    a.emit("c2 30")            # REP #$30
    a.emit("8a 29 ff 00 0a 85 00")  # TXA; AND #$00FF; ASL; STA $00
    a.emit("98 29 ff 00 18 65 00")  # TYA; AND #$00FF; CLC; ADC $00
    a.emit("c9 90 00")         # CMP #$0090 (144)
    a.branch(0x90, "msg_slot_ok")
    a.emit("a9 00 00")
    a.label("msg_slot_ok")
    a.emit("85 00")            # $00 = slot (0..143)
    a.emit("e2 30")            # SEP #$30
    lda_long(EFFECTIVE_LANG_ADDR)
    a.branch(0xF0, "msg_en_mode")

    # JA message path
    a.jsr("queue_nmi_ja_gfx02a")
    a.emit("c2 30")            # REP #$30
    a.emit("a5 00 0a 18 69 00 80")  # LDA $00; ASL; CLC; ADC #$8000
    a.emit("18")
    adc_long(d5_hdr + 0x1E)    # ja_msg_ptrs_off
    a.emit("aa")               # TAX
    a.emit("bf 00 00 d5")      # LDA $D50000,X (rel offset in ja_msg_blob)
    a.emit("18 69 00 80 18")   # CLC; ADC #$8000; CLC
    adc_long(d5_hdr + 0x20)    # ja_msg_blob_off
    a.emit("aa")               # TAX
    a.jmp("shared_msg_stripe_render")

    # EN message path (checks msg_needs_jp_font[slot] | room_font_policy[room])
    a.label("msg_en_mode")
    a.emit("c2 30")            # REP #$30
    lda_long(d5_hdr + 0x2A)    # msg_needs_jp_font_off
    a.emit("18 69 00 80 18 65 00 aa")  # + $8000 + slot -> X
    a.emit("e2 20 bf 00 00 d5")  # SEP #$20; LDA $D50000,X
    a.branch(0xD0, "msg_en_needs_jp")
    a.emit("c2 20")            # REP #$20
    a.emit("af 0b 01 7e 29 ff 01 18 69 00 80 18")  # ($7E010B & 0x1FF) + $8000
    adc_long(d5_hdr + 0x30)    # room_font_policy_off
    a.emit("aa e2 20 bf 00 00 d5")  # TAX; SEP #$20; LDA $D50000,X
    a.branch(0xD0, "msg_en_needs_jp")
    a.emit("e2 30")            # SEP #$30
    a.jsr("queue_nmi_en_gfx02a")
    a.branch(0x80, "msg_en_load_ptr")
    a.label("msg_en_needs_jp")
    a.emit("e2 30")            # SEP #$30
    a.jsr("queue_nmi_ja_gfx02a")
    a.label("msg_en_load_ptr")
    a.emit("c2 30")            # REP #$30
    a.emit("a5 00 0a 18 69 00 80 18")  # 2*slot + $8000
    adc_long(d5_hdr + 0x24)    # en_msg_ptrs_off
    a.emit("aa bf 00 00 d5")   # TAX; LDA $D50000,X (rel offset in en_msg_blob)
    a.emit("18 69 00 80 18")
    adc_long(d5_hdr + 0x26)    # en_msg_blob_off
    a.emit("aa")               # TAX

    # Shared 8x18 Stripe renderer matching $03:BBE6..BC48, reading from $D5:0000,X.
    # Entered with M=0, X=0, X = $D5 lo16 message pointer.
    a.label("shared_msg_stripe_render")
    a.emit("86 00")            # STX $00
    a.emit("8b f4 7f 7f ab ab")  # PHB; PEA $7F7F; PLB; PLB
    a.emit("ad 7b 83 a8")      # LDA $837B; TAY
    a.emit("a2 0e 00")         # LDX #$000E (8 rows)
    a.emit("64 02")            # STZ $02 (clears $02 and $FE flag in $03 ONCE before loop)
    a.label("msg_row_loop")
    a.emit("bf 7f bc 03")      # LDA $03BC7F,X (row Stripe VRAM header)
    a.emit("99 7d 83")         # STA $837D,Y
    a.emit("a9 00 23 99 7f 83")  # LDA #$2300; STA $837F,Y
    a.emit("da")               # PHX
    a.emit("e2 20")            # SEP #$20
    a.emit("a9 12 85 02")      # LDA #$12; STA $02
    a.emit("a6 00")            # LDX $00
    a.emit("a9 1f")            # LDA #$1F
    a.label("msg_col_loop")
    a.emit("24 03")            # BIT $03
    a.branch(0x30, "msg_pad_space")  # BMI pad_space
    a.emit("bf 00 00 d5")      # LDA $D50000,X
    a.emit("e8")               # INX
    a.emit("c9 fe")            # CMP #$FE
    a.branch(0xD0, "msg_write_tile")
    a.emit("85 03")            # STA $03 (set bit 7 end-of-message flag)
    a.label("msg_pad_space")
    a.emit("a9 1f")            # LDA #$1F (reload space tile; previous col left #$39 in A)
    a.label("msg_write_tile")
    a.emit("99 81 83")         # STA $8381,Y
    a.emit("a9 39 99 82 83")   # LDA #$39; STA $8382,Y
    a.emit("c8 c8 c6 02")      # INY; INY; DEC $02
    a.branch(0xD0, "msg_col_loop")
    a.emit("86 00")            # STX $00
    a.emit("c2 20 c8 c8 c8 c8")  # REP #$20; INY x4
    a.emit("fa ca ca")         # PLX; DEX; DEX
    a.branch(0x10, "msg_row_loop")  # BPL msg_row_loop
    a.emit("a9 ff 00 99 7d 83")  # LDA #$00FF; STA $837D,Y
    a.emit("98 8d 7b 83")      # TYA; STA $837B
    a.emit("ab 64 22 64 24")   # PLB; STZ $22; STZ $24
    a.emit("e2 30 a9 01 8d d5 13 6b")  # SEP #$30; LDA #$01; STA $13D5; RTL

    # ------------------------------------------------------------------
    # Hook 3: Message Box Close ($05:B11D -> JSL hook_msg_close; NOP; NOP).
    # Preserves full 16-bit C, X, Y, DB, P.
    # ------------------------------------------------------------------
    a.label("hook_msg_close")
    a.emit("08 e2 20")         # PHP; SEP #$20
    a.emit("9c 26 14 9c 88 1b")  # STZ $1426; STZ $1B88
    a.emit("c2 30 48 da 5a 8b")  # REP #$30; PHA; PHX; PHY; PHB
    a.emit("e2 30")            # SEP #$30
    lda_long(EFFECTIVE_LANG_ADDR)
    a.branch(0xD0, "close_keep_jp")
    a.emit("c2 30")            # REP #$30
    a.emit("af 0b 01 7e 29 ff 01 18 69 00 80 18")
    adc_long(d5_hdr + 0x30)    # room_font_policy_off
    a.emit("aa e2 20 bf 00 00 d5")  # TAX; SEP #$20 (keep 16-bit X!); LDA $D50000,X
    a.branch(0xD0, "close_keep_jp")
    a.emit("e2 10")            # SEP #$10 (M=1, X=1 for queue_nmi_en_gfx02a)
    a.jsr("queue_nmi_en_gfx02a")
    a.label("close_keep_jp")
    a.emit("ab c2 30 7a fa 68 28 6b")  # PLB; REP #$30; PLY; PLX; PLA; PLP; RTL

    # ------------------------------------------------------------------
    # Hook 4 & 5: Room 0x1C5 sprite 00 INIT ($3F:E296) & 0x14D exit ($3F:E44D).
    # Uses NMI/VBlank queue (NO mid-scanline $420B DMA!), preserves full C/X/Y/DB/P.
    # ------------------------------------------------------------------
    a.label("hook_room1c5_init")
    a.emit("08 c2 30 48 da 5a 8b e2 30")  # PHP; REP #$30; PHA; PHX; PHY; PHB; SEP #$30
    a.jsr("queue_nmi_ja_gfx02a")
    a.emit("ab c2 30 7a fa 68 28")        # PLB; REP #$30; PLY; PLX; PLA; PLP
    a.emit("a9 ff 8d bd 18 6b")          # LDA #$FF; STA $18BD; RTL

    a.label("hook_room14d_exit")
    a.emit("08 c2 30 48 da 5a 8b e2 30")  # PHP; REP #$30; PHA; PHX; PHY; PHB; SEP #$30
    lda_long(EFFECTIVE_LANG_ADDR)
    a.branch(0xD0, "room14d_keep_jp")
    a.jsr("queue_nmi_en_gfx02a")
    a.label("room14d_keep_jp")
    a.emit("ab c2 30 7a fa 68 28")        # PLB; REP #$30; PLY; PLX; PLA; PLP
    a.emit("9c bd 18 a9 a0 6b")          # STZ $18BD; LDA #$A0; RTL

    # ------------------------------------------------------------------
    # Hook 6: GFX Decompress ($00:BA28 -> JML hook_gfx_decompress).
    # Intercepts GFX 0x28, 0x2A, 0x2B; falls back to $00:BA2C for all others.
    # Preserves full 16-bit C, X, Y, DB, P and writes $7E:AD00 + $00..$02.
    # ------------------------------------------------------------------
    a.label("hook_gfx_decompress")
    a.emit("8b 5a")            # PHB; PHY (exact entry stack of $00:BA28 before X changes!)
    a.emit("08 c2 20 48 e2 30")  # PHP; REP #$20; PHA; SEP #$30
    a.emit("98")               # TYA (GFX ID)
    a.emit("c9 28")
    a.branch(0xF0, "gfx_028")
    a.emit("c9 2a")
    a.branch(0xF0, "gfx_02a")
    a.emit("c9 2b")
    a.branch(0xF0, "gfx_02b")
    # Fallback to vanilla $00:BA2C with DB=$00 and original C/P intact.
    a.emit("a9 00 48 ab")      # LDA #$00; PHA; PLB (DB = $00)
    a.emit("c2 20 68 28")      # REP #$20; PLA; PLP
    a.emit("5c 2c ba 00")      # JML $00BA2C

    a.label("gfx_028")
    lda_long(EFFECTIVE_LANG_ADDR)
    a.branch(0xF0, "gfx_028_en")
    a.emit("c2 30")
    lda_long(d5_hdr + 0x0C)    # ja_gfx028_off
    a.branch(0x80, "gfx_copy_2kb")
    a.label("gfx_028_en")
    a.emit("c2 30")
    lda_long(d5_hdr + 0x12)    # en_gfx028_off
    a.branch(0x80, "gfx_copy_2kb")

    a.label("gfx_02b")
    lda_long(EFFECTIVE_LANG_ADDR)
    a.branch(0xF0, "gfx_02b_en")
    a.emit("c2 30")
    lda_long(d5_hdr + 0x10)    # ja_gfx02b_off
    a.branch(0x80, "gfx_copy_2kb")
    a.label("gfx_02b_en")
    a.emit("c2 30")
    lda_long(d5_hdr + 0x16)    # en_gfx02b_off
    a.branch(0x80, "gfx_copy_2kb")

    a.label("gfx_02a")
    lda_long(EFFECTIVE_LANG_ADDR)
    a.branch(0xD0, "gfx_02a_ja")
    # EN mode: consult room_font_policy only during level modes ($0100 >= $0F).
    a.emit("ad 00 01 c9 0f")   # LDA $0100; CMP #$0F
    a.branch(0x90, "gfx_02a_en")
    a.emit("c2 30")
    a.emit("ad 0b 01 29 ff 01 18 69 00 80 18")
    adc_long(d5_hdr + 0x30)    # room_font_policy_off
    a.emit("aa e2 20 bf 00 00 d5")  # TAX; SEP #$20; LDA $D50000,X
    a.branch(0xD0, "gfx_02a_ja")
    a.label("gfx_02a_en")
    a.emit("c2 30")
    lda_long(d5_hdr + 0x14)    # en_gfx02a_off
    a.branch(0x80, "gfx_copy_2kb")
    a.label("gfx_02a_ja")
    a.emit("c2 30")
    lda_long(d5_hdr + 0x0E)    # ja_gfx02a_off

    a.label("gfx_copy_2kb")
    # Entered with M=0, X=0, A = BMLG offset of 2048 B stream in $D5.
    a.emit("18 69 00 80 aa")   # CLC; ADC #$8000; TAX ($D5 lo16 ptr)
    a.emit("a9 00 ad 85 00")   # LDA #$AD00; STA $00
    a.emit("e2 20 a9 7e 85 02 c2 20")  # SEP #$20; LDA #$7E; STA $02; REP #$20
    a.emit("a0 00 00")         # LDY #$0000
    a.label("gfx_copy_loop")
    a.emit("bf 00 00 d5")      # LDA $D50000,X
    a.emit("97 00")            # STA [$00],Y
    a.emit("e8 e8 c8 c8")      # INX; INX; INY; INY
    a.emit("c0 00 08")         # CPY #$0800
    a.branch(0x90, "gfx_copy_loop")
    a.emit("c2 20 68 28 7a ab 6b")  # REP #$20; PLA; PLP; PLY; PLB; RTL

    # ------------------------------------------------------------------
    # Hook 7: Title Screen Stripe Image ($00:85D4 -> JSL hook_title_stripe; BRA $00:85E3).
    # Entry: M=1, X=1, Y = $12. Preserves X, Y, DB, P.
    # ------------------------------------------------------------------
    a.label("hook_title_stripe")
    a.emit("08")               # PHP
    a.emit("c0 03")            # CPY #$03 (Title screen stripe entry)
    a.branch(0xD0, "stripe_default")
    lda_long(EFFECTIVE_LANG_ADDR)
    a.branch(0xF0, "stripe_default")
    a.emit("c2 20")            # REP #$20
    lda_long(d5_hdr + 0x34)    # ja_title_stripe_off
    a.emit("18 69 00 80 85 00")  # CLC; ADC #$8000; STA $00
    a.emit("e2 20 a9 d5 85 02")  # SEP #$20; LDA #$D5; STA $02
    a.emit("28 6b")            # PLP; RTL

    a.label("stripe_default")
    a.emit("da bb")            # PHX; TYX
    a.emit("bf d0 84 00 85 00")  # LDA $0084D0,X; STA $00
    a.emit("bf d1 84 00 85 01")  # LDA $0084D1,X; STA $01
    a.emit("bf d2 84 00 85 02")  # LDA $0084D2,X; STA $02
    a.emit("fa 28 6b")         # PLX; PLP; RTL

    code = a.resolve()
    assert len(code) <= CONTROL_BLOCK_OFFSET, (
        f"code pack ({len(code)} B) overlaps control block at 0x{CONTROL_BLOCK_OFFSET:04X}"
    )

    pack = bytearray(CODE_PACK_SIZE)
    pack[: len(code)] = code
    # Explicitly verify $90:8FF0..8FFF is zero-initialized on disk.
    assert pack[CONTROL_BLOCK_OFFSET : CONTROL_BLOCK_OFFSET + CONTROL_BLOCK_SIZE] == b"\x00" * CONTROL_BLOCK_SIZE

    entrypoints = {
        name: addr
        for name, addr in a.labels.items()
        if name.startswith("hook_") or name.startswith("nmi_")
    }
    return bytes(pack), entrypoints


def build_data_pack() -> bytes:
    """Build deterministic BMLG v1 pack for $D5:8000 from pinned localization audit."""
    audit = json.loads(AUDIT_JSON.read_text())
    pack = audit_localization.build_bmlg_pack(audit, local_dir=ROOT / "local")
    assert len(pack) == EXPECTED_BMLG_SIZE <= 32768, len(pack)
    assert sha(pack) == EXPECTED_BMLG_SHA, sha(pack)
    return pack


def _addr24_hex(addr: int) -> str:
    return bytes((addr & 0xFF, (addr >> 8) & 0xFF, (addr >> 16) & 0xFF)).hex()


def build_patches(entrypoints: dict[str, int]) -> list[dict]:
    """Return exact bounded ROM patches against demo11-native-product-r46."""
    return [
        {
            "offset": lorom(0x0085D4),
            "before": "b9d0848500b9d1848501b9d2848502",
            "after": "22" + _addr24_hex(entrypoints["hook_title_stripe"]) + "8009" + ("ea" * 9),
            "role": "Hook Title/Stripe pointer load ($00:85D4) -> JSL hook_title_stripe; BRA $00:85E3.",
        },
        {
            "offset": lorom(0x00BA28),
            "before": "8b5a4bab",
            "after": "5c" + _addr24_hex(entrypoints["hook_gfx_decompress"]),
            "role": "Hook GFX <$80 loader ($00:BA28) -> JML hook_gfx_decompress for 0x28/0x2A/0x2B EN/JA + room policy.",
        },
        {
            "offset": lorom(0x03BB20),
            "before": "85020a0a",
            "after": "5c" + _addr24_hex(entrypoints["hook_ow_level_name"]),
            "role": "Hook Overworld level name builder ($03:BB20) -> JML hook_ow_level_name.",
        },
        {
            "offset": lorom(0x03BB90),
            "before": "5ca6b610",
            "after": "5c" + _addr24_hex(entrypoints["hook_msg_entry"]),
            "role": "Hook Message Box entry ($03:BB90) -> JML hook_msg_entry (Mazo 0x191/0x192 + $10:B6A6).",
        },
        {
            "offset": lorom(0x03BBC9),
            "before": "c2308a0a",
            "after": "5c" + _addr24_hex(entrypoints["hook_msg_render"]),
            "role": "Hook Message Box renderer ($03:BBC9) -> JML hook_msg_render (EN/JA + auto-JP fallback).",
        },
        {
            "offset": lorom(0x05B11D),
            "before": "9c26149c881b",
            "after": "22" + _addr24_hex(entrypoints["hook_msg_close"]) + "eaea",
            "role": "Hook Message Box close ($05:B11D) -> JSL hook_msg_close; NOP; NOP to restore room font.",
        },
        {
            "offset": lorom(0x3FE296),
            "before": "2200b089ea",
            "after": "22" + _addr24_hex(entrypoints["hook_room1c5_init"]) + "ea",
            "role": "Repoint 0x1C5 sprite 0x00 INIT ($3F:E296) -> safe NMI VBlank ja_gfx02a hook in $90.",
        },
        {
            "offset": lorom(0x3FE44D),
            "before": "2240b089ea",
            "after": "22" + _addr24_hex(entrypoints["hook_room14d_exit"]) + "ea",
            "role": "Repoint 0x14D Overworld exit ($3F:E44D) -> EN-only NMI VBlank en_gfx02a restore in $90.",
        },
    ]


def write_symbols_toml(entrypoints: dict[str, int]) -> None:
    """Keep recomp/targets/demo11-native-product-r47/symbols.toml in sync with forged $90 entrypoints."""
    sym_path = ROOT / "recomp/targets" / TARGET / "symbols.toml"
    sym_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Symbol map for Brutal Mario Demo11 Product R47.",
        "#",
        "# All forged $90 (BM_LANG_R47_CODE_PACK) entrypoints MUST stay LLE (emit = false)",
        "# so AOT never reads ROM bank $10 as a LoROM mirror of bank $90.",
        "",
        '[[func]]',
        'name = "I_RESET"',
        'addr = "8000"',
        "bank = 0",
        "emit = false",
        'note = "Emulation RESET vector ($FFFC)"',
        "",
        '[[func]]',
        'name = "I_NMI"',
        'addr = "816a"',
        "bank = 0",
        "emit = false",
        'note = "Native NMI vector ($FFEA)"',
    ]
    for name, addr in entrypoints.items():
        lines.extend([
            "",
            "[[func]]",
            f'name = "r47_{name}"',
            f'addr = "{addr & 0xFFFF:04x}"',
            f"bank = {addr >> 16}",
            "emit = false",
            'note = "BM_LANG_R47_CODE_PACK forged bank $90"',
        ])
    sym_path.write_text("\n".join(lines) + "\n")


def prepare() -> None:
    parent_cfg_path = ROOT / "config/restorations" / f"{PARENT}.json"
    parent_cfg = json.loads(parent_cfg_path.read_text())
    r46_rom_path = ROOT / "local/restoration" / PARENT / "rom.sfc"
    r46_rom = r46_rom_path.read_bytes()
    assert len(r46_rom) == 4194304, len(r46_rom)
    assert sha(r46_rom) == R46_SHA, f"r46 ROM SHA-256 mismatch: {sha(r46_rom)}"
    assert parent_cfg["output"]["sha256"] == R46_SHA

    # Verify banks $D5 and $90 are unoccupied in parent packs.
    occupied_banks = {int(p["address"], 16) >> 16 for p in native_sprite_gap.packs(PARENT)}
    assert (DATA_PACK_ADDRESS >> 16) not in occupied_banks, "native bank D5 already occupied"
    assert (CODE_PACK_ADDRESS >> 16) not in occupied_banks, "native bank 90 already occupied"

    data_bytes = build_data_pack()
    code_bytes, entrypoints = build_code_pack_and_entrypoints()
    data_sha = sha(data_bytes)
    code_sha = sha(code_bytes)

    pack_dir = ROOT / PACK_SOURCE
    pack_dir.mkdir(parents=True, exist_ok=True)
    for fname, blob in ((DATA_PACK_FILE, data_bytes), (CODE_PACK_FILE, code_bytes)):
        fpath = pack_dir / fname
        write_verified(fpath, blob)

    patches = build_patches(entrypoints)
    patched_rom = bytearray(r46_rom)
    for patch in patches:
        off = patch["offset"]
        before = bytes.fromhex(patch["before"])
        after = bytes.fromhex(patch["after"])
        assert len(before) == len(after)
        assert patched_rom[off : off + len(before)] == before, (
            hex(off),
            patched_rom[off : off + len(before)].hex(),
            patch["before"],
        )
        patched_rom[off : off + len(after)] = after
    r47_sha = sha(bytes(patched_rom))

    cfg = json.loads(json.dumps(parent_cfg))
    cfg["id"] = TARGET
    cfg["target"] = "Brutal Mario Demo11 Product R47"
    cfg["base_restoration"] = PARENT
    cfg["base_output"] = {"size": 4194304, "sha256": R46_SHA}
    cfg["parent_restoration"] = PARENT
    cfg["scope"] = (
        "Add bilingual EN/JA localization switching (--lang en|ja|auto, Language=auto config, "
        "Esc/O Settings overlay, ~ lang console): mount BMLG v1 pack in bank D5 ($D5:8000, "
        "BM_LANG_R47_DATA_PACK, 30814B) and 65816 adapters + Host->Guest control block ($90:8FF0..8FFF) "
        "in system-mirror bank 90 ($90:8000, BM_LANG_R47_CODE_PACK, 4096B); localize Title stripe, "
        "GFX 0x28/0x2A/0x2B, Overworld level names, SMW + Mazo 0x191/0x192 message boxes with auto-JP "
        "fallback, and NMI VBlank-queued ($10:D8D0) font sync across 0x0FF/0x14D/0x17B/0x1C5."
    )
    cfg["native_sprite_gap"]["frozen_manifests"] = list(
        cfg["native_sprite_gap"]["manifests"]
    )
    cfg["native_sprite_gap"]["extra_packs"].extend(
        [
            {
                "variable": DATA_PACK_VAR,
                "pack_file": DATA_PACK_FILE,
                "address": f"{DATA_PACK_ADDRESS:06X}",
                "size": len(data_bytes),
                "sha256": data_sha,
                "executable": False,
                "source": PACK_SOURCE,
            },
            {
                "variable": CODE_PACK_VAR,
                "pack_file": CODE_PACK_FILE,
                "address": f"{CODE_PACK_ADDRESS:06X}",
                "size": len(code_bytes),
                "sha256": code_sha,
                "executable": True,
                "source": PACK_SOURCE,
            },
        ]
    )
    cfg["native_sprite_gap"]["extra_patches"] = patches
    cfg["code_patches"] = [
        {
            "address": f"{p['offset']:06X}",
            "before": p["before"],
            "after": p["after"],
            "role": p["role"],
        }
        for p in patches
    ]
    cfg["output"] = {"size": 4194304, "sha256": r47_sha}

    cfg_path = ROOT / "config/restorations" / f"{TARGET}.json"
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")

    write_symbols_toml(entrypoints)
    native_sprite_gap.prepare(TARGET)

    r46_music = ROOT / "local/restoration" / PARENT / "music-pack.bin"
    music_bytes = r46_music.read_bytes()
    assert sha(music_bytes) == MUSIC_PACK_SHA, sha(music_bytes)
    r47_music = ROOT / "local/restoration" / TARGET / "music-pack.bin"
    write_verified(r47_music, music_bytes)

    collected = build_smw_delta.collect_target_packs(TARGET)
    assert len(collected) == 71, f"expected 71 packs, got {len(collected)}"
    print(
        f"Prepared {TARGET}: rom_sha256={r47_sha}, "
        f"data_pack=({len(data_bytes)}B, {data_sha}), "
        f"code_pack=({len(code_bytes)}B, {code_sha}), packs={len(collected)}"
    )


if __name__ == "__main__":
    prepare()

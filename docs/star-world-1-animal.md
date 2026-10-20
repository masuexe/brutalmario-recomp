# Star World 1: LOVE ANIMAL comparison

Date: 2026-10-19. The user reports that returning after the LOVE ANIMAL sign
lacks the expected Koopa-corpse / no-respawn mechanism, and suspects that the
original demoOnly1 also has this problem. The comparison below separates
static corpse artwork from an enemy's actual death record. No ROM or runtime
behavior was changed during this investigation.

Disposition: the user reproduced the explained behavior and considers this
report resolved. Preserve the shared original gameplay rule; no no-respawn
patch is requested. This closes this report, not every course acceptance item.

## Result

The user clarified that a **living Koopa reappears**, rather than merely
missing corpse artwork, and selected fireballs / other killing methods.
The fireball path reproduces the reported resurrection in both cheap_demo
and the restored candidate, including the native build. No pipe visit is
needed. It is shared existing behavior, not introduced by the three-graphics
restoration or native recompilation.

A fireball converts opening sprite-list entry `$02`, sprite ID `$01`, into
an enemy-derived coin, sprite ID `$21` / status `$08`. The coin retains list
index `$02`. If it is left uncollected and unloads offscreen, `$1938+$02`
is cleared. Returning reloads the original living Koopa from that entry.
All three runs preserve Mario's lives, remain in room `$005`, and reproduce
this sequence with the sign flag `$14AF=1` on return. A reference control
that collects the fireball coin instead increases the coin counter, retains
the load record and does not respawn that Koopa.

The ordinary offscreen-removal path `$01:AC8E..ACA4` is byte-identical in
both versions. A sprite with status at least `$08` and a valid list index
has its load record cleared before its live slot is removed. The enemy-derived
coin satisfies those conditions. The observed coin/load-record sequence
agrees with that path; an instruction trace at the store was not collected.

This is distinct from the stomp case: an actual stomp puts the shell-less
Koopa into status `$03`, then removes its live slot while retaining its
load record. It does not respawn in either version. In the donor's no-stomp
control the living Koopa unloads and correctly respawns, confirming that the
return route exercises the loader.

The isolated native candidate also displays the same **fixed corpse
decorations** as cheap_demo with its legacy VRAM-access compatibility option
enabled. Two corpse-image crops match on the project's common RGB5 grid.
Those decorations appear even in a cheap_demo control that never kills the
opening Koopa; the control's two raw crops are identical to the killed case.
They are not dynamically placed at each enemy's death position, and the
sign script does not suppress enemy respawning.

No gameplay behavior was changed. Copying donor code cannot supply a missing
no-respawn rule here: the donor has the same fireball behavior. Making fireball
kills permanently remove the enemy even if its coin is abandoned would be a
separate gameplay-policy change, best scoped to this restored course rather
than changing the shared global coin/respawn handler. Other enemies, shell
kills, pipe/re-entry paths and unassisted full-course coverage remain open.

## Identical script and graphics

The relevant code is byte-identical in demoOnly1 and cheap_demo:

- `$27:D680..D718`: check `$14AF`; if it is zero and Mario's X high byte
  `$95` equals `$0E`, set `$14AF=1` and make six graphics transfers.
- `$27:DD40..DD70`: perform the VRAM DMA transfers.

The six source slices are identical in both versions and are supplied by
ExGFX `$100`, which was already present in demoOnly1. They are not one of
the three resources transplanted by the restoration. The trigger changes
VRAM artwork; it does not iterate through killed enemies or place a new
corpse at each death position. The examined Map16 layout buffers do not
change between the pre-trigger and post-trigger samples.

| VRAM word address | WRAM source | Bytes |
| --- | --- | ---: |
| `$0E00` | `$7E:B100` | `$80` |
| `$0F00` | `$7E:B300` | `$80` |
| `$0C00` | `$7E:B180` | `$80` |
| `$0D00` | `$7E:B380` | `$80` |
| `$0A00` | `$7E:B500` | `$100` |
| `$0B00` | `$7E:B700` | `$100` |

## Reference compatibility difference

Default pinned Snes9x rejects these writes during active display. In both
the recipient candidate and cheap_demo, `$14AF` changes to `$01`, but all
six target slices remain unchanged and disagree with their expected source
bytes. Since the script is one-shot, it does not retry the rejected upload.

Using `snes9x_block_invalid_vram_access=disabled` makes all six uploads
match their source slices exactly and reveals the corpse artwork. The native
candidate already accepts these transfers: all six slices also match exactly.
The visible native artwork therefore agrees with the donor under this
compatibility setting. Default Snes9x's missing visual change is not evidence
that the donor or restored ROM lacks the graphics. ZSNES 1.51 was not run in
this investigation; no exact historical-emulator equivalence is claimed.

## Reproduction and boundaries

The stomp diagnostic uses player coordinate shortcuts for one real stomp
and for reaching the existing sign trigger. The fireball diagnostic instead
grants Fire Mario and uses actual guest fireballs, leaving the resulting
coin uncollected. It holds Mario above terrain
and disables vertical scrolling during the return. Horizontal scrolling,
enemy loading and the sign script execute normally. Enemy status, load/death
records, `$14AF`, graphics and level progress are never poked. Lives remain
unchanged, with room `$005` active throughout the examined return.

```sh
python3 tools/m1.py native --target star-world-1 \
  --script recomp/inputs/star-world-1-animal.script --capture animal-native-new
SNESREF_CORE_OPTIONS=snes9x_block_invalid_vram_access=disabled \
  python3 tools/m1.py reference --target star-world-1 \
  --script recomp/inputs/star-world-1-animal.script --capture animal-reference-new
python3 tools/m1.py native --target star-world-1 \
  --script recomp/inputs/star-world-1-animal-fire.script --capture animal-fire-new
```

To derive the cheap_demo probe from that script:

1. Clear its intro flag with `poke 0109 00` before the initial map transfer.
2. After `dump map`, use `poke d7e2 05` before pressing Y, selecting the
   corresponding room `$005` without changing its contents.
3. Change the stomp coordinate from `94010001` to `80010001`: the donor's
   Koopa has walked to a slightly different X at this checkpoint. This
   adjustment is for the stomp probe only; the fireball probe uses identical
   firing coordinates in both versions.
4. Run `tools/probe_reference.py` with the prepared cheap_demo ROM and
   manifest, setting the same VRAM-access option. The receipt records this
   option. For the no-stomp control, replace the coordinate/stomp section
   after `dump koopa_before` with `wait 90`.

Local evidence:

- `star1-love-fire-uncollected-{reference,cheap,native}`: real fireball
  conversion, uncollected coin unload, cleared original load record and
  living-Koopa reload in all three hosts/versions.
- `star1-love-fire-candidate`: reference coin-collection control, retaining
  the record and preventing reload. The donor run of the earlier fire
  probe leaves its coin uncollected, illustrating the need to check pickup.
- `star1-love-stomp-v5-{candidate,cheap,native}`: real death, trigger,
  return and persistent load record; reference captures use default options.
- `star1-love-return-{candidate-vram-allowed,cheap-vram-allowed,native}`:
  exact six-slice uploads and visible fixed corpse decorations on return.
- `star1-love-final-{native,cheap-vram-allowed}`: repeat from the tracked
  script / documented donor adaptation; all return checkpoints remain alive.
- `star1-love-no-stomp-cheap-vram-allowed`: fixed corpse artwork without
  killing the Koopa; the living Koopa respawns as the reload control.
- `local/reports/star1-love-animal-comparison.json`: bounded assertions and
  source identities, including both stomp and fireball cases. Raw pictures,
  scripts and ROMs remain untracked.

Earlier survey attempts that entered death, missed the stomp, stopped short
of screen `$0E` or used stale camera tiles are exploratory and excluded from
these conclusions. Full framebuffer or full WRAM equality is not claimed:
HUD timing and other state differ between the hosts/versions.

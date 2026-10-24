# Lower-inner course and cap music

The lower-inner star course now selects existing demoOnly1 song `$60`. All
three caps select existing song `$79`; when the last active cap expires,
the controller resumes `$60`. No song data or music driver is transplanted.
The user confirmed on 2026-10-21 that the corrected music is completely normal.
The scoped music correction is accepted.

This report describes the demoOnly1 line. The later Demo 1-1 regression and
its corrected launch target are documented in [the Demo 1-1 follow-up](demo11-lower-inner-music.md).

## Why the earlier selections were wrong

In an unmodified cheap_demo room `$117` capture, the donor uploads a four-song
bank from `$3F:8008`, physical offset `$1F8008`. Its 6,136-byte image has
SHA-256 `da36affbc31a2ddcdd647334f4413509d79bba3f801e22730997b741704d840f`.
The sequences start at ARAM `$6800,$6808,$6810,$6818`.

The cap controller's `$21/$22` requests select the first/second sequences in
that already uploaded bank. They are not global custom-song file numbers.
A diagnostic `$22` request on this bank gives active SPC id `$22` and
sequence cursor `$680A`, selecting the second sequence. Forcing a global
`$22` during level loading instead selects a different bank and song.

The ordinary Mario star cue `$0D` is also a different tune. Neither matching
background graphics nor copying an invincibility request identifies the cap
music. `$0DDA` retains the background selection during temporary cap music;
its value alone cannot establish which cap tune is playing.

## Existing songs

`tools/audit_lower_inner_music.py` verifies both source ROMs against
`config/content-versions.json` and compares their reachable musical graphs.
It follows both intro/loop patterns, all eight channels and nested `$E9`
calls, retaining notes, duration/gate bytes, instruments, command arguments
and repeat counts. Relocated addresses and unreachable padding are omitted.
Unsupported commands are rejected; this is not a general music-id mapper.

| Cue | Donor sequence | Recipient id | Result |
| --- | --- | --- | --- |
| Course | `$6800` | `$60` | Corresponding revised arrangement; 12 of 16 intro/loop channel graphs match exactly |
| All three caps | `$6808` | `$79` | All 16 graphs match exactly |

The identical cap graph SHA-256 is
`d85b8df748dfe8c8c9eaead2cad761c83d7771db12fad1d456d2ccd6ce9b3caf`.
The course comparison differs in channels 0 and 3; `$60` is not claimed to
be byte-identical cheap_demo audio. The existing recipient arrangement is
used rather than importing a second copy of the composition.

Reproduce the structural check:

```sh
python3 tools/audit_lower_inner_music.py
```

The private report is `local/reports/lower-inner-music-identity.json`.

## Changes and runtime checks

Only seven selection bytes change relative to checkpoint `db1e865`:

- Header `$3A:B524`: `$1F` to `$61` (encoded song `$60 + 1`).
- Pickup immediates `$34:8085,$34:80C6,$34:8104`: `$0D` to `$79`.
- Expiry immediates `$34:83A5,$34:8429,$34:8469`: `$61` to `$60`.

The previous expiry immediates were still `$61`, despite the previous report
describing `$1E`; all three sites now explicitly resume the selected course song.
Both launch targets include the fix:

| Target | ROM SHA-256 |
| --- | --- |
| `star-world-lower-inner` | `359b4c3fb1b4c33d4ba73cc4f9e09db642e5864517aa5e9658a87e41e252cbb5` |
| `star-world-center` | `da880e47ec0aa81f06af8596e5b4c813bd3a934631041ffb9feba6a272a590b9` |

`recomp/inputs/star-world-lower-inner-music.script` tests each cap separately.
It uses an overworld shortcut, initializes a test cap in free sprite slot 0,
and positions Mario for real pickup collision. The subtype fixture is set
after initialization; the existing controller decrements each effect without
timer, music-queue, completion or SRAM writes. This tests the pickup/expiry
audio path, not a natural route to each cap block. All three effects become
active, expire naturally, queue `$79` then `$60`, and retain four
lives-minus-one on native and reference hosts.

A diagnostic reference-core ARAM dump during the cap effect matches all
416 uploaded bytes of recipient song `$79`, including header
`80 55 90 55 FF 00 02 54`. This verifies actual uploaded music, beyond queue
or background-id observations. After expiry, all 1,196 uploaded bytes match
existing song `$60`; the native capture's final ARAM dump also matches that
course payload. This does not substitute for human listening.

The existing assisted 100-coin route is also rerun through save and reset.
Current capture receipts and assertions are recorded in
`local/reports/lower-inner-music-qualification.json`. Older broader acceptance
and regression counts remain historical; they are not represented as new
checks on these identities.

The native audio capture retains all 3,286,108 produced PCM frames with no
history drops. Native/reference PCM durations differ by 0.625 ms. Envelope
comparison is diagnostic only; it is not waveform equivalence or a physical
device-output check. Unprocessed listening excerpts and a provenance receipt
are under `local/reports/lower-inner-music-listening/`.

## Accepted listening check

After the correction in `ab2df63`, the user reported that the music is completely
normal. This closes the requested course/cap/expiry music listening check.
Individual cap variants were not itemized in that report; all three variants
have the separate automated pickup/expiry evidence above.

Restart the launcher so an older process cannot retain the previous ROM:

```sh
python3 tools/play_demo_only1.py --restoration star-world-center --level star-world-lower-inner --show-location
```

Check the course theme, the Mario 64 cap cue after pickup, and return to the
course theme when the cap expires. The separate lower-inner target is also
rebuilt and can be launched with `--restoration star-world-lower-inner`.

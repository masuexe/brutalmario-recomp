# Deferred listening checks

The user initially reported a silent environment after accepting Snow Star's
normal and key exits on 2026-10-20. They have now reported that sound is
available again and the Sky Star playtest audio is normal. That closes the
current Sky Star listening item; it does not itemize every earlier track.
Continue gameplay/visual work and automatic audio checks without a mandatory
listening gate at every checkpoint.
Generated PCM, correct song data and non-silence are automated evidence, not
human hearing acceptance. Completed checkpoints may still be committed/pushed
under the existing authorization with this boundary recorded.

| Target / item | Automated evidence | Human listening status |
| --- | --- | --- |
| Snow Star (`star-world-lower-right`), restored BGM `$54` and ordinary effects | Loaded adapted song bytes match exactly; native/reference late music captures are non-silent; normal/key exits accepted by the user. | Not separately itemized in the gameplay report; include in the later combined listening session. |
| Upper-right course (`star-world-upper-right`), restored BGM `$5D` and ordinary effects | Loaded 940-byte song matches exactly after 1,200 active frames; native/reference late PCM is non-silent. Stage accepted after user entry/SMB3 brick checks and automated pipe/goal/DK/reset/death checks; full manual traversal waived. | Deferred until the user reports sound is available; no listening acceptance implied. |
| Sky Star (`star-world-middle-right`), restored BGM `$2E` and ordinary effects | Normal rocket/door/goal/save and timer-death/re-entry qualify on the matching native/reference builds. | User reports sound is available again and audio is normal in the Sky Star playtest. Stage listening accepted; individual effects were not enumerated. |
| Center cumulative candidate (`star-world-center`, ROM `e0fb3837…`), restored BGM across the eight hub courses and ordinary effects | Each restored track was byte-matched when its own course was accepted; the cumulative ROM pins `e0fb3837…` and its 16 bounded host checks plus 239 exact samples pass. | User reports the listening experience is fine when running `tools/play_demo_only1.py --restoration star-world-center` (2026-10-21). General listening acceptance for this build; individual tracks and effects were not enumerated. |

The center cumulative candidate is now the most recent build the user has
actually heard. That acceptance covers the build as a whole and does not
itemize earlier tracks or retroactively close the Snow Star and upper-right
rows, which were never separately sampled.

The upper-right SDL diagnostic reports output underruns in concurrent and
isolated runs, as does the earlier Snow Star diagnostic. The two new native
PCM captures are identical. Device continuity remains outside automated song
acceptance; include actual output in the later listening check before drawing
conclusions about audible behavior or a new content regression.

Use the target's isolated launcher for a later combined check if an essential
audible question arises, or if the user elects to sample the earlier tracks.
Do not request another listening check solely because it is in this history.
Record which items they actually heard and their result;
do not expand a general gameplay pass into an audio pass. New restored tracks
or sound discrepancies discovered during the silent window belong in this table.

The earlier subjective star-power music tempo concern remains deferred as
recorded in [the timing investigation](star-audio.md); the supplied A/B clips
sounded identical to the user. It is not reopened by silent testing.

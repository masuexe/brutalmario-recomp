# Deferred listening checks

The user reported a silent environment after accepting Snow Star's normal
and key exits on 2026-10-20. They will tell us when sound becomes available
again. Until then, continue gameplay/visual work and automatic audio checks;
do not request audible confirmation or block those milestones on listening.
Generated PCM, correct song data and non-silence are automated evidence, not
human hearing acceptance. Completed checkpoints may still be committed/pushed
under the existing authorization with this boundary recorded.

| Target / item | Automated evidence | Human listening status |
| --- | --- | --- |
| Snow Star (`star-world-lower-right`), restored BGM `$54` and ordinary effects | Loaded adapted song bytes match exactly; native/reference late music captures are non-silent; normal/key exits accepted by the user. | Not separately itemized in the gameplay report; include in the later combined listening session. |
| Upper-right course (`star-world-upper-right`), restored BGM `$5D` and ordinary effects | Loaded 940-byte song matches exactly after 1,200 active frames; native/reference late PCM is non-silent. Stage accepted after user entry/SMB3 brick checks and automated pipe/goal/DK/reset/death checks; full manual traversal waived. | Deferred until the user reports sound is available; no listening acceptance implied. |

The upper-right SDL diagnostic reports output underruns in concurrent and
isolated runs, as does the earlier Snow Star diagnostic. The two new native
PCM captures are identical. Device continuity remains outside automated song
acceptance; include actual output in the later listening check before drawing
conclusions about audible behavior or a new content regression.

Use the target's isolated launcher for a short sample when the user reports
sound is available. Record which items they actually heard and their result;
do not expand a general gameplay pass into an audio pass. New restored tracks
or sound discrepancies discovered during the silent window belong in this table.

The earlier subjective star-power music tempo concern remains deferred as
recorded in [the timing investigation](star-audio.md); the supplied A/B clips
sounded identical to the user. It is not reopened by silent testing.

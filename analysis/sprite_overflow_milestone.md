# SMS sprite-overflow projectile suppression - v0032

ROM: `../versions/v0032-ea5b8434/gaw-megadrive-v0032.bin`.

Source 495E checks C01B bit 6 before entering allocator 4965. The direct 4965
entry deliberately bypasses this condition. The native allocator previously
allowed all requests while a transient slot was available.

The native world renderer now computes an SMS overflow prediction from its
prepared 8x8 sprite list: entries count by Y on active lines 0..191, including
sprites clipped horizontally; more than eight on any line sets overflow.
It respects the SMS D0 end marker and wrapped/offscreen Y coordinates. This
does not use the different Mega Drive hardware sprite limits.

Two status stages advance in the existing VInt callback, without additional
VDP writes. Source measurements show prepared SAT overflow at frame 3135,
hardware SAT overflow at 3136 and IRQ status overflow at 3137, identically in
PAL and NTSC. The native stages reproduce that sequence and its clearing delay.
Foreground rendering only replaces the prepared prediction.

Guarded allocation is used at the translated equivalents of source calls
85C1, 8872, 903F, 9078, 90B2, 949B and 96B9. Direct calls, including enemies
38/39, 41 and 42, retain direct allocation. Unported behavior around source
98F1 (types 44 and later) remains outside this implementation.

validate_sprite_overflow.py compares source and native prepared/IRQ flags over
129 frames per region. Eleven actor fixtures exercise no objects, eight versus
ten overlapping sprite entries, horizontally clipped sprites and several
vertical boundary positions. All 258 frame comparisons match. Source status
and VRAM are never injected: only test actor RAM is installed.

validate_overflow_allocation.py lets real overlapping sprites establish status
before triggering attacks. Types 20, 2A and 40 are suppressed under overflow;
38 and 42 still allocate. All sixteen actor records match for ten cases per
region, excluding renderer collision-list descriptor bytes 27/28, for 320 record
comparisons. An earlier explicit-status injection experiment was discarded
because the source IRQ overwrites C01B; the retained test uses real overflow.

Guard-free walker40/pursuit decisions pass in PAL/NTSC; burst walkers/projectiles
pass in NTSC. Movement, four-direction scroll-object checks, title cadence and
the natural 65-line intro pass in both regions. sprite_overflow_patch_audit.json
binds sixteen reports to the exact cartridge and checks aliases/checksum.

This is status-dependent allocation fidelity, not SMS sprite flicker/clipping
or priority emulation. Every possible sprite layout and loading/IRQ boundary
has not been verified. The earlier intro timing/SAT limitations, unported
actors and conditional story/dungeons, full progression and ending remain.

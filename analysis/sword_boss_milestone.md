# Type6C and shared projectiles: v0116

ROM `versions/v0116-e7069055/gaw-megadrive-v0116.bin`,1 MiB,
SHA-256 `e7069055e4dca251b0905e83e9d212e55e991321058edb640ebab5c61f851b15`,
checksum754E. Type6C in room01AC; source stats5A1E0640 (HP90, attack30,
defense6, flags40). v0115 is an intermediate build with the old rendering cap.

## Native translation

54D9 ten-state table translated, including shared recovery14 and satellite
states16/18. Initial(128,72),64-tick flash/wait, four walking poses every16
ticks, slow eight-way pursuit with577F asymmetric bounds.55D0 literal movement
is quarter-pixel per tick,32 ticks per eight-pixel segment. On a selected attack,
the boss stops, waits32 ticks, animates22 ticks, spawns75, repeats, and returns
to its64-tick wait after the second shot. Normal6C choices do not reach16/18;
those shared dispatch entries are nevertheless translated and directly tested.

Native projectile75 (4518) initializes aimed vectors468E, accelerates toward
the hero, limits velocity by the source signed high byte, bounces at asymmetric
room bounds and returns toward its parent after contact or lifetime threshold.
Returning axes adjust near the parent and clear when both qualify. The common
tail deliberately runs even after clearing inside the state routine, retaining
the source's inactive-record residual bytes. Lifetime/timer writes and byte
coordinate comparisons preserve the original behavior.

Native satellite76 (46B4) uses literal4745..47F6 relative path tables, animation
completion to advance path, parent-relative positioning and bounds/sentinel
removal. State16 allocates four satellites, retaining last-successful-IY writes
on partial allocation failure; state18 waits until transient pool is empty.
Already-full pools with inherited RAM IY remain unsupported, as with prior
fan/burst routines. Tests use ROM IY8000 for that particular full-pool case.

Production uses conditional SGDK random calls. Original LD A,R/refresh stream
and absolute global clock behavior remain incomplete. Type6D55F1, including its
weapon-level damage filter and different choices, is not dispatched yet.

## Renderer correction

The type6C descriptor emits18 sprite parts. The native actor renderer incorrectly
rejected counts above16, making the new boss invisible despite matching actor
records. Removed that unsupported per-descriptor cap, retaining the total64
entry limit. Original09EE loops over the descriptor count. Main.c unchanged.

## Evidence and limits

- 660 direct original/native one-call cases:211 boss,324 projectile,125 satellite.
 All768 actor bytes exact. Two LD A,R sites use explicit register-preserving
 fixture inputs; other original state/aim/allocator/path instructions execute.
 Pursuit limits, all eight directions, attack gates, two-shot counter, partial/
 full allocation, signed-high-byte attraction cap, returning axes, path sentinels,
 animation completion and coordinate bounds included. Not an exhaustive state
 space or a reproduction of the original random stream.
- 18 controlled PAL/NTSC production segments,1518 frames with all768 actor bytes
 exact: appearance, pursuit, two shots, injected surviving/lethal pending damage,
 four explicitly selected satellite formations to final removal. Hero/boss/pool
 fixtures are injected into an exterior and native clock is aligned to source.
 These isolate logic; they do not prove natural full fights or absolute timing.
- Two actual destination entry/load tests into01AC after controlled neighbor
 relocation:47 relative actor frames and81 loaded tile pixel arrays at three
 samples each. All18 ordered boss SAT entries match at relative7/23/43, six lists,
108 entries. Arrival SMS/MD3445/3445 NTSC and3443/3443 PAL for these fixtures.
 Complete framebuffer/SAT sequences, natural travel and hardware are unproved.
- Scope audit reconstructs v0114 actors.c after removing these changes, including
 the rendering cap fix. Main.c/burst assets unchanged, three literal tables exact.
- Prior boss routines1789/1138/870/796/974 cases, prior burst1008 aligned frames,
 four charging-boss entry/SAT cases, ordinary PAL/NTSC timing, six inventory
 returns and two boss-death-to-gem chains pass against v0116.
- Unaligned NTSC burst contact diagnostic still reproduces MD2977/SMS2978 and
 post-frame clock difference73 modulo256. This actual timing gap is unresolved.

Next: native6D55F1, source clock/refresh/RNG, complete music/SFX and timing,
ending/progression/quest routes and a complete natural playthrough. Port incomplete.

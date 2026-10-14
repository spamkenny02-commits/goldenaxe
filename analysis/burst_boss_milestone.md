# Burst/disappearance bosses: v0114

ROM `versions/v0114-fa929315/gaw-megadrive-v0114.bin`, 1 MiB,
SHA-256 `fa9293155842594f13c97566a540bf3940ea0657bd513168a1770e592df16ba5`,
checksum1596. Type6A room0180 and type6B room0196.

Native54D3 -> AB40 eight-state appearance, eight-shot burst, disappearance
and57F8 relocation. Native4457 six-state projectile74 preserves the stopped
interval and the two variants:6A waits/flashes/clears;6B releases flying shots.
Original duplicate animation-period write leaves animation count unchanged;
period-zero behavior is deliberately preserved. Partial allocation failure
keeps writes through the last successfully allocated projectile, as on SMS.
Already-full pools with inherited RAM IY are still not modeled.

974 direct original/native cases compare all768 actor bytes:582 boss cases,
392 projectile cases. Placement candidates, allowed terrain, phase/proximity
rejections and retained partial X/Y writes included. Two LD A,R sites use an
explicit register-preserving input shim; full-pool source fixture supplies ROM
IY8000. Other source routine instructions execute unchanged. Production uses
conditional SGDK random calls, not the original refresh/RNG stream.

Four controlled PAL/NTSC production cycles compare all768 actor bytes over
1008 frames, through initial eight shots and disappearance, stopping before
random relocation. Hero and boss fixtures injected into the initial exterior.
The fixture explicitly aligns native world clock to source at frame2800.
This is required for matching hero/projectile contact parity, and is only a
test injection. It does not change production clock code.

An unaligned NTSC6B diagnostic remains in burst_contact_phase_report.json:
MD projectile contact/removal occurs2977, SMS2978; post-frame clocks differ
by73 modulo256. This real global-phase discrepancy remains unresolved.
The aligned comparison must not be presented as identical absolute timing.

Four destination-entry tests use controlled neighboring-room relocation then
normal left/right scroll and actual destination loading.47 relative initial
actor frames and46 loaded graphic tiles at three samples match each case.
Room0180 enters from0181 to avoid an invalid horizontal row wrap from017F.
Arrival times are recorded in individual reports; whole transition timing,
SAT/full framebuffer and natural routes/fights are not proved.

Patch audit reconstructs v0113 actors.c by removing only new boss/projectile
functions/dispatch and restoring collision publication range. Main.c and
charging boss data unchanged. Projectile44EA/44F2 tables match source bytes.
Regressions: first boss1789, satellite1138, composite870, charging796 direct
cases; ordinary PAL/NTSC timing; six menu returns including two first village
houses; two death-to-gem chains pass against this ROM.

Merchant menu corruption was corrected in v0096 by restoring the current
graphics class. v0114 retains that fix; six restoration cases compare124 tile
patterns before/after normal menu input, with four identified animated house
tiles excluded only from static equality. Full framebuffer equality is not
claimed. A separate v0097 fix restores the house animation scratch offset.

Next: type6C54D9 and6D55F1, source clock/RNG, full audio coverage, ending,
quests/progression saves and a natural complete playthrough. Port incomplete.

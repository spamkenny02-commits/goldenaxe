# v0093 - upward buffer-exchange timing

Original up-exit control flow 206A..20AC performs three 1280-byte buffer exchanges, versus one on down exits. Two exchanges were missing from the native foreground calendar. Source research instrumentation measures 79,385 foreground Z80 T states per exchange, in both regions. Two 68000 DBRA waits now retain that nominal work with interrupts enabled, using the master-clock ratio 15/7. Assets remain preconverted; there is no runtime Z80 interpreter.

The separate PAL publication continuation is needed for the down exit, but not up. This corrects the controlled upward PAL departure: state, room, position/velocity, animation/context and four actual hero pattern hashes agree for all 151 observed frames. Actual hero-only SAT lists agree throughout the transition. The six previously passing down/left/right cases remain exact in the same bounded fields.

NTSC up remains unresolved: native scrolling is one frame early, resumed state two frames early, and four hero-pattern frames differ. These differences are retained in the report. Neither software-map staging nor post-arrival enemy SAT lists are proved equivalent.

Further measurement isolates 20FF..2113, excluding the preceding IRQ wait: all 20 source transfers cost exactly 37,260 foreground T states, with no IRQ inside the measured interval, in both regions. See up_scroll_transfer_timing.json and water_cross_up_scroll_cycles_diagnostic.json. This is about 10.4 ms of source foreground work that native DMA does not reproduce as CPU work. A source phase model remains needed; adding arbitrary regional frame delays would not establish timing fidelity.

All source measurements use the original unmodified SMS ROM in a separate instrumented research core. Frame numbers describe fixtures, never cartridge playback data. The production ROM remains native 68000. Controlled initial water map, equipment, clock and departing enemies limit these comparisons; natural shore paths, combat, full images and audio require further validation.

# v0180 fresh IRQ before world reveal

SGDK VDP_waitVBlank(TRUE) skips the end-of-VBlank wait while display is
disabled. The VBlank status can then stay asserted,so SYS_doVBlankProcess
returns without a new vtimer interrupt. Original0BA7..0BB3 instead setsC02E
and waits for the IRQ to acknowledge it,irrespective of display state.

A dedicated compiled harness sweeps224 starting scanlines,display on/off,
existing wait_frame versus the same call followed by a fresh-vtimer gate,
in PAL and NTSC:1792 total calls. Baseline disabled-display calls return with
zero ticks in216 NTSC and224 PAL cases. The fresh gate returns after exactly
one tick in every tested position. This isolated harness has no game/audio
workload;it is evidence for waiting semantics,not complete hardware timing.
Baseline source,harness,raw results and report are immutable in
analysis/reveal-wait-v0179 with their manifest.

Production changes only reveal_world's initial wait before display enable:
capture vtimer,call wait_frame,then require vtimer to change. Global waiting,
audio,loader clock and all other modules are unchanged fromv0179.
All eight controlled standard-door transitions now sample18 fade-in frames,
including the PAL house exit that sampled19 previously. Existing exit fades
and32 contour ticks still pass. Hidden loading may wait an additional tick.

Regression evidence includes20 paid-passage scenarios,three save slots/cold
Continue,16 source-matched death/Continue contours and normalized images,
and31 capacity/HUD samples. These are controlled gameplay checks;full loading
duration,refresh RNG,combat synchronization,all waveform phases,hardware and
complete natural progression still require work.

# Predict original tempo and fade work from state, v0180

Independent models now reproduce original bank6 helpers807E and80C8,including
the complete83EF stop/mute path. They calculate instruction T states and the
resulting400-byte driver state from the input state;costs are not fitted to
observed durations. Tempo reload/increment wrap,fade countdown,per-channel
volume saturation and reset at fade completion are represented explicitly.

The isolated suite executes unchanged original bank6 code in a custom boot
fixture,with IRQs disabled. It checks1024 tempo and4096 fade states per region,
10240 total. Every helper cost and all400 resulting RAM bytes match. The
counter sweep includesall256 tempo values;fade states cover0/1/2/12 steps,
0/1/2/18 countdowns and allfour-volume combinations0/10/11/255. The255 volume
boundary is synthetic and is not a claim about normally reachable game state.

Live read-only instrumentation then captures both helper calls in the actual
controlled paid route6D->96,full destination actor mask,in PAL and NTSC.
601 calls of each helper per region yield2404 independently predicted cost
and400-byte state matches. All pre-existing original cycle-event arrays remain
identical to the archived v0179 source reference,so added observation has not
changed the observed emulated execution.

Full audio cost still needs arbitration,dispatch and seven channel/envelope
paths. The routines predicted here are components of that work. No arbitrary
loading wait or replacement RNG has been added;the production ROM and sources
remain byte-identicalv0180. Future full-reader/IRQ-phase prediction,physical
loading alignment,natural progression and hardware checks remain open.

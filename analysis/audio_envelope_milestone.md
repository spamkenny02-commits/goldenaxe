# Predict original854B volume envelopes, v0180

Independent models now calculate ADSR and table envelope instruction costs,
400-byte audio state and returned accumulator. ADSR covers attack,decay,
sustain/release,bounce/phase transitions,saturation and optional PSG muting.
80384 isolated original854B cases match across PAL/NTSC. All bank6 bytes are
unchanged;the fixture initializes IXDE40 and disables interrupts. The returned
A is checked even on muted channel termination,where it is not a volume.

All16 original table envelopes are checked at every offset up to the next
table,with six channel flag patterns,four tone types andthree explicit DE
inputs. Zero mode is also checked. 26800 cases match cost,state,A,DE and the
81/82 caller-frame unwinding behavior,including2160 direct caller returns.
A two-level fixture trampoline preserves the original POP/RET behavior;the
observation core records either ordinary return or the removed caller frame.

The source83 stream control reads memory at(++DE). This register is an explicit
model input;it is not replaced with an assumed adjacent table operand. The
isolated tests use documented ROM addresses. Arbitrary uncaptured RAM reads,
malformed streams and their natural reachability remain outside this scope.

On actual controlled6D->96/full-mask gameplay,1932 NTSC and2313 PAL envelope
calls match independent predictions. There are820/981 direct caller returns.
Modes0/1/2/6/7/8/16 occur on this route;no ADSR calls occur,so ADSR evidence is
isolated rather than a claim about this route. All original cycle-event arrays
remain identical to the archivedv0179 source traces. The original ROM and
emulated instruction timing are not modified by these observers.

Production ROM and every production source remain byte-identicalv0180.
Remaining work includes pitch,sequence/channel processing and reader entry/
region gating,then full futureIRQ-phase/physical loading prediction. This
milestone does not establish all waveforms,natural progression or hardware
equivalence and adds no fixed loading delay.

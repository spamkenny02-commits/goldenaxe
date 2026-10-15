# Predict original82C5 pitch and vibrato work, v0180

Independent state/instruction-cost prediction now covers zero pitch mode,
signed vibrato delay/rate/phase counters,16-bit delta accumulation and wrap,
direction reversal,and the eight original pitch tables. Table83 reads from
the incremented base address,as the source does;negative table values are
sign-extended. The model returns the source HL rather than a fitted frequency.

59400 isolated original82C5 fixtures per region,118800 total,match all400
audio RAM bytes,the complete helper cost and returnedHL. Bank6/callees remain
unchanged,IRQs disabled,IXDE40 explicitly initialized. Fixtures cover two
high-bit modes,eight base/seven delta boundaries,four delay/rate/phase counter
values,six signed steps,all eight table modes/all256 indices,two explicit
ROM-reading bases andfour channel flags. Many indices/bases are synthetic.

81/82 caller unwinding is represented from the instructions but is not reached
by these original table/index ranges. Zero observed unwind cases are not
evidence for that branch. It remains unverified rather than silently claimed.

On the actual controlled6D->96/full-mask paid route,the original helper runs
80 times in NTSC and101 in PAL. All181 calls match cost,state andreturnedHL.
Only mode0 occurs here;vibrato/table evidence is isolated,not natural route
coverage. The original complete cycle arrays remain identical to archived
v0179 source observations. No audio request or output state is injected in
this live observation beyond the documented initial gameplay fixture.

Production ROM and sources remain byte-identicalv0180. Sequence/channel work
and reader region gating remain before complete futureIRQ/load prediction;
full waveforms,source refresh RNG,natural progression and hardware are open.

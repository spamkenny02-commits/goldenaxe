# v0178: paid-loader fade and world-music hooks

Foreground-loading research exposed a real audio hook omission. Original16D0
setsC065 andDE06 toB0 while changing indoor->world graphics;1CAF selects82 before
1FA7 reveal. Read-only v0177 real6D->96 captures reproduce missing nativeB0 and
world82 only after reveal begins,in both regions. Baseline source/native latches
and fade state are preserved in analysis/hero-init-v0177.

Paid loader now calls sound_music(B0) before load_house_room and update_world_music
after loading,before palette/reveal. The existing elapsed-minus-one clock shift
includes the added work. Reader already implementedB0;no sequencer code changes.
These hooks apply only to the paid class1->class0 path,where graphics bank changes
are established. Other generic loader callers require their own source matching.

24 actual source/native paths cover six paid routes,empty/full actor masks and
PAL/NTSC.87->B0->82 order,B0 dispatch (reader fade12/18/18) and world request
before reveal compare. No audio-state/command injection occurs on these paths.
1800 separate aligned IRQ snapshots compare fade/seven-channel reader state and
audible PSG registers under controlled87/B0/82 requests. Muted noise frequency
is excluded;this is not a hardware/audio-waveform assertion.

3072 compiled actual full-loader clock cases and20 payment/poor/refusal/exit/menu
integrations pass on current ROM. Scope audit proves only two hooks changed;
all other production files,including hero/actor/sound/gift/save code,are unchanged.

Research also completed original2C63 model:13150 isolated cost/475-RAM-byte cases,
24 live hero entries/144 phases and24 complete foreground paths/72 comparisons
through fade entry. Models and117 evidence files are preserved separately in
analysis/hero-init-v0177. No model has yet been integrated as a physical delay.

Limits:physical loading remains too short on some paths,so fade progression and
command timestamps are not yet equal to SMS. Prior house-music phase,source audio
IRQ work/phase alignment,refresh RNG,other loader callers and full natural game
progression remain open. This release fixes command order,not complete fidelity.

# v0181 raw16-bit note duration correction

Original8357 raw-tone mode takes83D1..83EC and jumps directly to839B duration
multiplication. Its third byte is always a duration,including when bit7 is set.
The v0180 native common tail instead treated that bit as an omitted duration:
it reused c[13] and rewound the sequence cursor by one byte.

An isolated original8357 fixture reads actual unmodified bank6 bytes8421..8423
(21,3D,84) as a raw note/duration. A separate compiled native harness copies all
production source files and calls actual sound_sequence with the same audio
state and unmodified resources. Flags8/72/136,scale0/1/2/255,transpose0/1/127/
128/255,envelope0/1/128 andprior duration0/7/255 yield540 states per region.
All1080 v0180 cases differ in cursor and/or durations. Baseline code,reports,
states and native harness are immutable in analysis/raw-note-duration-v0180.

v0181 changes only the duration-reuse condition:raw tones always multiply the
explicit duration,while other tones/noise retain their existing reuse rule.
All1080 current cases compare every one of400 audio state bytes exactly.
These are boundary fixtures;natural reachability of the high-bit raw duration
is not asserted by this milestone.

Regression checks cover all13 music tracks(23400 IRQ states),all29 effects
(19140),and87/B0/82 fades in both regions(1800). All44340 reader/audible PSG
register snapshots compare;muted noise frequency is excluded. This does not
establish exact waveform/hardware behavior or complete natural progression.

ROM is1MiB,checksum686D. Every other production source is byte-identicalv0180.
The source sequencer cost model and full physical loading/IRQ alignment remain
unfinished;this correction is an independently reproduced behavior difference.

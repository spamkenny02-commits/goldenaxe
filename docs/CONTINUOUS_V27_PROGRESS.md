# V27 — Native audio sequencer

Lifted bank 6 $8000 into audio.c without linking the reference CPU in the
production source list. The driver handles seven channels, three prioritized
request slots, overlay effects, pause, fades, six-frame timing compensation,
notes/durations, pitch waves/vibrato, envelopes, stereo masks and stream
commands including loops and subroutines. Hardware PSG/stereo writes now use
a separate raw-byte platform API, with an ordered trace for host comparisons.

144,384 isolated original-instruction updates match RAM C000-DF8F and every
ordered PSG/stereo write. All thirteen music tracks run for 4,096 updates each
in both timing modes; all 29 effects run for 512. Mixed sequences add priority,
overlay/start/stop, pause/resume, fades and termination. Refresh-register
entropy is replayed. Tests caught an initial tempo error, a noise-channel
update timing error and the original pitch-wave jump's pointer increment.
The same suite passes ASan/UBSan. Reset, Pause, intro, final behavior and the
interpreter-free boot regressions pass; the native 68000 source list cross-links
and passes ELF/RAM/header checks. The uncalled audio driver is still removed
by linker garbage collection until its frame integration in the next step.

Unused/reserved requests have explicit malformed-input diagnostics; their
unreachable out-of-table instruction destinations are not treated as valid
music. The shared frame tick still uses its previous video/input behavior.
This checkpoint isolates the verified driver before full native IRQ integration;
console audio and console playability are not yet established.

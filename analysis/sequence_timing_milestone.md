# Source-semantic per-byte sequence timestamps

The native8357 sequence model now has a separate timed composition. It reuses
the authoritative semantic C with optional timestamp sidecar stores; ordinary
gameplay has neither the larger output object nor extra timing arithmetic.
The caller receives completed-OUT times in source Z80 T states relative to
helper entry, alongside the existing PSG list, DE, unwind and error outputs.
No source instructions are interpreted at runtime and no fixture deadlines
are used as assets. On rejection count is zero and the original state rollback
contract applies; stale sidecar slots are not publishable events.

## Source oracle and compiled checks

| Original8357 suite, each region | Cases | PSG bytes |
| --- | ---: | ---: |
| Notes/rest/duration |51712|680|
| Deterministic commands |29952|0|
| F1/F2 termination |192|192|
| F3 channel ownership |1920|2424|
| Nonzero8211 restoration |1728|2592|
| Mirrored DE/FE stream |128|0|
| Mirrored DF/FF stream |128|0|
| Total |85760|5888|

The original bank6 is unchanged. Only the custom fixture caller's hold loop
is removed for test speed. The observer records actual PSG port cycles/data,
all400 state bytes, source elapsed work, DE and caller-unwind return kind.
Every byte and timestamp agrees with the timed native output in PAL/NTSC.
M1 comes from retained source-verified vectors, not a new counter in this core.
The ordinary native output is also compared against the timed composition.

All85760 cases run again as compiled68000 in four bounded cartridges per
physical region. Each checks all400 bytes, T/M1, DE/unwind, source-observed
PSG bytes/times, then publishes the5888 events through the native queue.
Taking one logical tick early waits; taking at the supplied deadline returns
the expected byte/time. Zero failures. Absolute test epochs wrap32 bits.

Nine host boundary cases exercise unsupported controls, rejection after an
earlier write, the256-control guard at512 staged writes, and a successful
510-write sequence. State/work rollback, invalid event count and output-buffer
guards agree with the ordinary sequence API. These synthetic capacity cases
are not claims about natural gameplay reachability.

## Timing details and regression checks

The initial F3 annotation was16T late. Its existing command cost already
includes the future INC/JP dispatcher return. Events inside the handler must
subtract that prefolded postlude (16T tonal; the separate noise path uses18T).
The corrected tonal path agrees with the original on all ownership fixtures.
F1/F2 mute time precedes its following work; nested8211 latch writes occur
121T/126T after entry for zero/nonzero DE0F. All emitted offsets are checked
as ordered and within the complete helper duration.

The original audio reader differential still passes28644 cases against local
commit8f8e451:28555 successful transactions/streams and89 restored rejections,
with the unchanged digest680ebb69.... The validator now enumerates headers
actually present in that baseline, since newer experimental headers did not
exist there. The full game build still produces the exact v0203 binary,
checksum368C; none of this timing composition is wired into gameplay yet.

## Remaining scope

The noise8655 timed variant shares annotations but still needs its own source
oracle. Tone/frequency writes, dispatch/mute bursts and complete8000 composition
remain to be timed. A physical subframe consumer, global source phase and
combined producer/consumer budget also remain open. Queue checks here supply
logical time and do not establish actual PSG delivery timing or waveforms.

`analysis/sequence-timing-v0203/` archives source, fixtures, source calls/ports,
compiled diagnostic code/ROM, reports and hashes. Bulk proofs are compressed;
identical PAL/NTSC payloads share stored files. No full save states are requested.

```
python tools/build_audio_ports_core.py --sequence
python tools/validate_sequence_timing.py
python tools/validate_audio_stream_equivalence.py
```

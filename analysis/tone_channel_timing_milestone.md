# Complete84C7 tonal channels with per-byte PSG times

The separately named timed84C7 composition reuses the authoritative native C.
It rebases sequence events by the47T DEC/JR/CALL prefix, timestamps each of
the two frequency OUTs separately (42T apart), and locates envelope/release/
volume writes before their final10T RET. State, work, DE and channel return
behavior remain unchanged. The ordinary composition has no timing sidecar
stores or larger output objects.

## Source oracle and compiled68000

| Original84C7 suite, each region | Cases | PSG writes |
| --- | ---: | ---: |
| Retained channel matrix |10340|17928|
| Slot040 notes/controls |1248|2328|
| Slot070 notes/controls |1248|2328|
| Slot0A0 notes/controls |1248|2352|
| Slot100 notes/controls |1248|2328|
| Slot130 notes/controls |1248|2328|
| Slot160 notes/controls |1248|2328|
| Held/envelope/modulation |3024|5340|
| Total |20852|37260|

The oracle records original84C7 entry, actual PSG port cycles/data and the
normal/caller-unwind return. All of bank6 is intact; only the custom caller's
hold is removed. The full400-byte input and DE are checked against retained
fixtures, followed by all400 output bytes, complete T, DE, channel return,
ordered PSG values and every completed-OUT timestamp. Both regions pass.
M1 uses retained source-verified vectors rather than a new core counter.
The timed and ordinary native channels also agree on their semantic outputs.

Compiled68000 repeats all20852 cases per physical region, covering six tonal
slots, notes/controls, modulation, signed transpose and borrowed-noise channel
frequency routing. All37260 events per region pass native queue roundtrips
with WAIT one supplied logical tick early and exact-byte/time release at due.
Zero failures;5923 NTSC and4956 PAL frontend frames. These are test-harness
durations, not gameplay performance measurements.

Ten guarded host boundaries compare against the ordinary channel: unsupported
controls, rejection after an emitted prefix,256-control limits, overflow of
the512-event staging capacity, and a valid511-event sequence. Full state/DE/
work rollback and output guards pass. These synthetic limits do not imply
natural gameplay reachability.

## Regression and reporting

The shared compiled harness now accepts explicit per-suite slots and tonal
calls, in addition to noise and sequence calls. Noise was rerun through this
path:30670 cases/23759 events per region, no failures. Its standalone-sequence
branch also passes3840 F1/F2/F3/restoration cases and5208 queue events per
region after the harness changes. Whole-reader comparison
against local8f8e451 still passes28644 cases with unchanged digest680ebb69....
The full game rebuild remains exact v0203, checksum368C; timed channel code
is still unused by gameplay. No new numbered ROM is created for identical bytes.

Generalizing the shared reporter exposed a Python variable-name collision:
loop names replaced the channel name used for its JSON filename. The channel
identifier is now separate. Correctly identified reports were retained under
their intended names; raw oracle data and compiled results were unaffected.

## Remaining integration

Tonal and noise channel event lists now have source-semantic times. Global
dispatch/priority/mute bursts and whole8000 composition still need timestamps.
Physical subframe delivery, source phase propagation from boot and combined
production CPU budget remain unproved. Queue checks here use supplied logical
time and do not establish physical port pacing, waveform or full-game fidelity.

`analysis/tone-channel-timing-v0203/` contains compressed/deduplicated source
captures, fixtures, generated native code/ROM, reports and hashes. No full save
states are requested. Reproduce with:

```
python tools/build_audio_ports_core.py --tone-channel
python tools/validate_tone_channel_timing.py
python tools/validate_audio_stream_equivalence.py
```

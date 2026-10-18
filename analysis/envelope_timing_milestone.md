# Source-semantic envelope PSG timestamps

`source_audio_envelope_timed` preserves original854B accumulator, DE, unwind,
state and work outputs while returning the optional mute PSG event. Both
writing paths tail into863E and execute OUT864C then RET864E. The event time
is therefore `source_entry+(helperT-10)*15`, including a table-envelope POP
when the helper unwinds its caller. Suppressed and rejected paths leave the
event untouched. The API performs no PSG IO and does not enqueue automatically.

## Original source comparison

The port observer supports854B entry and two return PCs. A normal return
closes at3003; a table control's POP/RET skips that caller and closes at3053.
It separately records A and the return kind, without modifying CPU state.
The source fixtures retain all of original bank6. Only the custom caller's
three-frame hold is replaced with NOPs to reduce test duration; IRQs are off.

| Suite, each region | Source calls | PSG writes | Caller unwinds |
| --- | ---: | ---: | ---: |
| ADSR |40192|1776|0|
| Table envelopes |13400|252|1080|

Both PAL and NTSC agree on all400 RAM bytes, complete T, A, DE, unwind and
every actual PSG byte/deadline. Their raw call/port/metadata hashes are identical
between regions. M1 agrees with the existing source-verified model; the new
port observer itself does not count M1. ADSR covers values0..255, step/limit
boundaries, phases and ownership flags; tables cover all16 original tables
and their offsets, plus zero mode and controls80/81/82/83. These are controlled
component fixtures, not natural gameplay reachability claims.

## Host and compiled68000

53600 native cases additionally shift the semantic fixtures over all seven
channel slots and include eight rejected memory reads. All400 bytes, work,
DE, accumulator/unwind/write outputs and timed event agree. Eight extra host
calls check null arguments and invalid offset353 without state/DE/event changes.

The compiled tests run all53600 cases per physical region, with zero failures:
14198 NTSC and11880 PAL frames. Each region queues2028 events, verifies WAIT
one logical tick early, and retrieves the exact byte/deadline at its due time.
Absolute test epochs wrap32 bits. The previous noise-selector compiled suite
also passes again in both regions:9216 cases and4608 queue events per region.

The full game build is still exactly v0203, checksum368C. The new helper is
discarded as unused by the gameplay build. README and local Git track this
experimental work; no new numbered playable ROM is created for identical bytes.

## Remaining work and storage

Noise selection and envelope mute now have source-semantic event times.
Sequence controls, frequency writes and prefix bursts still need timed
composition into the whole8000 reader. The physical subframe clock, global
source-entry phase and combined scheduling cost remain open. Queue checks
use supplied logical times and do not prove actual port delivery timing.

Raw source calls/ports/metadata are written directly as verified lossless gzip
files. The archive `analysis/envelope-timing-v0203/` retains these compressed
proofs, source fixtures, diagnostic source/ROM and hashes. No full emulator
save states are requested. To reproduce:

```
python tools/build_audio_ports_core.py --envelope
python tools/validate_envelope_timing.py
```

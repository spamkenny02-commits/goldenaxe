# Complete8000 native stream with source-semantic per-byte PSG times

The timed reader now composes gate, arbitration, tempo, fade, dispatch,
priority/restoration, compensation and all seven tonal/noise slots. Every
successful prefix/channel list carries completed-OUT offsets in source Z80
T states from8000 entry. The sink copies temporary lists synchronously.
No instructions are interpreted at runtime and no captured deadline table
is included in gameplay assets.

Dispatch/priority reuse authoritative semantic C with optional sidecars.
Gate/fade use their existing work model and produce the ten-byte8412 mute
burst. OTIR's port operations are21T apart; the first is249T before the
complete mute path ends. Priority latch writes are rebased through their
calling paths. All these offsets are covered by the full-reader port oracle.

## Original source and compiled68000

| Reader suite, each physical region | Calls | PSG bytes |
| --- | ---: | ---: |
| Gate matrix |5376|26880|
| Retained live reader inputs |14424|40663|
| Compensation |2048|813|
| Global dispatch |1000|9458|
| Priority |1116|4196|
| Channel combinations |1536|6336|
| Noise reader exits |144|854|
| Total |25644|89200|

Custom DI callers replay each saved400-byte input and DE through original
bank6 routine8000. Fixture low-memory streams are retained except for the
bootstrap/caller. Every input/output byte, complete T, returned DE and actual
PSG handler byte/time agrees with retained vectors and the timed native reader
in PAL/NTSC. The ordinary capture reader also agrees on work, state, status,
track and ordered PSG bytes. M1 uses existing source-verified vectors rather
than a new counter in this observer. These are component replays of retained
inputs, including live captures; they are not new full-game playthroughs.

Eight bounded diagnostic cartridges repeat all25644 calls on compiled68000
in each physical region. All400 bytes, T/M1, DE/status/track and the89200
source-observed byte/deadline pairs pass, with zero failures. Their sinks
also pass every packet through the native FIFO: one tick early waits, exact
supplied logical time releases the correct event, and the queue is empty
after the call. Absolute test epochs cross32-bit wrap.

## Failure contract and regressions

3000 deterministic mutations compare the new timed stream with the ordinary
stream.2911 succeed and89 reject;27 of the rejections follow already-published
PSG writes. All400 bytes, DE, work, status/track and emitted bytes agree,
including partial earlier commits. Rejected contexts have no new source IO
oracle; this check establishes parity with the existing stream contract.
The stream has no outer rollback; earlier successful lists remain published.

The separate ordinary/fast capture/stream regression against local8f8e451
still passes28644 cases with digest680ebb69.... The complete gameplay build
remains exactly v0203, checksum368C. Its audio path has not been switched.

## Remaining integration

The complete supported native reader now has semantic timestamps. Existing
unsupported commands still follow their rejection paths. Production integration
needs an absolute source-entry clock, bounded buffering/backpressure and a
physical subframe consumer. Its combined compute/publication budget must be
measured, especially the thin NTSC loading margin. This composition currently
retains ordinary channel rollback copies; a timed fast composition can reuse
the already-audited fast-stream contract before that measurement.

No physical port pacing, global phase from boot, audible waveform or complete
game fidelity is established here. The source clock/loader is still separate
from the playable v0203. The goal remains unfinished.

## Storage and reproduction

`analysis/reader-timing-v0203/` preserves compressed/deduplicated raw source
calls/ports, fixture/code/ROM snapshots, reports and hashes. Raw generated
SMS test-ROM copies are removed from validation only after verifying their
lossless archived copies. The input ROM and numbered gameplay ROMs are kept.
No full save states are generated.

```
python tools/build_audio_ports_core.py --reader
python tools/validate_reader_timing.py
python tools/validate_reader_timing_68k.py
python tools/validate_timed_reader_failures.py
python tools/validate_audio_stream_equivalence.py
```

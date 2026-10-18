# Fused reader/master conversion: measured, not selected

This experiment tests whether one helper-to-master timestamp pass can replace
the relative reader pass followed by an absolute IRQ sink pass. Source work,
state and OUT dates must remain exact. It does not relax fidelity and does
not change the playable v0203 or the recommended fast timed IRQ adapter.

`source_audio_reader_master.c` specializes the authoritative timed reader's
emission hook, retaining fast channel semantics. It emits modular32-bit master
ticks from an explicit8000-entry epoch. The diagnostic IRQ adapter supplies
the same full/audio-only prefixes as before and skips the512-word conversion
buffer. Callback arrays are still temporary and must be copied synchronously.
The generic timed-reader API retains relative source T offsets.

The diagnostic master reader passes25,644 calls /89,200 source-observed writes
in each compiled68000 region, checking all400 audio bytes, DE, T/M1,
status/track, byte values and master times across32-bit epoch wrap. Queue
checks retain early WAIT and exact due behavior.3000 mutated contexts match
the fast untimed contract:2911 accept,89 reject,27 after earlier published
writes, digest993eb42c.... Ordinary and fast relative variants are also
regressed separately. Adapter parity now covers52 cases and208 calls across
canonical, normal timed, fast timed and fused master implementations.

## Whole-chain measurements

All variants verify24 source loading endpoints and1488 source PSG dates/bytes.
The measured interval includes source computation, base-video conversion and
actual transfers plus diagnostic date/value stores. Actor/hero/HUD font
uploads are still excluded. Same relative epoch, display disabled, no pacing.

| Variant | Worst NTSC frames | NTSC cases over budget | Worst PAL frames |
| --- | --- | --- | --- |
| Existing fast relative reader + absolute sink |23.115298|2/12|18.446948|
| Fused, base scaled once per packet |23.237045|4/12|18.510640|
| Fused, reader forced out of line |23.480065|6/12|18.694236|
| Fused, one multiply per event |23.259782|4/12|18.542562|
| Source interval |22.710426| |19.570750|

The final fused diagnostic is slower: worst NTSC deficit143.879 scanlines,
versus106.024 for the retained relative variant. It is therefore NOT the
selected integration path. Small-looking C loop reductions are insufficient
evidence of a68000 loading improvement. Forcing the complete reader out of
line also regresses performance; it is reverted.

Separate source-clock gate experiments are also rejected and fully reverted:

| Gate experiment | Worst NTSC frames | Cases over budget | Worst PAL frames |
| --- | --- | --- | --- |
| Four-byte gate via memcpy |23.517142|6/12|18.747837|
| Two-byte gate via memcpy |23.563814|8/12|18.682492|
| Two-byte gate with alignment hint |23.234866|4/12|18.536150|
| Original gate, forced inline |23.420383|6/12|18.691702|

The disassembly of the naive two-byte memcpy shows two byte copies into a
stack temporary; the alignment hint produces a direct TST.W, but the complete
loader still regresses. The retained source_clock.h is byte-identical to
982954c. The restored fast relative profile reproduces the previous measured
durations exactly in all24 cases. No gate experiment is included in the game.

## Storage and next work

The immutable `analysis/master-reader-research-v0203/manifest.json` preserves
both successful semantic proofs and rejected performance trials, with their
source snapshots/ROM hashes. Large regenerable copies are removed only after
lossless archived-byte comparison. Old source vectors and the earlier timed
IRQ baseline are referenced by verified hashes; numbered game ROMs are kept.

Continue from the existing fast relative adapter, not the fused diagnostic.
The next useful performance work is a cost breakdown of the loading stages
and IRQ calls against their source deadlines, followed by optimization of
measured hot paths. Do not repeat these rejected compiler/gate changes.
Physical subframe pacing, global phase from boot and complete gameplay
fidelity remain unfinished. This milestone does not justify raising the
overall completion estimate.

```
python tools/validate_reader_timing_68k.py --master
python tools/validate_reader_timing_68k.py --fast
python tools/validate_reader_timing_68k.py
python tools/validate_timed_reader_failures.py --master
python tools/validate_timed_irq_boundaries.py
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --master-timed-audio
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --fast-timed-audio
```

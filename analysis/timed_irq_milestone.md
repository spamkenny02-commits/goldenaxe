# Absolute source-clock PSG dates and measured loading cost

The separate source-clock prototype now joins its IRQ adapter to the complete
timed native8000 reader. The playable game remains byte-identical v0203.

## Composition and source evidence

`SourceTimedIrqContext` embeds the canonical IRQ context as its first member.
It reuses the same staging, diagnostics and commit sequence, substituting only
the audio reader. Source reader T offsets become modular32-bit master dates:
`entry_elapsed + (entry_to_8000_T + OUT_T) * 15`. Entry0137 follows the72T
interrupt accept/vector; its audio-only8000 prefix is247T. Full IRQ prefix
comes from the pre-audio stages plus17T CALL. C02E remains uncommitted while
audio runs, so it selects the original path without inspecting zero stages.
Packet buffers are temporary; sinks copy retained data synchronously.

Both ordinary-snapshot and fast timed variants match the original-reader
byte/deadline oracle for all24 retained room-loading contexts:660 NTSC and828
PAL writes. Endpoint source RAM/work and physical base graphics remain checked.
The fast reader omits nested rollback copies using the existing fast-stream
contract. On rejection failed-channel state may change, its writes are
discarded, and earlier successful lists remain published. No outer rollback
is promised. It must not silently replace a capture/transactional reader.

Compiled68000 fast-reader validation passes25,644 calls and89,200 writes per
region, comparing all400 audio bytes, DE, T/M1, status/track and source times.
The same native queue checks early WAIT, exact due time and32-bit epochs.
3000 deterministic mutations pass matching fast-stream semantics:2911 accept,
89 reject, including27 after earlier writes. These mutations have no source
execution oracle for arbitrary rejected inputs.

52 adapter boundary cases /156 adapter calls compare canonical, timed and
fast timed behavior, DE/state hashes, full/audio-only, invalid graphics/region,
unsupported audio, reset/nested diagnostics, absent sinks, timer boundaries
and master-clock wrap. A fixed audio-only mute verifies source247T prefix,
116T first OUT and21T spacing independently. The11 legacy boundary cases
and13,725 source wait cases also pass. No physical pacing is implied.

## Measured CPU budget

Read-only68000 PC markers bracket the complete four-call loading chain,
base-video conversion and actual VRAM/CRAM/PSG transfers. Deadline conversion
and diagnostic date/byte stores are included. Source and physical regions
match. The display is off; actor/hero/HUD font tile uploads are excluded.
These are controlled loader contexts, not complete gameplay timing.

| Reader | NTSC compute/transfer frames | PAL compute/transfer frames |
| --- | --- | --- |
| Timed, nested snapshots |23.4954..24.6324|18.9357..19.7940|
| Fast timed |21.9738..23.1153|17.5879..18.4469|
| Original source interval |22.7104|19.5707|

Fast timed still exceeds the NTSC whole-chain budget in2/12 contexts, worst
106.024 scanlines, about0.405 frame. PAL passes12/12 with at least351.803
scanlines remaining. Avoiding a stage-array read saves less than0.0011 frame;
the first-pass sources/reports are preserved separately. This does not solve
the NTSC deficit. The comparable older untimed fast profile had only1.638
scanlines of minimum NTSC headroom.

An additional diagnostic records packet sizes to compare availability against
each source-byte deadline. This adds trace/size stores, so it is a separate
profile, not a substitute for the table above. It records5/660 late NTSC bytes,
worst10,379 master ticks (3.035 scanlines), and0/828 late PAL bytes, minimum
36,081 ticks (10.55 scanlines). Availability is measured at packet function
entry, before sink/queue overhead, and is therefore optimistic. Each full
packet is available there; packet counts must not be treated as byte counts
(PAL includes mute lists). Relative budget-entry/source epochs are compared;
global physical/source phase alignment from boot is still unestablished.

## Remaining work and reproduction

Reduce the NTSC cost without changing source state/event dates, then integrate
bounded queue/backpressure and a physical subframe consumer with a justified
epoch. Positive whole-chain or packet margins alone do not prove schedulability.
No audible waveform, real hardware or complete-game fidelity proof exists.
The native source-clock pipeline is still separate from the playable ROM.

```
python tools/validate_reader_timing_68k.py --fast
python tools/validate_timed_reader_failures.py --fast
python tools/validate_timed_irq_boundaries.py
python tools/validate_native_irq_context_boundaries.py
python tools/validate_native_source_wait.py
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --timed-audio
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --fast-timed-audio
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --fast-timed-audio --audio-readiness
```

`analysis/timed-irq-v0203/manifest.json` retains source/report snapshots and
lossless compressed/deduplicated diagnostic builds/captures. Older source
vectors are referenced by verified immutable hashes. Generated diagnostic
copies are removed only after archived-byte verification. Numbered gameplay
ROMs, source input and Git history are preserved; no push is performed.

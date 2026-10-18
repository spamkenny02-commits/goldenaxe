# Native bounded divisions reduce measured source-clock loading cost

The source-clock prototype now uses native68000 DIVU where its quotient is
proven to fit16 bits. Work/state and source PSG deadlines are unchanged.
The playable ROM is still byte-identical v0203; this is not yet physical
clock integration.

## Measure first

The retained71c4f81 fast timed loading cartridge is restored from its verified
immutable archive. Read-only PC observations pair every modeled IRQ entry
and return, including return SP. Six graphics checkpoint recorder sites are
observed: one outlined callback plus two LTO-inlined copies. Watching only
the callback entry would miss two checkpoints. All24 whole-chain durations
reproduce their previous exact master counts.

IRQ wall time accounts for12.069% NTSC /13.266% PAL of those12 cases per
region. The largest residuals are before1706 (pattern decoding) and between
24B9 and video conversion (remaining map/HUD/finish). Outlined function counts
also find922 NTSC /728 PAL general unsigned32-bit division calls. Inlined
clock operations are not included in those call counts.

The observer can drain/reset its own storage each physical frame, enabling
call counts without changing CPU state or overflowing its8192-record buffer.
All whole-chain durations must still equal the established measurement.
IRQ timing stops before its final RTS; that instruction belongs to the
foreground residual. Recorder bookkeeping and physical interrupts remain
included. These intervals are diagnostic partitions, not exact source-stage
publication boundaries or a statistical instruction-cost profile.

## Two bounded arithmetic changes

In `source_clock_repeat`, a32-bit dividend and16-bit divisor can use DIVU
exactly when the dividend's high word is smaller than the divisor. The
denominator is nonzero because tstates is already validated. Larger divisors
or overflowing16-bit quotients retain the general32-bit division fallback.

The two pattern command-window functions already compute
`min(until_vint / 15, 65535)`. A shared helper clamps at983025 master ticks
before dividing, proving that each remaining DIVU quotient fits. Saturation,
division floors, clock boundaries and writes are unchanged.

The final measured library division count falls to24 per region. This is a
call-count reduction; only the following complete-chain measures establish
the actual gain. Layout, marker and IRQ effects remain included.

| Version | Worst NTSC frames | Worst NTSC deficit, lines | Worst PAL frames |
| --- | --- | --- | --- |
| Previous fast timed prototype |23.115298|106.024|18.446948|
| Bounded repeat division only |23.051830|89.395|18.395295|
| Repeat + saturated pattern windows |22.981518|70.973|18.353042|
| Source interval |22.710426| |19.570750|

The worst NTSC deficit shrinks by33.1%, from0.405 to0.271 frame. Two of12
NTSC contexts remain over budget. PAL retains12/12 below budget, with at least
381.195 scanlines remaining. Across12 cases the total CPU/transfer saving is
1464225 NTSC master ticks and1207203 PAL ticks. The independent read-only
stage profiler reproduces every new whole-chain timing exactly too.

With additional packet-readiness diagnostics,4/660 NTSC bytes still miss
their relative deadlines (minimum margin -3638 master ticks, about -1.064
lines), versus5/660 and -10379 before. PAL has0/828 late bytes and a42885-tick
minimum margin. This separate profile includes diagnostic stores; packet
function-entry availability is optimistic and excludes later queue overhead.
No global epoch from boot or physical byte pacing has been established.

## Verification

- 8000 immutable-reference clock cases pass on host and in compiled68000
 PAL/NTSC. Cases include near-VINT, counter/refresh wrap, zero/disabled guards,
 large repetitions and16-bit divisor boundaries65520/65535/65550.
- 1070469 compiled68000 pattern-window cases pass per physical region: every
 master tick0..PAL period1070460, plus saturation and32-bit boundaries.
 The oracle is independent general C division followed by the original clamp.
- All16 source checkpoints from each of24 full loading inputs pass host and
 compiled68000 PAL/NTSC: phase/R/M1, RAM/audio, IRQ offsets and buffer data.
- The timed physical-video loading profile checks all1488 original source
 PSG byte/deadline pairs and endpoint VRAM/CRAM in24 matching-region contexts.
- 52 adapter cases /208 calls pass. The complete game rebuild remains v0203,
 SHA7660a4b5..., checksum368C. Numbered ROMs are preserved in local Git.

## Remaining work and reproduction

Continue profiling the large foreground intervals before changing generic
clock checks. The current helpers have eliminated nearly all outlined general
division calls; another arithmetic rewrite is unlikely to remove the entire
remaining NTSC deficit. Bounded queue/pacing, full graphics coverage, global
entry phase and whole-game fidelity remain unfinished.

The immutable `analysis/native-divu-loading-v0203/manifest.json` preserves
sources, reports, the repeat-only intermediate and compressed/deduplicated
diagnostic proofs. Input/numbered ROMs remain intact. Generated test copies
are removed only after archived-byte verification. Git remains local.

```
python tools/profile_timed_loading_cost.py --clock-calls
python tools/validate_clock_repeat_fast.py
python tools/validate_clock_repeat_fast_68k.py
python tools/validate_pattern_window_divu.py
python tools/validate_native_room_finish.py --planned
python tools/validate_native_room_finish_68k.py --planned
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --fast-timed-audio
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --fast-timed-audio --audio-readiness
python tools/profile_timed_loading_cost.py --current --clock-calls
```

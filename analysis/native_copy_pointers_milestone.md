# Cached copy pointers remove the retained loader's NTSC CPU deficit

The separate source-clock prototype now fits all24 matching-region loading
contexts into their source intervals. The playable ROM remains exactly v0203.
No physical output pacing, complete graphics upload or whole-game claim follows.

## Read-only instruction cost evidence

`build_md_cost_core.py` builds a distinct emulator DLL with host-only counters,
then restores the original emulator source byte-for-byte. At each native
instruction entry it attributes the elapsed master ticks to the preceding PC,
in64-byte bins. The frontend adjusts the per-frame cycle origin explicitly.
Every histogram sum equals the independently observed begin/end interval for
every case. All diagnostic endpoint checks also pass. Neither the cartridge
nor its CPU state/cycles are modified by this observation.

Bins can straddle functions; nearest-symbol labels are hints only. Hardware
IRQ acceptance and DMA waits are wall time charged to the preceding PC.
The out-of-range bin would aggregate PCs beyond0x3ffff; it is empty in these
runs. This is instruction-entry wall accounting, not intrinsic opcode timing.

The old pattern-plan copy bin at0x12240 accounts for36,669,388 NTSC master
ticks across12 cases (15.30% of the chain), with475,212 instructions. Its
disassembly reloads `plan->decoded` and `end->decoded` for every byte because
the compiler cannot exclude aliasing with the destination. A second hot copy
reloads `map->tilemap` and `graphics->patterns` during the1536-byte mirror.

## Two changes, unchanged virtual effects

The verified pattern plan is immutable ROM. `planned_window` now snapshots
its decoded bound and stream pointer before copying bytes into the RAM mirror.
It retains the same byte order, destination stride4, source/cursor/index
updates and clock-block boundaries. No IRQ-visible intermediate write is
batched across a virtual interrupt.

The already-modeled DI transfer in `source_room_finish` snapshots its data
pointers before the forward1536-byte mirror copy. Descriptor objects remain
separate from their data buffers. Clock work, DI/EI/status handling and all
source writes remain in the original order.

| Prototype | NTSC maximum frames | PAL maximum frames |
| --- | --- | --- |
| Previous native-DIVU milestone |22.981518|18.353042|
| Pattern-plan copy only |21.212167|16.898592|
| Both cached-pointer copies |19.948909|15.842399|
| Original source interval |22.710426|19.570750|

All12 matching NTSC contexts now fit, with at least723.570 scanlines
(2.762 frames) remaining. All12 PAL contexts fit, minimum1167.027 scanlines
(3.728 frames). Across12 cases per region, total measured wall cost falls
from239,674,889 to207,066,972 NTSC master ticks and from228,901,828 to196,669,407
PAL ticks: about13.6% /14.1% less complete-chain cost. The new observer
independently reproduces all24 exact whole-chain timings too.

The separate packet-readiness diagnostic reports0/660 late NTSC bytes and
0/828 late PAL bytes. Minimum margins are80,726 and141,417 master ticks
(23.604 and41.350 lines). These are packet function-entry availability,
before queue/sink overhead, on a relative source/budget epoch. Extra diagnostic
stores are included. Positive margins do not establish a physical schedule.

## Verification and scope

All16 original source checkpoints for each of24 full loading inputs pass on
host and compiled68000 PAL/NTSC: RAM/audio, phase/R/M1, IRQ offsets and data
buffers. The timed physical-video profile still matches all1488 original PSG
byte/deadline pairs and endpoint VRAM/CRAM. Its193 base tiles,768 map words
and32 colors are real transfers, but actor/hero/HUD font uploads remain excluded.

An additional16 logical phase/IFF/pending/blocked cases compare the planned
assets with immutable scalar C on both physical regions: all16384 pattern
bytes,336 RAM bytes,400 audio bytes, clock outputs and full IRQ traces agree.
The1,070,469-per-region native divide/clamp check also passes after the file
change. The whole-game rebuild retains SHA7660a4b5... and checksum368C.

The immutable `analysis/native-copy-pointers-v0203/manifest.json` preserves
source snapshots, observer code/DLL, instruction data, the intermediate
pattern-only result and compressed/deduplicated diagnostic builds. Generated
copies are removed only after archived-byte verification. Input ROM, numbered
playable ROMs and local Git history remain intact.

Next connect the source-timed stream to its bounded queue and physical output
consumer, measuring actual port timing and backpressure. The new headroom
removes the measured CPU blocker for these contexts; global boot alignment,
additional graphics classes/actors and complete-game fidelity remain open.

```
python tools/build_md_cost_core.py
python tools/profile_md_instruction_cost.py
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --fast-timed-audio
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --fast-timed-audio --audio-readiness
python tools/profile_md_instruction_cost.py --current
python tools/validate_native_room_finish.py --planned
python tools/validate_native_room_finish_68k.py --planned
python tools/validate_pattern_windows_68k.py --planned
```

# Source-timed reader connected to the bounded native FIFO

The native source-clock loader can now publish its exact PSG byte/deadline
packets into the native FIFO through `SourceQueuedIrqContext`. The playable
ROM remains byte-identical v0203. Physical clock/port pacing remains open.

## Producer and backpressure contract

`source_psg_queue_push_bytes` atomically publishes separate byte/deadline
sidecars using the established FIFO order/capacity/cursor rules. It validates
the entire packet before touching storage or advancing head. It avoids a
second512-event staging array in the reader callback. Pending data and inputs
must be disjoint. One main producer and one IRQ consumer share one68000;
compiler barriers and atomic16-bit cursors are not a multicore/host-thread lock.

`SourcePsgStream` retries the same complete packet on FULL using a caller
progress/wait callback. It never exposes a partial packet. Impossible packet
sizes, invalid/order errors or explicit cancellation latch a fault and fence
later callbacks. Initialization requires an empty queue and stopped consumer;
invalid initialization leaves the stream unchanged. The progress callback
must not reenter/reset the producer. It must make progress or cancel; this
module supplies no clock or deadline-compliance guarantee.

`source_irq_queue_bind` retains the first-member IRQ layout and requires at
least512 queue slots, accommodating every bounded individual reader packet.
It preserves caller RAM/audio/input/trace fields. Its IRQ adapter substitutes
the fast timed reader and reports stream faults before IRQ RAM/trace commit,
with zero invalid work and a distinct0x900 diagnostic. `last_audio.count`
reports bytes actually published when that stream faults.

Audio state can have advanced and earlier packets can already be published
on failure. This is the existing nontransactional fast-stream contract:
stop/reset the session and consumer, never retry that IRQ. Callers must also
stop the consumer on other failed source IRQs, such as unsupported commands,
reset or nested diagnostics. FIFO backpressure does not invent source T/M1.
Consumers must respect a latched stream fault.

## Verification

- 980029 stream/sidecar checks pass on host and compiled68000 PAL/NTSC.
 Sidecar operations agree with the established typed FIFO. An independent
 ordered stream delivers90000 bytes with32-bit deadline and16-bit cursor
 wrap, complete-packet retry and cancellation/error fencing.
- Actual emulated VINT callbacks consume12000 further events per region while
 the main stream producer blocks/retries. Packet-end markers detect partial
 publication. The frame counter is a test clock, not a PSG timing proof.
- The previous FIFO regression still passes705805 checks/119273 events and
12000 VINT-consumed events per physical region; its host maximum-capacity
 test is retained.
- 24 source loading inputs are tested in four modes: empty/prefilled FIFO,
 ordinary/wrapped epoch and cursor. All96 host cases and96 cases on each
 compiled physical region preserve all16 source checkpoints, RAM/audio,
 clock phase/R/M1, IRQ traces and exact source PSG byte/deadline lists.
5952 source events per physical region are checked over those four modes.
 Full modes prefill512 older sentinels and pump them one at a time, forcing
 genuine whole-packet retries. The pump clock is supplied logically.
- 11 setup/fault cases pass host and compiled68000 PAL/NTSC: unbound, small or
 nonempty setup, order/sticky/cancel faults, valid FULL retry, silent/muted
 success, original reader rejection and cancellation after a source-derived
 successful prefix. Queue faults cannot masquerade as valid clock work or
 successful IRQ RAM/trace commit. Partial publication counts are explicit.

## Complete-chain cost

A separate controlled cartridge runs the real source-checked four-call load
with the512-event queue, then drains it using the logical completion clock,
emitting actual PSG bytes before physical base-video conversion/transfers.
Every one of1488 stored source bytes/dates and all endpoint VRAM/CRAM checks
still pass. All controlled loads fit the queue, with zero progress callbacks.

| Physical region | Worst CPU/transfer frames | Source interval | Minimum margin |
| --- | --- | --- | --- |
| NTSC |20.435467|22.710426|596.092 lines /2.275 frames|
| PAL |16.334560|19.570750|1012.980 lines /3.236 frames|

The cost includes enqueue, dequeue, diagnostic stores and real port writes,
plus193 base tiles,768 map words and32 palette colors. Actor/hero/HUD font
uploads remain excluded. Port writes are deliberately deferred until the
calculation finishes in this diagnostic: stored deadlines are not measured
physical delivery times. There is no paced-consumer, live-input epoch,
subframe latency, global boot alignment or full-game fidelity claim here.

## Next work and preservation

Connect the queue consumer to an actual physical clock and measure real PSG
port timestamps against source deadlines, including interrupt/burst overhead,
backpressure and late-event behavior. Positive CPU margin alone does not prove
that schedule. Preserve live input sampling and source phase when integrating
the pipeline into the game; captured loading contexts are test inputs only.

`analysis/queued-audio-v0203/manifest.json` retains source/report snapshots,
generated vectors and compressed/deduplicated diagnostic builds. Older source
oracles are referenced by verified immutable hashes. Only verified generated
copies are cleaned. The input ROM, numbered game ROMs and local Git are kept.

```
python tools/validate_psg_stream.py
python tools/validate_queued_loading.py
python tools/validate_queued_irq_faults.py
python tools/validate_psg_queue.py
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --queued-audio
```

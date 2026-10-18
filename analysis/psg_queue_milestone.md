# Native deadline queue for PSG publication

`source_psg_queue.c/.h` adds a caller-owned FIFO of byte/deadline pairs for
the experimental source-clock audio publisher. No game code calls it yet;
the complete game build still produces exactly v0203, checksum368C.

The producer validates a complete batch's capacity and ordering before writing
any payload, then publishes its16-bit head after a compiler barrier. Rejection
leaves storage/cursors untouched. FULL is explicit backpressure, never a drop.
The IRQ consumer copies one due event before releasing its16-bit tail. Equal
deadlines preserve insertion order; future events stay queued. Both32-bit
deadline wrap and16-bit cursor wrap are supported within the documented
less-than2^31 tick comparison horizon.

This targets one main-loop producer and one IRQ consumer on a single68000.
The queue is not a multi-CPU/host-thread synchronization primitive. Storage,
input and output must not overlap; initialization requires a stopped consumer.
The caller owns timestamp units, physical clock, retry policy and PSG writes.

## Validation

`python tools/validate_psg_queue.py` compiles the same contract test for the
host and68000 and executes the latter in PAL/NTSC. Each runs705805 checks and
119273 events, with zero failures. Cases include capacities1/2/4/8/16, exact,
future and overdue deadlines, equal-time ordering, both wraps, invalid inputs,
corrupt cursor distance and atomic rejection. Randomized batches compare
against a separate linear FIFO using nonwrapping relative time. Host-only
testing also fills and drains the maximum32768-entry capacity three times;
that storage size is intentionally not allocated on Mega Drive.

A second compiled test runs a real emulated VINT callback while the main loop
produces variable-size batches. The producer retries FULL; each batch shares
one captured deadline. The callback checks byte sequence, due time and an
end-of-batch marker when it stops draining. Each region consumes12000 bytes
with zero failures. NTSC completes in5147 frontend frames; PAL in4559,
including the sequential contract test. This uses frame ticks solely as a
test clock and makes no subframe delivery accuracy claim.

The first interrupt-test draft sampled `vtimer` separately for each byte.
An interrupt could then split the nominal batch's deadlines over two frames,
invalidating its end-marker assertion. Capturing a single deadline before
filling the test batch fixes that fixture assumption; queue code is unchanged.

## Remaining integration

The native audio routines still return byte lists without semantic per-byte
timestamps. Those timestamps need to be derived from the original instructions
and checked against the new source port oracle. They must not be loaded from
retained test fixtures. A physical subframe clock/consumer, global source-entry
phase propagation and combined producer/consumer CPU budget also remain open.
No physical PSG writes occur in this queue test. The thin NTSC video budget
from the previous milestone is not enlarged by adding this infrastructure.

Source, generated tests, compiled diagnostic ROM and logs are preserved under
`analysis/psg-queue-v0203/`, with hashes in its manifest. No full emulator save
states were generated. Numbered playable ROM archives remain unchanged.

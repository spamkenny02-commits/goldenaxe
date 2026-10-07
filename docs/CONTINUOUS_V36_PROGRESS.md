# V36 — faithful bulk shadow transfers

VDP writes now compare/copy fragments within one 32-byte pattern boundary.
Unchanged fragments stay clean; changed fragments preserve exact pattern,
name-row, SAT and sprite-status invalidation. VRAM and CRAM addressing wrap as
before; command latch, code, read-buffer behavior and zero-length writes remain
equivalent. A source inside VRAM/CRAM uses scalar writes so overlapping copies
observe prior bytes exactly as the original port API does.

Queue copies use contiguous ROM/RAM spans, split at bank and mirrored RAM
boundaries. Platform SRAM reads remain scalar. Vertical screen animation uses
the same block primitive. The MD freestanding runtime/header now supplies
memcmp, so this does not introduce a dependency on a host C library.

The 4,274 ROM-free hardware comparisons execute both old scalar writes and the
block path, comparing all shadow bytes, registers, exact dirty state and port
state probes. They cover wraps, boundary/large lengths, partial command latches,
all codes, aliasing and unchanged data. Normal, ASan and UBSan runs pass.
Every existing original-game local regression/differential target, sanitizer
suite and the compiled completion gate passes too. Leak checks are disabled
locally for the documented process-inspection restriction.

The native build passes actual ELF/vector/RAM/header checks: 475,604-byte ROM,
BSS 31,514 at FF0000-FF7B1A, checksum 7F7F. Emulator boot/audio/300 gameplay
frames pass; idle advances 148 game updates versus V35 136. The controller
exit route uses 721 gameplay physical frames instead of 947, with both SMS and
MD recording 346 gameplay updates and ending at cell 94, position [56,104],
HP 24 and state 0C. Attack, Pause, inventory and movement also pass.

Profiling now includes hot instruction addresses. The large gameplay bucket
contains an inlined frame-wait loop; it is not evidence that gameplay arithmetic
grew slower. The physical adapter's all-512 dirty-slot scan is the next measured
cost to reduce, along with three-plane tile expansion. Cadence remains short
of original SMS speed. Full-game replay, sprite clipping and hardware validation
are still open. Private ROM/images/captures are not committed.

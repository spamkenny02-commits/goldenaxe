# V18 — native display transition prerequisites

Continued directly after the V17 checkpoint. Lifted palette fade-in $0AA4,
fade-out $0B12 and the sixteen-ring world reveal $1FA7 into ui.c, using the
portable video shadow and platform frame boundary. The RGB component order,
two-frame waits, display-register updates and each ring's write order match
original execution.

48 unaccelerated original Z80 comparisons cover three routines, four palette
patterns and four display-flag combinations. Input and Pause events occur
during the transitions. Each frame compares RAM C000-DF7F, all VRAM and VDP
registers; final CRAM and elapsed frames are also compared. The transition
suite passes strict C11 and ASan/UBSan. Existing differential suites and
portability/MD structure checks were rerun.

These routines prepare main state 08 ($24B6). That complete state is not yet
registered as native: its scene selection, loading, entity initialization and
presentation still need an integrated differential test. Main-state coverage
therefore remains 3/12, with one instruction-bridge call site. Six MD hooks,
original IRQ/video queue/audio equivalence and a linked/play-tested MD build
remain outstanding. Frame comparisons use the shared IRQ replacement.

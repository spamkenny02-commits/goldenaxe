# V25 — Native ending and credits

Lifted main state 0E ($6EBE), including waiting for remaining enemies,
palette animation, Arthur centering, final item graphics, nine-crystal
reveal, staged blackout and the credit-line parser/VDP ring-buffer scroll.
Main-state registration is 11/12; title/intro (00) remains bridged.

Validation: four full original-instruction comparisons, including both world
palette modes, already-centered/moving Arthur and Pause events. RAM outside
the reference Z80 stack, complete VRAM/CRAM and VDP registers are compared
after each shared frame; final SRAM and exact frame totals match. The moving
cases exposed a missing player walk-pose advance at $3309. This now follows
the original after both blocked and successful movement attempts.

Strict regression tests, ASan/UBSan for the ending, portability and MD source
checks pass. The full original IRQ/audio is not yet integrated; frame tests
continue to share the native video/input tick. No linked or play-tested MD
ROM is claimed.

Next: title/intro, audio/IRQ, remaining presentation hooks and console build
and integration validation. Work continues without a phase confirmation.

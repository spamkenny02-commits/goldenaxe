# V26 — Native title/intro and the first 68000 link

All twelve main states now dispatch high-level C. Lifted the complete
introduction ($0C98), scripted scene changes, text timing, actor animations,
palette transitions, title animation ($146D) and new/continue picker ($14ED).
C skip propagation replaces assembly stack unwinding; C02A is obsolete SP
metadata and is excluded explicitly from the differential comparison.

Twenty complete original-instruction comparisons cover attract mode, five
skip points, new-game selection, all three saved slots on both SRAM pages,
empty-slot refusal, button cancellation and cursor-selected cancellation.
RAM/VRAM/CRAM/registers match every shared frame; SRAM and elapsed frames
match at return. Intro ASan/UBSan and impacted strict regression suites pass.
A host boot integration test reaches title, name creation, new game and
24 gameplay updates with no instruction interpreter linked.

The MD production build also excludes sms_compat.c/recompiled.c. GCC 14.2.0
cross-links a 427,470-byte ROM with 25,148 bytes of BSS. Inspection caught a
critical linker problem: an empty .data did not advance the location counter
to work RAM, so BSS followed ROM text. Explicit memory regions fix this:
actual ELF checks verify every mutable B/D symbol at FF0000-FF623C, reset
entry 000200, and absence of interpreter symbols. Header/checksum checks
pass (checksum F87C). Added freestanding memmove and fixed toolchain archive
extraction for workspaces that cannot preserve upstream owner IDs.

This is a verified native link, not a console playability claim. Five platform
presentation hooks, original full IRQ/audio and full-game integration remain.
Frame comparisons still share the native video/input tick. Next: audio/IRQ,
remaining presentation hooks, emulator and hardware validation.

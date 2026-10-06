# V28 — Full native IRQ and audio integration

Lifted $0038/$0137 and all three line callbacks into irq.c. The status read
acknowledges pending flags and the half-written VDP command latch. Synchronous
VBlank presents video, advances native audio, samples input/Pause edges and
updates timers/frame count. Asynchronous VBlank advances audio/timer only.
NMI preserves the original 20-count Pause debounce.

3,072 independent raw-original IRQ cases compare RAM C000-DF8F, complete
VRAM/CRAM/registers, status reset and ordered PSG/stereo writes. Cases cover
both DE03 modes, collision/overflow status flags, half-written VDP commands,
all three line callbacks, music/effects, inputs, Pause counts, timer boundaries,
frozen palette/HUD uploads and queues. All 256 NMI counter values match.
IRQ ASan/UBSan and the 144,384-update audio suite pass.

Game sound commands now enter their original DE06/DE08 request slots. Two
world waits now set C02E through the synchronous barrier. Integration exposed
collapsed linked-room wipes and room-return fades; these use their complete
native UI routines. Impacted gameplay, entry, menu, service, ending, inventory,
effect, scene and UI regressions pass. Interpreter-free boot produces PSG
writes and reaches gameplay with no audio diagnostics.

The native-only 68000 ROM cross-links at 432,418 bytes, BSS 25,152 bytes in
FF0000-FF6240, reset 000200 and checksum FB5E. Header/ELF checks pass. These
are instruction-independent C IRQ semantics; MD asynchronous/line scheduling,
five remaining hooks and emulator/hardware validation are still outstanding.

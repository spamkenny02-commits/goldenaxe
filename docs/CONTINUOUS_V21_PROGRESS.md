# V21 — native synchronous IRQ video and transfer queue

Lifted video presentation $013E-$0199 and queue $0293 into presentation.c.
The portable frame tick now uploads scroll/line registers, SAT, pending
three-plane resource data, HUD strips and palettes, then consumes queued
block and rectangle transfers. Frozen frames preserve their original palette
and HUD suppression. The queue resets C034/DD00 and consumes rectangle row
counters. Zero block/row counters retain their original 256-iteration meaning.
Block groups contain 32 bytes because OUTI and DJNZ both decrement B.

The Mega Drive frame barrier now generates these shadow updates before copying
the shadow to its physical VDP. This makes queue/palette changes visible in
that barrier instead of waiting for the following shadow upload.

256 isolated comparisons cover the queue alone and the original IRQ video
block, frozen/unfrozen frames, four HUD phases, pending glyph resources,
empty/mixed queues, ROM/RAM/primary-page SRAM transfers, rectangles, wrapping
and zero counters. RAM C000-DF7F, all VRAM, CRAM and VDP registers are checked.
The original video-block test runs actual instructions and stops at $019C;
VCounter is fixed at $F0 to allow the scanline barrier to complete. It does not
execute the audio or input parts of the IRQ and is not a cycle/timing proof.

All strict differential/regression suites were rerun after frame integration,
including 4,148 entry cycles, 6,144 entity-resource cases and 128 death menus.
The transition fixture now initializes a valid video queue before its frames;
its previous arbitrary RAM pattern was not a valid queued-command precondition.
The complete ASan/UBSan target also includes the presentation suite. Original
ROM data remains local and ignored.

Main coverage remains 7/12, with five bridged states and five empty MD hooks.
IRQ status/line/asynchronous paths, audio, complete-game integration and a
linked/play-tested MD build remain. Isolated video comparisons establish this
block's tested behavior; frame suites still share the native video/input tick.

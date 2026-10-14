# Dungeon key-door dispatch - v0042

ROM: [gaw-megadrive-v0042.bin](../versions/v0042-2230c2b4/gaw-megadrive-v0042.bin).
SHA-256: `2230c2b4badf9c0086cfcd0fd2ca45cea0e8942a79631252ee24306ddd8409ff`.
Size: 524288 bytes. Additive checksum: `CF95`.

The native gameplay loop now calls the translated 5BB4..5C93 key-door dispatch.
Held up/left/right input, facing direction, exact wall position and original
map collision attributes determine whether a locked passage can open. Ordinary
keys decrement; item C0EF (native item 15) acts as the master key. The source
consumes the ordinary key before its empty-marker guard; this order is retained.
Opening updates the current room's persistent flag and, for side passages, the
opposite flag in the adjacent room with horizontal nibble wrapping. The current
map is rebuilt from its existing cells, preserving other cell changes, and
requests source effect A5. Base map reconstruction was factored for reuse.

The separate source fixture runs original 5BB4..5C93, 1976 and 1DE2 on all 512
rooms with sixteen direction/key/master-key configurations. It bypasses only
the isolated IRQ barrier at 0B95, keeps VDP IRQs disabled, initializes HUD
statistics and preserves the original key dispatch and redraw code. The native
harness includes exact production source copies and invokes their dispatch.
All 8192 cases match playable cells, SMS map words, all 256 persistent room
flags and remaining keys. Source execution records 180 openings and 120 key
consumptions. The cases include empty inventory, one/two ordinary keys, master
key with five ordinary keys, downward facing, and non-door terrain.

The independent 8192 persistent-map comparisons still pass after factoring the
map builder. PAL/NTSC dungeon entry/exit, dungeon scrolling and movement timing
regressions also pass. Eight reports are bound by the
[audit](../versions/v0042-2230c2b4/key_doors_patch_audit.json).

Live controller integration, repeated contacts, crossing the opened passage,
returning through the opposite side and save/Continue persistence still require
verification. These fixtures directly call dispatch with controlled inputs;
they do not establish natural dungeon progression. Native audio waveform and
source redraw latency are not compared. Room-clear triggers, remaining puzzle
scripts, enemies, bosses and ending remain incomplete.

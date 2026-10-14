# Ending source reference and native credits module, based on v0152

Previous goal turn fixed source0940 object order in v0152. This turn advances the missing complete ending. Production ROM remains v0152; no new game ROM is claimed to contain the ending yet.

Source main state table00DC selects6EBE for game state14. Final boss death4BA4..4C5C sets14 only when dungeon numberC037>=10. Actual14C resource entry through controlled neighboring-room scroll does not itself change the dungeon number; the reference fixture explicitly seeds10 when injecting final death. This prevents confusing a final-boss resource test with natural final-dungeon progression.

Reference fixture: enter a dungeon doorway after exterior relocation, relocate to14B boundary and use normal right scrolling into actual14C. HP24/hurt255 protect setup. At3700 set dungeon10, replace actors with one type7 death-state0 at128,72, and place hero168,112/hurt0/HP24. No later RAM/VRAM mutations occur. Original death, particles, automatic movement, gem display, terrain clearing, narrative/credits and final wait execute normally. C at19000 returns to title. Both PAL/NTSC enter14 at3881, begin credits at4893, finish them at12317 and return at19000. These are controlled reference timings, not natural victory or native equivalence.

Original sequence:

-6EBE clears hero hurt, repeatedly runs24F3 until non-hero recordsC330..C8D0 disappear.
-6ED8 clearsC0AE, waits216 palette ticks through70C8/70D4, sets hero state0, walks Y to80 then X to128 using forced cardinal input and24F6.
-6F15 requests music8D, loads gem bitmap5 at VRAM3780, chooses hero descriptor8495/pose1 and bank4:A241 bitmap. It clears nine actor records and initializes type6 gem descriptors2ACD at radius40 using original044E/0450 trigonometry. Each of nine display flags becomes1 after four waits plus the following palette wait: observed4157/4162/...4197 NTSC and4158/...4198 PAL.
-6FAB waits240+120, requests music88, then clears eleven palette slotsA0,A2..A7,AC..AF, waiting30 IRQs after each.
-6FCE fills the name map with08FF, uploads it, expands the credits font at1600, changes hero descriptor84E1/pose0/baseBC and rebuilds sprites.
-7004 copies bank12:B34E length0500 toC900, initializes eight-byte stateDCC0..DCC7, and runs7061 plus7027 fractional scroll. Each tick adds0030, advances vertical scroll by its integer carry modulo224 and emits a row when bit11 changes. Rows wrap7EC0->7800 over28 rows. Negative text bytes insert blank rows; a zero terminator sets done. After completion only a new B/C press acknowledges and resets main state0.

ending_data.c exports the original1280 text bytes and80-character reverse-search glyph map. The native text array adds one zero sentinel modeling the cleared source RAM immediately after the0500-byte copy; this is not replacement text. ending_credits.inc translates7061 row composition and7027 fractional arithmetic. These files are not yet included in the production ending path.

Standalone original/native harness comparison passes7425 snapshots: all eight state bytes, vertical scroll and all64 bytes of the last emitted row match at every tick through the entire narrative/staff text and final done flag. Source7061 glyph lookup/spacing/row wrapping and7027 arithmetic execute unmodified. Only0384 VRAM transfer is redirected to capture the same64 bytes in RAM, and7048 IRQ/outer-loop tail returns for single-step observation. Native test runs compiled68000 code, not a Z80 interpreter. Final state is FF010070C07801CE30. No arithmetic, glyph or random shim is used.

Next: integrate6EBE orchestration with the real native world loop while preserving the source render/IRQ phase; port forced centering, nine-gem placement/show cadence and palette erase; connect row writes to native28-row background scrolling, credits font/resources and music8D/88; verify source/native scene resources, complete runtime timeline and B/C return. Full natural final-dungeon progression and victory remain unproved.

Other full-port gaps remain: source auxiliary object records, original RNG/global clock, absolute loading/hidden-animation phase, SMS per-scanline clipping/flicker, inherited loot-expiry presentation, remaining quests/save/audio hooks, complete framebuffer/audio equivalence, hardware and a natural complete playthrough. Goal remains active.

# Internal portal source reference — production still v0051

The original SMS 5CFB..5D4B transition has now been exercised for all 36 script entries in both NTSC and PAL: 72 controlled source cases. The original user ROM and the local input copy have identical bytes. The profiling core adds read-only instruction/cycle hooks; it supplies no gameplay behavior or modified ROM instructions.

Origin maps with the solved class flag (4) were captured by executing original 1976/1A7C/1BCD/2279, rather than guessing which blocks reveal stairs. Fixtures seed that flag, the captured map, hero position and a frozen actor after a real dungeon entrance. Controller input from an adjacent traversable tile then enters the portal. This establishes portal behavior for these states, not natural puzzle completion or travel through the game.

Confirmed source sequence:

1. 5CFB requires C0A6 bits 4+5 and the exact pre-movement C060 coordinate. It removes the script return address, so subsequent suffix handlers are skipped on success. Prefix handlers before the portal still execute.
2. 18E2 saves the current eight primary actor occupancy bits, then switches the room id. The fixture leaves the first primary actor alive, yielding the expected source mask 80 in the origin room.
3. 1F78 requests sound A6. It performs twenty waits with the live IRQ, wiping the whole 32-by-24 nametable with word 18FF. Step n starts at word n and advances by twenty words, up to the 7E00 boundary. This includes the HUD. It then disables the display and clears the SAT.
4. 2260 selects the destination palette, decodes/prepares its map and rebuilds its software tile map. The destination visited flag is set.
5. The first cell 0C determines arrival: x=(index&15)*16+8, y=(index&F0)+16. Without that cell, the fallback is 128,88. Only high position bytes are written; fractional bytes survive. The hero faces down. The source changes to state 8, which performs the full room/actor initialization before state 12 resumes.

The Python translation of the wipe algorithm matches all 1440 complete frame maps (72 cases times twenty frames), not just blank-tile counts. The audit checks original loop addresses, cycle markers, source arrival positions, destination flags and origin actor masks. It starts each wipe from actual VRAM at its first wait, preserving preceding combat-shutter redraws and floor animation.

Room 1A7 illustrates ordering: its shutter redraw delays the portal trigger from frame 3414 to 3419 NTSC / 3418 PAL. The portal returns at 3443 / 3441 respectively. Ordinary cases in this fixture trigger at 3414 and return at 3437. Room initialization after that return varies with destination assets: 8..39 further NTSC frames or 6..32 PAL frames in these samples. A single fixed transition delay would be wrong. Foreground cycle measurements still include non-IRQ busy waits, so they cannot all be treated as region-independent asset costs.

Reproduce with tools/capture_portal_prepared_rooms.py, tools/profile_portals.py (and --pal), then tools/audit_portal_source.py. Evidence and the matching tools are preserved under analysis/portal-source-v0051. The current ROM remains v0051; this is source research and no native portals have been enabled yet.

Next implementation: emit the 36 coordinate/destination records, dispatch prefixes and suffixes in exact source order, reproduce the verified twenty-step wipe, keep the display hidden during destination preparation/actor loading, preserve fractional arrival position and reset transient objects, then compare settled maps, palette, flags, actor masks and transition timing to this reference. The native loader must account for destination graphics work rather than reuse an instantaneous room switch. Other puzzle scripts, natural progression, bosses and ending also remain incomplete.

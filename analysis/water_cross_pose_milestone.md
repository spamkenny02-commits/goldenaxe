# v0092 - water departure pose preparation

The source 2C63/369F initializes the arrival animation using the departing terrain context. 2C8D subsequently classifies the arrival terrain. The resulting bitmap is published at a following IRQ. Previously native reset animation immediately after scrolling, before the actor graphics loading interval, and retained the old context through the first resumed iteration. This displayed the wrong water pose throughout loading.

Arrival preparation is now deferred until the end of that loading interval. It prepares the water bitmap before changing context, and skips a duplicate end-of-iteration preparation. PAL vertical exits retain a separate publication/gameplay continuation phase; horizontal exits complete in the same preparation iteration. The right NTSC exit initializes the animation one IRQ before completing bitmap preparation, following the original right-exit continuation.

## Current evidence

Eight controlled all-water software-map departures were compared with the original SMS, four directions in PAL/NTSC, for 151 frames each. Down/left/right pass in both regions: game state, room, position, velocity, animation, context and four actual hero VDP patterns match frame by frame. During these six transitions the actual sprite lists match and contain exactly four hero sprites, with no departing enemies.

The v0089 down-departure diagnostic previously had 27 differing hero-pattern frames NTSC and 24 PAL. All 51 differences disappear in the same controlled sequence. This is bounded evidence; it is not a natural water route or whole-image comparison.

The existing 54 within-room water cases, 44 spell cases and ordinary movement/three scroll-direction/eight deterministic-enemy checks are rerun on the final binary and bound by the audit.

## Unresolved

Both up-departure cases still differ in scrolling/preparation timing, hero state and some patterns. They remain explicitly listed in the diagnostic and pose report. Six passing directions do not validate the two failing up cases.

Native mutable cells are published one frame early in NTSC. Native software-map buffer staging also differs while scrolling; this change does not resolve those memory phases. Post-arrival enemy sprites can differ and are outside the four-hero-sprite transition assertion. Full rendered images and audio have not been validated.

Read-only original-Z80 profiling records 2260/190B, 24C5, 1780, 18E1 and 24ED. For the upward destination room 85, actor graphics work spans 2,001,677 foreground T states; source loader control begins at frame 2853 NTSC / 2850 PAL in this fixture. The existing native loading budget alone does not model the earlier upward swap/transfer phases. See water_cross_source_timing.json; these observations are research evidence, not captured-state playback in the cartridge.

Natural shore traversal, equipment acquisition, combat, remaining abilities, full enemies/bosses, quests, ending and complete playthrough remain unfinished.

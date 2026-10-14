# v0097 - correct house animation destination

The SMS 6A41 instruction loads the house animated-pattern destination from C9E0. The native metatile buffer starts at C900, so the equivalent offset is E0. animate_house_room used 1E0, selecting tile 130 in the first houses instead of tile 61. This left the intended animation static and wrote the original four animated patterns into unrelated tiles.

Only the destination lookup changes. The original bitmap resource, cadence and delayed publication are retained. Four comparisons use the normal controller routes to houses 0 and 2 in PAL/NTSC, align the native video clock once at frame 3300, and compare four actual VRAM tile pixel arrays for 118 consecutive frames. Both source animation poses are observed. Previously 59 frames per case differed; all 472 frames now match. This is bounded local animation timing evidence, not global timing equivalence.

The six inventory-return cases continue to compare all static background tiles among the first 124 before/after the menu. Their four source-animated tiles are located through C9E0 and kept separate; natural global clock phases can differ. Earlier pre-menu full-pattern equality was coincidental while the native animation was frozen. Static equality is required before and after the menu, and raw animated differences remain in the report. First-merchant transactions/refusals and its natural controller route are rerun.

All houses, complete rendered framebuffers, audio and natural global animation phase remain unverified. Full game progress, bosses/quests/ending and scrolling arrival timing are still incomplete.

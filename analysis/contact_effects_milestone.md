# Contact effects — v0051

ROM: versions/v0051-3161f829/gaw-megadrive-v0051.bin (512 KiB, checksum C36F).

Eleven original contact handlers are now translated to native 68000 C, in their original order before shutter/clear suffixes:

- Seven 5C96 scripts: stationary, aligned, unchanged direction, facing UP with UP held, and an exact C060 coordinate. The current class-specific persistent bit is written before the already-triggered guard. D selects top/left/right flags in the room identified by E, which is often a different room. The current room then redraws with its persistent transformation. Side neighbours use the original nibble wrap.
- One 5CC7 script in room 173: the same UP gate at coordinate 0168, opening the right passage if its cell is nonempty, then setting DC1B to 4D and updating its two-by-two tile rectangle. DC1B == 4D prevents repeats. This routine does not mark the generic class bit.
- Three 5CEC scripts: when a specified cell becomes zero and the persistent class bit is clear, mark it and attempt to open all currently blocked passages. This condition is independent of enemy count.

Generated room_contact.inc stores operands decoded from original script instructions; there is no Z80 runtime in the production game. Internal portals remain absent.

Validation on this exact ROM: 8192 isolated original-script cases compare 160 cell bytes, 1280 map bytes, all 256 persistent bytes, keys, enemy count, shutter state/direction and all 336 loot bytes. The scripts execute twice. Cases cover stationary gate positives, missing UP, wrong direction, changed direction, movement, misalignment, wrong coordinate, existing flags, nonempty cells, an empty right passage and final-clear suffix ordering. Ninety cases request the original redraw effect; no key is consumed.

Live fixtures cover all eleven rooms twice (new and already-triggered), in NTSC and PAL: 44 cases. A real dungeon entry precedes controlled room/hero/frozen actor setup. Stationary contacts use controller UP. Empty-cell scenarios inject the cleared cell and corresponding map, so they do not prove natural block destruction. All settled cells/maps/flags/loot/count/keys match. New effects are observed at frame 3410 except the room 173 marker, which follows its door redraw at 3415 NTSC / 3414 PAL on both systems. Existing triggers remain consumed.

Regression evidence: 20 live combat-door scenarios, 18 key-door crossing/return cases and bounded hero, scroll and deterministic enemy timing in both regions. A visual spot check of room 173 confirms the updated room renders on both systems, without claiming full pixel equivalence. contacts_patch_audit.json binds nine current reports to this binary and checks source copies, generated metadata and prefix/suffix order. It also proves the production delta from v0050 is confined to the new contact metadata/effects and their dispatch call; other production source files are unchanged.

Remaining work: 36 internal portals (including room load, hero placement and timing), other puzzle scripts and movable blocks, natural dungeon progression, remaining AI, quests, bosses and ending. Full visual/audio fidelity and generic IRQ/loading phase remain unverified. The live fixtures are not an end-to-end game completion test.

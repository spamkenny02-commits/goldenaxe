# Clear rewards and key collection (v0048)

ROM: 512 KiB, SHA256 e796cfbe1b6d15a67200953b17ab67546d9ce111a15c554da513f7eb15849b3c, checksum ACBC.

## Native behavior added from the original routines

Three more script targets are decoded from B762: 5E75 marks the graphics-class reward flag and redraws transformed cells (also creates a key in room 113); 5E9C marks bit 3, opens blocked passages through 5E57 and creates a key; 5FB1 marks the graphics-class flag and redraws. They apply to 20 rooms: nine exterior 5FB1 scripts and eleven dungeon scripts. Together with the 49 passage-clear handlers, native dispatch now covers 69 clear events. Contact-gated script prefixes remain separate work.

All consume C0A2 zero by setting 80, even when the persistent reward flag was already set. Existing flags suppress duplicate rewards. Exterior flags use bit 0, dungeon transformations bit 2, and 5E9C uses bit 3. Reward flags are stored before redraw/key appearance, matching source ordering.

Original 5EE1 searches six transient slots and falls back to overwriting slot six when all six are occupied. Only type/state/flags/Y/X are initialized; other record bytes are preserved. The native factory matches that behavior, including a fully occupied seventh record.

Source key behavior 2A3A..2A6A is now implemented for transient type 14: tile 96 and descriptor 84CE, collision armed only when the hero is walking/idle in state 1, and no ordinary-loot expiry timer. Collection runs through the existing contact mechanism, clears the record, requests effect 96 and increments keys only below 99. This also enables collecting type-14 keys from existing random drop tables. RNG fidelity itself remains incomplete.

The existing full redraw is factored into a shared routine; its approximate foreground/VBlank schedule is retained. This cartridge runs native C/68000 logic; no Z80 interpreter is introduced.

## Evidence for this build

- 8192 source/native clear configurations across 512 rooms, four counter states and four flag/allocation configurations. The 69 original script paths execute with unrelated contact prefixes disabled. Cells, maps, all flags, counter, keys and all 336 transient-record bytes match. Dispatch is repeated twice. The configurations include empty, partially occupied and fully occupied loot slots, and already-rewarded flags.
- 8192 original/native key-door regressions: 180 opening cases and 120 ordinary-key consumption cases.
- 32 live final-particle/reward cases, 16 per region. Rooms 113/131 test inventories 2, 98, 99 and 255; room 1B5 tests a redraw reward without a key. Already-rewarded guards are tested in all three rooms. The particle uses type 66's zero-drop table to exclude provisional RNG differences.
- Room 113 uses controller UP for collection. Room 131 starts the hero at the reward centre because the direct path from Y128 is obstructed; this does not prove natural access to that key. Source/native settled cells, maps, all flags, full loot records, counter and keys match.
- An idle case in each region keeps the uncollected key present through frame 4000, 596 frames after appearance, beyond ordinary loot expiry.
- Actual earned room-113/131 flags and key count 3 are transferred to the normal village save route. Two cold reloads preserve all 256 room flags and keys. Source/MD save payloads match over all 592 bytes in both slots. Uninterrupted dungeon-to-save-point travel is not implied.
- Twelve original clear-passage live cases and eighteen key-door controller cases still pass. Exterior movement/scroll and eight controlled enemy movements remain exact in the existing timing comparisons in both regions.
- Visual inspection of idle room 113 captures confirms the key is rendered on both consoles; full sprite compositing/pixel fidelity is not asserted.

Eleven reports plus the audit are archived with this ROM. The intermediate v0047 build is retained but explicitly marked incomplete; use v0048.

## Remaining work

5ECD combines a key reward with push-block passage state and remains unported. The next step is to port C0A8/C0A9 block/passage state, contact-triggered openings/closures and 5ECD rewards together. Full natural routes, other quests, bosses and ending remain incomplete. Loading/redraw timing is approximate, with previously recorded one-frame horizontal and multi-frame upward offsets; audio waveforms and complete transition pixels remain unverified.

# Dungeon scrolling - v0040

ROM: [gaw-megadrive-v0040.bin](../versions/v0040-a4f0f052/gaw-megadrive-v0040.bin).
SHA-256: `a4f0f052ea5cb60c04f60c0dcae01245099b920464fa83e14eb198d2b2743122`.
Size: 524288 bytes. Additive checksum: `9AA9`.

The production 68000 cartridge now allows class-2 rooms to scroll in all four
directions. Original Z80 routines 21C5/21CB update only C0B9; C0BA retains the
dungeon layer. Native neighboring-room arithmetic now preserves this bit,
including horizontal nibble wrapping and vertical low-byte wrapping.
House scrolling remains disabled. Before the destination map scrolls, the
native code selects its dungeon/dark palette following bank-5 BE78 and marks
the destination visited following 1BCD. Existing object hiding and persistence
run for dungeon transitions as well as exterior transitions.

Sixteen controlled production transitions pass against the original ROM:
four directions from rooms 1F0 and 1F8, in NTSC and PAL. The exterior map and
starting position are fixtures; normal controller input opens the actual
dungeon entrance, then a controlled edge position triggers the actual scroll.
Targets include 1FF (horizontal wrap), 100/108 (vertical wrap) and dark rooms
1F7/1F9. First resumed room, hero position, 160 cell bytes, 1280 SMS map bytes,
thirteen fixed palette colors, visited flag and all 256 persistence masks
match the source. Two frozen visible actors, including an auxiliary slot,
exercise hardware sprite-table disappearance during scrolling; none remain
visible in the checked scrolling frames.

Twenty entrance/exit regression cases, eight exterior object-scroll cases and
existing movement/enemy timing comparisons also pass for the same ROM.
[Audit and eight bound reports](../versions/v0040-a4f0f052/dungeon_scroll_patch_audit.json).

This does not establish a complete playable dungeon. Conditional cell changes,
room metadata and puzzles, keys, quests, remaining enemies, bosses and ending
remain incomplete. Lantern activation and complete tile animation are pending.
Natural routes through the dungeon and full transition pixels are unverified.
Some setup/loading durations differ: gameplay resumes up to three frames early
on NTSC and two on PAL in these fixtures; horizontal cases match or resume one
frame early. No room-specific timing constants were introduced to conceal this.

Next: port room metadata 1976, persistent conditional cell transformations
1A7C and dungeon door flags 1BCD, checking original Z80 execution before
claiming puzzle or key progression.

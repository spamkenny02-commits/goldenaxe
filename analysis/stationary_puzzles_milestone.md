# Stationary puzzle milestone - v0056

ROM SHA-256 e969452902935eca93d236542d0a8048a2859e0918693c3b8ae59f19c611147c
512 KiB, checksum 6346. v0055 retained as an intermediate build.

31 original room scripts are now dispatched natively: seven 5E29 redraws,
three 5DEE remote persistent flags, one 5E01 key, six 5E0D passage openings,
and fourteen 5E45 marker/blocked-passage scripts. All require stationary UP
(flags & 77 == 14) at the exact original coordinate. Persistent bit 4 is
written before the repeat guard. Rooms 129/16C/1EB retain their original
suffix order. Room 16C's moving portal can discard the stationary suffix.
All fourteen 5E45 rooms use transformation 9; marker software-map/VDP
updates also occur when all edges were previously opened.

Evidence bound to this ROM:
- 496 selected script fixtures (31 rooms x 16 input/coordinate/flag/loot
  combinations), each executes the original script twice; 7696 other
  cases check nonselected room setup. Cells, software tile maps, all 256
  flags, keys, enemy count, shutter state/direction and 336 loot bytes match.
- 124 live cases (31 rooms x initial/repeat state x NTSC/PAL), controlled
  room/hero/frozen actor setup after a real dungeon entrance, then actual
  controller UP. Final states and trigger frame match.
- Four portal regressions: 14B and 16C in both regions; loaded state and
  twenty visible wipe frames match. Loading latency is reported separately.
- Existing bounded hero/scroll sequences and eight deterministic enemy
  motions still have zero differing state frames in both regions.
- Audit reconstructs the exact v0054 main by removing only the new helper,
  table include and two dispatch calls; all other production files match.

Not a complete-game validation: natural dungeon routes/combat, ten 5D59
item-message rewards, all bosses/quests/ending, full pixels, waveforms and
redraw latency remain incomplete or unverified.

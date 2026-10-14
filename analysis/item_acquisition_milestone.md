# Item acquisition milestone - v0060

ROM SHA-256 b2742e8311c22e93fcc49693b9332a5e0d13de95af0a85ca72712419f6d51fd6
512 KiB, additive checksum E49E. Intermediate builds v0057-v0059 retained.

The ten original stationary 5D59 item scripts now run natively. Exact UP,
alignment, coordinate and persistent-bit repeat guards precede the grant.
The room flag is set before checking weapon ownership in 1B6. Room 11D
sets weapon level 2; 1B6 sets level 1 only when the player has no weapon.
Other rooms grant torch, ice bell, airship, canoe, magic rope, running boots,
master key and ship. Granting an item does not imply all its abilities have
already been ported.

6317 frontend: original item-name strings and charset, bottom five-row frame,
held-object hero pose, original item icon and six hero tiles, music command
8C, minimum 180-frame wait, directional/B/C confirmation, room/music/HUD
restoration. New resources are original ROM bytes, not captured images.
The production source is 68000 C/SGDK; it does not execute a source Z80 CPU.
Message opening/closing latency and sound waveforms are not yet proven exact.

Evidence:
- 160 selected original/native grant fixtures, sixteen combinations per room,
  each called twice. Inventory, all 256 flags, cells/maps, loot and keys match.
  8032 additional cases compare nonselected room setup. The unit SMS fixture
  retains 6317's item-number write and stubs the remaining modal frontend;
  the native unit fixture calls the same production grant helper directly.
- 44 live PAL/NTSC cases: ten first/repeat rewards plus 1B6 owned-weapon
  levels 1 and 2. Room/hero/frozen actor setup is controlled after an actual
  dungeon entrance. The controller triggers the scripts and confirms them.
- 20 stable reward windows: 3000 visible VDP words, 760 decoded tile pixel
  patterns and 160 held-pose sprite entries match source hardware state.
- Ten earned inventory/room-flag snapshots transferred to the existing save
  route, saved with normal controller input and cold-loaded. All 592 payload
  bytes match SMS; the full route back from each dungeon is not established.
- Existing bounded hero/scroll and eight deterministic enemy-motion timing
  comparisons still have zero differing state frames in both regions.
- The audit restores the exact v0056 main by removing the item helper block,
  include and dispatch call, and verifies all other prior production files.

Known remaining floor phase differences after confirmation at frame 3900:
NTSC room 157 (one cell), 19B (two); PAL 19B (two), 1A9 (one). These cells
remain within the original 41/4E/4F/50 animated-floor sequence. Other cells,
software map words, inventory, flags, loot and music commands match. The
complete 6A66 bitmap animation/workload is still unported; the precise cause
of these phase offsets is not yet established.

Full natural progression, all item abilities, quests, enemy/boss behavior,
ending, complete visual sequences and audio waveform fidelity remain open.

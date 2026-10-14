# Dungeon bitmaps and reward recovery - v0063

ROM SHA-256 62366fff149b56f25a62b8e10bdd13615bdef58efa3548362ab3ac857bf2f07b
512 KiB, additive checksum 3C76. Intermediate v0061-v0062 retained.

The native 6A66 animation now replaces six dungeon tile bitmaps every eight
world-clock ticks, using the original three poses in order 0,1,2,1. The
source queue bank FF selects SRAM: the data comes from the original RLE
stream at 2F55F..2F6C8, decoded by the source into SRAM 9000..93FF.
The generated C asset contains the first 576 decoded bytes. Tile conversion
and deferred VDP upload use the existing native renderer; room loaders
discard a pending upload when changing rooms.

The item-message recovery now accounts for source 637D..638A clear/HUD work
before the existing full-room redraw. Foreground source costs measured in
rooms 157,19B,1A9 are 324139..324168 Z80 T-states in NTSC and 333564 in PAL.
These include the source's VBlank wait; they are a frame budget model, not
proof of exact instruction phase on the Mega Drive.

Current-ROM evidence:
- 8192 isolated source/native cases, including 1024 actual source SRAM-to-VDP
  uploads: all 192 pattern bytes and native pending-upload values match.
- 93 consecutive live bitmap frames in each region match all six patterns
  after explicitly synchronizing the source/native clock once. All three
  poses are covered; natural absolute clock phase is not established.
- Three reward rooms per region: first floor resumption matches in four
  cases; two NTSC cases resume one frame early. Steady scan/phase is exact
  in PAL and one frame early in NTSC, compared over 180 frames per case.
  Previously the first resumption was four to five frames early.
- 8192 item-grant fixtures, 44 controlled live item cases and 20 stable
  item-window VDP/SAT comparisons pass on this ROM. The ten save/cold-load
  comparisons remain evidence from v0060; they were not rerun for v0063.
- Existing bounded hero/scroll sequences and eight deterministic enemy
  motion comparisons still have zero differing state frames in both regions.
- The patch audit binds all ten reports, source assets, measured source
  timing profiles and current production files. Removing this patch restores
  the exact v0060 main; other previous production files are unchanged.

Next: resolve natural world-clock resets and the remaining NTSC recovery
phase, then continue natural dungeon progression and the missing gameplay
abilities. Complete enemy/boss behavior, quests, ending, full visual
sequences and audio waveform fidelity remain incomplete or unverified.

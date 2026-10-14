# Charging actors3A/3B - v0021

ROM: `versions/v0021-27c56ec8/gaw-megadrive-v0021.bin`.
SHA-256: `27c56ec87e272f87f6d6bf368e5f34bd9b85264956b87932d74e281df5aa5cf5`.

The port previously had no behavior dispatcher for actors3A/3B. Their original
state table919B selects91A9..927E. Both types now execute a translation of this
state machine as compiled68000 code. Graphics and statistics retain the
original room resources.

The actor appears only on terrain03 or19. Its initial32-tick emergence uses
descriptor8AF5, with contact disabled. It then enables contact, changes to8B1F
and walks at half a pixel per tick, using the source85D9 sequence. At the end
of a walking step it checks the leading-edge obstacle, then chooses another
direction, another step, or an attempted charge. A charge requires the hero
to share a sixteen-pixel row or column; the vertical alignment has priority
when both match, including identical coordinates.

Charging switches to descriptor8BAF and source927F's eight-tick, one-pixel
step. The source also has a separate state-selection tick between steps;
the native port retains that timing. A charge has a32-step budget. At each
step boundary, an obstacle stops it without decrementing that budget;
otherwise the budget wraps/decrements as an eight-bit value and zero ends
the charge. Walking visuals return without resetting fields that the source
retains. No projectile is emitted by these two actor types.

The actor extractor now preserves the complete586D..5877 terrain table,
including the two bytes used by spawn BC=0902, and the original927F sequence.

## Verification

Live SMS/native core comparisons pass in both NTSC and PAL:

- 72 deterministic state/direction/budget cases.
- 48 blocked-terrain cases for flag20/80, including charge-budget retention.
- 192 source-observed random choices, with all four charge directions and
  unaligned and identical-position heroes. Native RNG choices are controlled
  only for these fixtures; the full source R stream is not reproduced.
- Eight free charge trajectories compared through their original boundary
  stops, including the exact counter and state-selection timing.
- Four accepted terrain appearances and six terrain refusals per region,
  with explicitly controlled random choices and IRQ phase.

The charging-state suite totals4086 actor-record comparisons per region,
8172 overall. Bytes27/28 are excluded because the two renderers allocate
collision-list descriptor indices differently. Other record bytes are
compared directly to the running source game.

Cold-boot save checkpoints in rooms44 and56 additionally show both actor
types emerging, walking and charging during4200 frames per console/room.
No RAM fixtures are used in those room runs. The checkpoint is test data and
does not prove natural progression or identical random walks/spawn timing.
Room48 was also explored, but source3B did not charge in that run; it is not
included as evidence of charging behavior.

Targeted regression checks pass for38/39 and their bouncing1F shots, four-way
scroll visibility in both regions, natural hero/scroll timing and deterministic
enemy movement in both regions, and title cadence/video in both regions.
The previously documented intro-start and transition-setup offsets remain.

`charging_patch_audit.json` binds twelve reports to this exact512KiB ROM,
checks its additive checksum and aliases, and verifies that the supplied SMS
ROM is unchanged. The numbered v0021 and its archived reports are retained
alongside all earlier ROMs.

## Remaining work

This is a further actor-family milestone. Types3C onward, dungeon/conditional
quest behavior, original RNG and clock,495E sprite-overflow handling, remaining
audio event coverage, exact intro reveal/startup timing and full-game
progression/rendering verification remain unfinished.

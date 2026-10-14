# Orbit enemy and homing projectile - v0027

ROM: `../versions/v0027-d7bdb3f6/gaw-megadrive-v0027.bin`.

Enemy 42 now follows source 9730..983E: entrance, expansion of the elliptical
path, source sine/facing tables, three attack orientations, projectile allocation
and recovery. The asymmetric left-side attack choice is retained. Projectile
1C follows 415C..4190, including its eight aimed segments and boundary checks
at segment completion. Shared aiming still serves existing projectiles.

PAL and NTSC deterministic comparisons cover seven state transitions, 1024
phase/amplitude cases, 3072 attack-facing samples, eight projectile octants,
eight consecutive homing segments and 12 lifetime/boundary guards. There are
131638 actor-record comparisons across both regions; renderer collision-list
descriptor bytes 27/28 are excluded. Native random choices are controlled and
moving targets are explicit RAM fixtures. Original random-stream equivalence
is not established.

Cold-start save checkpoints in rooms 1D and 2D show orbit movement and projectile
births on both consoles without runtime RAM writes. These checkpoints contain
80 HP so the hero survives to observe attacks; production cartridge health and
balance are unchanged. This does not prove natural progression or complete combat.

Existing burst/bouncing projectiles, movement, title cadence and scrolling checks
also pass on this ROM hash. All eight scrolling direction/region cases contain
zero non-hero sprite errors over 342 native transition frames, preserve the hero
and actor persistence mask, and resume gameplay. The original scrolling fix is
documented in `scroll_objects_milestone.md`; source setup-frame timing differences
described there remain. This is a sprite-visibility check, not complete pixel or
timing equivalence.

`validation/orbit_patch_audit.json` binds eleven current reports to the cartridge,
verifies the extracted orbit assets, identical ROM aliases and additive checksum.
The numbered archive retains that evidence without replacing older ROMs.

The full port remains incomplete: conditional story/dungeon behavior, source
495E sprite-overflow allocation suppression, intro startup offsets, exact random
streams and full progression/ending still require work.

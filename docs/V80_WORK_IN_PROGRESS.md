# V80: correct combat targets and boundaries in15B

The dungeon10 controller excludes type45 turrets from15B melee targets.
The checked production `entity45_handler` initializes a fixed source,
periodically spawns type20 projectiles and has no death state. Previously,
the controller swung126 times at the same turret before dying.

Chasing real enemies exposed unintended crossings back into15A, respawning
15B. Combat pathfinding now clamps its goals and intermediate nodes to the
room interior. Its cache distinguishes combat bounds from ordinary travel,
so the actual route exit remains available. Both changes affect only the
controller, only dungeon10/15B; no production gameplay was changed.

Native full-entry final-source run `v80_combat_bounds` arrives15B with18HP
and0MP, stays there and dies at69869 frames. It does not complete the dungeon.
Private report SHA256:
`8b9bc16ae5de6c9cb6fd0ae7eebf632269eaa765853e21aa430aa497b6fc959f`.

Separate SMS equipped13C suffix `v80_sms_suffix` passes `validate_segment`:
19378 frames,13 room visits,23 boss hits,one boss death,credits and title
confirmed,108HP remaining. This is a suffix test, not a full-entry proof.
Private report SHA256:
`792f439928926a87b2f4831a227137f053b686e25a45a2996b50e8b7e395071c`.

59 Python tool tests pass, including target selection and a regression
for reopening the travel path after combat-bound pathfinding. Remaining
work is surviving the real81/80 enemies in15B and reaching the final boss
with sufficient resources from the original entry checkpoint.

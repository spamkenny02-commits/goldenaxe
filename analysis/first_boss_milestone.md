# First boss: v0110

ROM: `versions/v0110-c64afe1e/gaw-megadrive-v0110.bin`, 1 MiB,
SHA-256 `c64afe1e8e4802f49f8e1408a3c03a26e8443e729179308052a5af1ca157ca75`, checksum EC4B.

Type 64 dispatch at 506B selects bank 2 table A754. The native C implementation
translates states 0/2/4/6/8/10: initial position and 64-tick flash, 32-tick
vertical movement at 0.25 pixels per tick, direction counters, attack selection,
32-tick pause, three aimed type72 shots or five directional type73 shots.
It retains fields the source does not reset, including animation phase and
horizontal velocity during attack pauses. The fan retains writes to the last
successful allocation when subsequent allocation fails inside the same burst.

Projectile 72 translates 43D2 and its 4405 template, including the source's
absolute slot 25/26 adjustments (native slots 9/10): high dx byte +/-1 and
low dy byte -40h without borrowing. Projectile73 translates 442B/3DAF with
five velocities from 443D, then rendering direction 1. Shared bounds/lifetime
follow 3DFA, including room high byte 1 dungeon bounds. No Z80 interpreter is
included in the production ROM.

The complete-loop comparison exposed a collision-box publication difference:
the original renderer 0940 follows actor behavior. Boss and its two shot types
now publish boxes using current descriptor/animation/visibility, like the gem.
v0109 is preserved as an intermediate build with that difference; use v0110.

## Evidence

- `tools/validate_first_boss.py`: 1,789 original/native direct cases; all 768
  actor bytes match. 1,320 boss state cases and 469 projectile cases. The SMS
  fixture replaces ONLY two LD A,R instructions with LD A,B/NOP and LD A,C/NOP
  to supply explicit gate/choice bytes. Other routines/callees execute original
  instructions. This proves conditional behavior given inputs, not RNG fidelity.
- `tools/validate_first_boss_gameplay.py`: six production-loop cases, PAL/NTSC
  x appearance or either attack. 308 total frames with all 768 actor bytes equal.
  Controlled records/hero position are injected in an exterior. Segments stop
  before random selection. This is not a naturally reached dungeon fight.
- `tools/audit_first_boss_patch.py`: main.c unchanged from v0108, actor changes
  limited to the new behavior/dispatch/projectiles/collision publication;
  three literal resource slices match original ROM.
- Ordinary timing PAL/NTSC and six inventory return cases pass. First-boss
  lethal-hit/death/gem/reward chains pass both regions, including real boss room
  115 after normal dungeon entry with particles enabled (controlled relocation
  and lethal-damage injection as disclosed by validate_gems.py).

## Remaining work

The production gate/choice uses SGDK random(), not original Z80 refresh values.
Already-full fan pools can write through an inherited source IY register; that
cross-routine side effect is not yet reproduced. Natural boss-room entry,
complete combat, pixel/SAT equality, audio and hardware timing are not proved
by these cases. Other boss types, ending, quests and complete playthrough remain
unfinished. Earlier NTSC upward-scroll and some slow-scroll timing differences
remain recorded in the arrival-pose milestone. No global completion claim.

Reproduce: extract_first_boss.py; build.ps1; validate_first_boss.py --generate;
build_first_boss_harness.ps1; validate_first_boss.py;
validate_first_boss_gameplay.py; audit_first_boss_patch.py;
measure_timing.py (with/without --pal); validate_inventory_restore.py;
validate_gems.py --boss --focus; validate_gems.py --boss --particles --dungeon.

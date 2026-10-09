# V54 — dungeon 9 SMS pass reproduced, native traversal incomplete

The large-boss controller now checks active type-117 projectiles in slots
24..31 before starting a swing. With no hero invulnerability, a projectile
within Manhattan distance 48 triggers a reachable retreat that maximizes
separation from both projectile and boss. Attack animations still finish;
during invulnerability the controller retains its offensive opening.

The original SMS equipped dungeon-9 scenario passes the strict validator:
25 room visits, one staircase, one key spent, all 90 boss HP removed in 15
real hits, crystal collection/acknowledgment and return to overworld cell
$0EB with 124 HP. The runner changes gameplay only through joypad input
after one initial equipped fixture. This is a test-controller improvement,
not a change to the game's Z80/C damage rules or production ROM.

43 tooling tests pass. Room visits now include HP, MP, potion and curse at
arrival. The successful SMS run was repeated with this diagnostic data and
has identical strict validation, 17286 frames and 124 final HP. Boss arrival
is 86 HP, 8 MP, no potion and no curse.

Native MD dungeon 9 still fails: it arrives at the boss with 18 HP, 16 MP and
no potion, dies after two hits at frame 41504. A shield-facing approach trial
was tested and reverted: boss arrival 10 HP, two hits before death. It does
not improve the route. The wider boss margin experiment was also rejected:
SMS died after four hits, and MD reached $19E but timed out at 30000 frames
before reaching the boss.

SMS dungeon 10 still fails at $16A, edge 15, before the boss. The room-entry
trace reveals repeated unintended $18D/$18E crossings, then reserve depletion
and a renewed curse in $13D. Arrival at $13E: 24 HP, 8 MP, no potion and an
active curse. Arrival at $16A: 24 HP and 0 MP. These are diagnostic findings,
not a completed dungeon/ending proof.

Resume with MD resource preservation before the dungeon-9 boss, then inspect
the dungeon-10 retreat/backtrack behavior around $18E and antidote timing.

Private reports, original ROMs, RAM dumps and binaries remain ignored.
See dungeon_traversal_v54.json for compact validation and code hashes.

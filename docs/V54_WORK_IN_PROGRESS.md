# V54 — dungeon 9 SMS pass, native traversal pending

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
arrival to locate resource loss in future runs. The first successful SMS
report predates that added diagnostic data; combat decisions are identical.
Native MD dungeon 9 is running; dungeon 10 remains unfinished. The wider
boss margin experiment was rejected: SMS died after four hits, and MD
reached $19E but timed out at 30000 frames before reaching the boss.

Private reports, original ROMs, RAM dumps and binaries remain ignored.
See dungeon_traversal_v54.json for compact validation and code hashes.

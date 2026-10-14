# Shared pursuit/melee/charge bosses: v0113

ROM `versions/v0113-58543772/gaw-megadrive-v0113.bin`, 1 MiB,
SHA-256 `585437724e49ca97f2595072459324a3311708c915f12e2c7532837c15feaae5`,
checksum 5F24. Type68 room0175 and type69 room01C3; later7A/7B share51AE.

## Native behavior

Translates51AE's ten even states0..18, pursuit chooser577F, velocity helper5467,
melee preparation/attack/reset and charging/rebound phases. Type68 normally
selects melee; type69 can choose26-tick charge preparation instead. Initial
position(128,56),64-tick flash/wait, source descriptor/animation writes retained.
Pursuit uses source eight-way axis lookup and asymmetric room bounds, sixteen
ticks per eight-pixel segment. Facing is retained during pursuit, as in source.

Melee waits8 then attacks24 ticks before normal state2 reset. Charge chooses a
source vector or hero-directed octant, moves in32-tick segments, checks Y[56,144)
and X[48,208), chooses rebound directions and stops after13 boundary responses.
Stopping snaps coordinates to an eight-pixel grid and clears fractional position
and velocities exactly as537B. Source literals548A,54AB,54CB,57DB extracted.

Random inputs are optional helper parameters for direct comparison. Production
passesNULL and samples SGDKrandom only at executed random sites. This preserves
conditional call placement, not original04E1 or Z80 refresh/RNG sequences.
Current-state collision descriptors publish after behavior and flash like0940.

## Evidence

- 796 original/native direct cases compare all768 actor bytes. All ten states,
  four shared types, chase axis/limit cases, eight charge directions and aiming,
  four boundary rebound sets, counters and selected forced lifetime expiry.
  Fixture replaces six LD A,R sites with explicit register-preserving input
  shim and04E1 with an explicit byte. Other state/aim/bounds instructions execute
  original code. Arbitrary combinations of all record fields are not enumerated.
- Twenty controlled production segments across two types and PAL/NTSC compare
  all768 actor bytes over772 frames: initial appearance/pursuit, melee, charge
  windup, flight and final boundary reset. Actors/hero positions are injected
  in an exterior and segments stop before random decisions. Type68 charge states
  are shared-table coverage; its normal attack branch does not initiate charge.
- Four actual destination-entry cases use normal dungeon doorway after exterior
  relocation, then a controlled neighboring-room boundary and production right
  scroll/load into0175/01C3. All47 relative actor frames and107 loaded sprite
  tile pixel arrays at three samples match per case. Boss SAT has fifteen ordered
  entries at three visible relative samples(7,23,43), all equal after coordinate/
  tile normalization: twelve sampled lists,180 entries. Complete SAT/framebuffer
  equality over whole encounters is not proved.
- Absolute entry timing differs: room0175 SMS/MD3484/3485 NTSC and3475/3476 PAL;
  room01C3 SMS/MD3447/3448 NTSC and3444/3446 PAL. The MD is one/two frames late.
  Relative alignment must not be presented as matching full loading cadence.
- Patch audit reconstructs v0112 after removing shared51AE additions and restoring
  the collision condition. Main.c/composite assets unchanged, four literal tables
  exact. First boss1789 routines/six segments; satellite boss1138/twelve segments;
  composite boss870/ten segments with previously disclosed random timers; ordinary
  timing PAL/NTSC, six inventory returns and two boss-death/gem chains pass.

## Source inherited E route

An artificially forced interior segment lifetime expiry can retain caller E and
use it as a bounce-table selector at53A7. Direct tests supply E0..3 explicitly;
production does not model arbitrary inherited Z80 registers and supplies0.
The audit verifies this branch cannot occur during an ordinary68/69 charge:
every source vector has absolute components171/413 in8.8 fixed point, therefore
the major axis advances at least51 pixels per32-tick segment. The interior is
at most160 pixels across, so a boundary is reached within four segments, before
the initialized lifetime128 can expire. A rebound resets that lifetime.
Assumes normal state16/rebound velocities, per-tick bounds checks and normal
damage flags40(no velocity-clearing knockback); freeze suspends both integration
and counters. This is not a claim about corrupted/externally forced records or
future7A/7B spawning. Remaining full-game fidelity still requires natural testing.

Original RNG/refresh, natural full fights/routes, complete audio, ending, remaining
bosses and complete playthrough remain unfinished. Earlier scrolling timing and
first-boss full-pool inheritedIY side effect remain open. Next: types6A/6B fixed
54D3, then6C54D9 and6D55F1; ending state14 remains unimplemented.

Reproduce: extract_charging_boss.py; build.ps1; validate_charging_boss.py --generate;
build_charging_boss_harness.ps1; validate_charging_boss.py;
validate_charging_boss_gameplay.py; validate_charging_boss_entry.py;
audit_charging_boss_patch.py. Regression reports preserved with numbered ROM.

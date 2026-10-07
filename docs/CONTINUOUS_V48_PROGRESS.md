# V48 — Original-instruction magic and boss validation

## Scope and findings

Boss types are selected by bit 6 of `map_entity_stats`, which identifies
99..109. The tests use their actual `gaw_entity_handler_targets` wrappers.
The oracle executes the original Z80 without handler acceleration, captures
its refresh samples, restores shared RAM, replays those samples and compares
all $C000..$DFDF bytes. CPU stack/mapper scratch above that range is excluded.
A test-only initial refresh seed varies branch choices; it is absent from the
native MD image. These are controlled routine fixtures, not game acquisition
or controller-only boss encounters.

### Fixed behavior

- Types 99/100: correct which position counter increments/decrements for each
  direction, including wrap and reversal at counter 5.
- Type 101: repair transcribed slow/fast motion records and boundary mode
  changes. An even refresh sample selects the random/table path instead of
  looping until odd. Initialize the 20-step cooldown and execute movement or
  pause countdown in the original call, including original $04E1 LFSR updates.
- Type 103: implement its true $5193 wrapper and $A972 controller state table,
  five part records, position patterns, damage reaction, retreat, respawn and
  clearing. Its parts use states $10..$16, and immediately notice the parent
  retreat/death after entering their attack state. The old dispatch sent this
  type to the $51AE behavior used by types 104/105/122/123. The old final test
  also called $51AE for type 103; the new oracle calls the actual wrapper.
- Types 104/105/122/123: attack decisions now call the original-style LFSR
  rather than consuming only an untransformed refresh sample.

### Passing original-instruction cases

| Suite | Cases | Checks |
|---|---:|---|
| Boss phases and type-103 parts | 5792 | Valid states, timers, animation, direction, occupied auxiliary slots, weapon gates, damage and varied refresh samples |
| Boss death/reward | 2530 | All progression indices 0..10, countdown boundaries, explosion capacity and 11 complete 182-call sequences |
| Magic projectiles (types 3/4) | 256 | Initialization/active state, direction, level, bounds, blocking tiles and environment |
| Player item actions | 304 | Four magic entry points add 256 resource/counter/projectile/healing boundary cases to the existing 48 item/transition cycles |

The death countdown finishes as reward type 15 for indices 0..9, or main
state $0E for index 10. This verifies the ending handoff, not ending playback.
The item-action suite checks shared RAM, VRAM, CRAM, VDP registers and SRAM;
its blocking actions additionally compare each observed frame. The boss and
projectile suite checks shared RAM; it does not prove their complete rendering.

## Validation

- 8578 magic/boss cases and 304 item cases pass ASan/UBSan with leak detection
  disabled because local process inspection is unavailable.
- Existing 4992 combat cases, final compatibility, 72 complete full-screen
  effect cycles, native-only boot and 12 SRAM cycles pass.
- Compiled coverage, portability and MD backend audits pass. Coverage
  registration remains distinct from full-game equivalence.
- Native MD ELF/header/vector/RAM checks pass: 481196 bytes, checksum CA62,
  BSS 32296, RAM end FF7E28. No instruction interpreter is linked.
- Rebuilt controller combat regression passes: 61 attack entries, five enemy
  HP reductions, three deaths, four ranged projectile spawns, two player hits,
  final HP 16 and position [136,104] in cell $93. Outcomes can vary with native
  hardware entropy and timing; exact random trajectories are not asserted.
- Controller sanctuary save, SRAM-only fresh-process continue and all 49152
  settled SMS-to-MD viewport pixels pass again.

## Reproduction

After preparing the private original ROM data:

```sh
make test-magic-boss test-player-items test-combat test-final test-full-effects
ASAN_OPTIONS=detect_leaks=0 make test-magic-boss-sanitize
PREFIX=/path/to/m68k-elf- sh md/build_md.sh
python3 tools/test_md_combat_emulator.py --core /path/to/core.so --nm /path/to/m68k-elf-nm
python3 tools/test_md_sanctuary_emulator.py --core /path/to/core.so --nm /path/to/m68k-elf-nm --reference-rom /path/to/private.sms
```

The original ROM, embedded original data, full game image, emulator dumps and
captures stay private/ignored. Boss arena controller fights, normal acquisition
and use of magic, reward collection and full ending playback remain open.

# V47 — controller combat, original-Z80 checks and AI fixes

## Result

`tests/scenarios/combat_field.json` reaches a real encounter through normal
travel: starting cell $95, village $94, then field $93. The map contains four
type-38 enemies (HP 2) and one type-32 ranged enemy (HP 6). The controller walks
and attacks through several waypoints, then releases all input. No entities,
HP, inventory, positions or main states are injected.

The runner's optional `--combat` observes all 32 entity records after physical
frames. It records attack-pose entry, player HP reductions with hit flash and
previously observed attacker metadata, enemy HP reductions, deaths and ranged
projectiles. A kill requires transition from a live hostile type to death type
1, HP zero and matching saved type. Non-gameplay transitions reset observation,
so scene clearing cannot masquerade as damage or a kill. The observer is
sampling evidence, not a cycle-by-cycle event trace.

`pulse_buttons` releases only the specified action button between presses,
keeping the requested direction held. The existing `pulse` option retains its
release-all behavior for the save menus.

## Bugs found through original instructions

`make test-combat` calls the original routines without their accelerators and
compares shared RAM with the native operation. It excludes only the original
CPU stack/mapper workspace above $DFDF. New coverage:

- 2688 collision cases: actor slot classes, hitbox IDs, edge coordinates,
  distance, alternating-frame gating, immunity, cooldown, flags, attack versus
  defense and pending-damage byte wrap.
- 1152 damage/death/recoil cases: player versus enemy/boss branches, HP and
  damage boundaries, defenses, sword exception, directions and blocked recoil.
- 1152 AI cases for the actual encounter's types 32 and 38: valid states,
  phases, directions, spawn animation completion, pending damage and counter
  values 0/1/2. Each call records the original LD A,R entropy values and replays
  them through the host platform before the native call.

These comparisons exposed real differences and now pass all 4992 cases:

1. Type 32 returned after spawn animation completion. The original immediately
   chooses movement in the same call; the native routine now falls through.
2. Type 38 also returned between spawn completion, direction selection and
   movement setup. The corresponding original fall-through is restored.
3. At $87A1, the original decrements a temporary counter but writes it back only
   when selecting a new direction. The native version had committed it on
   every movement completion. Write-back and byte wrap now match the original.
4. The $4C78 wrapper clears pending damage before copying a new clone and
   restores it only on the parent. Native cloning had copied pending damage
   into the child. Child pending damage is now zero.

The fixes affect shared family handlers; the new AI oracle specifically tests
encounter types 32 and 38, not every member or every full-game situation.

## Actual emulator results after rebuilding

The new full native MD image is 479560 bytes, checksum DAB5, BSS 32296,
RAM end FF7E28. Actual ELF/header/vector/RAM and interpreter-exclusion checks
pass. It is 32 bytes smaller than V44, with unchanged persistent RAM.

| Observation | Native MD | Original SMS |
|---|---:|---:|
| Sampled attack-pose entries | 61 | 61 |
| Observed enemy HP reductions | 3 | 3 |
| Observed enemy deaths | 2 | 3 |
| Observed ranged projectile spawns | 4 | 3 |
| Observed player HP reductions | 2 | 2 |
| Final HP | 16 | 16 |
| Final position | [136,104] | [120,96] |
| Total physical emulator frames | 4830 | 1907 |

Both runs end in gameplay at cell $93. MD kills two HP-2 enemies, damages the
HP-6 enemy to HP 4, and retains three live map enemies. Death animation clears
the killed slots. Two type-16 projectile contacts reduce player HP 24 -> 20 ->
16 with hit flash 47 at the sampled checkpoints.

The wrapper requires successful enemy damage and death, projectile spawning,
player damage, survival and consistent remaining-enemy counts. A temporary
report with the death evidence removed is rejected with `No enemy death
observed`. The published test does not accept swinging at empty space.

The hardware entropy inputs differ: native MD uses its platform entropy,
whereas SMS uses the Z80 refresh register. Random movement and resulting
positions/death counts differ; the equal final HP is an observed result, not
a requirement of identical random combat. No full combat pixel equivalence,
input-phase equivalence or speed gain is claimed. Controlled entropy replay
proves the tested AI branches separately from those hardware differences.

## Regression validation

- All 4992 new original-Z80 cases also pass ASan/UBSan; leak detection disabled
  because local LeakSanitizer process inspection is unavailable.
- Final compatibility, 48 complete player-item cycles, 6144 map-resource cases,
  3072 IRQ cases plus 256 NMI cases, native-only boot and 12 SRAM cycles pass.
- The controller-only sanctuary route, SRAM-only process restart and 49152-pixel
  SMS viewport comparison pass again on the rebuilt image.
- Seven tool tests, Python syntax checks, coverage/portability/backend audits
  and diff whitespace checks pass.

## Reproduction

From the repository root with private prepared game data:

```sh
make test-combat test-final test-player-items test-map-resources test-irq
python3 tools/test_md_combat_emulator.py \
  --core /path/to/genesis_plus_gx_libretro.so \
  --nm /path/to/m68k-elf-nm \
  --reference-rom /path/to/private_game.sms
```

The SMS reference is optional. Private binaries, traces, screenshots and logs
remain in ignored `md/build/combat-test/`.

## Remaining work

This validates one encounter with melee and ranged threats. Other enemies,
bosses, inventory/magic combat, death/game-over recovery, loot collection,
full playthrough and ending still need controller routes. Physical hardware,
PAL/NTSC behavior, MD page-1 SRAM, exact sprite overflow timing and combined
fine horizontal scroll/right vertical lock remain open.

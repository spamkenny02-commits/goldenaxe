# V49 — Real-arena boss fights, rewards and loot

## Controlled checkpoint scope

`tools/test_md_boss_emulator.py` validates all ten boss rooms on the rebuilt
native MD image and the original SMS ROM. The runner boots normally, then
prepares one equipped checkpoint before invoking production state 6. That
resume/scene path loads the actual room, original full boss HP and graphics.
There are no writes to work RAM after the fixture; the write helper rejects
any attempted later write. The adaptive driver reads positions but applies
only libretro joypad buttons. Inventory selection, potion use, healing magic,
attacks, collisions, damage, deaths and reward confirmations run in game code.

The initial fixture has HP/cap 128, MP/cap 120, sword level 3, axe level 2,
armor/shield level 3, healing magic level 1 and one potion. No equipment or
health is replenished by the runner during combat. This is prepared equipment
and room arrival, not a normal dungeon/acquisition playthrough. The driver
stays near weapon reach, targets the type-101 satellites, and uses production
inventory menus for healing when needed.

Room identities come from `world_entity_types`; HP comes from `map_entity_stats`.
Dungeon indices were checked against the original bank-4 $BC8C map records,
including their row masks. Type 102 is an orbit satellite, not another arena.

## Observed fights

Both platforms pass all ten fights. Each HP chain starts at the original full
value, decreases on observed hits, ends at zero and changes into type 7.
Death animation, nine completed crystal presentations/pickups and the final
boss ending handoff are required. Reward completion includes acknowledgement,
restored player control, cleared boss slot and full HP, not just an early
progress flag while a blocking item sequence is still running.

| Type | Arena | Dungeon | Initial HP | Hits MD / SMS | Player hits MD / SMS | Final HP MD / SMS |
|---|---|---:|---:|---:|---:|---:|
| 99 | $144 | 2 | 30 | 3 / 3 | 2 / 2 | 128 / 128 |
| 100 | $115 | 6 | 60 | 8 / 8 | 6 / 6 | 128 / 128 |
| 101 | $163 | 5 | 72 | 8 / 8 | 7 / 6 | 128 / 128 |
| 103 | $179 | 7 | 60 | 6 / 6 | 2 / 5 | 128 / 128 |
| 104 | $175 | 1 | 12 | 2 / 2 | 1 / 1 | 128 / 128 |
| 105 | $1C3 | 3 | 32 | 4 / 4 | 3 / 2 | 128 / 128 |
| 106 | $180 | 4 | 30 | 3 / 3 | 3 / 3 | 128 / 128 |
| 107 | $196 | 8 | 80 | 8 / 8 | 7 / 7 | 128 / 128 |
| 108 | $1AC | 9 | 90 | 15 / 15 | 9 / 10 | 128 / 128 |
| 109 | $14C | 10 | 90 | 23 / 23 | 14 / 14 | 32 / 36 |

Type 101 spawns all eight satellites in slots 24..31, and the run records all
eight being killed. Type 103 spawns all five parts in slots 17..21. Boss
projectiles are recorded by their actual type 112..119. Healing uses only the
prepared potion/magic and the normal reward restoration. The final boss takes
23 axe hits; MD ends with HP 32 and SMS with HP 36 at main state $0E. The ending
handoff is verified; the complete ending movie is not covered here.

A separate bounded sword probe reaches the final arena and makes 17 sampled
sword attack entries on MD. The final boss stays at HP 90, with no damage/death;
the same rejection check passes on SMS. The positive axe encounter passes.
Four altered copies of a real result (missing death, uncollected reward, zero
player HP, reduced initial boss HP) are rejected by the result validator.

Physical frame counts, trajectories and some projectiles/player hits differ
because hardware entropy and cadence differ. No complete boss viewport pixel
comparison or speed equivalence is claimed. Captures were inspected locally;
original binaries and captures remain private/ignored.

## Production fixes exposed by the route

### Crystal presentation and restoration

The old type-15 pickup skipped the shared $6317 item presentation and applied
full healing directly. It now calls the common native item-grant sequence,
then restores HP through the original per-point HUD animation and reselects
room music. The shared sequence now includes the modal strip/font, item text,
Arthur's item pose and sprite staging, reward music, 180-frame delay, fresh
button confirmation, restored inventory font and rebuilt world/HUD.

`tests/test_boss_reward.c` compares 18 complete original $2A6B calls covering
all nine crystal indices, varied SRAM pages and normal/maximum HP capacity.
Every observed frame compares shared RAM, VRAM, CRAM and VDP registers; final
SRAM is also compared. All 18 cycles pass, also under ASan/UBSan.

### Enemy loot and visual explosions

Satellite deaths exposed false crystals. The native death routine used only
32 bytes of the original loot table and treated the enemy drop class as a
byte offset. The original first searches the saved enemy type, falls back to
the current world layer only if unmatched, mixes class with the random high
bits and rotates by four bits to choose a threshold/type pair.

The complete 160-byte table and original selection are restored. Visual
explosions with saved type 0 now clear without decrementing the map-enemy
counter, matching the direct $4B3F->$57EB branch. A legacy phase-9 assertion
encoded the old decrement; it is corrected and its pickup test now supplies
the required confirmation. Its old coverage expectation is updated to the
current registered type-32 handler.

2816 new original-instruction cases cover drop classes, saved type 0, unknown
types, interior/overworld context, empty/full pickup slots and 64 initial
refresh samples. Combined with V48, the magic/boss suite now has 11394 cases.
All pass ASan/UBSan with local leak detection disabled.

## Regressions and build

- Final compatibility, 304 player-item cases, 4992 combat cases, phase 9,
  native-only boot and 12 save/reboot cycles pass.
- Eight ROM-free tool tests, Python syntax, diff checks and the compiled
  coverage/portability/backend audits pass.
- Full native MD ELF/header/vector/RAM checks pass: 484500 bytes, checksum
  3383, BSS 32296, RAM end FF7E28; no instruction interpreter is linked.
- Rebuilt controller field combat passes with two deaths and final HP 20.
  Loot may now restore HP during that route; actual HP drops remain recorded.
- Sanctuary/save/fresh-process continue and the 49152-pixel settled SMS
  viewport comparison pass again on the rebuilt image.

## Reproduction

With private prepared original data and a pinned core:

```sh
make test-boss-reward test-magic-boss test-final test-player-items test-combat
ASAN_OPTIONS=detect_leaks=0 make test-magic-boss-sanitize
PREFIX=/path/to/m68k-elf- sh md/build_md.sh
python3 tools/test_md_boss_emulator.py \
  --core /path/to/genesis_plus_gx_libretro.so \
  --nm /path/to/m68k-elf-nm \
  --reference-rom /path/to/private.sms
```

The SMS argument is optional; `--bosses 101 109` selects a subset. Private
results, dumps and captures default to ignored `md/build/boss-test/`.
Normal dungeon traversal, equipment/magic acquisition and full ending playback
remain separate work, along with console hardware and PAL/NTSC validation.

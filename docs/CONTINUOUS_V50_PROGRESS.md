# V50 — merchant/items, full magic cycles and completed ending

## Production fixes

- Potion merchants: the previous `!pass_price()` condition could not match the
  nonzero potion price. Recognition now reads the original five-cell table $752E.
- Permanent HP/MP rewards: preserve the carry from CP $14 into SBC HL,BC,
  restore original $9021/$9035 dialogue, and use the original HP animation waits.
- Full-screen effects: damage lookup uses selected_item * 4 + level, rather than
  level * 5. The former test fixture selected item 1/level 1 and hid this error.

## Original-instruction comparison

| Suite | Verified cases |
| --- | ---: |
| Merchants: purchases/refusals, all 23 shops and offer slots | 354 complete cycles |
| Fixed items/capacities: pickup, persistence and inactive cases | 38 |
| Full-screen effects: selected items 1/6, both levels, slots/modes/phases/corners | 144 complete cycles |
| Services | 1024 cursors, 25 drawings, 72 complete cycles |
| Player items | 304 complete cycles |
| Boss rewards | 18 complete cycles |
| Collision/damage/AI | 4992 |
| Boss phases/death/rewards/projectiles | 8578 |
| Loot | 2816 |
| Ending | 4 complete sequences |
| Display transitions | 48 |
| World routes / scrolling | 320 / 220 complete cycles |
| Native save/reboot/continue | 12 complete cycles |
| Tooling metadata / negative report checks | 11 tests |

New merchant/item/full-effect tests compare original and native RAM, VRAM,
CRAM, VDP registers, SRAM and frame timing; frame traces are compared where
applicable. Merchant/item and all 144 full-effect cases pass ASan/UBSan with
leak detection disabled because process inspection is unsupported locally.
Native boot/save tests link no instruction interpreter.

## Emulator integration

The final boss starts at full HP from one prepared equipped checkpoint. Every
subsequent action is controller input. Both backends complete its defeat, the
nine crystal sprites, all 224 credit scroll values, confirmation and actual title
state $12 (MD: 15067 emulator frames; SMS: 10820). This is more than the previous
V49 handoff to ending state $0E.

| Dungeon | Native MD full route | Original SMS full route |
| --- | --- | --- |
| 1-4 | Validated: entry, boss, crystal, outside exit | Completed pilot runs |
| 5 | Incomplete controller pilot | Completed pilot, including corrected return |
| 6 | Incomplete controller pilot | Strict validation: 42 visits, 3 stairs, 8 boss hits |
| 7 | Not yet validated through the dungeon | Strict validation: 21 visits, 3 stairs, 6 boss hits |
| 8-10 | Not yet validated through the dungeon | Experimental routes remain incomplete |

Earlier V49 full-HP arena tests for all ten bosses remain separate evidence.
A completed arena test does not validate travel through its dungeon. The dungeon
fixture prepares equipment once outside the entrance and forbids subsequent RAM
writes. It does not prove equipment acquisition or a fresh uninterrupted game.
Route scripts and metadata are retained for the next iteration; see
V50_WORK_IN_PROGRESS.md for recovery paths and outstanding cases.

## Native build

- 484504 bytes; header checksum $BB38; reset vector $000200.
- Text 484248 bytes, data 0, BSS 32296; RAM ends at $FF7E28.
- ELF/ROM checks pass; production contains no Z80 interpreter/instruction bridge.
- Original ROM, binaries, screenshots and work RAM dumps stay ignored/private.

# V46 — controller-only save interaction and restart

## Result

A complete gameplay interaction now connects normal overworld movement to the
save menu and a fresh-process continue. Production game C and the full MD
image remain unchanged from V44 (479592 bytes, checksum 5223, BSS 32296).

`tests/scenarios/sanctuary_save.json` starts a new game, travels from cell $95
to village $94, walks to its central house, enters interior $00 through the
normal door and approaches the save marker. The world callback opens the save
service; pulsed button-2 controller input confirms the dialogue and slot 0.
The scenario checks cells and main states at each relevant stop, saved name,
HP, currency, slot and return cell. It releases the controller and settles.

This route performs no work RAM edits, direct service calls, teleports or
emulator savestate loads. The injected V45 service scenarios remain separate
regressions, not evidence of normal arrival.

## Emulator evidence

`tools/test_md_sanctuary_emulator.py` runs the route, exports logical SRAM and
starts a new emulator process using only that SRAM. Continue checks the
complete 592-byte payload (with the original C0C0/C0C1 adjustment), selected
slot and restored HP before scene entry. The player returns to village $94
with HP 24, resumes 300 physical gameplay frames and preserves all cartridge
bytes outside the known $1000-$149F scene/map scratch.

With the private SMS reference supplied, the same controller steps pass on
the original game. Sampled state-transition sequences and game-counter values
match, as do the final interior position [136,72] and HP 24. All 49152 pixels
of the settled 256x192 viewport match using the existing fixed DAC conversion.
No fitted palette, tolerance, alignment or emulator-state transplant is used.

The full MD scenario takes 4542 physical emulator frames (2360 sampled gameplay
frames); SMS takes 2076 (1338 gameplay frames). Both counters reach 2014 total
sampled game ticks; the sampled gameplay-only tick totals differ by one at a
state boundary. This is functional/raster evidence, not a speed improvement
or a claim of physical input-phase equivalence. The scenario contains a long
confirmation pulse window, including idle/attack animation after the save.

A temporary scenario expecting slot 1 instead of the actually selected slot 0
fails with `Controller route did not save to the expected slot`. The positive
route passes. The temporary negative input and all captures stay ignored.

## Regressions

- All seven V45 emulator persistence/signature scenarios pass again.
- All 12 native-only host save/reboot/continue/overwrite cycles pass again.
- Reset reference: 58 SRAM cases plus VDP state pass.
- Intro reference: 20 complete title/new/continue/cancel cycles pass.
- Service reference: 1024 cursors, 25 drawings and 72 modal cycles pass.
- Seven tool tests and Python syntax checks pass.
- Native SRAM integration ASan/UBSan passes with leak detection disabled.

The runner adds optional `pulse`, `expect_state` and `expect_saved_slot` JSON
fields and captures each controller checkpoint. Existing SRAM and controller
scenarios retain their previous behavior. Logical SRAM assertions currently
use the MD cartridge layout; the SMS run removes only that layout-specific
field and still checks states/cells and the final raster.

The remote V45 CURRENT_STATUS.md was truncated during transfer. This commit
restores its complete content and advances it to V46. Publication checks each
uploaded Git blob against its local content hash.

## Reproduction

From the repository root, with the private build and pinned local core:

```sh
python3 tools/test_md_sanctuary_emulator.py \
  --core /path/to/genesis_plus_gx_libretro.so \
  --nm /path/to/m68k-elf-nm \
  --reference-rom /path/to/private_game.sms
```

The reference ROM is optional. Private SRAM, screenshots, inputs derived for
the reference and logs remain in ignored `md/build/sanctuary-test/`.

## Remaining work

This covers one starting-village save route. Other dialogue/service locations,
combat and monster routes, MD page-1 mapper operation, full playthrough and
ending, PAL/NTSC physical hardware and battery/power-loss behavior still need
validation. Combined fine horizontal scroll/right vertical lock and exact
sprite-overflow timing also remain open.

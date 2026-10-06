# V33 — SMS sprite status without cartridge data

The portable video shadow now derives overflow (40) and collision (20) from SMS
sprites when the 192-line Mode 4 display is enabled. The native IRQ records these
alongside VBlank in C01B; the gameplay renderer already tests overflow there.
The calculation uses the first eight visible SAT entries on each scanline,
transparent pattern pixels, the D0 terminator, wrapped Y, clipped X, 8/16-pixel
height, zoom, the left shift and the sprite pattern bank.

This is frame-level status for the mode used by Golden Axe Warrior. It is not
a cycle-accurate VDP, extended-display-mode support, or proof of matching every
revision of SMS hardware. The fixed 192-line calculator uses 6,336 bytes of
local bitmap/count scratch. VRAM/configuration writes invalidate a cached
result; a status read clears latched flags, and the next VBlank latches them again.
The runtime cost and interrupt stack use still need a 68000 measurement.

Private cartridge access moved from video.c into rom.c. The video shadow/status
modules can therefore be linked and executed with no ROM initializer, no
interpreter and no placeholder game. Both production source lists include the
cartridge service and status calculator.

## Checks actually executed

GitHub Actions run [37541425111](https://github.com/spamkenny02-commits/goldenaxe/actions/runs/37541425111)
at implementation commit 30f5eb2efbe83a24561958ca601b929aac0720a6 passed:

- 6,948 synthetic comparisons with an independent scanline-first, per-pixel
  oracle, including every Y value and size/zoom mode, X edges, transparent
  overflow, ninth-sprite exclusion, SAT terminators and 4,096 seeded random cases.
- The same comparisons under AddressSanitizer and UndefinedBehaviorSanitizer.
- Shadow writes, configuration/pattern-bank changes, status cache invalidation,
  read/clear and relatching on the next VBlank.
- Existing MD conversion tests, strict C11 syntax and portability/backend audits.

The private ROM secret is absent. Original-game behavioral suites were skipped,
and their workflow condition now exposes that as a skipped step, not a successful
behavioral run. The last full local reference comparison and actual 68000 build
remain V32. The terminal connection is still unavailable, so V33 has not been
rebuilt/run on the Mega Drive emulator and its cost has not been measured.

## Remaining integration

Rebuild V33 and rerun all original-game comparisons when execution is restored.
Then measure cadence and interrupt stack, validate physical sprite clipping
against the SMS eight-per-line output, exercise genuine screen crossings through
controller input, and continue a full-game replay. Hardware validation remains.
The coverage gate already passed at V32 (12 states, 127 entity types, 512 world
entries); coverage alone is not a complete-game equivalence claim.

For comparison of hardware concepts, see the primary emulator implementation
[Genesis Plus GX, pinned vdp_render.c](https://github.com/ekeeke/Genesis-Plus-GX/blob/49c584764893b0505ac7f768a754f97330fa4392/core/vdp_render.c),
in particular parse_satb_m4 and render_obj_m4. The native calculator and its
separate pixel oracle use ROM-independent synthetic fixtures.

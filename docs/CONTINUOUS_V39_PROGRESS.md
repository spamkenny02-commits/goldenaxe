# V39 — Preserve the SMS 224-pixel vertical wrap on Mega Drive

SMS Mode 4's 192-line viewport addresses a 28-row name table modulo 224.
MD's 32-row plane instead wraps at 256. Copying SMS vertical scroll directly
to VSRAM therefore produces wrong source rows in intro/credit-style scrolling.

## Change

The low five vertical-scroll bits remain in VSRAM. The coarse 32-pixel part
rotates the source SMS rows while uploading MD Plane A/B names. All visible
physical source rows stay within rows 0..27 and reproduce (line + scroll) % 224.
The right-locked eight name columns retain unscrolled rows and VSRAM zero.

Changing the coarse base or lock state refreshes all 28 rows. Later dirty SMS
rows rotate into the corresponding physical rows; right-lock mode also retains
the unrotated dirty-row destinations. Each row reads its 32 SMS descriptors
once into a 64-byte temporary and uploads both physical planes.

## Checks added

- 49152 host visible-line comparisons for all vertical values.
- 15360 dirty-mask comparisons, covering every single logical row and dense
  masks, with/without the right-column lock.
- The standalone production 68000 video fixture runs all 256 vertical values
  with/without right lock, changes a logical descriptor on each odd scroll
  value, and checks sprite overlap and the viewport mask. Together with V38's
  three palette stages this checks 515 stages / 29532160 rendered pixels.

This initial checkpoint awaits the expanded GitHub hardware run. V38's 172032
pixel run is already successful (Actions 37596443981). No private full-game
build, screenshot or cadence measurement is claimed for V39 while local
execution is unavailable. Private-ROM CI tests remain conditional/skipped
without the reference input.

Horizontal scroll is zero in the locked-column fixture. Combined fine
horizontal scrolling and right-column vertical lock is not declared exact.
The current MD backend also still needs rendered eight-sprite line clipping.

## Next

Complete the expanded hardware verification, check the zoomed sprite-Y boundary
against independent SMS hardware, then implement actual native sprite clipping.
Resume private-game controller/save/combat/playthrough and cadence checks when
local execution is restored.

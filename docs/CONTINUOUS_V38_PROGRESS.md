# V38 — SMS background colour zero on native Mega Drive

V37's genuine world crossing exposes flat grass rendered black on MD. SMS Mode 4
uses the selected background palette's entry zero as a visible colour; it never
blocks a sprite even when the descriptor has priority. MD pattern colour zero is
transparent, so a single converted plane cannot reproduce that behaviour.

## Change

Plane A retains the exact SMS pattern, flips, palette and priority. Plane B now
uses a solid MD-only tile with palette 2/3 colour 1 mapped to SMS background
palette 0/1 colour 0. This filler always has low priority. Both planes share the
SMS scroll values and each changed name row uploads both descriptors.

The bottom Window mask uses a separate solid pixel index and CRAM entry, so it
continues to show the SMS backdrop independently. The palette-black line handler
updates the extra zero-colour entry and, when selected, the Window backdrop.

## Verification introduced

- ROM-free host conversion tests enumerate all 8192 descriptors and 1024
  background/sprite priority combinations.
- A standalone 68000 fixture links the production video shadow and native MD
  backend, with generated patterns and controller/frame-barrier logic only.
  It contains no original game data and executes no game dispatcher.
- A pinned Genesis Plus GX core renders three fixture stages. The independent
  indexed-pixel oracle checks 172032 pixels, including sprite overlap, both
  zero-colour palettes, palette changes, one dirty name descriptor and the
  192-line viewport mask. GitHub Actions builds and runs this fixture.

GitHub Actions run 37596443981 passes both host and native-video jobs. The
standalone 68000 image is 6516 bytes, BSS 25171, checksum 8D82; all 172032
rendered pixels match. The harness waits for an explicit startup sentinel and
compares Mode 5 normal intensity using the pinned core's 14/15 channel maximum.
Private-ROM CI comparisons are explicitly skipped without the reference input.
Local execution is unavailable; no new full-game ROM build, cadence measurement
or real-game screenshot comparison is claimed for this change.

## Next

Correct the SMS 224-pixel vertical name-table wrap on MD's 256-pixel plane and
extend the fixture to exercise every vertical-scroll value. Recheck the private
game route and cadence when local execution is restored. Full playthrough,
hardware testing and exact sprite line-limit rendering remain outstanding.

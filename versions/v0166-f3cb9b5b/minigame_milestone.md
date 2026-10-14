# Paid card minigame milestone v0166

ROM: versions/v0166-f3cb9b5b/gaw-megadrive-v0166.bin
SHA-256: f3cb9b5b9731933f7ba686412f77702be75872f74daee3d945cd17681d136895

Native translation of B00A/66B5/66F6 and6719/67CA/680A/68C7.
House5F is reached from four outside contexts13/5C/A7/DE; successful entry
charges10 pieces, switches to room0B and displays original instructions.
Stationary UP selects ten original coordinates0248..026C. Three ordinary
cards are recorded atDC03/DC06/DC09; at most one special is accepted, and
repeated special draws are retried. Lucky converts negatives to positives;
inverse converts both directions (its table deliberately continues through
both consecutive pairs tables until the FF sentinel). All tables, nine
original texts and confirmation OUIN glyphs are exported directly from ROM.

Rewards use original signed8-bit score summation, saturation and per-piece95
requests/two-frame waits. Positive saturated0 retains the original DJNZ
zero-counter behavior:256 increments, displayed reward0, final gold255.
Replay costs another10 and clears the grid; decline or insufficient gold
returns to house5F at hero88/58. Entry refusal/insufficient funds preserve gold.
The existing contour reveal is reused after the20-step interleaved exit wipe.
Absolute room-change timing is still unproved.

Evidence bound to this ROM:
- minigame_unit_report.json:19491 source/native cases. All32 roll indices,
  ten slots, three special states and three prior ordinary-card counts;
  flag/coordinate rejections;64 arbitrary flip tile values and all64 possible
  ordinary-card triples at all256 gold values. Original6719/67CA/680A execute;
  frontends observed/skipped, supplied RNG first byte followed by0 on retry.
  All64 relevant cells, stage, gold, text pointer, displayed count, actual unit
  count, final95 request and random call count compare exactly.
- minigame_gameplay_report.json:12 PAL/NTSC controlled real-door integrations:
  ordinary/lucky/inverse games, accepted replay, poor entry, declined entry.
  Normal confirmation, instructions, card selection, payout and return paths.
  Ordinary scenarios open and close inventory after the first card, preserving
  selected cells and stage. Four confirmation font tiles/48 frame bytes,
  stable1040-byte dialogue bitmap, all observed gold change values and game
  cells/static returned-house cells compare. Animated returned NPC cell
  differences are explicitly retained; no absolute publication-timing claim.
- house_gold_gameplay_report.json: eight prior PAL/NTSC gains/losses/saturation
  and HUD restoration regressions still pass.
- house_dialogue_report.json: six existing village dialogues plus natural
  walking conversation, restoration and display-enabled checks still pass.
- minigame_patch_audit.json verifies source assets, hook-only main change,
  unchanged actors/plain-dialogues/gold code and current ROM/header integrity.

RNG LIMITATION: production uses the existing provisional SGDK random generator.
Live tests supply source04E1 roll bytes and seed native randbase per selection,
while all other source frontend/rule code executes. Tests prove original roll
mapping and rejection behavior, not matching natural RNG streams, refresh
register values or probability/timing under natural play. Other conditional
quests, natural full playthrough, global timing, scanline clipping, inherited
loot expiry visuals and full audio/video/hardware fidelity remain open.

Intermediate v0164/v0165 are retained and marked superseded; validated v0166
contains both the inverse-table continuation and four-glyph OUIN correction.

# Gold house milestone v0163

ROM: versions/v0163-cd04a76a/gaw-megadrive-v0163.bin
SHA-256: cd04a76a8046e85c5efc4c20d575923ef63d9fd85635a1195260aee3d37d7189

Native house3F script AF25/6497 now implements the original33 gold contexts.
The original651C compressed table and both8DF6/8E30 text strings are exported
unchanged. Stationary UP requires original coordinate02DC and flags&77==14.
193D marks C100+outside bit2 before the dialogue; revisits do not repeat.
Signed amounts clamp gains to255 and losses to0. Each actual piece requests95
and waits two video frames. The displayed substitution uses the actual count.
The overlay preserves the room patterns, border font, room map and scratch,
while retaining the changed gold HUD before restoration.

Evidence:
- house_gold_unit_report.json:13992 cases executing original AF25/6497 versus
  compiled native decisions. All256 starting gold values in33 contexts, plus
  visitation/flag/coordinate boundaries. Original050C is observed rather than
  rendered,1E48 returns after the actual95 request,627A skips final frontend.
- house_gold_gameplay_report.json:8 controlled actual-door integrations in
  PAL/NTSC, towns54/90/80/16; gain, loss and both saturation directions.
  Original source ROM has no patches. Initial hero and clock are controlled.
  Final1040-byte text bitmap, gold/visit fields, static room map, gold HUD and
  no-second-reward behavior match. Adjacent gold changes are2 frames apart.
  Initial gold change frames are retained; absolute publication timing is
  not asserted. Four animated NPC map words may differ and are retained.
- house_dialogue_report.json: six existing village NPC conversations and
  walking conversation restoration, including absence of disabled/black field.
- house_gold_patch_audit.json binds source33 amounts/texts, main-only hook,
  unchanged actor/ordinary-dialogue code, ROM headers/checksum and reports.

Not a full port completion claim. Paid minigame66B5/66F6 remains unported,
other conditional quests and complete natural progression remain to audit.
RNG/global timing, scanline clipping, inherited loot expiry visuals and full
hardware/audio/video equivalence remain incomplete or unverified.

# Fairy capacity milestone v0170

ROM: versions/v0170-a4972307/gaw-megadrive-v0170.bin
SHA-256: a4972307b03cc976890bda1e45b339767e6611492bb5f0fecce70ad1f83e9e78

Native roomAF B205 ->5FC7 capacity rewards in all eight602A contexts:
life18/1D/82/C9, magic32/C0/E5/EC. Original flags&77 ==14 deliberately
returns without a reward. CP carry remains live into SBC HL,BC: coordinate
025C matches when masked flags>14; for flags<14 the subtract borrow means
025D is the actual match. This is modeled and tested, not normalized away.
193D marks previous-outside room bit2 before the prelude. Rewards cannot repeat.

Life item2A uses original BBB9 bank4 compressed heart icon; magic item1C uses
raw bank4 A801+1C*128 icon. Both texts and labels are copied from original ROM.
The existing6317 modal now accepts these two icon types instead of reading past
its former27-entry inventory icon array. After the prelude, the room metadata
transformation is applied; held reward/music/wait uses the existing modal.
Capacity adds8 as an8-bit byte then clamps results>=128 to128. Magic refills
immediately to its new cap. Life advances one HP/95 request/two waits until cap,
including modulo256 behavior for isolated extreme fixture inputs.

Original1E4E also blanks unused HUD capacity slots. v0169 retained a third orb
when a controlled fixture reduced initial magic cap24 to16; v0170 clears unused
life/magic cells before the reward backup. Raw prior HUDs and ROM hash retained
in analysis/fairy_hud_baseline_v0169.json. This fix is confined to fairy rewards.

Evidence bound to v0170:
- fairy_unit_report.json:11200 actual source/native cases, all eight contexts,
  all256 byte capacities, extreme current HP, visit-bit guards, accepted and
  rejected flags/coordinates including the preserved CP/SBC borrow. Actual
  B205/5FC7/193D/602A/5FF1..6028 execute;6277 observes text pointer,631A returns
  after original6317 stores item,1E48 counts after real95 requests. All flags,
  HP/MP/caps/item/text/refill counts/requests compare. No arithmetic shim.
- fairy_gameplay_report.json:24 PAL/NTSC controlled actual-door integrations,
  eight contexts plus cap/full boundaries including124 fixtures not claimed
  naturally acquired. Source ROM unpatched. Stable1040-byte prelude,38 held
  font/icon/hero pattern tiles, fields/refill sequence/two-frame cadence,
  160 transformed cells,128 final HUD visual words (bits0..12) and static
  restored map compare. Animated map words excluded with differences retained.
- fairy_walk_gameplay_report.json:2 PAL/NTSC actual town18 door integrations,
  hero placed at136/88 then ordinary UP movement approaches the fairy. Same
  frontend/reward/HUD checks pass without direct action/state injection.
- house_quest_gameplay_report.json:12 existing six-gift PAL/NTSC regressions,
  their38 held pattern tiles and restored equipment/curse/room fields pass.
- fairy_patch_audit.json: main change only include/hook and two icon branches;
  prior actor/dialogue/gold/minigame/quest/save sources unchanged, original
  contexts/text/labels/icons and current ROM/header/aliases/evidence verified.

v0168/v0169 are retained as superseded builds. This is not a full completion
claim: paid passage6036/616F remains unported, complete natural progression and
SRAM quest persistence unproved. Original RNG/global timing, sprite scanline
clipping, inherited loot expiry visuals and full audio/video/hardware fidelity
remain open. Source original save payload already stores the room visitation
flag and HP/MP capacities; no save-format changes were introduced.

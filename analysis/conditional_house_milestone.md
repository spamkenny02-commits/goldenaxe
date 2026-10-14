# Conditional house milestone v0167

ROM: versions/v0167-cbcbfa73/gaw-megadrive-v0167.bin
SHA-256: cbcbfa73d37247540e914aae9cb642aba3f8ae05df60aa51e2f4331590592377

Native ACB9/AD55 conditional branches into6603,6614/661C/6624/6634.
Room02 with previous outsideCE selects three NPCs at025C/02E0/0344.
Original C0D7 (save27, ninth crystal flag) high bit chooses the before/after
story variants. The non-CE ordinary context tables remain unchanged.
Room07 with previous outside22 selects02D4: C0D2 (save22, dungeon4 flag)
zero gives A077; nonzero and C0F7 (save47) nonzero gives A17F. First eligible
interaction marks C0F7=1 before showing A0E6 and awarding100 pieces, capped
at255. Actual count and source95 requests are preserved. At starting255,
source DJNZ B=0 gives256 increments, ending255; native reproduces this.
All nine ROM texts are exported exactly. Shared save payload already contains
these three bytes; save serialization code is unchanged. Dialogues preserve
room patterns/font/map/scratch and retain final HUD gold before restoration.

Evidence bound to v0167:
- conditional_house_unit_report.json:5040 actual source/native cases. Every
  value of C0D7, all256 gold amounts, zero/nonzero/boundary prerequisite and
  reward flags, accepted/rejected direction/coordinate conditions. Actual
  ACB9/AD55 scripts run;050C captures HL,627A returns and1E48 counts units
  after the real95 request. No flag, condition or gold arithmetic shim.
  Text PC, gold, reward flag, prerequisite/story preservation, displayed count,
  actual count and final request compare exactly.
- conditional_house_gameplay_report.json:24 controlled PAL/NTSC integrations
  through actual CE/02 and22/07 doors, using the unpatched original ROM.
  Six before/after story dialogues and six reward branches per region:
  not ready, first100, saturated5, wrapped256, already rewarded, and a nonzero
  prerequisite byte without bit80. Stable1040 bitmap bytes, later fields,
  every observed gold value, two-frame unit cadence, final HUD and static
  room map compare. Reward revisits do not pay again. Animated NPC words are
  excluded from static comparison and raw differences retained. Source text
  onset is not instrumented; only native active-frame onset is recorded.
- house_dialogue_report.json: six old village NPCs and natural walking
  conversation/restoration/display-enabled regression pass.
- conditional_house_patch_audit.json: hook/include-only main change relative
  to v0166, nine source strings/four call operands/conditional branch bytes,
  unchanged actor/plain/gold/minigame/quest/save sources and ROM integrity.

Full faithful port remains incomplete. Natural acquisition of prerequisites,
complete SRAM quest progression and a full natural playthrough are unproved.
Provisional RNG/global timing, scanline clipping, inherited loot expiry visuals
and full audio/video/hardware equivalence remain open.

Next identified missing indoor classes:
- roomAF B205 ->5FC7: once-only life/magic capacity reward depending on previous
  outside table602A; automatic coordinate interaction excludes flags14.
- room9F B19E ->6036: priced passage, table6087 and yes/no60BC; successful payment
  copies DC38/39 to DC37/38 and DC48/49 to DC47/48 before redrawing.
These are findings only, not implemented in v0167.

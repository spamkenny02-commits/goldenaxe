# V82: two15B controller probes rejected

Both native runs use the V80 entry fixture and V75 window8/V76 caster-room
retreat prefix. Both enter15B with18HP/0MP and neither defeats the final boss.

- V81: retreat from flashing type80/81 targets while hero flash<=8 and
  distance<40. Death in15B at70679 frames. Damage chain18→16→14→4→2→0.
  SHA256 `f7877d8e984e0bfbe504537846f24b70f13079347ee5e08f2f56eafb19cf890b`.
- V82: same retreat, prioritize type81 over nearby type80. Death in15B
  at69165 frames, no enemy deaths there. Damage chain18→16→6→0.
  SHA256 `bb1d7549d655d8ddfd442c98b6b23e7ff4debe684003a24056c932e5cfbc213b`.

Both experimental policies were removed. V80 controller behavior remains
the baseline. It kills three type80 enemies and one type81 before dying;
its type81 body hit costs10HP compared with2HP for type80. Future probes
should use checked axe/body geometry to avoid unsafe diagonal approaches,
rather than repeat generic retreat or danger-priority targeting.

59 Python tool tests pass. There is still no full-entry dungeon10 pass.
No production game code or fixture equipment changed in these probes.

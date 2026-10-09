# V75: late-room retreat controller

The opt-in `--late-retreat` dungeon10 controller retreats from flashing
type81/96 targets in13C. Its default window0 waits until the hero is vulnerable;
`--late-retreat-window 8` starts before hero invulnerability expires and
keeps frozen targets safe to approach. This changes joypad
decisions only; game code, encounter statistics and progression are unchanged.

Native full-entry trial `v75_retreat_md10` reaches14A with40HP/0MP, then
14B with10HP,15A with8HP and15B with8HP. It dies before the final boss
at71214 emulator frames. The prior matching controller reaches14A with
2HP and dies there at62105 frames. This is progress, not a completed
entry-to-ending validation.
This uses the window8 policy. A separate equipped13C trial of that policy
reaches the final boss with48HP/32MP but dies after14 hits at39100 frames;
the two policies therefore have different resource/timing tradeoffs.

Private full-entry report SHA256:
`c2e8e90e4b8b196690aaa0a648fed938252b38d849cd0090f7e2b1195039804d`.

The earlier zero-hero-flash retreat variant passes the strict13C suffix
validator:13 visits,23 boss hits,one boss death,credits and title confirmed,
76HP remaining at37862 frames. Its private report SHA256:
`7c05defb85c424f63521bcf9ad8ccf74e61d1fbceffeb0fd1043ea764dba6190`.
This separate equipped checkpoint is not evidence of full-entry completion.

The potion is already used by the runner below24HP during traversal;
earlier claims that it was reserved for the final boss were incorrect.
Remaining work is survival through15B/16B/16C/15C and the final encounter
from the full-entry fixture. The optional controller has a regression test;
56 Python tool tests pass.

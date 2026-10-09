# V60 — shield direction checked across damage and flash boundaries

The original-Z80 combat suite now compares384 type92/93 direction-gate
cases instead of32: both types, four enemy/hero directions, pending damage
0/2/12/255 and flash0/1/48. All game RAM matches the unaccelerated original
$5049 wrapper. This adds352cases; the total suite passes9228cases. The
48 tooling tests pass. There is no production C or ROM change.

Three controller experiments were rejected and fully reverted:

- Axe geometry against types90/92/93 avoids body contact but can stall
  while trying to satisfy shield orientation. Native10 was cancelled while
  stalled in17D; SMS10 dies in18A at25070frames.
- Ignoring shields more than40Manhattan pixels away during a swing makes
  native10 die in18A at61688frames, SMS10 in18A at25294frames, and regresses
  the previously completed SMS9 to a boss-room death at13338frames.
- Spending the last fire reserve against type90 when HP<=32 makes native10
  die in18A at60425frames and SMS10 in18A at25732frames. It leaves no magic
  on arrival in18A. The experimental late-fire CLI option is removed.

The retained V59 controller was restored. A fresh original-SMS9 run passes
strict room-order, full90HP boss, genuine15hits, reward/acknowledgement,
key/stair and outside-return checks:17286frames,25visits,124HP at exit.
This is a dungeon9 regression pass, not a dungeon10 completion.

Combat reports now include live direction and source/target hitbox IDs in
entity snapshots, plus direction/weapon-box data for swings and direction/
position data for player damage. These are read-only observations intended
to identify a reachable shield flank in future attempts. They do not alter
controller decisions. Existing V59 potion-first remains optional because
it regresses SMS10 while letting native10 pass13E and reach18A.

Full native9 and full10 remain open. The17B south entry,17C switch and
later route still await integration verification. See the compact JSON
for failed attempts and hashes. Private ROMs, binaries, images and RAM dumps
remain untracked.

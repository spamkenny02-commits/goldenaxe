# v0177: remember quest gifts and transform their room

The native631A quest-gift frontend omitted193D/1A7C. On v0176,actual town27's
armor gift left outside flag0 while SMS marked2;the gift cell stayed visible.
Town6A's primary3 script has an unconditional magic-owned grant,so a second UP
gave the reward again on MD (two held-gift phases versus one SMS). Both failures
were reproduced before editing,and their diagnostic field/cell/request records
are preserved under analysis/quest-gift-persistence-v0176.

Production now ORs outside-town flag2 and prepares the original metadata-selected
transformation/map before show_item_reward_text backs up the room. Thus the modal
returns to the transformed room,including after inventory. The existing general
class1 reload path already reads this outside flag. No save layout or reward
prerequisite/equipment-effect code changed.

32 controlled PAL/NTSC gift contexts pass:flags0 and128 each test six actual town
doors (armor2/3,primary2/3,oil,shield3),plus two original table contexts (C7 oil,
55 remedy). C7/55 have no discovered direct door to09/0F;their fixtures enter the
actual4C->09 door then set the outside context before interaction. They are not
claimed naturally reachable routes. The source ROM remains unpatched.

Five samples per context compare equipment/curse/capacity/room and outside flag.
Static room cells compare during/after reward and after inventory/second UP;two
640-word map samples compare with only remaining NPC24..2F animation words
excluded. The granted NPC cell31 is never excluded. Raw animation differences
are retained. Exactly one held-gift phase and38 font/icon/hero tiles compare.
Initial128 tests preserve that unrelated bit while marking2.

1836 original/native decision/effect cases still pass,as do the two265-byte hint
cases and20 paid-passage integrations. The scope audit verifies every other
production source file against v0176 and checks current ROM/header/aliases.

Limits:complete natural quest reachability/progression,exterior leave/re-entry,
SRAM roundtrip for these gifts,exact dialogue/reward timing and full frames/audio
remain unproved. Paid-exit physical loading duration,hero/IRQ cost models,source
refresh RNG,auxiliary/clipping/hardware and full faithful port remain unfinished.

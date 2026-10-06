# V14 — native interactive scripts and UI

Implemented the shared UI engine and the last three bridged world scripts:
ADEE (card game), B00A (card-game entry) and B19E (stairs/payment). Every one
of the 512 world callback registrations now selects C or an original RET.
The generic world callback interpreter fallback has been removed.

Native original routines: dialogue $050C, border $0877, name-table upload $0914,
display reset $0B24, name-table wipe $1F78 and menus $60BC/$6093/$60B1.
Messages resolved through bank-2 tables now select the direct bank-3 resource.
Host and Mega Drive presentation hooks use the common message/upload code.

Differential coverage:

- 12 menu input scenarios across three menus.
- 8 reference-ROM messages and 7 custom substitution/numeric/page-break cases.
- 46 deterministic branches covering stairs, payment, insufficient money,
  card-game phases, modifiers, saturation, replay and exit.
- 285 draws across 95 RNG seeds and three slot scenarios. Original LD A,R
  entropy is captured and replayed; this proves equivalent behavior with the
  same entropy inputs, not identical random streams across platforms.
- 3 existing callbacks exercising bank-2 message lookup.

Each case compares RAM C000-DF7F, all 16 KiB VRAM, CRAM, VDP registers and
host frame counts. DF80-DFFF is original CPU stack workspace. Test helpers
provide controlled routine arguments, ordered input and entropy replay.

Original timing quirks are retained: currency changes wait two frames per
step; converted card pairs wait 15 frames according to their second byte;
a positive settlement clipped to zero retains the original DJNZ behavior.

Remaining: three interpreter call sites and eight empty MD presentation hooks.
Native registration does not imply full-game equivalence. No linked or playable
Mega Drive ROM is claimed. The reference ROM remains local and ignored.

# V83: checked axe geometry exposes the remaining15B barrier

Native full-entry probe `v83_geometry` uses the unchanged V80 fixture and
V75 window8/V76 caster-room-retreat prefix. In dungeon10/15B only, it
replaces the Manhattan melee threshold for types80/81 with
`axe_openings(..., margin=2)`. Without an opening, it retreats at distance<24;
otherwise it retains the ordinary pursuit. All actions remain joypad inputs.

The run fails at75933 emulator frames in15B, with0HP. It enters that room
with18HP/0MP/no potion, matching the baseline prefix. It kills three type80
enemies and one type81. Unlike V80, no type81 body hit is recorded there:
three type80 hits cost6HP, then six turret-projectile hits exhaust12HP.
Avoiding the10HP body hit is insufficient to finish this room.

At death the remaining type81 has32HP at[63,120], and the remaining type80
has18HP at[48,120]. The hero is at[64,96]. Final live terrain descriptors
are E0 across the central band at Y96/104 (sampled X40..216); the controller
cannot walk through that band with the current equipment. The geometry
helper gives no axe opening at a straight24-pixel separation for box5/5,
but gives openings at16/20 pixels with margin2. No attacks are recorded
after frame69850, while the final projectile hits continue until75932.
These observations explain the prolonged unsuccessful pursuit in this run;
they do not establish that a different route or equipment is required.

The prefix's last24MP are spent on healing in13C, before arrival in13B.
The event trace records24→0MP there with no subsequent MP recovery.
The next experiment should examine preserving usable magic for the
unreachable15B targets while surviving the preceding rooms. Do not repeat
geometry-only retreat as though it resolves the resource/terrain barrier.

The experimental policy was removed. The retained controller, fixture,
production C and native ROM are unchanged.59 Python tool tests pass;
compilation and whitespace checks pass. No full-entry dungeon10 success is
claimed, and the existing separate suffix proofs remain separate.

Private result SHA256:
`633554b0d27a14490774f66d82b481d807456f0bb758a832b74f60688dd9df11`.
The report, screenshots and RAM dump remain untracked.

# v0177 persistence follow-up: actual re-entry,SRAM and cold houses

No production source or ROM changed. This stage strengthens evidence for the
v0177 quest-gift fix rather than generating another identical numbered binary.

Twelve source/native actual door cases cover six gift contexts in PAL/NTSC.
After the initial controlled door/hero/quest setup,ordinary controller buttons
walk out,step away,re-enter and approach the giver again. A read-only observer
chooses directions from position/state;there are no RAM writes after3400.
Exactly one original reward phase remains across the first gift,inventory,
second interaction and re-entry. Static cells/maps and saved equipment match.
Remaining NPC pose differences are recorded and excluded from static comparisons.

Initial re-entry fixtures include world visited bit1 and original traversal item
C0EC. The earlier persistence-only fixtures deliberately started the outside
flag0;these are not a natural reached-room state and do not unlock world terrain.
Town27 is on water. A fixed down/up exit route also failed at town92,whose exit
needs a different approach;the controller now probes a free outward direction
and reverses it to return. No terrain or collision routine is patched/bypassed.
Exterior actors were cleared in the initial door fixture and their resulting
empty persistence mask is retained;this is not a natural-combat walking claim.

Twelve save/cold-load cases transfer actual v0177 gift snapshots to the established
save-point route. All256 room flags,17 items,equipment,curse,maximum health and
dungeon6 story state compare before transfer. Actual slot1 menus write SRAM,
a fresh emulator starts and Continue reloads it. Full592-byte SMS/native payloads
and loaded fields match. This is not uninterrupted walking from gift to save NPC.

Twelve additional cold-house tests boot those actual SRAM files through Continue,
then use controlled exterior/door/hero relocation to revisit the corresponding
house. All3100 equipment/item/visit-flag fixtures are removed in this mode. No
saved gift bit is injected. Two normal UP attempts and inventory roundtrip yield
zero reward phases;static transformed rooms and loaded fields match. Journey
from saved checkpoint to each gift town is not asserted.

run_core gains an optional button provider for state-aware controller tests;
default scheduled input semantics remain unchanged. All observations/control
live in validation tools. Current production files and ROM match archived v0177.

The previous v0177 six-report snapshot is immutable. Additional tools,SRAM,
captures and four new reports are archived separately under additional-persistence.
Its manifest binds this evidence without replacing the earlier snapshots.

Remaining:complete natural quest/save progression and final victory,physical
loading/IRQ/hero costs,source refresh RNG,auxiliary entities/scanline clipping,
complete audio/frame equivalence and hardware validation. Full port is incomplete.

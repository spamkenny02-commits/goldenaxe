# V57 — antidote compared against original Z80

The player-item suite now executes the original bank-0 $2FBE antidote
handler and compares it with native C, including all game RAM, VRAM,
CRAM, VDP registers, SRAM and observed frame boundaries. 24 new cases
cross curse values 0/1/2/255, inventory presence 0/1 and three equipment
variants. A clear curse leaves the item unused; an active curse clears
both curse and antidote flags and refreshes the selected-item graphics.
The item suite passes all 328 cycles; 47 tooling tests also pass.

Delaying the dungeon-10 antidote until room $13D was tested from the
ordinary equipped entrance fixture, with joypad input only afterwards.
It regresses both platforms: SMS dies in $15E at frame 15436, native MD
in $15E at frame 27540. The experiment is reverted. The retained V56
controller and corrected south-entry route are unchanged. No production
C change, ROM rebuild or dungeon-10 completion is claimed.

The single antidote is needed earlier to survive the first caster circuit.
The next investigation should prevent a renewed curse in $13D rather
than keep the hero cursed through the intervening draining-enemy rooms.
Native south entry into $17B, the $17C remote switch and stairs to $13C
remain unverified in a full-entry integration run. Native dungeon 9 also
remains incomplete; original SMS dungeon 9 retains its earlier pass.

See dungeon_traversal_v57.json for compact failed-run evidence and hashes.
Private original ROMs, captures, binaries and RAM dumps stay untracked.

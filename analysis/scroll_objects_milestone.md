# Hide old objects during exterior scrolling - v0019

ROM: `versions/v0019-865fe0a9/gaw-megadrive-v0019.bin`.

The outgoing room's monsters remained in the native actor sprite list while
the background moved. Their flags were never cleared on edge crossing. The
original routine 21A1 first saves the primary actor persistence mask (18E9),
then clears byte 3 of every non-hero object (21B6..21C0), and calls 0938 to
rebuild its sprite list with the hero visible.

The native transition now follows those operations. `hide_world_objects`
clears display/contact flags on the 16 actor records, seven loot records and
spell record. Types, positions, HP and other record bytes are retained until
normal destination-room loading replaces the records. The persistence mask
is saved before clearing flags. The hero's display bit is set and the sprite
table is rebuilt immediately. Rendering also excludes non-hero objects for
the complete state-10 interval, including destination graphics loading.

`validate_scroll_objects.py` starts from the normal new-game route into A4,
then installs two visible frozen actors (one in an auxiliary slot) and one
coin. A later one-time edge-position write triggers the actual game transition
in each direction. These are test-only fixtures, never compiled into the ROM.
The tests inspect the hardware sprite attribute tables of both consoles,
not merely the native object flags. There are ten non-hero sprite tiles before
crossing. All eight direction/region cases pass; 342 native transition frames
contain no old non-hero sprites and retain the hero. The primary live mask is
preserved. Destination monsters become visible again on the three occupied
destination maps; the north destination 94 is empty, as in the source.

The source can retain the previous hardware SAT during setup for 5..8 frames
after entering state 10. Its rebuilt SAT contains only the hero before actual
scrolling. The native port hides the old objects immediately on entering the
transition. This fixes their visibility during scrolling; exact setup-frame
visual equivalence is not claimed. In the controlled north case the remaining
preparation/loading timing is 4..5 frames shorter, and two PAL controlled paths
differ by one frame. These are existing general timing limitations.

Natural hero movement and three exterior-scroll routes retain identical
room/hero state sequences in PAL and NTSC. The deterministic eight-enemy motion
comparison and the title cadence/video checks in both regions also pass.
`scroll_objects_patch_audit.json` binds these six reports to this exact ROM,
checks both aliases and the additive cartridge checksum. Full game validation,
all enemy AI, and complete transition pixel/timing equivalence remain pending.

Versions v0017 and v0018 remain available; v0018 is an intermediate build and
v0019 is the verified result. Intro startup profiling was investigated before
this user-reported scroll bug took priority; its incomplete work does not
change this ROM's intro behavior.

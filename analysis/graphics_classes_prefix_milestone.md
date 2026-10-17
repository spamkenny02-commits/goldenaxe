# Graphics prefix: three room classes

Research only; this helper is not wired into the playable renderer.

The changed-bank, display-off source prefix 16D0..1706 now accepts exterior,
house and dungeon rooms. The 175F classification branches retain their own
instruction costs. Existing class-0 callers use the same implementation.

56 source cases cover seven room identifiers, four R seeds and PAL/NTSC.
Phase, R, total M1, 331 RAM bytes, 400 audio bytes, IRQ entry times and decoded
patterns agree with the original instructions. Eight controlled real-door
foreground costs agree as well. Both physical regions execute all 56 cases
in the compiled 68000 test kernel with zero failures. The existing 24 planned
room-finish cases and decoder batch regression also pass.

Foreground costs differ by source branch: exterior 868344 T, low-number house
598893 T, F-column house 598934 T, dungeon 574863 T. These are source work
counts, not playable game speed measurements.

The isolated source fixture starts with quiet audio, a changed graphics bank,
display off, timer 2, IM1 and an acknowledged initial VDP status. The palette
copy is costed but its destination is not exposed by this prefix API. Same-bank
returns, display-on fades and the rest of house/dungeon loading remain outside
this milestone. The helper change alone left the v0202 ROM byte-identical.

Reproduction: `python tools/validate_graphics_classes_prefix.py`, followed by
`python tools/validate_graphics_classes_prefix_68k.py`. Reports are
`graphics_classes_prefix_report.json` and `graphics_classes_prefix_68k_report.json`
in this directory. The latter binds the generated cases and helper hashes.

# Dialogue publication boundaries - v0080

Native 68000 ROM, 1 MiB, additive checksum E818. Header ROM end 000FFFFF;
odd-byte 8 KiB SRAM remains at 200001..203FFF. The code crossed the old
512 KiB capacity during this work, so the cartridge was doubled as authorized.

Read-only source tracing shows that 0621/0666 publishes after punctuation,
066B/06D6 publishes after spaces, and 0756 invokes the text interpreter for
each substituted name/number, publishing at the substitution's terminator.
The old native renderer merged these stages into whitespace-separated words.
In particular, the source displays the name A alone before adding its comma;
that complete bitmap was absent from v0076 native hardware VRAM.

The renderer now keeps substitution boundaries, ends segments at the original
ten punctuation values (plus B0 normalized to a dash), publishes following
spaces separately, and publishes explicit/automatic line breaks and the final
terminator. The wrap preflight still uses native width calculation; it does
not reproduce the source's partial word drawing and clearing before a wrap.
The shared publication helper retains the established native transfer then
wait behavior. Moving its wait before transfer was investigated but changed
the last scroll pose duration and did not align first-page timing; this remains
a source IRQ/transfer ordering problem to solve, not a completed fidelity check.

Current-ROM natural name-A first-page evidence, without ROM/RAM modifications:

| Measurement | SMS NTSC | MD NTSC | SMS PAL | MD PAL |
| --- | --- | --- | --- | --- |
| Story entry | 1490 | 1490 | 1489 | 1489 |
| First page wait | 1596 | 1605 | 1583 | 1592 |
| Initial room active | 2454 | 2421 | 2448 | 2417 |

Each source trace completes 37 bitmap uploads representing 29 distinct full
bitmap shapes before the first page wait. Every shape now appears in order in
native hardware VRAM, with all native pixel colors restricted to the expected
1/3 pair. The name-only pose appears at 1495..1497 NTSC and 1493..1495 PAL.
These checks do not establish equal upload counts, dwell times, partial
transfer frames, palette phases, whole-framebuffer equality or audio timing.
The first page is nine frames late in both regions. The initial room remains
33/31 frames early; the scripted final acknowledgement is at frame 2400.

Source foreground preparation costs, excluding IRQ handler execution:

| Source range | Z80 T states | Purpose |
| --- | --- | --- |
| 7444 -> 0524 | 9465 | Clear software window, enter interpreter |
| 0524 -> 0554 | 22011 | Reset text state, clear 1040 bitmap bytes |
| 0554 -> 057D | 25553 | Build border and tile references |
| 057D -> 0595 | 157371 | Initialize 130 hardware bitmap tiles |
| 0914 -> 059B | 44825 | Upload software name table |

The 0595 -> 0914 interval contains an IRQ wait and is phase dependent. Glyph
drawing, punctuation/space uploads and IRQ suppression must be accounted for
before asserting equal first-page duration. This is preferable to a fixed
delay that would only fit one text/name/input sequence.

Current checks: opening actual CRAM 0..30 for 41 frames per region and original
font, complete four-pose scroll frame lists, twelve final acknowledgements,
six NPC conversations plus a natural walking route, 43 merchant cases,
bounded hero/scroll/eight deterministic enemy motion comparisons PAL/NTSC.
Save and five free-healer cases per region are also rerun for this ROM.
Their reports, rather than this document, are authoritative for outcomes.

Reverting the renderer block and removing its publication helper restores
the exact v0076 main.c. Extracted assets and healer code are unchanged;
rom_header.c and build padding change only cartridge capacity. v0077..v0079
remain preserved intermediate binaries, not validated releases.

Global clock/palette 31, source IRQ ordering, case/control and substitution
edge cases, full enemy/boss behavior, abilities, quests, ending, audio fidelity
and a natural complete playthrough remain unfinished.

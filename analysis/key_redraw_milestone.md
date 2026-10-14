# Key-door redraw schedule - v0043

ROM: [gaw-megadrive-v0043.bin](../versions/v0043-94317503/gaw-megadrive-v0043.bin).
SHA-256: `94317503805abf9288dd056b64a4f8b61d92dc3c9b2a51227813777879f01fb1`.
Size: 524288 bytes. Additive checksum: `676B`.

Native key opening now retains the foreground reconstruction work and video
barrier observed at original 5E90/1DE2. The original 2279/22E2 instruction loops
take exactly 192686 Z80 T states for 640 tile words. The generated include uses
this cost plus rounded 32000T HUD and 5000T metadata allowances. Scheduling
uses the existing region-dependent foreground budget (59736/71364 minus the
approximate 3072T IRQ reserve), counts native work already spent, then retains
one VBlank barrier before the map upload. This models a common routine, with
no room-specific or direction-specific delay constants. Ordinary movement
does not incur this schedule. Effect A5 is requested before reconstruction,
matching its position in original 5C4E, rather than after the upload.

Six read-only source instruction/cycle profiles cover top/left/right openings
in NTSC/PAL. The source cartridge is unmodified. The research DLL observes PCs,
registers and executed cycle deltas; it supplies no state or Z80 execution to
the native cartridge. Each map-loop measurement matches the instruction sum.
Metadata and HUD work vary and are not claimed cycle exact. Source video IRQ
waits remain observed rather than replaced in these live profiles.

Compared with archived v0042 profiles, first movement after redraw improves
from four frames early to one early in NTSC, and from three early to exact in
PAL. Eight aligned post-resumption position/counter frames match in each case.
The complete first crossing still has additional offsets:

| Direction | NTSC MD minus SMS | PAL MD minus SMS |
| --- | ---: | ---: |
| Up | -5 frames | -3 frames |
| Left | -1 frame | 0 frames |
| Right | -2 frames | 0 frames |

These are controlled gameplay paths from rooms 120/121, not all rooms or IRQ
phases. Upward transition setup/loading still needs work. Full redraw pixels
and audio waveforms remain unverified; the pause comparison measures gameplay
state, not complete hardware sprite presentation.

8192 original/native key-dispatch cases continue to match. Eighteen live
controller cases, eighteen death/Continue cases, two save/cold-load cases and
ordinary movement timing regressions pass. Save tests transfer controller-made
door states to the save route; uninterrupted travel there is unverified.
Nine reports and six current profiles are bound by the
[audit](../versions/v0043-94317503/key_redraw_patch_audit.json).
The six prior profiles are preserved with v0042 for comparison.

Remaining scope includes precise IRQ/upload phase, vertical loading timing,
room-clear and other puzzle scripts, remaining enemies, quests, bosses and
ending. This milestone does not establish a complete playable game.

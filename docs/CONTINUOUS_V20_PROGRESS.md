# V20 — native game-over menu

Continued after the V19 save by lifting state 14 ($257D): audio-command
selection, grayscale fade, font resources, menu descriptors and borders,
queued video commands, input edges, checkpoint selection and currency penalty.
Quit returns to state 00; continue selects state 06, which V19 made native.

The contextual font loader now accepts a resource pointer and is shared with
the existing choice menus. Grayscale $263E preserves the second palette and
uses the original first-palette RGB-intensity lookup and component fade order.

128 complete unaccelerated original Z80 comparisons cover four palettes,
four input scenarios, both checkpoint modes and four currency boundaries.
RAM C000-DF7F, all VRAM and VDP registers are compared after every shared
frame; final CRAM, frame count and chosen next state are checked. Strict C11,
ASan/UBSan and existing regression/portability checks pass.

Main-state registration is 7/12. States 00, 0E, 10, 12 and 16 remain bridged;
five MD hooks remain empty. This menu test compares the queued commands but
uses the shared frame replacement: full original video-queue/IRQ/audio
equivalence is still outstanding, as is a linked/play-tested MD build.

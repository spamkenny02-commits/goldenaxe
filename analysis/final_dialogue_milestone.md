# Final dialogue acknowledgement - v0064

ROM SHA-256 065f144627e9938c4e2af2601214c3c17b25aa84e08a96ad941b27a99156c444
512 KiB, additive checksum D292.

Source 7447..7451 (opening story) and 627A..6282 (NPC conversation) wait for
new C021 & 3F input after rendering. Unlike 07EE, this final wait neither
updates the continuation marker nor resets the global interrupt clock.
The native show_dialogue_text now uses a separate wait_dialog_end helper:
four directions and B/C acknowledge the text; A/Start remain native pad
aliases. Holding the previous confirmation does not dismiss the final text.
Inter-page and service waits retain their existing implementation for now.

Current evidence:
- Twelve natural opening sequences: each of the six SMS buttons/directions,
  PAL and NTSC, without RAM injections. Final text is byte-identical over
  all 1040 bitmap bytes at four observations, marker words match source
  VRAM and remain stable, and held confirmation cannot skip the final wait.
- Six controlled village conversations preserve exact text and restored
  state/patterns. One controller-only walking conversation also passes;
  162 entry/exit frames retain an enabled display and nonblack playfield.
- Existing bounded hero/scroll and eight deterministic enemy-motion checks
  still have zero differing state frames in PAL and NTSC.
- The patch audit removes the new helper and changes its single call back
  to recover the exact v0063 main; prior production assets are unchanged.

This is a final-confirmation behavior correction, not an overall timing fix.
Removing the inappropriate final marker redraw also removes its native delay.
First-room activation now occurs at frame 2421 versus SMS 2454 in NTSC, and
2417 versus SMS 2448 in PAL in the six-input test: 33 / 31 frames early.
The initial loader must account for the source work independently; do not
restore a spurious marker redraw just to hide that missing loading time.

Next: implement the genuine inter-page clock resets and smooth bitmap scroll,
then source-derived initial loading/IRQ accounting and live visual comparison.
Natural clock phase, all item abilities, quests, full enemy/boss behavior,
ending, complete visuals and audio waveform fidelity remain unfinished.

# v0203: outgoing-map flash at horizontal scroll completion

The v0202 reproduction walks from the initial clearing into the village and
back. At the final origin reset, the horizontal scroll DMA was queued before
the destination map copy. The displayed frame could therefore expose part
of the outgoing map while that copy was being published. End-of-frame VRAM
was already correct, so a VRAM-only comparison missed the visible defect.

v0203 queues the map copy first. At the terminal +/-256 offset the visible
half already holds the destination. The hidden half is completed before the
scroll origin returns to zero, so both halves agree when the origin changes.

`tools/validate_scroll_publish.py --baseline` reproduces the flash on v0202:
4755 incorrect background pixels leaving the clearing, and 16153 returning
to it, for the tested NTSC route. The subsequent corrected run verifies ten
transition completions across horizontal/vertical routes in PAL and NTSC.
No background changes occur during the checked post-publication frames.

Across 3004 captured frames, full PNGs are byte-identical to v0202 except
the three reproduced flash frames (the departure is exercised in both routes).
All observed room, transition direction/stage/step and game-state values remain
identical on every compared frame. PAL images remain byte-identical throughout.
The ROM is 1 MiB, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.

Limits: initial exterior routes only. Sprite rectangles are excluded from the
stability check, but included in the full-frame before/after comparison.
The existing NTSC vertical penultimate-pose hold is reported separately;
this patch does not change it or establish complete SMS cadence equivalence.
The full game remains under development.

Reproduce with `python tools/validate_scroll_publish.py --baseline`, then
`python tools/validate_scroll_publish.py`. `--reuse` rechecks existing captures
after verifying their ROM hashes. Reports are attached to the numbered release.

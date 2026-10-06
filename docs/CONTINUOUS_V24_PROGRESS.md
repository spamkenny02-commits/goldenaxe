# V24 — Native save, shop, inn and upgrade services

Main state 16 ($7390) and all four dispatch branches now execute services.c.
The implementation includes portraits and their eight mask-reveal passes,
save names and three slots, choice cursors, merchandise records/prices,
purchase refusals and payments, healing, inn fades/delay, magic awards and
capacity changes. The original slot copy is exactly $0250 bytes.

Recovered the indirect handlers $74C6-$752D and $7A09-$7B32 from the reference
ROM because the earlier reachable listing omitted them. No instruction bridge
is used by these services. Main-state registration is 10/12; 00 and 0E remain.

Added native two-stage descriptor decoder $0BD3: incrementing/literal runs
first populate D100, then a two-lane decoder produces the caller destination.
The RAM decoder can now consume that intermediate RAM stream.

A two-page SRAM comparison exposed a previous $16EF defect: native scene
restoration always wrote its animation workspace to page zero. It now honors
the selected page; scene tests doubled from 36 to 72.

Validation: 1,024 choice-cursor comparisons, 25 full portrait/slot/shop
drawings and 72 complete services against original Z80 execution, including
per-frame RAM/VRAM/registers and final CRAM/all SRAM/frame counts. Cases cover
confirmed/cancelled saves, both SRAM pages, payments/refusals, magic refills,
inns and each upgrade NPC. The service suite passes ASan/UBSan. Existing
menu, inventory, UI, scene and gameplay-entry regressions also pass.

Frame tests share the native video/input tick. Audio/full IRQ equivalence,
five MD hooks, cross-link and console playability remain outstanding.

Next: ending and title/intro, then audio/IRQ and complete backend validation.

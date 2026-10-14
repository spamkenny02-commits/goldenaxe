# Deferred intro sprite upload - v0031

ROM: `../versions/v0031-cec4ef9e/gaw-megadrive-v0031.bin`.

Source 1061/108B builds sprite records through 0A60/0A78 into DD40/DD80;
0978 terminates that RAM list. It does not upload VRAM. IRQ 015E..016A uploads
the RAM list on the subsequent VBlank. The native intro instead wrote sprites
directly by CPU immediately after advancing behavior.

intro_tick now queues its sprite table for the following VBlank process, using
SGDK DMA_QUEUE. This applies only to intro animation sprites. The queued source
is SGDK's sprite cache, consumed before the next intro behavior update. Loading
and leaving the intro retain their explicit sprite clears.

The unchanged read-only natural-boot profiler compares hardware SAT entries at
matching scene/counter/clock/logical states. Relative to the immutable v0030
baseline, NTSC mismatches fall from 118 to 15, PAL from 111 to 16. All 7516 native
logical actor-state samples still match source observations. The remaining 31
SAT differences are retained in the report: this is improved fidelity, not
complete sprite or animation timing equivalence. Phase-key comparisons can
reuse source counter epochs; they do not prove absolute frame alignment.

One remaining difference to investigate is that the source IRQ can upload a
prepared list while foreground text/loading code is busy, whereas queued native
DMA is flushed by SYS_doVBlankProcess. Moving VDP writes into an IRQ requires
examining interrupted VDP transfers and cache ownership; that was not done here.
The palette pipeline is also unverified and was not changed by this patch.

All three scene reveals retain five-frame passes and matching completed pattern
data in PAL/NTSC. The full 65-line natural intro returns to the title; title cape,
warrior fade and logo checks pass after skipped and natural intros in both
regions. Hero movement and four-direction scroll-object checks also pass.
intro_sat_patch_audit.json binds twelve current reports, compares the archived
baseline and verifies cartridge aliases and checksum. Older ROMs are retained.

Loading offsets, partial scanline equivalence, remaining SAT differences,
conditional story/dungeons, sprite-overflow allocation suppression and full
progression remain pending. The full port is not complete.

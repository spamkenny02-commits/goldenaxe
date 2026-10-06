# V16 — native Pause and equipment restoration

Continued immediately after the V15 Git checkpoint.

Implemented original main state $02 / routine $00F4 in C: status strip, fixed
font/text, frame waits, NMI Pause input, equipment restore, HUD rebuild and
sound-command timing. The same function registry drives state dispatch and the
coverage probe: 3/12 main states are native; nine remain bridged.

Added native status-box/font/text primitives ($638D/$6398/$0812), equipped-item
restoration ($7219/$722A) and four-plane pixel remapping ($1D0D). Pixel conversion
preserves shifts in scratch RAM D100-D16F as well as VRAM bytes. The inventory
presentation hook now uses these native services on both host and Mega Drive.

48 complete Pause cycles cover six equipment selections, four NMI timings and
both ordinary and zero-capacity HUD cases. Zero HUD counters retain the original
DJNZ 256-iteration behavior. Every cycle compares RAM outside original CPU stack
workspace, all VRAM/CRAM/registers and elapsed frame counts.

Sixteen direct remapping cases cover four tables and one through four tiles.
Their original-execution comparison exposed a reference-model omission: the
original uses BD for VDP control, which aliases BF on SMS. Implemented A7/A6/A0
VDP port decoding and checked all 32 data/control port pairs with original Z80
I/O instructions, including status acknowledgement. Hardware mapping reference:
https://github.com/mamedev/mame/blob/master/src/mame/sega/sms.cpp (sms_io).

Validation: strict C11 suites, ASan/UBSan (sandbox leak checks disabled), compiled
registration probe, MD syntax/structure and portability audits. ROM is local.
Frame comparisons use the shared IRQ replacement, not an original full-SMS IRQ
trace. Sound-command timing is tested; audio synthesis is not.
Remaining: effect states 1/2, nine main states, six MD hooks, IRQ/video queue/audio,
full-game integration
and a linked/play-tested Mega Drive build. Registration is not behavioral proof.

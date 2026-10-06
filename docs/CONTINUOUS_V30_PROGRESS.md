# V30 — Hardware interrupts and asynchronous audio on Mega Drive

Connected level 6 VBlank and level 4 line interrupts through register-preserving
68000 entry points. The frame barrier waits on C02E instead of a display-status
poll. VBlank invokes the native synchronous/asynchronous IRQ; audio and timers
continue while the main thread computes. Line callbacks reproduce display
disable, horizontal-scroll reset and palette blackout. Physical VDP uploads
mask line interrupts while allowing VBlank sound/timers. Start supplies Pause
NMI, and PAL/NTSC selects the original driver's DE03 compensation. The original
SMS ROM independently reports NTSC DE03=80 in the same emulator.

Added actual ELF vector checks and hardware IRQ counters in the private emulator
harness. GCC O2/LTO and row-level name-table uploads improve the idle gameplay
check from 70 to 139 updates over 300 physical frames. It records 299 gameplay
VBlank interrupts, 160 asynchronous ones and 45 line callbacks earlier in boot.
The original SMS achieves 298 updates over the same 300 physical frames, so MD
performance remains unfinished. The updated image is 471,702 bytes, BSS 25,174
at FF0000-FF6256, checksum 6178; no interpreter is linked.

Fixed cartridge ROM-end metadata when a linker emits an odd byte count. Private
captures and state remain ignored. Standalone video/MD conversion, 256 video IRQ
comparisons, 3,072 full IRQ comparisons, 256 NMI cases and interpreter-free boot
regressions pass. The harness can run the original SMS reference and scripted
controller inputs. Five presentation hooks, exhaustive integration and hardware
testing still remain.

An additional physical-controller sequence exercises attack, Pause/resume,
inventory open/close and four movement directions on both MD and original SMS.
Both return to gameplay at cell 95, HP 24 and the same final player coordinates;
MD records 304 gameplay updates, SMS 305. The small timing difference and this
limited route do not establish complete gameplay equivalence.

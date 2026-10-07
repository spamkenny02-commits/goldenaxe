# V35 — restored native build, profiling and a real screen crossing

V34's persistent sprite-status workspace is now checked with the actual private
reference ROM and 68000 toolchain. Every existing local regression/differential
target and ASan/UBSan passes. The compiled completion gate passes 12 main states,
127 entity types and 512 world entries, with no interpreter call or empty MD
presentation hook. This is coverage, not a complete playthrough.

The linked cartridge is 475,512 bytes, BSS 31,514 at FF0000-FF7B1A, checksum
D956. Native ELF/vector/RAM/header checks pass. The emulator reaches title,
name creation and new-game gameplay with audible PSG. Idle gameplay advances
136 updates in 300 physical frames; it still misses original SMS cadence.

The optional local Genesis Plus GX instrumentation counts master cycles at
instruction addresses without altering guest cycles or game state. The enabled
profile run reproduces full work RAM, game/IRQ counters, audio peak and cadence
from the ordinary run. The largest measured instruction buckets are shadow
VDP writes (36.862%) and physical shadow conversion/upload (21.282%). These
are symbol address buckets, not inclusive call graphs. Instructions include
refresh/bus waits; exception-entry gaps and stopped time are not attributed.

The first genuine controller-only screen crossing now passes on both native
MD and original SMS: cell 95 to 94, final position [56,104], HP 24 and gameplay
state 0C. MD takes 947 physical gameplay frames for 345 gameplay updates;
SMS takes 348 for 346. Short input-step endpoint phases differ by a few pixels,
then the final idle step settles to the same position. The route is retained
in tests/scenarios/world_exit.json and expected-cell assertions catch failure
to cross. No game RAM, inventory or progression is patched.

Local sanitizers run with ASAN_OPTIONS=detect_leaks=0 because LeakSanitizer's
process inspection is unavailable in this sandbox. ASan and UBSan are enabled.
The original cartridge data and all emulator captures/build artifacts stay
private and ignored. The default CI still skips reference-ROM suites without
the private secret; its source checks do not imply these local tests ran there.

Next: bulk VDP transfers with differential dirty-state/port tests, then measure
cadence again, validate MD sprite clipping, expand controller routes and keep
working toward a complete playthrough and physical-hardware validation.

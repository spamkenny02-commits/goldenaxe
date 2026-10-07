# Mega Drive backend

This backend runs the portable C core directly on the 68000. It converts the
16 KiB SMS VDP shadow into MD patterns, Plane A, palette and SAT. There is no
instruction interpreter in the production image. Cartridge SRAM is an odd-byte
32 KiB window at 0x200001-0x20FFFF; SMS words use explicit little-endian helpers.

Build with a m68k-elf GCC/binutils toolchain:

```sh
FETCH_TOOLCHAIN=1 ./md/build_md.sh
```

Output: ignored `md/build/gaw_md.bin` plus ELF/map. This contains your private
original-game data and must not be committed to the public repository.

For a reproducible headless emulator check, build Genesis Plus GX:

```sh
git clone https://github.com/ekeeke/Genesis-Plus-GX.git /tmp/gpgx
git -C /tmp/gpgx checkout 49c584764893b0505ac7f768a754f97330fa4392
make -C /tmp/gpgx -f Makefile.libretro HAVE_CHD=0 -j4
python3 tools/test_md_emulator.py --core /tmp/gpgx/genesis_plus_gx_libretro.so --nm md/toolchain/bin/m68k-elf-nm
```

The check drives title/name/new-game selection and requires 300 emulator
frames of gameplay, at least 24 game updates and audible PSG. Private captures
and metadata are written under md/build/emulator. This limited boot path is
verified on V35, including a controller-only screen crossing from cell 95 to 94.
Full-game/hardware behavior, actual sprite clipping and performance remain.
Frame-level SMS sprite overflow/collision flags and their persistent workspace
pass local reference/sanitizer tests and the native emulator checks.
Scroll animation is implemented in the portable core,
and no empty presentation hooks remain. Actual linked level 4/6 vectors are checked. The MD
VBlank ISR services native sync/async IRQ paths, including audio while the main
thread computes. Start sends the SMS Pause NMI; PAL/NTSC selects the original
audio compensation mode. Line IRQs are blocked during physical VDP uploads to
protect address commands; VBlank remains enabled.

Default builds use `-O2 -flto`; set `MD_OPT_FLAGS` to change optimization.
The private emulator harness also accepts `--reference-sms --rom /path/game.sms`
to run the original hardware reference and `--play-inputs /path/inputs.json` for
controller sequences after gameplay starts. Each JSON step has a positive
`ticks` count and a `buttons` list (`up`, `down`, `left`, `right`, `button1`,
`button2`, `pause`). Duration follows the game's C02F counter, including menus.

To run the checked first-screen exit on either native MD or original SMS, use
`--play-inputs tests/scenarios/world_exit.json`; optional `expect_cell` fields
make missed crossings fail rather than silently accepting an idle screen.
The result includes world-cell transitions and the final game state.

Instruction-cycle profiling uses an optional local emulator build:

```sh
python3 tools/instrument_gpgx.py /tmp/gpgx
make -C /tmp/gpgx -f Makefile.libretro HAVE_CHD=0 -j4
python3 tools/test_md_emulator.py --core /tmp/gpgx/genesis_plus_gx_libretro.so --nm md/toolchain/bin/m68k-elf-nm --profile --output md/build/profile
```

Counters observe ROM instruction addresses and master cycles, including bus/VDP
waits charged during instructions. Symbol buckets are instruction locations, not
inclusive call graphs; IRQ-entry gaps and stopped CPU time are not attributed.
V35 checked that enabling the profiler preserves full work RAM, input/output
counters, game cadence and audio peak compared with the ordinary run.

V36 uses faithful bulk SMS-shadow transfers and a freestanding memcmp. The
local frame tests and sanitizers pass; the native image is 475,604 bytes, BSS
31,514 and checksum 7F7F. Idle cadence is 148 updates/300 physical frames; the
checked exit uses 721 gameplay physical frames. This is still below SMS cadence.
The profile also reports the 64 hottest instruction addresses to distinguish
inlined wait loops from computation inside the same symbol bucket.

V37 consumes bounded dirty-pattern ranges and expands sprite resources one
pattern per block. The native image is 476,460 bytes, BSS 31,518, checksum BC9D.
Local reference/sanitizer tests pass; idle is 239 updates/300 physical frames
and the checked exit uses 508 gameplay physical frames. Screen comparison
reveals that SMS background color zero is incorrectly transparent on MD; its
zero-color layer/scroll/priority mapping remains to fix.

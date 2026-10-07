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
Full-game/physical-hardware behavior and performance remain. Native sprite
clipping and zoom now pass the generated V41 hardware fixtures.
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
V38 introduces a zero-colour filler layer and an independent hardware fixture.
No newer full-game cadence is measured while local execution is unavailable.

V38's standalone hardware fixture uses generated patterns and colours. It links
production video.c/platform_md.c directly, without game data or gameplay:

```sh
PREFIX="$PWD/md/toolchain/bin/m68k-elf-" sh tools/build_md_video_fixture.sh
python3 tools/test_md_video_emulator.py --core /tmp/gpgx/genesis_plus_gx_libretro.so --nm md/toolchain/bin/m68k-elf-nm
```

Three stages check every output pixel against an independent indexed oracle,
including both background palette-zero colours, sprite priority, palette/name
updates and the bottom viewport mask. The fixture also runs in GitHub Actions.
GitHub Actions run 37596443981 passes: the actual standalone image is 6516
bytes, BSS 25171, checksum 8D82 and all 172032 pixels match. This fixture does
not constitute a full-game, performance or physical-hardware validation.

V39 maps coarse vertical scroll into the 28 logical name rows, keeping physical
VSRAM in 0..31 to avoid MD's incompatible 256-pixel plane wrap. Dirty rows are
rotated, with unscrolled right columns retained when locked. The fixture now
runs 515 stages (29532160 pixels): all 256 vertical values with/without right
lock, H-scroll zero, plus the original palette/viewport stages. GitHub Actions run 37597060478
passes all stages (7052-byte fixture, BSS 25175, checksum 187C). Combined fine
H-scroll/right V-lock and full-game cadence still need verification.

V40 corrects the portable sprite-status Y wrap for E0 zoomed sprites. The
ROM-free SMS II hardware-reference collision fixture runs every Y in all four
height/zoom modes, using generated Z80 code and the actual VDP status port:

```sh
cc -std=c11 -Wall -Wextra -Werror -O2 -Isrc/include src/video_status.c tests/test_sms_sprite_hardware.c -o md/build/sms_sprite_hardware_test
python3 tools/test_sms_sprite_emulator.py --core /tmp/gpgx/genesis_plus_gx_libretro.so --compare md/build/sms_sprite_hardware_test
```

GitHub Actions 37599618930 passes all 1024 observed cases, including direct
portable-C comparison, in 3083 emulated frames. This targets collision
visibility; frame-level sprite
status is not a scanline-accurate VDP model or a physical-console proof.

V41 uses private sprite pattern copies at VRAM 4000–7FFF to mask output rows
after the eighth SMS sprite on each line and implement 2x zoom. A 64-slot cache
tracks source tile, row mask and mode; captured source dirty bits refresh copies
without requiring a SAT change. The 192-line count scratch and caches are
persistent. Plane names, viewport mask and original source patterns do not
alias these slots.

```sh
make test-md-sprite test-md-sprite-sanitize
```

The hardware fixture adds 17 clipping/zoom/bank/source-edit/shift/reset stages.
Actions 37603203186 passes all 532 stages / 30507008 pixels plus the host/sanitizer
helpers and 1024 directly observed SMS status cases. The actual standalone image
is 9928 bytes, BSS 25943, checksum 92EA. Backend reinitialization forces the SAT
cache to rebuild, preserving subsequent pattern-only edits without a SAT change.
No new private full-game build/cadence or physical-console result is claimed.

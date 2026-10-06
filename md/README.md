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
verified; full-game/hardware behavior, two scroll hooks and performance
are still being completed. Actual linked level 4/6 vectors are checked. The MD
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

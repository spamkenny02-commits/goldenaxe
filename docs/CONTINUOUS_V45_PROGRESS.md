# V45 — SRAM save, restart and continue validation

## Result

The existing production save/continue implementation passes connected
persistence checks. No production C behavior, ROM data, binary size or RAM
allocation changed. The tested full-game image is the V44 479592-byte native
MD build (checksum 5223, BSS 32296).

`make test-save-cycle` links only native C, without the interpreter. Twelve
cycles cover three slots on each of two mapper pages, then overwrite each
slot with a different name, HP and currency. Each cycle drives the save menu,
checks last-slot metadata and preservation of unrelated SRAM, resets all
work RAM/video/audio/input state, drives title/continue and checks the entire
592-byte payload plus restored HP. It then rebuilds the scene and advances
12 gameplay updates, checking cell, HP and currency. Only cartridge SRAM
survives the reset. ASan/UBSan passes; leak detection is disabled because the
local process-inspection facility is unavailable.

The private-ROM differential suites also pass: 58 reset/SRAM cases, 20
intro/title/new/continue/cancel cycles and service menus (1024 cursors,
25 drawings, 72 complete cycles).

## Actual Mega Drive emulator checks

`tools/test_md_emulator.py` now accepts logical 32768-byte SRAM via
`--sram-in` / `--sram-out`. The pinned Genesis Plus GX backing is 65536 bytes;
logical byte i maps to physical odd byte 2*i+1. This is independent of the
core's word-swapped 68000 work RAM. Import happens before the first emulated
frame; export happens before unload. Bad input sizes and last-slot mismatches
fail the test.

`tools/test_md_save_emulator.py` runs seven separate processes:

1. New game and save to slot 0.
2. Import SRAM, continue slot 0, save to slot 1.
3. Import SRAM, continue slot 1, save to slot 2.
4. Import SRAM and continue slot 2 without saving.
5. Import SRAM, continue slot 2, overwrite slot 0.
6. Import SRAM and continue the overwritten slot 0.
7. Corrupt one signature byte, restart and check new-game entry and erased
   slots, while preserving reserved bytes and the other mapper page.

All seven pass and resume at least 300 physical gameplay frames with audio
and IRQ checks. Every observed continue checks all 592 serialized bytes
before scene entry, adjusting only C0C0/C0C1 from C0C2/C0C3 as the original
continue routine does, and checks separately restored HP and selected slot.
Save checks name, HP, return cell and currency. Between processes, only SRAM
is transferred: no emulator savestate or work RAM snapshot is loaded.

SRAM $1000-$149F is production scene/map scratch, so preservation comparisons
exclude that workspace. Slot writes are confined to their 592-byte payload
at $0400, $0800 or $0C00 and last-slot byte $0030. Host tests use distinct
payloads for overwrites; MD tests validate the production boot payload.

## Reproduction

Use the private prepared ROM and the existing native MD build. For example:

```sh
make test-save-cycle test-reset test-intro test-services
python3 tools/test_md_save_emulator.py \
  --core /path/to/genesis_plus_gx_libretro.so \
  --nm /path/to/m68k-elf-nm
```

Generated SRAM, screenshots and logs stay in ignored `md/build/save-cycles/`.
The public repository contains only code, checks and this report.

## Limits and next work

Service arrival is a controlled RAM transition from gameplay into the
production save service. All menu confirmation and SRAM writing then execute
through production C and controller input. Traveling to the sanctuary and
entering it through normal collision/interaction remains a separate route
test. Both mapper pages are covered on the native host; this MD scenario uses
the normal boot page. Physical cartridge battery behavior, power loss during
writes, PAL/NTSC hardware and a full playthrough remain unverified.

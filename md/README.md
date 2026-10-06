# Mega Drive backend

This backend runs the portable/decompiled C core on the 68000. Original SMS-only
hardware accesses that still occur in mechanically translated routines feed a
16 KiB SMS VDP shadow; the backend converts dirty SMS 4bpp patterns, the current
name table, palette and SAT into Mega Drive VDP format at VBlank.

Build with a `m68k-elf-` GCC/binutils toolchain (the same target used by SGDK):

    ./md/build_md.sh

Output: `md/build/gaw_md.bin`.

The ROM header declares odd-byte cartridge SRAM at 0x200001..0x20FFFF for the
SMS save-RAM compatibility layer. The gameplay C is endian-safe: all emulated
SMS 16-bit RAM words use explicit little-endian helpers.

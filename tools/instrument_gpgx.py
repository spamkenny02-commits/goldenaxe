#!/usr/bin/env python3
"""Add optional instruction-cycle counters to a local Genesis Plus GX checkout.

The counters only observe the emulator; they never alter emulated CPU cycles,
controller input, game RAM, or cartridge data. Rebuild the libretro core after
running this script. This does not modify or distribute the game's ROM.
"""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    args = parser.parse_args()
    cpu = args.checkout / 'core/m68k/m68kcpu.c'
    exports = args.checkout / 'libretro/link.T'
    original = cpu.read_bytes().decode()
    newline = '\r\n' if '\r\n' in original else '\n'
    source = original.replace('\r\n', '\n')
    if 'gaw_profile_begin' in source:
        print('Genesis Plus GX instruction profiler already installed')
        return
    helpers = '''static unsigned gaw_profile_enabled;
static unsigned long long gaw_profile_cycles[0x80000];
void gaw_profile_begin(void)
{
  memset(gaw_profile_cycles, 0, sizeof gaw_profile_cycles);
  gaw_profile_enabled = 1;
}
void gaw_profile_end(void) { gaw_profile_enabled = 0; }
const unsigned long long *gaw_profile_get_cycles(void) { return gaw_profile_cycles; }

'''
    edits = [
        ('void m68k_run(unsigned int cycles)', helpers+'void m68k_run(unsigned int cycles)'),
        ('    /* Decode next instruction */',
         '    unsigned gaw_profile_pc = REG_PC;\n'
         '    unsigned gaw_profile_start = m68k.cycles;\n\n'
         '    /* Decode next instruction */'),
        ('    USE_CYCLES(CYC_INSTRUCTION[REG_IR]);',
         '    USE_CYCLES(CYC_INSTRUCTION[REG_IR]);\n'
         '    if (gaw_profile_enabled && gaw_profile_pc < 0x100000)\n'
         '      gaw_profile_cycles[gaw_profile_pc >> 1] += m68k.cycles - gaw_profile_start;'),
    ]
    start = source.find('void m68k_run(unsigned int cycles)')
    end = source.find('\nint m68k_cycles(void)', start)
    if start < 0 or end < 0:
        parser.error('Unsupported emulator execution function')
    function = source[start:end]
    for before, after in edits:
        if function.count(before) != 1:
            parser.error('Unsupported emulator revision; profiler anchor is not unique')
        function = function.replace(before, after)
    source = source[:start]+function+source[end:]
    link = exports.read_text()
    if 'global:' not in link:
        parser.error('Unsupported libretro symbol export file')
    link = link.replace('global:', 'global: gaw_profile_*;', 1)
    cpu.write_bytes(source.replace('\n', newline).encode())
    exports.write_text(link)
    print('Instruction-cycle profiler installed; rebuild with Makefile.libretro')


if __name__ == '__main__':
    main()

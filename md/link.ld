OUTPUT_FORMAT("elf32-m68k")
ENTRY(_start)
SECTIONS {
 . = 0x00000000;
 .vectors : { KEEP(*(.vectors)) }
 . = 0x00000200;
 .text : { *(.text.start) *(.text*) *(.rodata*) }
 .data 0x00FF0000 : AT(LOADADDR(.text)+SIZEOF(.text)) { __data_start = .; *(.data*) __data_end = .; }
 .bss (NOLOAD) : { __bss_start = .; *(.bss*) *(COMMON) __bss_end = .; }
 __data_load = LOADADDR(.data);
 ASSERT(__bss_end <= 0x00FFFF00, "68K RAM overflow into stack")
 ASSERT(__data_load + SIZEOF(.data) <= 0x00200000, "ROM image overlaps SRAM window")
}

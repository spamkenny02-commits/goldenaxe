OUTPUT_FORMAT("elf32-m68k")
ENTRY(_start)
MEMORY {
 ROM (rx) : ORIGIN = 0x00000000, LENGTH = 0x00200000
 RAM (rw) : ORIGIN = 0x00FF0000, LENGTH = 0x0000FF00
}
PHDRS {
 rom PT_LOAD FLAGS(5);
 ram PT_LOAD FLAGS(6);
}
SECTIONS {
 .vectors 0x00000000 : { KEEP(*(.vectors)) } > ROM :rom
 .text 0x00000200 : { *(.text.start) *(.text*) *(.rodata*) } > ROM :rom
 .data : { __data_start = .; *(.data*) __data_end = .; } > RAM AT> ROM :ram
 .bss (NOLOAD) : { __bss_start = .; *(.bss*) *(COMMON) __bss_end = .; } > RAM :ram
 __data_load = LOADADDR(.data);
 ASSERT(__bss_start >= ORIGIN(RAM), "Mutable state is outside 68K work RAM")
 ASSERT(__bss_end <= 0x00FFFF00, "68K RAM overflow into stack")
 ASSERT(__data_load + SIZEOF(.data) <= 0x00200000, "ROM image overlaps SRAM window")
}

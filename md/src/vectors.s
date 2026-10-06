    .section .vectors,"a"
    .long 0x00FFFF00
    .long _start
    .rept 26
    .long _vblank_stub
    .endr
    .long _md_line_irq
    .long _vblank_stub
    .long _md_vblank_irq
    .rept 33
    .long _vblank_stub
    .endr

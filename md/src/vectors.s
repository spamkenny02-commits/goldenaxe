    .section .vectors,"a"
    .long 0x00FFFF00
    .long _start
    .rept 62
    .long _vblank_stub
    .endr

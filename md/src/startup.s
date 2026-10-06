    .section .text.start,"ax"
    .globl _start
_start:
    move.w  #0x2700,%sr
    lea     0x00FFFF00,%sp
    move.b  0x00A10001,%d0
    andi.b  #0x0F,%d0
    beq.s   1f
    move.l  #0x53454741,0x00A14000
1:
    lea     __data_load,%a0
    lea     __data_start,%a1
    lea     __data_end,%a2
2:  cmpa.l  %a2,%a1
    bcc.s   3f
    move.b  (%a0)+,(%a1)+
    bra.s   2b
3:
    lea     __bss_start,%a1
    lea     __bss_end,%a2
4:  cmpa.l  %a2,%a1
    bcc.s   5f
    clr.b   (%a1)+
    bra.s   4b
5:
    jsr     md_main
6:  bra.s   6b

    .globl _vblank_stub
_vblank_stub:
    rte

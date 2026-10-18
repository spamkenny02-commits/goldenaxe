    .text
    .align 2
    .global source_md_psg_wait_emit
source_md_psg_wait_emit:
    move.l %d2,-(%sp)
    move.l %d3,-(%sp)
    move.l %a2,-(%sp)
    /* SGDK ABI: scalar arguments occupy four-byte stack slots. */
    move.w 18(%sp),%d2
    move.w 22(%sp),%d3
    move.l 24(%sp),%a0
    move.l #0xc00011,%a1
    lea .Lsingle(%pc),%a2
    move.w 30(%sp),%d0
    cmpi.w #1,%d0
    bne .Lkind4
    lea .Lpair(%pc),%a2
    bra .Lprepare
.Lkind4:
    cmpi.w #2,%d0
    bne .Lprepare
    lea .Lquad(%pc),%a2
    bra .Lprepare
.Lprepare:
    /* Round upwards to the next20-master-tick counter value. All expensive
     * preparation happens before entering the intended line. */
    moveq #0,%d1
    move.w %d3,%d1
    addi.w #19,%d1
    divu.w #20,%d1
    addi.w #133,%d1
    cmpi.w #171,%d1
    bcs .Lraw
    subi.w #171,%d1
.Lraw:
    cmpi.w #148,%d1
    bcs .Lselected
    addi.w #85,%d1
.Lselected:
    move.w %d1,%d3
    cmpi.w #133,%d3
    bcs .LlastV
    /* raw85 also represents the rounded-up end-of-line target3420. */
    cmpi.w #3400,22(%sp)
    bhi .LlastV
.Lvwait:
    cmp.b 0xc00008,%d2
    bne.s .Lvwait
    move.b 0xc00009,%d1
.Lnegative:
    cmp.b %d3,%d1
    bcc.s .Lemit
    /* HC00..84 is after the negative-valued portion,so a skippedFF sample
     * still emits late rather than waiting an entire frame. */
    cmpi.b #133,%d1
    bcs.s .Lemit
.LnegativeRead:
    /* Signed order follows85..FF,00..7F. The maximum polling gap is far
     * smaller than the last00..7F span; the initial sample above also
     * handles entry already past this negative-valued target. */
    cmp.b 0xc00009,%d3
    bgt.s .LnegativeRead
    bra.s .Lemit
.LlastV:
    cmp.b 0xc00008,%d2
    bne.s .LlastV
    move.b 0xc00009,%d1
.LlastStart:
    cmpi.b #133,%d1
    bcs .Llast
    move.b 0xc00009,%d1
    bra .LlastStart
.Llast:
    cmp.b %d3,%d1
    bcc.s .Lemit
.LlastRead:
    cmp.b 0xc00009,%d3
    bhi.s .LlastRead
.Lemit:
    jmp (%a2)
.Lsingle:
    move.b (%a0)+,(%a1)
    bra .Lreturn
.Lpair:
    move.b (%a0)+,(%a1)
    .rept 19
    nop
    .endr
    move.b (%a0)+,(%a1)
    bra .Lreturn
.Lquad:
    move.b (%a0)+,(%a1)
    .rept 8
    nop
    .endr
    move.b (%a0)+,(%a1)
    .rept 8
    nop
    .endr
    move.b (%a0)+,(%a1)
    .rept 8
    nop
    .endr
    move.b (%a0)+,(%a1)
.Lreturn:
    move.l (%sp)+,%a2
    move.l (%sp)+,%d3
    move.l (%sp)+,%d2
    rts

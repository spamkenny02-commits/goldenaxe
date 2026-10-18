    .text
    .align 2
    .global source_md_psg_replay
source_md_psg_replay:
    movem.l %d2-%d7/%a2-%a4,-(%sp)
    move.l 40(%sp),%a2
    move.l 44(%sp),%a0
    move.w 50(%sp),%d7
    tst.w %d7
    beq .Lreplay_empty
    tst.w 10(%a2)
    bne .Lreplay_fault
    move.l (%a2),%d4
    move.w 4(%a2),%d2
    move.w 6(%a2),%d3
    move.w 8(%a2),%d6
    subi.w #256,%d6
    cmpi.w #6,%d6
    beq .Lreplay_valid
    cmpi.w #57,%d6
    bne .Lreplay_fault
.Lreplay_valid:
    move.l #0xc00011,%a1
    lea .Lreplay_hphase(%pc),%a3
.Lreplay_next:
    move.l (%a0),%d5
    lea .Lreplay_single(%pc),%a4
    cmpi.w #2,%d7
    bcs .Lreplay_poll
    move.l 6(%a0),%d0
    sub.l %d5,%d0
    cmpi.l #630,%d0
    bne .Lreplay_try_quad
    lea .Lreplay_pair(%pc),%a4
    bra .Lreplay_poll
.Lreplay_try_quad:
    cmpi.w #4,%d7
    bcs .Lreplay_poll
    cmpi.l #315,%d0
    bne .Lreplay_poll
    move.l 12(%a0),%d0
    sub.l %d5,%d0
    cmpi.l #630,%d0
    bne .Lreplay_poll
    move.l 18(%a0),%d0
    sub.l %d5,%d0
    cmpi.l #945,%d0
    bne .Lreplay_poll
    lea .Lreplay_quad(%pc),%a4
.Lreplay_poll:
    .global source_md_psg_replay_sample
source_md_psg_replay_sample:
    move.w 0xc00008,%d0
    moveq #0,%d1
    move.w %d0,%d1
    clr.b %d1
    sub.w %d2,%d1
    move.w %d0,%d2
    clr.b %d2
    lsr.w #8,%d1
    cmp.w %d6,%d1
    bcs .Lreplay_delta
    /* NTSC EA->E5 and PAL02->CA are backwards rawV discontinuities.
     * Normal FF->00 is already represented by the bytewise difference. */
    add.w %d6,%d1
    andi.w #255,%d1
    cmp.w %d6,%d1
    bcc .Lreplay_fault
.Lreplay_delta:
    tst.w %d1
    beq .Lreplay_horizontal
    mulu.w #3420,%d1
.Lreplay_horizontal:
    andi.w #255,%d0
    add.w %d0,%d0
    move.w (%a3,%d0.w),%d0
    sub.w %d0,%d3
    neg.w %d3
    ext.l %d3
    add.l %d3,%d1
    move.w %d0,%d3
    tst.l %d1
    bmi .Lreplay_fault
    add.l %d1,%d4
    move.l %d4,%d1
    sub.l %d5,%d1
    bmi .Lreplay_poll
    jmp (%a4)
.Lreplay_single:
    move.b 4(%a0),(%a1)
    addq.l #6,%a0
    subq.w #1,%d7
    bne .Lreplay_next
    bra .Lreplay_done
.Lreplay_pair:
    move.b 4(%a0),(%a1)
    .rept 18
    nop
    .endr
    move.b 10(%a0),(%a1)
    lea 12(%a0),%a0
    subq.w #2,%d7
    bne .Lreplay_next
    bra .Lreplay_done
.Lreplay_quad:
    move.b 4(%a0),(%a1)
    .rept 7
    nop
    .endr
    move.b 10(%a0),(%a1)
    .rept 7
    nop
    .endr
    move.b 16(%a0),(%a1)
    .rept 7
    nop
    .endr
    move.b 22(%a0),(%a1)
    lea 24(%a0),%a0
    subq.w #4,%d7
    bne .Lreplay_next
.Lreplay_done:
    move.l %d4,(%a2)
    move.w %d2,4(%a2)
    move.w %d3,6(%a2)
.Lreplay_empty:
    moveq #0,%d0
    bra .Lreplay_return
.Lreplay_fault:
    move.w #1,10(%a2)
    moveq #1,%d0
.Lreplay_return:
    movem.l (%sp)+,%d2-%d7/%a2-%a4
    rts
    .align 2
.Lreplay_hphase:
    .set .Lreplay_h,0
    .rept 256
    .set .Lreplay_ord,.Lreplay_h
    .if .Lreplay_h>=233
    .set .Lreplay_ord,.Lreplay_h-85
    .endif
    .if .Lreplay_ord<133
    .set .Lreplay_ord,.Lreplay_ord+171
    .endif
    .word (.Lreplay_ord-133)*20
    .set .Lreplay_h,.Lreplay_h+1
    .endr

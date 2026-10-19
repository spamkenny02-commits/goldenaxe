; Hardware timer only. No original game/audio reader code,no PSG writes.
; 68k RAM publication: seq,V,counterHi,counterLo,ready,error.
        org 0
        jp start
        defs 0x100-$,0
config: dw 0,0
        db 0,0
        defs 0x200-$,0
start:  di
        ld sp,0x1ff0
waitgo: ld a,(0x105)
        or a
        jr z,waitgo
        ld hl,(0x102)
        ld b,9
bank:   ld a,l
        ld (0x6000),a
        srl h
        rr l
        djnz bank
        ld ix,(0x100)
        ld a,(0x104)
        ld d,a
seed:   ld a,(0x7f08)
        cp 100
        jr nz,seed
        ld hl,100
        ld c,100
        ld e,0
        call publish
        ld (ix+4),1
loop:   ld b,48
delay:  djnz delay
        ld a,(0x7f08)
        ld b,a
        sub c
        ld c,b
        cp 5
        jr c,addlines
        add a,d
        cp 5
        jr nc,fault
addlines:
        add a,l
        ld l,a
        jr nc,nocarry
        inc h
nocarry:
        call publish
        jr loop
publish:
        inc e
        ld (ix+0),e
        ld (ix+1),c
        ld (ix+2),h
        ld (ix+3),l
        inc e
        ld (ix+0),e
        ret
fault:  ld (ix+5),1
stopped:
        halt
        jr stopped

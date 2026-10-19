; PSG output service only: no game or original reader logic.
; 68k status: seq,V,counterHi,counterLo,ready,error,headMirror,tail,grant,busy.
; ZRAM0106=head,0107=stop; 1000..12BF=32x22byte descriptor ring.
; 68k writes ZRAM only under short BUSREQ grants. Z80 never reads 68kRAM.
        org 0
        jp start
        defs 0x100-$,0
config: dw 0,0
        db 0,0
        defs 0x110-$,0
command:defs 6,0
counter:dw 100
lastv:  db 100
sequence:db 0
tail:   db 0
readptr:dw 0
entryptr:dw 0
sourceptr:dw 0
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
        ld hl,0x1000
        ld (readptr),hl
seed:   ld a,(0x7f08)
        cp 100
        jr nz,seed
        call clock
        ld (ix+4),1
loop:   ld a,(0x107)
        or a
        jp nz,stopped
        ld a,(0x106)
        ld b,a
        ld a,(tail)
        cp b
        jr nz,fetch
        ld (ix+8),1
        ld b,8
idle:   djnz idle
        call clock
        jr loop
fetch:  ld (ix+8),0
        ld (ix+9),1
        call clock
        ld hl,(readptr)
        ld de,command
        ld bc,6
        ldir
        push hl
        call clock
        pop hl
        ld a,(command+5)
        or a
        jp z,fault
        cp 17
        jp nc,fault
        ld c,a
        ld a,(command+4)
        cp 3
        jp nc,fault
        cp 2
        jr z,check630
        or a
        jr nz,copyvalues
        ld a,c
        cp 1
        jp nz,fault
        jr copyvalues
check630:
        ld a,c
        cp 9
        jp nc,fault
copyvalues:
        ld a,16
        sub c
        ld e,a
        ld d,0
        add hl,de
        ld a,0x10
        sub c
        ld e,a
        ld d,0x18
        ld b,0
        ldir
        ld a,(tail)
        inc a
        ld (tail),a
        ld (ix+7),a
        and 31
        jr nz,saveptr
        ld hl,0x1000
saveptr:
        ld (readptr),hl
        call clock
        call prepare
        call clock
coarse: ld de,(command)
        or a
        sbc hl,de
        jr z,near
        bit 7,h
        jr z,late
        inc hl
        ld a,h
        or l
        jr z,near
        ld de,7
        add hl,de
        bit 7,h
        jr z,close
        ld (ix+8),1
        jr coaststart
close:  ld (ix+8),0
coaststart:
        ld b,8
coast:  djnz coast
        call clock
        jr coarse
near:   ld (ix+8),0
        ld a,(sequence)
        inc a
        ld (ix+0),a
        ld a,(command+2)
        ld b,a
vwait:  ld a,(0x7f08)
        cp b
        jr z,setup
        sub b
        cp 5
        jr c,late
        ld c,a
        ld a,(0x104)
        add a,c
        cp 5
        jr c,late
        jr vwait
late:   ld (ix+8),0
        ld a,(sequence)
        inc a
        ld (ix+0),a
        call setupregs
        jp (iy)
setup:  call setupregs
hwait:  ld a,(0x7f08)
        cp b
        jr nz,emit
        ld a,(0x7f09)
        add a,123
        cp c
        jr c,hwait
emit:   jp (iy)
prepare:
        ld a,(command+5)
        ld c,a
        ld a,(command+4)
        cp 2
        jr z,select630
        ld a,16
        sub c
        ld e,a
        ld d,0
        ld hl,burst315
        add hl,de
        add hl,de
        add hl,de
        jr selected
select630:
        ld a,8
        sub c
        ld e,a
        ld d,0
        ld hl,burst630
        add hl,de
        add hl,de
        add hl,de
        add hl,de
        add hl,de
        add hl,de
        add hl,de
selected:
        ld (entryptr),hl
        ld a,0x10
        sub c
        ld l,a
        ld h,0x18
        ld (sourceptr),hl
        ret
setupregs:
        ld iy,(entryptr)
        ld hl,(sourceptr)
        ld de,0x7f11
        ld a,(command+3)
        add a,123
        ld c,a
        ld a,(command+2)
        ld b,a
        ret
burst315:
        rept 16
        ld a,(hl)
        inc l
        ld (de),a
        endm
        jr finished
burst630:
        rept 7
        ld a,(hl)
        inc l
        ld (de),a
        ld bc,0
        add hl,bc
        endm
        ld a,(hl)
        inc l
        ld (de),a
finished:
        call clock
        ld (ix+9),0
        jp loop
clock:  ld a,(0x7f08)
        ld b,a
        ld a,(lastv)
        ld c,a
        ld a,b
        sub c
        cp 6
        jr c,delta
        ld c,a
        ld a,(0x104)
        add a,c
        cp 6
        jr nc,fault
delta:  ld e,a
        ld d,0
        ld hl,(counter)
        add hl,de
        ld (counter),hl
        ld a,b
        ld (lastv),a
        ld a,(sequence)
        inc a
        ld (ix+0),a
        ld (ix+1),b
        ld (ix+2),h
        ld (ix+3),l
        inc a
        ld (sequence),a
        ld (ix+0),a
        ret
fault:  ld (ix+5),1
stopped:
        ld (ix+4),0
        ld (ix+8),0
        ld (ix+9),0
halted: halt
        jr halted

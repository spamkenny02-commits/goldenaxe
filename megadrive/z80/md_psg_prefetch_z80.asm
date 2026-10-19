; Experimental sixteen-buffer PSG transport. Game/source reader remain 68000.
; Same 32x22 byte ZRAM ring and 10 byte native mailbox as md_psg_output_z80.
; IX owns active descriptor; IY owns the write-only 68000 status mailbox.
        org 0
        jp start
        defs 0x100-$,0
config: dw 0,0
        db 0,0
        defs 0x110-$,0
counter:dw 100
lastv:  db 100
sequence:db 0
tail:   db 0
readptr:dw 0
writeptr:dw commands
nextready:db 0
prefetches:dw 0
maxready:db 0
        defs 0x200-$,0
commands:defs 16*16,0
        defs 0x400-$,0
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
        ld iy,(0x100)
        ld ix,commands
        ld hl,0x1000
        ld (readptr),hl
seed:   ld a,(0x7f08)
        cp 100
        jr nz,seed
        call clock
        ld (iy+4),1
loop:   ld a,(0x107)
        or a
        jp nz,stopped
        call available
        jr nz,fetch
        ld (iy+8),1
        ld b,1
idle:   djnz idle
        call clock
        jr loop
fetch:  ld (iy+8),0
        ld (iy+9),1
        call invalidate
        call sample
        call copy
        call advancewrite
        call sample
coarse: ld e,(ix+0)
        ld d,(ix+1)
        or a
        sbc hl,de
        jp z,near
        bit 7,h
        jp z,late
        inc hl
        ld a,h
        or l
        jp z,near
        inc hl
        ld a,h
        or l
        jp z,near
        inc hl
        ld a,h
        or l
        jp z,near
        ld de,17
        add hl,de
        bit 7,h
        jr z,close
        ld a,(nextready)
        cp 15
        jr nc,grant
        call available
        jr z,grant
        ; Do not take a new descriptor near the active deadline.
        ; Local values are separate from the producer's ring slots.
        ld (iy+8),0
        call invalidate
        call sample
        push ix
        ld ix,(writeptr)
        call copy
        call sample
        call advancewrite
        pop ix
        ld a,(nextready)
        inc a
        ld (nextready),a
        ld b,a
        ld a,(maxready)
        cp b
        jr nc,recorded
        ld a,b
        ld (maxready),a
recorded:
        ld hl,(prefetches)
        inc hl
        ld (prefetches),hl
        call sample
        jp coarse
grant:  ld (iy+8),1
        jr coaststart
close:  ld (iy+8),0
coaststart:
        ld b,1
coast:  djnz coast
        call clock
        jp coarse
near:   ld (iy+8),0
        call invalidate
        call sample
        ; Prepare output registers before the target line, not after it.
        ; Private clock samples use the main set; EXX preserves this setup.
        call setupregs
        exx
        ld b,(ix+2)
vwait:  ld a,(0x7f08)
        cp b
        jr z,setup
        sub b
        cp 5
        jr c,latewait
        ld c,a
        ld a,(0x104)
        add a,c
        cp 5
        jr c,latewait
        jr vwait
latewait:
        ; This path actually waited; only the coarse path can reuse a sample.
        call sample
        exx
        jr emit
late:   ld (iy+8),0
        call invalidate
        ; Coarse/finished just sampled. No grant or wait before this burst.
        call setupregs
        jr emit
setup:  call sample
        exx
hwait:  ld a,(0x7f08)
        cp b
        jr nz,emit
        ld a,(0x7f09)
        add a,123
        cp c
        jr c,hwait
emit:   ld bc,0x7f11
        jp (hl)
available:
        ld a,(0x106)
        ld b,a
        ld a,(tail)
        cp b
        ret
invalidate:
        ld a,(sequence)
        inc a
        ld (iy+0),a
        ret
advanceix:
        push hl
        push ix
        pop hl
        ld a,l
        add a,16
        ld l,a
        push hl
        pop ix
        pop hl
        ret
advancewrite:
        ld hl,(writeptr)
        ld a,l
        add a,16
        ld l,a
        ld (writeptr),hl
        ret
copy:   ld hl,(readptr)
        push ix
        pop de
        ld bc,6
        rept 6
        ldi
        endm
        ; Metadata read and destination selection may be slower on a new CPU
        ; register allocation; bound the subsequent value copy separately.
        push hl
        call sample
        pop hl
        ld a,(ix+5)
        or a
        jp z,fault
        cp 17
        jp nc,fault
        ld c,a
        ld a,(ix+4)
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
        push hl
        push ix
        pop hl
        ld a,l
        add a,16
        pop hl
        sub c
        ld e,a
        ld (ix+8),a
        ld d,0x18
        ld (ix+9),d
        ld b,0
        ldir
        push hl
        call sample
        pop hl
        ld a,(tail)
        inc a
        ld (tail),a
        ld (iy+7),a
        and 31
        jr nz,saveptr
        ld hl,0x1000
saveptr:
        ld (readptr),hl
        call sample
        ld a,(ix+5)
        ld c,a
        ld a,(ix+4)
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
        ld (ix+6),l
        ld (ix+7),h
        ret
setupregs:
        ld l,(ix+6)
        ld h,(ix+7)
        ld e,(ix+8)
        ld d,(ix+9)
        ld a,(ix+3)
        add a,123
        ld c,a
        ld b,(ix+2)
        ret
burst315:
        rept 16
        ld a,(de)
        inc e
        ld (bc),a
        endm
        jr finished
burst630:
        rept 7
        ld a,(de)
        inc e
        ld (bc),a
        ld hl,0
        add hl,de
        endm
        ld a,(de)
        inc e
        ld (bc),a
finished:
        call sample
        ld a,(nextready)
        or a
        jr z,empty
        dec a
        ld (nextready),a
        call advanceix
        ; Grant is still revoked, busy remains set and publication stays odd.
        ; Reuse the finished sample for a ready command on/past its line.
        ld e,(ix+0)
        ld d,(ix+1)
        or a
        sbc hl,de
        jr z,readyline
        bit 7,h
        jr z,readyemit
        inc hl
        ld a,h
        or l
        jr z,readywait
        inc hl
        ld a,h
        or l
        jr z,readywait
        ld hl,(counter)
        jp coarse
readywait:
        call setupregs
        exx
        ld b,(ix+2)
        jp vwait
readyline:
        call setupregs
        jp hwait
readyemit:
        call setupregs
        jp emit
empty:  call advanceix
        ld (iy+9),0
        jp loop
clock:  call sample
        ld a,(sequence)
        inc a
        ld (iy+0),a
        ld (iy+1),b
        ld (iy+2),h
        ld (iy+3),l
        inc a
        ld (sequence),a
        ld (iy+0),a
        ret
sample: ld a,(0x7f08)
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
        ret
fault:  ld (iy+5),1
stopped:
        ld (iy+4),0
        ld (iy+8),0
        ld (iy+9),0
halted: halt
        jr halted

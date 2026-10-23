"""Instruction-derived map-building work at 6B33/6C65; excludes interrupts/waits."""
def level1_cost(work):
    total=16 # LD IX,LD B,last DJNZ correction
    for n in range(22):
        e=work[n*32:n*32+32]
        if not e[0]:total+=94;continue
        total+=624+(58 if e[1]<14 else 0)
        if e[1]==21:total+=89 if e[4]==2 else 75
    return total

def level2_cost(work,blocks):
    prefix=sum([11,7,13,19,4,19,4,4,7,14,15,19,19,19,11,4,19,19,7,19])
    total=16
    for n in range(4):
        e=work[n*32:n*32+32];b=blocks[e[2]*6:e[2]*6+6];address=int.from_bytes(b[:2],'little')+e[1]
        carries=sum(((address+row*64)&255)+64>=256 for row in range(b[4]))
        total+=prefix+b[4]*(75+48*b[5])-5-carries+133+48
        if e[2]==9:total+=37
    return total

def advance1(work):
    for n in range(22):
        off=n*32
        if not work[off]:continue
        work[off+1]=(work[off+1]+1)&255
        if work[off+1]==22:
            work[off+1]=0;work[off+4]+=1
            if work[off+4]==3:work[off]=0

def advance2(work):
    for n in range(4):
        off=n*32;work[off+2]+=1
        if work[off+2]==10:work[off+2]=7;work[off+9]+=1

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

def multiply_cost(sample,amplitude,cosine=False):
    total=(7 if cosine else 0)+sum([7,4,7,13,7,10,4,4,11 if sample<0 else 12,4,4])
    total+=33 if amplitude&128 else 16
    total+=sum(33 if amplitude&bit else 27 for bit in [64,32,16,8,4,2])
    return total+(22 if amplitude&1 else 16)+10

def orbit_cost(phase,clock,x,sine):
    amplitude=16+(8-(clock&7) if clock&8 else clock&7)
    sx=sine[(phase+64)&255];sx=sx-256 if sx&128 else sx
    sy=sine[phase];sy=sy-256 if sy&128 else sy
    dx=(sx*2*amplitude)>>8;target=x+dx
    total=19+4+5+10+7+7+12+(22 if clock&8 else 12)+7+4+23+19+17+multiply_cost(sx,amplitude,True)
    total+=13+4+19+8+(11 if dx<0 else 12)
    if not 0<=target<256:total+=12
    else:
        total+=7+7+7
        if target<4 or target>=252:total+=12
        else:total+=7+19+17+multiply_cost(sy,amplitude)+13+4+7+19+23
    return total+19+7+19+13+7+7+19+10

def sprites_prefix_cost(snapshot,sine):
    total=16+10 #6E3F prefix, finalDJNZ correction, tailJP0938
    for n in range(8):
        e=snapshot[0x330+n*48:0x360+n*48]
        cost=34 if not e[0] else orbit_cost((e[0x10]-9)&255,snapshot[0x2f],snapshot[0x313],sine)
        total+=76+cost
    return total

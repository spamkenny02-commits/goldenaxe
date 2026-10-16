"""Original8211 standalone effect restoration, including DE and Z80 T/M1."""
from audio_dispatch_cost import POINTER_COST,CHANNEL_COPY_COST
from audio_dispatch_refresh import POINTER_M1,CHANNEL_COPY_M1

def restore_effect_refresh(rom,state,command,de):
    if not 0x90<=command<=0xac:raise NotImplementedError(hex(command))
    r=bytearray(state);cost=17;m1=1;writes=[]
    r[14]=command;cost+=13+4+13+4+10+4+10;m1+=7
    if not r[15]&128:
        cost+=10+(12 if not r[15] else 7+10)+7+6+7+7+11
        m1+=7 if not r[15] else 8
        target=0x160 if r[15] else 0x130;r[target]=r[15]
        writes.append((r[target+1]+31)&255)
    cost+=7+10+17+POINTER_COST+6+6+7+6+7;m1+=3+POINTER_M1+5
    def read(a):return rom[0x18000+(a&0x3fff)]
    pointer=0x8b30+(command-0x90)*2;header=read(pointer)|(read(pointer+1)<<8)
    channel=read(header+2);header+=1
    def result():return dict(state=bytes(r),tstates=cost,m1_fetches=m1,de=de,writes=writes)
    if channel!=0xc0:
        cost+=7+10+14+7+4+10;m1+=7;de=0xdf60;target=0x160;background=0xd0
        if r[target]&128:r[15]=r[target];cost+=13+10;m1+=2;return result()
        cost+=7+12;m1+=2;r[15]=1
    else:
        cost+=12+13+4+10;m1+=4
        if r[0x160]&128:
            cost+=7+7;m1+=2
            if not r[0x160]&64:r[15]=128;cost+=12+13+10;m1+=3;return result()
            cost+=7;m1+=1
        cost+=10+14+7+4+10;m1+=6;de=0xdf30;target=0x130;background=0xa0
        if r[target]&128:r[15]=r[target];cost+=13+10;m1+=2;return result()
        cost+=4;m1+=1;r[15]=0
    cost+=13+10+23+CHANNEL_COPY_COST;m1+=4+CHANNEL_COPY_M1
    r[background]|=4;r[target:target+9]=bytes(read(header+i) for i in range(9))
    r[target+9]=0x30;r[target+10]=1;r[target+0x27:target+0x2a]=bytes(3)
    de=0xde00+target+0x30
    return result()

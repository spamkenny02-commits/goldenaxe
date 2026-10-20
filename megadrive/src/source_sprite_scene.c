#include "source_sprite_scene.h"
static u8 word(const u8 *bank,u16 address,u16 *value)
{
    if(address<0x8000 || address>=0xbfff) return 0;
    address-=0x8000;*value=bank[address]|((u16)bank[address+1]<<8);return 1;
}
u8 source_sprite_scene(u8 *ram,const u8 *bank,SourceSpriteSceneOutput *output)
{
    u8 sat[192],sorted[128],collision[64],changed[32],order[32];
    u16 n,j,k,total=0,active=0,address,pointer,start,count,slot;
    u8 rotating,x,y,base,flag;const u8 *entity,*frame;
    SourceSpriteSceneOutput result;
    if(!ram || !bank || !output) return 0;
    for(n=0;n<192;n++) sat[n]=ram[0x1d40+n];
    for(n=0;n<128;n++) sorted[n]=ram[0x1100+n];
    for(n=0;n<32;n++) changed[n]=0;
    rotating=ram[0x47]>=8 || (ram[0x1b]&64);
    if(rotating) {
        start=(ram[0x2f]&3)*32;
        for(n=0;n<32;n++) {
            if(!word(bank,0x8000+start+n*2,&address) || address<0xc300 ||
               address>0xc8d0 || (address-0xc300)%48) return 0;
            slot=(address-0xc300)/48;entity=ram+address-0xc000;
            if(entity[0] && ((entity[3]&1) || !slot)) order[active++]=slot;
        }
    } else {
        /* The source scans31..0 and inserts before equal Y values. */
        for(n=32;n>0;n--) {
            slot=n-1;entity=ram+0x300+slot*48;
            if(!(entity[3]&1) && slot) continue;
            /* 0938 sets hero visibility before the ordering pass. */
            y=entity[0x11];j=0;
            while(j<active && y<sorted[64+j]) j++;
            for(k=active;k>j;k--) {sorted[k]=sorted[k-1];sorted[64+k]=sorted[63+k];}
            sorted[j]=slot;sorted[64+j]=y;active++;
        }
        sorted[active]=255;
        for(n=0;n<active;n++) order[n]=sorted[n];
    }
    for(n=0;n<active;n++) {
        slot=order[n];entity=ram+0x300+slot*48;
        address=(entity[8]|((u16)entity[9]<<8))+(u8)(entity[10]*2);
        if(!word(bank,address,&pointer)) return 0;
        address=pointer+(u8)(entity[11]*2);
        if(!word(bank,address,&pointer) || pointer<0x8000 || pointer>=0xc000) return 0;
        start=pointer-0x8000;flag=bank[start];count=flag&127;
        if(!count || count>64-total || (u32)start+3+(u32)count*3>16384) return 0;
        frame=bank+start;collision[slot*2]=frame[1];collision[slot*2+1]=frame[2];changed[slot]=1;
        x=entity[0x13];y=entity[0x11];base=(flag&128)?0:entity[2];
        for(j=0;j<count;j++) {
            y+=frame[3+j];x+=frame[3+count+j*2];
            sat[total+j]=y;sat[64+(total+j)*2]=x;
            sat[65+(total+j)*2]=base+frame[4+count+j*2];
        }
        total+=count;
    }
    /* At64 entries the real terminator aliases the first X byte. */
    sat[total]=208;
    ram[0x303]|=1;
    ram[0x24]=(0xdd40+total)&255;ram[0x25]=(0xdd40+total)>>8;
    ram[0x26]=(0xdd80+total*2)&255;ram[0x27]=(0xdd80+total*2)>>8;
    if(!rotating) for(n=0;n<128;n++) ram[0x1100+n]=sorted[n];
    for(n=0;n<32;n++) if(changed[n]) {
        ram[0x300+n*48+0x1b]=collision[n*2];ram[0x300+n*48+0x1c]=collision[n*2+1];
    }
    for(n=0;n<192;n++) ram[0x1d40+n]=sat[n];
    result.count=total;result.y_end=0xdd40+total;result.xy_end=0xdd80+total*2;
    result.rotating=rotating;result.bank=12;*output=result;return 1;
}

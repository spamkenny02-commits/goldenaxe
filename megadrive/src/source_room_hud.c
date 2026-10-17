#include "source_room_hud.h"
#include "source_ram_planes.h"
#define S(t,m) do { if(!source_clock_plain(clock,t,m,source_irq_interrupt,context)) return 0; } while(0)
static u8 seq(SourceClock *clock,SourceIrqContext *context,const u8 *ticks,u16 count)
{
    u16 n,total=0;u8 t,fetches=0;
    if(clock->iff && !clock->first && !clock->pending && !clock->blocked)
    {
        for(n=0;n<count;n++) {t=ticks[n];total+=t;fetches+=(t==8 || t==14 || t==19 || t==20 || t==21)?2:1;}
        if(source_clock_block(clock,total,fetches)) return 1;
    }
    for(n=0;n<count;n++) { t=ticks[n];S(t,(t==8 || t==14 || t==19 || t==20 || t==21)?2:1); }
    return 1;
}
#define SEQ(a) do { if(!seq(clock,context,a,sizeof(a))) return 0; } while(0)
static void put(SourceIrqContext *context,SourceWorldMapData *map,u16 address,u8 value)
{
    if(address<0xdc00) map->tilemap[address-0xd600]=value;
    else if(address<0xdd00) map->cells[address-0xdc00]=value;
    else context->ram[80+address-0xdd00]=value;
}
static void word(SourceIrqContext *context,SourceWorldMapData *map,u16 address,u8 low,u8 high)
{
    put(context,map,address,low);put(context,map,address+1,high);
}
static u8 room_map(SourceClock *clock,SourceIrqContext *context,const u8 *tiles,SourceWorldMapData *map)
{
    static const u8 prefix[]={11,11,11,11,10,7};
    static const u8 lookup[]={17,11,4,8,4,7,4,4,4,4,4,7,10,11,7,4,11,11,11,10,8};
    static const u8 lookup_tail[]={11,7,6,7,10,10};
    static const u8 advance[]={7,6,7,6,4,4,7},row_tail[]={4,4,7};
    u16 x,y,index,destination=0;SEQ(prefix);
    for(y=0;y<20;y++)
    {
        /* Include the final column/row branches in a whole-row span when
         * no IRQ can observe its intermediate tile words. */
        if(source_clock_block(clock,7+16*((y&1)?603:597)-5+15+(y<19?12:7),
                              16*((y&1)?88:84)+5))
        {
            for(x=0;x<32;x++)
            {
                index=map->cells[(y>>1)*16+(x>>1)]*8+(y&1)*4+(x&1)*2;
                map->tilemap[destination++]=tiles[index];map->tilemap[destination++]=tiles[index+1];
            }
            continue;
        }
        S(7,1);
        for(x=0;x<32;x++)
        {
            u16 pairs,k;
            /* Two ordinary columns:597T/84M1 on even rows,603T/88M1 on
             * odd rows. Leave the final two columns for their exit branch.
             * The mirror writes are committed before the next IRQ boundary. */
            pairs=0;
            if(!(x&1) && x<30)
                pairs=source_clock_repeat(clock,(y&1)?603:597,(y&1)?88:84,(30-x)>>1);
            if(pairs)
            {
                for(k=0;k<pairs*2;k++)
                {
                    index=map->cells[(y>>1)*16+((x+k)>>1)]*8+(y&1)*4+((x+k)&1)*2;
                    map->tilemap[destination++]=tiles[index];map->tilemap[destination++]=tiles[index+1];
                }
                x+=pairs*2-1;continue;
            }
            SEQ(lookup);
            if(!(y&1)) S(12,1);else { S(7,1);S(8,2); }
            S(8,2);
            if(!(x&1)) S(12,1);else { S(7,1);S(8,2); }
            SEQ(lookup_tail);
            index=map->cells[(y>>1)*16+(x>>1)]*8+(y&1)*4+(x&1)*2;
            SEQ(advance);map->tilemap[destination++]=tiles[index];map->tilemap[destination++]=tiles[index+1];
            S(x<31?12:7,1);
        }
        SEQ(row_tail);S(y<19?12:7,1);
    }
    for(x=0;x<5;x++) S(10,1);
    return 1;
}
static u8 gauge(SourceClock *clock,SourceIrqContext *context,SourceWorldMapData *map,u8 value,u8 maximum,u8 magic)
{
    static const u8 health_prefix[]={10,10,13,4,13,4,4,4,7,4};
    static const u8 magic_prefix[]={10,10,20,4,4,4,4,7,4};
    static const u8 subtract[]={4,7,4},full[]={7,7,6,7,6},health_empty[]={10,6,7,6};
    static const u8 store[]={7,6,7,6};
    u16 n,m,count=(maximum>>3)&31,address=magic?0xdbde:0xdb5e;
    if(!count) count=256;
    if(magic) SEQ(magic_prefix);else SEQ(health_prefix);
    for(n=0;n<count;n++)
    {
        SEQ(subtract);
        if(value>=8)
        {
            value-=8;SEQ(full);word(context,map,address,magic?0x90:0x8b,0x19);address+=2;
            S(n+1<count?13:8,1);
            if(n+1==count) { S(10,1);break; }
        }
        else
        {
            S(12,1);
            if(magic)
            {
                S(4,1);
                for(m=n;m<count;m++)
                { SEQ(store);word(context,map,address,0x91,0x19);address+=2;S(m+1<count?13:8,1); }
            }
            else
            {
                S(7,1);S(8,2);S(7,1);S(8,2);SEQ(store);
                word(context,map,address,0x8f-(value>>1),0x19);address+=2;S(n+1<count?13:8,1);
                for(m=n+1;m<count;m++)
                { SEQ(health_empty);word(context,map,address,0x8f,0x19);address+=2;S(m+1<count?13:8,1); }
            }
            S(10,1);break;
        }
    }
    return 1;
}
u8 source_hud_prepare(SourceClock *clock,SourceIrqContext *context,SourceWorldMapData *map,const u8 *bank4,const u8 *hud)
{
    static const u8 prefix[]={7,13,10,10,17,7};
    static const u8 offsets[]={7,7,7,6,7,7,7,6};
    static const u8 icon_prefix[]={10,10,10,17},icon_row[]={11,11,4},icon_tail[]={10,10,7,4,4,12,4};
    static const u8 dispatch[]={11,4,17,7,4,10},dispatch_tail[]={11,4,4,12,7,6,7,4,4};
    static const u8 gems_prefix[]={10,14,7},gem_present[]={7,7,19,19,11,14,19,19};
    static const u8 gold_prefix[]={13,10,10,7,17},digit_loop[]={4,4,12},digit_tail[]={4,4,7,4,7,6,10,6,10};
    static const u8 gold_tail[]={7,7,12,6,10,6,10},return_gauge[]={14,10,10};
    static const u8 priority[]={7,7,7,6,6};
    const u8 *source=bank4+0x26ab;u8 *output=map->tilemap+0x500;
    u16 n,row,col,number,pos,q,address;
    SEQ(prefix);
    if(!source_ram_planes(clock,context,&source,output,0xdb00,2)) return 0;
    S(10,1);S(7,1);
    if(source_clock_block(clock,128*67-5,128*9))
        for(n=0;n<128;n++) {output[n*2]=(u8)(output[n*2]+0xd0);output[n*2+1]|=0x18;}
    else
        for(n=0;n<128;n++)
        {SEQ(offsets);output[n*2]=(u8)(output[n*2]+0xd0);output[n*2+1]|=0x18;S(n<127?13:8,1);}
    SEQ(icon_prefix);
    for(row=0;row<2;row++)
    {
        SEQ(icon_row);
        for(col=0;col<4;col++) { S(16,2);output[0x58+row*64+col]=context->low[0x1e91+row*4+col];S(col<3?13:8,1); }
        SEQ(icon_tail);S(row==0?12:7,1);
    }
    S(10,1);S(7,1);
    for(number=0;number<4;number++)
    {
        SEQ(dispatch);S(15,2);SEQ(dispatch_tail);
        if(!number)
        {
            SEQ(gems_prefix);
            for(n=0;n<9;n++)
            {
                S(12,2);
                if(hud[5+n]&128)
                {
                    SEQ(gem_present);address=0xdb00+context->low[0x1edd+n*2];
                    word(context,map,address,context->low[0x1edc+n*2],0x59);
                }
                else S(12,1);
                S(6,1);S(10,2);S(10,2);S(n<8?13:8,1);
            }
            S(10,1);
        }
        else if(number==1)
        {
            SEQ(gold_prefix);
            for(pos=0;pos<2;pos++)
            {
                if(pos) { S(7,1);S(17,1); }
                q=pos?(hud[4]%100)/10:hud[4]/100;
                S(7,1);for(n=0;n<q;n++) SEQ(digit_loop);
                SEQ(digit_tail);word(context,map,0xdbd0+pos*2,0xf0+q,0x18);
            }
            SEQ(gold_tail);word(context,map,0xdbd4,0xf0+hud[4]%10,0x18);
        }
        else if(!gauge(clock,context,map,hud[number==2?2:0],hud[number==2?3:1],number==2)) return 0;
        SEQ(return_gauge);S(number<3?13:8,1);
    }
    S(10,1);S(7,1);
    if(source_clock_block(clock,128*46-5,128*6))
        for(n=0;n<128;n++) output[n*2+1]|=0x40;
    else
        for(n=0;n<128;n++) {SEQ(priority);output[n*2+1]|=0x40;S(n<127?13:8,1);}
    S(10,1);return 1;
}
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,SourceGraphicsCheckpoint checkpoint,void *user)
{
    if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
    return !checkpoint || checkpoint(user,pc,clock,context);
}
u8 source_room_hud_prepare(SourceClock *clock,SourceIrqContext *context,
                            SourceGraphicsData *graphics,SourceWorldMapData *map,
                            const u8 *bank4,const u8 *hud,SourceGraphicsCheckpoint checkpoint,void *user)
{
    if(!clock || !context || !graphics || !map || !bank4 || !hud ||
       !map->cells || !map->tilemap || !graphics->metatiles || context->ram[0x2e]) return 0;
    S(17,1);S(17,1);
    if(!room_map(clock,context,graphics->metatiles,map) || !point(clock,context,0x1de5,checkpoint,user)) return 0;
    S(17,1);
    if(!source_hud_prepare(clock,context,map,bank4,hud)) return 0;
    return point(clock,context,0x1de8,checkpoint,user);
}
#undef SEQ
#undef S

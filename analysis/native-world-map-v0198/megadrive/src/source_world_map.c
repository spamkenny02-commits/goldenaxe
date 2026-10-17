#include "source_world_map.h"
#include "source_ram_planes.h"
#define S(t,m) do { if(!source_clock_execute(clock,t,m,SOURCE_CLOCK_NONE,source_irq_interrupt,context)) return 0; } while(0)
static u8 seq(SourceClock *clock,SourceIrqContext *context,const u8 *ticks,u16 count)
{
    u16 n;for(n=0;n<count;n++) S(ticks[n],ticks[n]==20?2:1);return 1;
}
#define SEQ(a) do { if(!seq(clock,context,a,sizeof(a))) return 0; } while(0)
static u8 *memory(SourceIrqContext *context,SourceWorldMapData *map,u16 address)
{
    if(address>=0xdd00 && address<0xde00) return context->ram+80+address-0xdd00;
    if(address>=0xdc00 && address<0xdd00) return map->cells+address-0xdc00;
    if(address>=0xd600 && address<0xdc00) return map->tilemap+address-0xd600;
    return 0;
}
static u8 patch(SourceClock *clock,SourceIrqContext *context,SourceWorldMapData *map,
                 const u8 *tiles,u16 cell,u8 tile)
{
    static const u8 prefix[]={11,11,7,4,7,11,11,11,10,11,11,4,7,4,7,4,11,11,11,4,7,4,4,4,11,10,11,4,16,7,7,4,7,4,7,4,7,4,7,4,16,10};
    u16 address=0xd600+(cell&0xf0)*8+(cell&15)*4,pointer,n,row;
    u8 *write=memory(context,map,0xdc00+cell);
    if(!write) return 0;
    SEQ(prefix);*write=tile;
    pointer=(u16)context->ram[0x34]|((u16)context->ram[0x35]<<8);
    if((pointer&0xff00)!=0xdd00) return 0;
    for(n=0;n<5;n++) context->ram[80+((pointer+n)&255)]=n<3?2:n==3?(u8)address:(u8)(address>>8);
    pointer=(pointer&0xff00)|((pointer+5)&255);
    context->ram[0x34]=pointer;context->ram[0x35]=pointer>>8;
    for(row=0;row<2;row++)
    {
        for(n=0;n<4;n++)
        {
            S(16,2);write=memory(context,map,address+row*64+n);
            if(!write) return 0;
            *write=tiles[tile*8+row*4+n];
        }
        if(!row)
        {
            S(7,1);S(4,1);S(4,1);
            if(((address+4)&255)+60<256) S(12,1);
            else { S(7,1);S(4,1); }
        }
    }
    S(10,1);S(10,1);S(10,1);return 1;
}
static u8 copy8(SourceClock *clock,SourceIrqContext *context,const u8 *source,u8 *destination)
{
    u16 n;for(n=0;n<8;n++) { S(n<7?21:16,2);destination[n]=source[n]; }return 1;
}
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,SourceGraphicsCheckpoint checkpoint,void *user)
{
    if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
    return !checkpoint || checkpoint(user,pc,clock,context);
}
#define POINT(pc) do { if(!point(clock,context,pc,checkpoint,user)) return 0; } while(0)

u8 source_world_map_load(SourceClock *clock,SourceIrqContext *context,u16 room,u8 flags,
                          const u8 *map_bank,const u8 *bank2,SourceGraphicsData *graphics,
                          SourceWorldMapData *map,SourceGraphicsCheckpoint checkpoint,void *user)
{
    static const u8 classify[]={11,11,11,11,17,13,4,7,7,13,7,7,7,13,7,7,7,7,4,13,10};
    static const u8 decode_call[]={11,4,7,13,7,7,6,7,4,10,7,17};
    static const u8 metadata_prefix[]={17,17,13,4,11,7,13,20,4,4,10,12,10};
    static const u8 scan[]={7,4,7,4,7,11,12},found[]={7,4,7,4,12,6},missing[]={7,4,12,10,12};
    static const u8 select[]={13,4,12,17},persistent[]={13,7,12,7,10,4,4,7,4,7,4,4,7,10};
    static const u8 transformation[]={17,20,4,7,4,10,10,4,4,12,7,6,7,4,4};
    static const u8 below_prefix[]={10,11,4,7,10,7},below_scan[]={7,6,10};
    static const u8 clear[]={13,7,12,10};
    static const u8 restore[]={17,17,13,4,5,13,4,7,10,10,10,11,11},copy_prefix[]={10,10,10};
    static const u8 special[]={17,20,10,4};
    const u8 *source,*record;u16 offset,n,cell;u8 kind,value,matched=0;
    if(!clock || !context || !map || !graphics || !map->cells || !map->tilemap ||
       !graphics->metatiles || !map_bank || !bank2 || !(flags&1) || context->ram[0x2e] ||
       (room!=0x1a && room!=0x3c && room!=0x36 && room!=0x87 && room!=0x6d && room!=0x96)) return 0;
    S(17,1);SEQ(classify);S(16,1);SEQ(decode_call);
    offset=(room*2)&255;n=(u16)map_bank[offset]|((u16)map_bank[offset+1]<<8);
    source=map_bank+(n&0x3fff);
    if(!source_ram_planes(clock,context,&source,map->cells,0xdc00,1)) return 0;
    POINT(0x192a);SEQ(metadata_prefix);
    offset=0x3b62;
    while(bank2[offset] && bank2[offset]!=(u8)room) { SEQ(scan);offset+=4; }
    if(bank2[offset]) { SEQ(found);record=bank2+offset+1; }
    else { SEQ(missing);record=context->low+0x199e; }
    S(10,1);
    for(n=0;n<3;n++) { S(16,2);map->metadata[n]=record[n]; }
    SEQ(select);S(16,1);SEQ(persistent);SEQ(transformation);
    cell=map->metadata[1];kind=map->metadata[2];
    if(kind!=0 && kind!=4) return 0;
    if(!kind) { S(4,1);S(12,1); } else S(7,1);
    S(17,1);
    if(!patch(clock,context,map,graphics->metatiles,cell,kind)) return 0;
    SEQ(below_prefix);cell+=16;
    source=memory(context,map,0xdc00+cell);if(!source) return 0;value=*source;
    for(n=0;n<4;n++)
    {
        SEQ(below_scan);
        if(value==context->low[0x1b05+n*2])
        {
            S(7,1);if(!patch(clock,context,map,graphics->metatiles,cell,context->low[0x1b06+n*2])) return 0;
            matched=1;break;
        }
        S(6,1);S(n<3?13:8,1);
    }
    if(!matched) S(10,1);
    S(4,1);S(13,1);context->ram[80]=0;SEQ(clear);POINT(0x192d);
    SEQ(restore);
    if(!copy8(clock,context,graphics->metatiles+0x98,graphics->metatiles+0x1c0)) return 0;
    SEQ(copy_prefix);
    if(!copy8(clock,context,graphics->metatiles+0x98,graphics->metatiles+0x1f0)) return 0;
    S(10,1);SEQ(special);S(15,2);S(11,1);S(10,1);S(10,1);S(10,1);
    context->ram[80]=0;S(16,1);context->ram[0x34]=0;context->ram[0x35]=0xdd;
    for(n=0;n<5;n++) S(10,1);
    POINT(0x24bc);return 1;
}
#undef POINT
#undef SEQ
#undef S

#include "source_graphics_load.h"
#include "source_ram_planes.h"

static u8 step(SourceClock *clock,SourceIrqContext *context,u16 ticks,u8 m1,u8 effect)
{
    return source_clock_execute(clock,ticks,m1,effect,source_irq_interrupt,context);
}
#define S(t,m) do { if(!step(clock,context,t,m,SOURCE_CLOCK_NONE)) return 0; } while(0)
static u8 sequence(SourceClock *clock,SourceIrqContext *context,const u8 *ticks,u16 count)
{
    u16 n;for(n=0;n<count;n++) S(ticks[n],1);return 1;
}
#define SEQ(a) do { if(!sequence(clock,context,a,sizeof(a))) return 0; } while(0)

static u8 copy(SourceClock *clock,SourceIrqContext *context,const u8 *source,u8 *destination,u16 count)
{
    u16 n;
    for(n=0;n<count;n++) { S(n+1<count?21:16,2);destination[n]=source[n]; }
    return 1;
}
#define COPY(s,d,n) do { if(!copy(clock,context,s,d,n)) return 0; } while(0)


static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,
                SourceGraphicsCheckpoint checkpoint,void *user)
{
    if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
    return !checkpoint || checkpoint(user,pc,clock,context);
}
#define POINT(pc) do { if(!point(clock,context,pc,checkpoint,user)) return 0; } while(0)

u8 source_graphics_load_class0(SourceClock *clock,SourceIrqContext *context,
                               const u8 *patterns,const u8 *bank2,const u8 *bank11,
                               SourceGraphicsData *data,SourceGraphicsCheckpoint checkpoint,void *user)
{
    static const u8 backup_prefix[]={10,10,10},backup_second[]={10,7};
    static const u8 patch_prefix[]={17,13,4,5,13,4,7,10,10,10,11,11};
    static const u8 bank_change[]={7,13,17,13,4,11,7,13,17};
    static const u8 lookup[]={11,4,4,12,7,6,7,4,10};
    static const u8 extra_prefix[]={10,13,4},extra_tail[]={10,7};
    static const u8 extra_record[]={7,6,4,10,11,11,4,7,11,11,11,10,11,10};
    static const u8 extra_next[]={10,10,4,12},extra_end[]={7,6,4,10,10};
    static const u8 attribute[]={4,5,7,7,7,7,6,6,6,12};
    static const u8 terrain_prefix[]={13,4,10},terrain_call[]={7,13,10,7,17};
    static const u8 sram_prefix[]={13,7,13,10,10,10,10},sram_tail[]={10,13,7,13};
    const u8 *source,*table;u16 n,count=0,terrain_address;
    if(!data || !bank2 || !bank11 || !data->patterns || !data->metatiles ||
       !data->backup || !data->terrain || !data->saved_terrain) return 0;
    if(!source_graphics_prefix_class0(clock,context,patterns,data->patterns,&source)) return 0;
    /* Prefix already checkpoints at1706; do not fetch it twice. */
    if(checkpoint && !checkpoint(user,0x1706,clock,context)) return 0;
    S(10,1);S(7,1);S(17,1);
    if(!source_ram_planes(clock,context,&source,data->metatiles,0xc900,2)) return 0;
    POINT(0x170e);
    SEQ(backup_prefix);COPY(data->metatiles+0x1c0,data->backup,8);
    SEQ(backup_second);COPY(data->metatiles+0x1f0,data->backup+8,8);POINT(0x1720);
    /* 1A30 class0/C0AC0 restores both animated metatiles from C998. */
    SEQ(patch_prefix);COPY(data->metatiles+0x98,data->metatiles+0x1c0,8);
    SEQ(backup_prefix);COPY(data->metatiles+0x98,data->metatiles+0x1f0,8);S(10,1);
    SEQ(bank_change);SEQ(extra_prefix);SEQ(lookup);SEQ(extra_tail);
    n=(u16)bank2[0x259]|((u16)bank2[0x25a]<<8);
    if(n<0x8000 || n>=0xc000) return 0;
    table=bank2+(n&0x3fff);
    while(table[count]<128)
    {
        if(count>=128) return 0;
        SEQ(extra_record);COPY(data->metatiles+table[count]*8,data->metatiles+0x400+count*8,8);
        SEQ(extra_next);count++;
    }
    SEQ(extra_end);S(8,2);S(8,2);
    for(n=0;n<count*4;n++)
    {
        SEQ(attribute);
        data->metatiles[0x401+n*2]=(data->metatiles[0x401+n*2]&31)|table[count+1+n];
    }
    S(4,1);S(11,1);POINT(0x1733);
    SEQ(terrain_prefix);SEQ(lookup);SEQ(terrain_call);
    terrain_address=(u16)context->low[0x1759]|((u16)context->low[0x175a]<<8);
    source=bank11+(terrain_address&0x3fff);
    if(!source_ram_planes(clock,context,&source,data->terrain,0xd100,4)) return 0;
    POINT(0x1748);
    S(17,1);
    if(!step(clock,context,4,1,SOURCE_CLOCK_DI)) return 0;
    SEQ(sram_prefix);COPY(data->terrain,data->saved_terrain,1024);SEQ(sram_tail);
    if(!step(clock,context,4,1,SOURCE_CLOCK_EI)) return 0;
    S(10,1);POINT(0x24b9);return 1;
}
#undef POINT
#undef COPY
#undef SEQ
#undef S

#include "source_room_finish.h"
#include "source_wait_restore.h"
#define S(t,m) do { if(!source_clock_execute(clock,t,m,SOURCE_CLOCK_NONE,source_irq_interrupt,context)) goto reject; } while(0)
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,SourceGraphicsCheckpoint checkpoint,void *user,u8 fetched)
{
    if(!fetched && !source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
    return !checkpoint || checkpoint(user,pc,clock,context);
}
#define POINT(pc,f) do { if(!point(clock,context,pc,checkpoint,user,f)) goto reject; } while(0)

u8 source_room_finish(SourceClock *clock,SourceIrqContext *context,
                       SourceGraphicsData *graphics,SourceWorldMapData *map,const u8 *hud,
                       SourceRoomFinish *result,SourceGraphicsCheckpoint checkpoint,void *user)
{
    static const u8 upload_prefix[]={4,11,7,11,10,10,7};
    SourceWaitOutput wait;u16 n,row,col,batch;
    if(!result) return 0;
    result->wait_taken=result->error=0;
    if(!clock || !context || !graphics || !map || !hud || hud[15]>=4 ||
       !graphics->patterns || !map->cells || !map->tilemap || !context->low) goto reject;
    S(17,1);for(n=0;n<4;n++) S(11,1);S(17,1);POINT(0x0b95,0);
    if(!source_wait(clock,context,&wait)) goto reject;
    result->wait_taken=wait.taken;POINT(0x0bb3,1);
    if(!source_wait_restore(clock,context)) goto reject;
    POINT(0x22a3,1);
    if(!source_clock_execute(clock,4,1,SOURCE_CLOCK_DI,source_irq_interrupt,context)) goto reject;
    for(n=0;n<sizeof(upload_prefix);n++) S(upload_prefix[n],1);
    for(row=0;row<12;row++)
    {
        /* OUTI and DJNZ each decrement B:128 bytes per B=0 row. DI makes
         * these stable blocks safe across VINT; pending is kept for IN. */
        batch=source_clock_repeat_disabled(clock,29,3,127);
        if(batch!=127)
            for(col=0;col<127;col++) { S(16,2);S(13,1); }
        S(16,2);S(8,1);S(4,1);S(10,1);
    }
    for(n=0;n<1536;n++) graphics->patterns[0x3800+n]=map->tilemap[n];
    if(!source_clock_execute(clock,11,1,SOURCE_CLOCK_STATUS,source_irq_interrupt,context) ||
       !source_clock_execute(clock,4,1,SOURCE_CLOCK_EI,source_irq_interrupt,context)) goto reject;
    for(n=0;n<5;n++) S(10,1);
    POINT(0x1deb,0);
    if(!source_room_palette(clock,context,map,hud,checkpoint,user)) goto reject;
    return 1;
reject:
    result->error=1;return 0;
}
u8 source_room_palette(SourceClock *clock,SourceIrqContext *context,SourceWorldMapData *map,
                        const u8 *hud,SourceGraphicsCheckpoint checkpoint,void *user)
{
    static const u8 palette_lookup[]={13,4,10,11,4,4,12,7,6,7,4,10};
    u16 n,offset;
    if(!clock || !context || !map || !map->cells || !context->low || !hud || hud[15]>=4) return 0;
    for(n=0;n<3;n++) S(10,1);
    for(n=0;n<16;n++) { S(n<15?21:16,2);map->cells[0xb0+n]=context->low[0x1e20+n]; }
    for(n=0;n<sizeof(palette_lookup);n++) S(palette_lookup[n],1);
    S(16,1);offset=0x1e2e + hud[15]*2;
    map->cells[0xb6]=context->low[offset];map->cells[0xb7]=context->low[offset+1];
    S(13,1);S(4,1);
    if(!hud[14]) S(12,1);
    else
    {
        S(7,1);S(13,1);S(4,1);S(4,1);
        if(context->ram[0x2f]&2) S(12,1);
        else { S(7,1);S(10,1);S(16,1);map->cells[0xb6]=0x16;map->cells[0xb7]=1; }
    }
    S(13,1);S(7,1);
    if(context->ram[0x2f]&2) S(12,1);else { S(7,1);S(4,1); }
    S(13,1);map->cells[0xbf]=(context->ram[0x2f]&2)?2:1;
    S(10,1);POINT(0x24bf,0);return 1;
reject:
    return 0;
}

#undef POINT
#undef S

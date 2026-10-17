#include "source_room_finish.h"
u8 palette_case(u8 blink,u8 slot,u8 counter,u8 refresh,const u8 *low,u8 *palette,u32 *out)
{
 SourceClock clock;SourceIrqContext ctx={0};SourceWorldMapData map;u8 ram[336]={0},audio[400]={0},hud[16]={0},cells[256];u16 n;
 source_clock_init(&clock,262,0,refresh,0,0,0);ram[0x2f]=counter;hud[14]=blink;hud[15]=slot;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.input.lines=262;ctx.input.reset_mask=16;map.cells=cells;
 if(!source_room_palette(&clock,&ctx,&map,hud,0,0)) return 0;
 for(n=0;n<16;n++) palette[n]=cells[0xb0+n];
 out[0]=clock.foreground_tstates;out[1]=clock.foreground_m1;out[2]=clock.refresh;return 1;
}

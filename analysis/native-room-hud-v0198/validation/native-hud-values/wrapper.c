#include "source_room_hud.h"
u8 hud_value_case(const u8 *hud,const u8 *bank4,const u8 *low,u8 *memory,u32 *out)
{
 SourceClock clock;SourceIrqContext ctx={0};SourceWorldMapData map;
 static u8 tilemap[1536],ram[336],audio[400];u16 n;
 if(!source_clock_init(&clock,262,0,0,0,0,0)) return 0;
 for(n=0;n<80;n++) ram[n]=0;
 for(n=0;n<256;n++) {tilemap[1280+n]=memory[n];ram[80+n]=memory[512+n];}
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.input.lines=262;ctx.input.reset_mask=16;
 map.tilemap=tilemap;map.cells=memory+256;
 if(!source_hud_prepare(&clock,&ctx,&map,bank4,hud)) return 0;
 for(n=0;n<256;n++) {memory[n]=tilemap[1280+n];memory[512+n]=ram[80+n];}
 out[0]=clock.foreground_tstates;out[1]=clock.foreground_m1;return 1;
}

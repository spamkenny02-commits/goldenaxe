#include <genesis.h>
#include "../../../megadrive/src/source_room_finish.h"
#include "expected.h"
volatile u32 gaw_budget[24][16],gaw_budget_cases,gaw_budget_failures;
volatile u16 gaw_budget_done;
volatile u32 gaw_graphics_marks[24][6];
static u16 profile_row,profile_point;
static u8 graphics_mark(void *user,u16 pc,const SourceClock *clock,const SourceIrqContext *ctx)
{
 (void)user;(void)pc;(void)clock;(void)ctx;
 if(profile_point>=6) return 0;gaw_graphics_marks[profile_row][profile_point++]=vtimer;return 1;
}
extern volatile u32 gaw_irq_ticks,gaw_irq_calls;
extern volatile u32 gaw_exec_calls,gaw_repeat_calls,gaw_repeat_groups,gaw_repeat_reps;
static u8 ram[336],audio[400],pixels[16384],meta[2048],backup[16],terrain[1024],saved[1024],cells[256],tilemap[1536];
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);VDP_setVInterrupt(TRUE);SYS_enableInts();
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  SourceClock clock;SourceIrqContext ctx={0};SourceGraphicsData data;SourceWorldMapData map;SourceRoomFinish finish;
  u32 started,mark1,mark2,mark3,mark4,period=cases[row].phase[3]*3420;s32 raster=(s32)(cases[row].phase[1]*3420)+(s32)(cases[row].phase[0]-cases[row].phase[2]);u8 accepted;
  if((cases[row].phase[3]==313)!=SYS_isPAL()) continue;
  while(raster<0) raster+=period;
  while((u32)raster>=period) raster-=period;
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  for(n=0;n<16384;n++) pixels[n]=0xa7;
  for(n=0;n<2048;n++) meta[n]=0xa7;
  for(n=0;n<1024;n++) terrain[n]=0xa7;
  for(n=0;n<256;n++) cells[n]=0xa7;
  for(n=0;n<1536;n++) tilemap[n]=0xa7;
  source_clock_init(&clock,cases[row].phase[3],raster,cases[row].refresh,cases[row].phase[8],cases[row].phase[9],cases[row].phase[10]);
  ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.bank6=bank6;ctx.input.lines=cases[row].phase[3];ctx.input.reset_mask=16;
  data.patterns=pixels;data.metatiles=meta;data.backup=backup;data.terrain=terrain;data.saved_terrain=saved;map.cells=cells;map.tilemap=tilemap;
  SYS_doVBlankProcess();gaw_irq_ticks=gaw_irq_calls=0;gaw_exec_calls=gaw_repeat_calls=gaw_repeat_groups=gaw_repeat_reps=0;started=vtimer;profile_row=row;profile_point=0;
  accepted=source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,graphics_mark,0);mark1=vtimer;
  if(accepted) accepted=source_world_map_load(&clock,&ctx,cases[row].room,1,(cases[row].room&128)?bank9:bank8,bank2,&data,&map,0,0);mark2=vtimer;
  if(accepted) accepted=source_room_hud_prepare(&clock,&ctx,&data,&map,bank4,cases[row].hud,0,0);mark3=vtimer;
  if(accepted) accepted=source_room_finish(&clock,&ctx,&data,&map,cases[row].hud,&finish,0,0);mark4=vtimer;
  gaw_budget[row][0]=mark4-started;gaw_budget[row][1]=clock.elapsed;gaw_budget[row][2]=clock.foreground_m1;gaw_budget[row][3]=clock.irq_count;gaw_budget[row][4]=1;
  gaw_budget[row][5]=mark1-started;gaw_budget[row][6]=mark2-mark1;gaw_budget[row][7]=mark3-mark2;gaw_budget[row][8]=mark4-mark3;
  gaw_budget[row][9]=gaw_irq_ticks;gaw_budget[row][10]=gaw_irq_calls;gaw_budget[row][11]=started;
  gaw_budget[row][12]=gaw_exec_calls;gaw_budget[row][13]=gaw_repeat_calls;gaw_budget[row][14]=gaw_repeat_groups;gaw_budget[row][15]=gaw_repeat_reps;
  if(profile_point!=6 || !accepted || ctx.error || clock.elapsed!=cases[row].expected[2] || clock.foreground_m1!=cases[row].expected[4] || clock.refresh!=cases[row].expected[10]) gaw_budget_failures++;
  for(n=0;n<336;n++) if(ram[n]!=cases[row].after_ram[n]) gaw_budget_failures++;
  for(n=0;n<400;n++) if(audio[n]!=cases[row].after_audio[n]) gaw_budget_failures++;
  gaw_budget_cases++;
 }
 gaw_budget_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}

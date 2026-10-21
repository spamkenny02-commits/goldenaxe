#include "source_game_irq.h"
#define source_irq_interrupt source_game_irq_interrupt
#define source_wait source_game_wait_core
#include "source_wait.c"
#undef source_wait
#undef source_irq_interrupt
u8 source_game_sprite_frame(SourceClock *clock,SourceGameIrqContext *c,const u8 *bank,
 SourceSpriteSceneOutput *scene,SourceWaitOutput *wait,SourceSpriteSceneTrace trace,void *user)
{
 static const u8 restore[]={10,13,14,14,10,10,10,10,4,4,10,10,10,10,10};u16 n;u8 mapper;
 if(!clock || !c || !c->bound || c->error || c->ram[0x2e] || !scene || !wait) return 0;
 if(trace && !trace(user,0x938,clock,c->ram)) return 0;
 c->producer_active=1;
 if(!source_sprite_scene_timed(clock,c->ram,bank,scene,source_game_irq_interrupt,c,0,0)) {c->producer_active=0;return 0;}
 c->producer_active=0;
 if(!source_clock_plain(clock,17,1,source_game_irq_interrupt,c) ||
    !source_clock_checkpoint(clock,source_game_irq_interrupt,c)) return 0;
 if(trace && !trace(user,0xb95,clock,c->ram)) return 0;
 mapper=c->ram[0x1fff];
 if(!source_game_wait_core(clock,&c->timed.core,wait)) return 0;
 if(trace && !trace(user,0xbb3,clock,c->ram)) return 0;
 for(n=0;n<15;n++) {
  if(!source_clock_execute(clock,restore[n],(n==2 || n==3)?2:1,SOURCE_CLOCK_NONE,source_game_irq_interrupt,c)) return 0;
  if(n==1) c->ram[0x1fff]=mapper;
 }
 if(!source_clock_checkpoint(clock,source_game_irq_interrupt,c)) return 0;
 return !trace || trace(user,65535,clock,c->ram);
}

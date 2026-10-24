#include "source_room_reveal.h"
#define S(t,m) do {if(!source_clock_plain(clock,t,m,source_irq_interrupt,context)) return 0;} while(0)
#define E(t,e) do {if(!source_clock_execute(clock,t,1,e,source_irq_interrupt,context)) return 0;} while(0)
#define G(a) source_room_get(context,a)
#define P(a,v) source_room_put(context,a,v)
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,
 SourceGraphicsCheckpoint checkpoint,void *user)
{
 if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
 return !checkpoint || checkpoint(user,pc,clock,context);
}
#define POINT(pc) do {if(!point(clock,context,pc,checkpoint,user)) return 0;} while(0)
/* Includes RST28 and its RET. VINT stays enabled, HINT disabled. Display
 * enable is a video concern; it does not change the logical IRQ schedule. */
static u8 latch(SourceClock *clock,SourceIrqContext *context)
{
 S(11,1);E(4,SOURCE_CLOCK_DI);S(4,1);S(11,1);S(4,1);S(11,1);
 E(4,SOURCE_CLOCK_EI);S(10,1);return 1;
}
u8 source_room_reveal_prepare(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,u8 *vram,SourceGraphicsCheckpoint checkpoint,void *user)
{
 u16 chunk,n,address=0x3800,pointer,count,previous_count;u8 value,bank;
 SourceWaitOutput waited;
 if(!clock || !context || !context->ram || !context->audio || !context->full_ram || !rom) return 0;
 /* Mode4/192, VINT enabled and HINT disabled is SourceClock's contract. */
 if(!(G(0x11)&32) || (G(0x10)&16)) return 0;
 S(10,1);S(10,1);S(10,1);S(17,1);
 if(!latch(clock,context)) return 0;
 S(4,1);S(4,1);S(12,1);
 for(chunk=0;chunk<3;chunk++)
 {
  for(n=0;n<256;n++)
  {
   S(4,1);S(11,1);if(vram) vram[address]=0xff;address++;
   S(11,1);S(10,1);S(4,1);S(11,1);if(vram) vram[address]=0x18;address++;
   S(4,1);S(n<255?12:7,1);
  }
  S(chunk<2?13:8,1);
 }
 S(10,1);S(17,1);POINT(0x0aa4);
 /* Preserve the loaded target palette before clearing the current one.
  * Each LDIR iteration is observable by an intervening audio IRQ. */
 S(10,1);S(10,1);S(10,1);
 for(n=0;n<32;n++){S(n<31?21:16,2);P(0x1cc0+n,G(0x1ca0+n));}
 S(17,1);S(10,1);S(10,1);S(10,1);S(7,1);P(0x1ca0,0);
 for(n=1;n<32;n++){S(n<31?21:16,2);P(0x1ca0+n,G(0x1ca0+n-1));}
 S(10,1);S(13,1);value=G(0x11);S(4,1);S(7,1);S(8,2);
 if(!latch(clock,context)) return 0;
 E(11,SOURCE_CLOCK_STATUS);S(17,1);POINT(0x0b95);
 /* The pending hero bitmap's leading byte is the original tile count.
  * No inferred frame budget and no value taken from a later snapshot. */
 previous_count=context->input.tile_count;
 if(G(0x42))
 {
  bank=G(0x42);pointer=G(0x43)|((u16)G(0x44)<<8);
  if(bank>=16 || pointer>=0xc000) return 0;
  count=rom[pointer<0x8000?pointer:(u32)bank*16384+(pointer&0x3fff)];
  context->input.tile_count=count?count:256;
 }
 if(!source_wait(clock,context,&waited)) return 0;
 if(checkpoint && !checkpoint(user,0x0bb3,clock,context)) return 0;
 if(!source_wait_restore(clock,context)) return 0;
 if(checkpoint && !checkpoint(user,0x0ac0,clock,context)) return 0;
 S(8,2);if(!latch(clock,context)) return 0;
 S(4,1);S(13,1);P(0x11,value|96);
 S(13,1);S(4,1);S(7,1);if(!latch(clock,context)) return 0;
 POINT(0x0ace);context->input.tile_count=previous_count;return 1;
}
u8 source_room_reveal_fade(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,SourceGraphicsCheckpoint checkpoint,void *user)
{
 u16 pointer=0x0b0a,n,guard;u8 step,mask,current,desired,value,changed;
 SourceWaitOutput waited;
 if(!clock || !context || !context->ram || !context->audio || !context->full_ram || !rom) return 0;
 S(10,1);
 for(guard=0;guard<64;guard++)
 {
  S(7,1);step=rom[pointer];S(4,1);S(step?5:11,1);
  if(!step){POINT(0x1fb6);return 1;}
  S(17,1);S(7,1);mask=(step*2)|step;S(4,1);S(14,2);S(10,1);changed=0;
  for(n=0;n<32;n++)
  {
   S(19,2);desired=G(0x1cc0+n);S(4,1);desired&=mask;S(4,1);
   S(19,2);current=G(0x1ca0+n);S(4,1);current&=mask;S(4,1);
   S(19,2);value=G(0x1ca0+n);S(current==desired?12:7,1);
   if(current!=desired)
   {
    S(current<desired?12:7,1);S(7,1);
    if(current<desired)value+=step;else{value-=step;S(12,1);}
    S(4,1);changed++;S(19,2);P(0x1ca0+n,value);
   }
   S(10,2);S(n<31?13:8,1);
  }
  S(4,1);S(4,1);S(changed?12:7,1);if(!changed){S(6,1);pointer++;}S(10,1);
  S(changed?7:12,1);
  if(changed)
  {
   S(17,1);S(17,1);
   if(!source_wait_complete(clock,context,&waited) || !source_wait_complete(clock,context,&waited))return 0;
   S(12,1);
  }
 }
 return 0;
}
#undef POINT
#undef P
#undef G
#undef E
#undef S

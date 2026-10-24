#include "source_room_contours.h"
#define S(t,m) do {if(!source_clock_plain(clock,t,m,source_irq_interrupt,context))return 0;} while(0)
#define E(t,e) do {if(!source_clock_execute(clock,t,1,e,source_irq_interrupt,context))return 0;} while(0)
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,SourceGraphicsCheckpoint callback,void *user)
{
 if(!source_clock_checkpoint(clock,source_irq_interrupt,context))return 0;
 return !callback || callback(user,pc,clock,context);
}
#define POINT(pc) do {if(!point(clock,context,pc,checkpoint,user))return 0;} while(0)
static u8 word(SourceClock *clock,SourceIrqContext *context,u8 *vram,u16 address,SourceVdpDirty *dirty)
{
 u16 source=address+0x5e00;u8 value;
 if(source<0xc000)return 0;
 /* The paired DI/EI has expired by the final RET. With no intervening
  * VINT, publish both bytes before the next clock operation. */
 if(source_clock_block(clock,139,17))
 {
  value=source_room_get(context,source-0xc000);if(vram[address&0x3fff]!=value)source_vdp_dirty_vram(dirty,address);vram[address&0x3fff]=value;
  value=source_room_get(context,(u16)(source+1)-0xc000);if(vram[(address+1)&0x3fff]!=value)source_vdp_dirty_vram(dirty,address+1);vram[(address+1)&0x3fff]=value;
  return 1;
 }
 /* CALL2003 is accounted by the caller. Original RST28 latches DE. */
 S(11,1);E(4,SOURCE_CLOCK_DI);S(4,1);S(11,1);S(4,1);S(11,1);E(4,SOURCE_CLOCK_EI);S(10,1);
 S(10,1);S(11,1);
 S(7,1);value=source_room_get(context,source-0xc000);S(11,1);if(vram[address&0x3fff]!=value)source_vdp_dirty_vram(dirty,address);vram[address&0x3fff]=value;
 S(6,1);S(7,1);S(7,1);value=source_room_get(context,(u16)(source+1)-0xc000);
 S(11,1);if(vram[(address+1)&0x3fff]!=value)source_vdp_dirty_vram(dirty,address+1);vram[(address+1)&0x3fff]=value;S(10,1);return 1;
}
u8 source_room_contours(SourceClock *clock,SourceIrqContext *context,const u8 *rom,u8 *vram,
 SourceGraphicsCheckpoint checkpoint,void *user)
{return source_room_contours_marked(clock,context,rom,vram,0,checkpoint,user);}
u8 source_room_contours_marked(SourceClock *clock,SourceIrqContext *context,const u8 *rom,u8 *vram,
 SourceVdpDirty *dirty,SourceGraphicsCheckpoint checkpoint,void *user)
{
 SourceWaitOutput waited;u16 contour,n,address;u8 height,width,carry;u16 sum;
 if(!clock || !context || !context->ram || !context->audio || !context->full_ram || !rom || !vram)return 0;
 S(14,2);S(7,1);
 for(contour=0;contour<16;contour++)
 {
  S(17,1);S(17,1);POINT(0x0b95);
  if(!source_wait(clock,context,&waited))return 0;
  if(checkpoint && !checkpoint(user,0x0bb3,clock,context))return 0;
  if(!source_wait_restore(clock,context))return 0;
  if(checkpoint && !checkpoint(user,0x0b95,clock,context))return 0;
  if(!source_wait(clock,context,&waited))return 0;
  if(checkpoint && !checkpoint(user,0x0bb3,clock,context))return 0;
  if(!source_wait_restore(clock,context))return 0;
  S(19,2);address=rom[0x2011+contour*4];S(19,2);address|=(u16)rom[0x2012+contour*4]<<8;
  S(19,2);width=rom[0x2014+contour*4];
  for(n=0;n<(width?width:256);n++)
  {S(6,1);address++;S(6,1);address++;S(17,1);if(!word(clock,context,vram,address,dirty))return 0;S(n+1<(width?width:256)?13:8,1);}
  S(19,2);height=rom[0x2013+contour*4];
  for(n=0;n<(height?height:256);n++)
  {
   S(7,1);S(4,1);sum=(address&255)+64;carry=sum>255;address=(address&0xff00)|(sum&255);S(4,1);S(carry?7:12,1);
   if(carry){S(4,1);address+=256;}S(17,1);if(!word(clock,context,vram,address,dirty))return 0;S(n+1<(height?height:256)?13:8,1);
  }
  S(19,2);
  for(n=0;n<(width?width:256);n++)
  {S(6,1);address--;S(6,1);address--;S(17,1);if(!word(clock,context,vram,address,dirty))return 0;S(n+1<(width?width:256)?13:8,1);}
  S(19,2);
  for(n=0;n<(height?height:256);n++)
  {
   S(7,1);S(4,1);sum=(address&255)+192;carry=sum>255;address=(address&0xff00)|(sum&255);S(4,1);S(carry?12:7,1);
   if(!carry){S(4,1);address-=256;}S(17,1);if(!word(clock,context,vram,address,dirty))return 0;S(n+1<(height?height:256)?13:8,1);
  }
  for(n=0;n<4;n++)S(10,2);
  S(4,1);S(contour<15?12:7,1);
 }
 POINT(0x2002);return 1;
}
#undef POINT
#undef E
#undef S

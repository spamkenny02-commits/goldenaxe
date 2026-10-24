#include "source_actor_list.h"
#define S(t,m) do {if(!source_clock_plain(clock,t,m,source_irq_interrupt,context)) return 0;} while(0)
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,
 SourceGraphicsCheckpoint checkpoint,void *user)
{
 if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
 return !checkpoint || checkpoint(user,pc,clock,context);
}
#define POINT(pc) do {if(!point(clock,context,pc,checkpoint,user)) return 0;} while(0)
static u8 clear(SourceClock *clock,SourceIrqContext *context,u8 *bytes,u16 count)
{
 u16 i;
 for(i=1;i<count;i++) {S(i+1==count?16:21,2);bytes[i]=bytes[i-1];}
 return 1;
}
u8 source_actor_list(SourceClock *clock,SourceIrqContext *context,
 const u8 *bank12,SourceActorListData *data,
 SourceGraphicsCheckpoint checkpoint,void *user)
{
 u16 n,j,room,offset;u8 type,mask,bits=0,count=0,value,*e;
 if(!clock || !context || !context->ram || !bank12 || !data ||
    !data->actors || !data->active_count || !data->room || !data->masks ||
    !data->progression || (data->room[0]|((u16)data->room[1]<<8))>=512) return 0;
 S(7,1);S(13,1);S(10,1);S(10,1);S(10,1);S(10,1);data->actors[0]=0;
 if(!clear(clock,context,data->actors,768)) return 0;
 S(16,1);room=data->room[0]|((u16)data->room[1]<<8);
 if(room>=512) return 0;
 S(11,1);S(11,1);S(11,1);S(10,1);S(11,1);S(14,2);S(10,1);S(7,1);
 for(n=0;n<8;n++)
 {
  S(7,1);value=bank12[0x234e +room*8+n];S(6,1);S(19,2);data->actors[n*48]=value;
  S(15,2);S(n<7?13:8,1);
 }
 POINT(0x17ae);S(14,2);S(7,1);
 for(n=0;n<8;n++)
 {
  e=data->actors+n*48;S(19,2);type=e[0];S(7,1);S(type<32?12:7,1);
  if(type>=32)
  {
   S(4,1);S(7,1);S(11,1);S(11,1);S(10,1);S(11,1);offset=0x20ea+(type-32)*4;
   for(j=0;j<4;j++) {S(7,1);value=bank12[offset+j];S(19,2);e[j<3?24+j:3]=value;if(j<3) S(6,1);}
  }
  S(10,1);S(15,2);S(n<7?13:8,1);
 }
 POINT(0x17de);S(16,1);room=data->room[0];S(7,1);S(7,1);mask=data->masks[room];S(14,2);S(7,1);
 for(n=0;n<8;n++)
 {
  S(8,2);mask=(mask<<1)|(mask>>7);S(mask&1?12:7,1);
  if(!(mask&1))
  {
   S(4,1);S(15,2);S(10,1);S(4,1);S(4,1);S(6,1);S(10,1);S(7,1);e=data->actors+n*48;e[0]=0;
   if(!clear(clock,context,e,48)) return 0;
   S(4,1);S(8,2);
  }
  S(10,1);S(15,2);S(n<7?13:8,1);
 }
 POINT(0x1805);S(10,1);S(10,1);S(4,1);S(7,1);
 for(n=0;n<8;n++) {S(7,1);bits|=data->actors[n*48+3];S(11,1);S(n<7?13:8,1);}
 S(7,1);S(bits&64?7:12,1);
 if(bits&64)
 {
  S(16,1);offset=context->ram[0x37];S(7,1);S(10,1);S(11,1);S(7,1);value=data->progression[offset];S(4,1);S(value?7:12,1);
  if(value)
  {
   S(10,1);S(10,1);S(10,1);S(10,1);data->actors[0]=0;
   if(!clear(clock,context,data->actors,384)) return 0;
   S(4,1);S(10,1);
   if(!(value&128)) {S(7,1);S(13,1);data->actors[0]=15;}
  }
 }
 POINT(0x1839);S(10,1);S(10,1);S(10,1);
 for(n=0;n<8;n++)
 {
  S(7,1);type=data->actors[n*48];S(4,1);S(type?7:12,1);if(type) {S(4,1);count++;}
  S(11,1);S(n<7?13:8,1);
 }
 S(4,1);S(4,1);S(count?12:7,1);if(!count) {S(7,1);count=128;}
 S(13,1);*data->active_count=count;POINT(0x1853);return 1;
}
#undef POINT
#undef S

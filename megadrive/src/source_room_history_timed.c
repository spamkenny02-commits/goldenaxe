#include "source_room_history_timed.h"
#define S(t,m) do {if(!source_clock_plain(clock,t,m,interrupt,context)) return 0;} while(0)
/* A CPIR repeat may accept an IRQ before reading the next byte. Decide its
 * final/repeat timing only after that boundary, not from pre-IRQ memory. */
static u8 scan(SourceClock *clock,const u8 *bytes,u8 count,u8 value,u8 *found,
 SourceClockInterrupt interrupt,void *context)
{
 u8 i,match;
 for(i=0;i<count;i++)
 {
  if(!source_clock_checkpoint(clock,interrupt,context)) return 0;
  match=bytes[i]==value;S(match || i+1==count?16:21,2);
  if(match) {*found=1;return 1;}
 }
 *found=0;return 1;
}
u8 source_room_history_timed(SourceClock *clock,SourceRoomHistoryData *data,
 SourceRoomHistoryOutput *output,SourceClockInterrupt interrupt,void *context)
{
 static const u8 exceptions[6]={0x1e,0x5e,0x9c,0xb8,0xbe,0xc9};
 SourceRngTimedOutput draw;u8 dungeon,length,attempts,room,value,found,i,j;
 if(!clock || !data || !output || !data->room || !data->seed || !data->history || !data->masks) return 0;
 output->calls=output->restored=output->last_value=0;
 S(13,1);dungeon=data->room[1]!=0;S(4,1);S(dungeon?12:7,1);
 length=dungeon?4:16;attempts=dungeon?5:3;S(7,1);
 for(i=0;i<attempts;i++)
 {
  S(11,1);S(17,1); /* PUSH BC; CALL1C25/1C58. */
  S(13,1);room=data->room[0];S(10,1);S(10,1);
  if(!scan(clock,data->history,length,room,&found,interrupt,context)) return 0;
  S(found?12:7,1);
  if(!found)
  {
   S(10,1);S(10,1);S(10,1);
   for(j=length-1;j;j--) {S(j==1?16:21,2);data->history[j]=data->history[j-1];}
   S(13,1);data->history[0]=room;
  }
  S(17,1);
  if(!source_rng_timed(clock,data->seed,&draw,interrupt,context)) return 0;
  value=draw.value;output->calls++;output->last_value=value;
  S(10,1);S(10,1);
  if(!scan(clock,data->history,length,value,&found,interrupt,context)) return 0;
  S(found?11:5,1); /* RET Z. */
  if(!found)
  {
   if(dungeon)
   {
    S(10,1);S(10,1);
    if(!scan(clock,exceptions,6,value,&found,interrupt,context)) return 0;
    S(found?11:5,1);
   }
   else {S(12,1);}
   if(!found)
   {
    S(4,1);S(7,1);S(7,1);room=data->masks[value];S(4,1);S(room?11:5,1);
    if(!room) {S(10,1);data->masks[value]=255;output->restored++;S(10,1);}
   }
  }
  S(10,1);S(i+1==attempts?8:13,1);
 }
 S(10,1);return 1;
}
u8 source_room_actor_prefix(SourceClock *clock,u8 *flags,u8 *objects,
 SourceRoomHistoryData *data,SourceRoomHistoryOutput *output,
 SourceClockInterrupt interrupt,void *context)
{
 u16 i;
 if(!clock || !flags || !objects || !data || !output || !data->room ||
    !data->seed || !data->history || !data->masks) return 0;
 S(17,1);S(10,1);S(10,1);S(10,1);S(7,1);flags[0]=0;
 for(i=1;i<32;i++) {S(i==31?16:21,2);flags[i]=flags[i-1];}
 S(10,1);S(10,1);S(10,1);S(10,1);objects[0]=0;
 for(i=1;i<336;i++) {S(i==335?16:21,2);objects[i]=objects[i-1];}
 S(17,1);
 if(!source_room_history_timed(clock,data,output,interrupt,context)) return 0;
 S(17,1);
 return source_clock_checkpoint(clock,interrupt,context);
}
#undef S

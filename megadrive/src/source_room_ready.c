#include "source_room_ready.h"
#define S(t,m) do {if(!source_clock_plain(clock,t,m,source_irq_interrupt,context)) return 0;} while(0)
#define G(a) source_room_get(context,a)
#define P(a,v) source_room_put(context,a,v)
static void word(SourceIrqContext *ctx,u16 a,u16 value)
{source_room_put(ctx,a,value);source_room_put(ctx,a+1,value>>8);}
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,SourceGraphicsCheckpoint checkpoint,void *user)
{
 if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
 return !checkpoint || checkpoint(user,pc,clock,context);
}
#define POINT(pc) do {if(!point(clock,context,pc,checkpoint,user)) return 0;} while(0)
u8 source_room_tail(SourceClock *clock,SourceIrqContext *context,const u8 *rom,
 SourceGraphicsCheckpoint checkpoint,void *user)
{
 u16 n,room,pointer,coordinate;u8 count,graphics,found=0,command,previous,bits=0;
 if(!clock || !context || !context->ram || !context->audio || !context->full_ram || !rom || G(0x40)>2) return 0;
 S(17,1);POINT(0x5b20);S(10,1);
 for(n=0;n<3;n++){S(16,1);word(context,0x1ce0+n*2,0xc0b0);}
 S(20,2);coordinate=G(0x60)|((u16)G(0x61)<<8);S(20,2);word(context,0x62,coordinate);
 S(13,1);count=G(0x30a);S(13,1);P(0x64,count);S(7,1);S(13,1);
 S(16,1);room=G(0xb9)|((u16)G(0xba)<<8);S(11,1);S(10,1);S(11,1);
 pointer=0xb762+room*2;S(7,1);count=rom[pointer];S(6,1);S(7,1);graphics=rom[pointer+1];S(20,2);word(context,0xa4,count|((u16)graphics<<8));
 S(13,1);count=G(0xa2);S(4,1);S(count&128?7:12,1);
 if(count&128){S(7,1);S(13,1);P(0xa8,2);}S(10,1);
 S(17,1);POINT(0x1caf);S(13,1);graphics=G(0x40);S(7,1);S(graphics==1?12:7,1);
 if(graphics==1)
 {
  S(13,1);room=G(0xb9);S(7,1);S(7,1);command=0x87;S(room==0xbf?7:12,1);
  if(room==0xbf){S(7,1);command=0x8b;S(12,1);}
 }
 else
 {
  S(graphics>=2?12:7,1);
  if(!graphics)
  {
   S(10,1);S(10,1);S(13,1);room=G(0xb9);
   for(n=0;n<11;n++){S(rom[0x1d02+n]==room || n==10?16:21,2);if(rom[0x1d02+n]==room){found=1;break;}}
   S(7,1);command=0x82;S(found?7:12,1);if(found){S(7,1);command=0x84;S(12,1);}
  }
  else
  {
   S(10,1);S(10,1);S(4,1);S(7,1);
   for(n=0;n<8;n++){S(7,1);bits|=G(0x603+n*48);S(11,1);S(n<7?13:8,1);}
   S(7,1);S(bits&64?12:7,1);
   if(bits&64){S(7,1);S(13,1);P(0xae,1);S(7,1);command=0x86;}
   else{S(4,1);S(13,1);P(0xae,0);S(7,1);command=0x83;S(12,1);}
  }
 }
 POINT(0x1cf8);S(10,1);S(7,1);previous=G(0x65);S(7,1);P(0x65,command);S(command==previous?11:5,1);
 if(command!=previous){S(13,1);context->audio[6]=command;S(10,1);}
 POINT(0x24ed);S(7,1);S(13,1);P(0x1d,12);S(10,1);S(10,1);POINT(0x1fa7);return 1;
}
u8 source_room_load_class0_ready(SourceClock *clock,SourceIrqContext *context,
 const SourceRoomLoadInput *input,SourceRoomLoadData *data,const u8 *rom,
 SourceActorListData *actors,SourceActorGraphicsData *graphics,
 SourceRoomLoadOutput *output,SourceGraphicsCheckpoint checkpoint,void *user)
{
 u8 *body;
 if(!context || !context->full_ram || !data || !data->graphics || !data->map || !actors || !graphics) return 0;
 body=context->full_ram;
 if(data->room!=body+0xb9 || data->flags!=body+0x90 || data->objects!=body+0x4b0 || data->masks!=body+0x200 ||
    data->graphics->metatiles!=body+0x900 || data->graphics->backup!=body+0x80 || data->graphics->terrain!=body+0x1100 ||
    data->map->cells!=body+0x1c00 || data->map->tilemap!=body+0x1600 || actors->actors!=body+0x600 ||
    actors->progression!=body+0xce || graphics->allocated!=body+0x67) return 0;
 if(!source_room_load_class0_graphics(clock,context,input,data,rom,actors,graphics,output,checkpoint,user)) return 0;
 S(10,1);S(17,1);POINT(0x2c63);
 if(!source_hero_initialize(clock,context,rom,checkpoint,user)) return 0;
 output->completed=8;
 if(!source_room_tail(clock,context,rom,checkpoint,user)) return 0;
 output->completed=9;return 1;
}
#undef POINT
#undef P
#undef G
#undef S

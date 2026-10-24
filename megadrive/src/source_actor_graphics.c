#include "source_actor_graphics.h"
#define S(t,m) do {if(!source_clock_plain(clock,t,m,source_irq_interrupt,context)) return 0;} while(0)
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,
 SourceGraphicsCheckpoint checkpoint,void *user)
{
 if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
 return !checkpoint || checkpoint(user,pc,clock,context);
}
#define POINT(pc) do {if(!point(clock,context,pc,checkpoint,user)) return 0;} while(0)
u8 source_actor_remap(SourceClock *clock,SourceIrqContext *context,
 u8 *patterns,u8 *terrain,u16 address,u16 bytes,u8 remap)
{
 u16 n,tile,row,bit,plane,index,tiles=bytes/32;u8 value,carry,color,acc;
 if(!clock || !context || !context->low || !patterns || !terrain || !bytes || (bytes&31)) return 0;
 for(n=0;n<3;n++) S(11,1);
 S(4,1);S(4,1);S(15,2);S(4,1);S(4,1);S(10,1);S(4,1);S(4,1);
 S(0xa2+remap<256?12:7,1);if(0xa2+remap>=256) S(4,1);
 S(11,1);S(4,1);S(10,1);S(10,1);S(10,1);
 for(n=0;n<16;n++) {S(n<15?21:16,2);terrain[n]=context->low[0x1da2 +remap+n];}
 S(4,1);S(4,1);for(n=0;n<3;n++) {S(4,1);S(8,2);}
 for(tile=0;tile<tiles;tile++)
 {
  S(11,1);S(4,1);S(10,1);
  if(!source_clock_execute(clock,4,1,SOURCE_CLOCK_DI,source_irq_interrupt,context)) return 0;
  S(8,2);S(7,1);S(12,2);S(12,2);S(10,1);S(10,1);
  for(n=0;n<32;n++) {S(20,2);terrain[16+n]=patterns[tile*32+n];S(n<31?13:8,1);}
  S(8,2);S(4,1);S(12,2);S(12,2);
  if(!source_clock_execute(clock,4,1,SOURCE_CLOCK_EI,source_irq_interrupt,context)) return 0;
  S(10,1);S(10,1);S(4,1);
  for(row=0;row<8;row++)
  {
   S(7,1);
   for(bit=0;bit<8;bit++)
   {
    S(4,1);S(4,1);color=0;
    for(plane=0;plane<4;plane++)
    {
     index=16+row*4+3-plane;S(15,2);value=terrain[index];carry=value>>7;terrain[index]=value<<1;
     S(4,1);color=(color<<1)|carry;if(plane<3) S(4,1);
    }
    S(4,1);S(7,1);value=terrain[color];S(7,1);terrain[48+row*8+bit]=value;S(4,1);S(bit<7?13:8,1);
   }
   S(4,1);
   for(plane=0;plane<4;plane++)
   {
    S(7,1);acc=0;
    for(bit=0;bit<8;bit++)
    {
     if(!(plane&1)) S(4,1);
     index=48+row*8+((plane&1)?bit:7-bit);S(15,2);value=terrain[index];carry=value&1;terrain[index]=value>>1;
     S(4,1);acc=(plane&1)?(acc<<1)|carry:(acc>>1)|(carry<<7);
     if(plane&1) S(4,1);
     S(bit<7?13:8,1);
    }
    S(11,1);patterns[tile*32+row*4+plane]=acc;
   }
   S(4,1);S(7,1);S(4,1);S(7,1);S(10,1);
  }
  S(4,1);S(7,1);S(4,1);S(4,1);
  S((address&255)+32<256?12:7,1);if((address&255)+32>=256) S(4,1);
  address+=32;S(tile+1<tiles?13:8,1);
 }
 for(n=0;n<4;n++) S(10,1);
 return 1;
}
u8 source_actor_graphics(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,SourceActorGraphicsData *data,
 SourceGraphicsCheckpoint checkpoint,void *user)
{
 static const u8 setup[]={7,4,7,4,4,11,11,10,11,7,13,7,6,7,6,7,11,7,13,4,7,11,11,11,11,11,4};
 u16 slot,n,descriptor,address,end,previous;u8 type,tile=0,packed,*entity;const u8 *source;
 if(!clock || !context || !rom || !data || !data->actors || !data->patterns || !data->terrain || !data->allocated) return 0;
 S(14,2);S(10,1);
 for(slot=0;slot<8;slot++)
 {
  entity=data->actors+slot*48;S(19,2);type=entity[0];S(7,1);S(10,1);
  if(type>=32)
  {
   S(7,1);S(4,1);S(4,1);S(14,2);S(10,1);S(19,2);
   for(previous=0;previous<slot && data->actors[previous*48]!=type;previous++)
   {S(4,1);S(10,1);S(19,2);S(7,1);S(15,2);S(12,1);}
   if(previous<slot)
   {S(4,1);S(10,1);S(19,2);S(12,1);S(19,2);packed=data->actors[previous*48+2];S(19,2);entity[2]=packed;}
   else
   {
    S(4,1);S(10,1);S(19,2);entity[2]=tile;
    for(n=0;n<sizeof(setup);n++) S(setup[n],1);
    S(8,2);S(8,2);S(11,1);S(11,1);POINT(0x18ac);S(17,1);
    descriptor=0x825f+(type-32)*3;packed=rom[descriptor];
    address=rom[descriptor+1]|((u16)rom[descriptor+2]<<8);
    source=rom+(u32)(packed&15)*16384+(address&0x3fff);address=0x6000+tile*32;
    if(!source_pattern_decode(clock,context,&source,data->patterns+0x2000+tile*32,address,&end)) return 0;
    POINT(0x18af);S(10,1);S(10,1);S(10,1);S(7,1);
    if(packed&240)
    {
     S(17,1);if(!source_actor_remap(clock,context,data->patterns+0x2000+tile*32,data->terrain,address,end-address,packed&240)) return 0;
    }
    else S(10,1);
    POINT(0x18b7);for(n=0;n<10;n++) S(8,2);
    tile=(end>>5)&255;S(4,1);S(12,1);
   }
  }
  S(10,1);S(15,2);S(4,1);S(10,1);
 }
 S(4,1);S(13,1);*data->allocated=tile;POINT(0x18e1);return 1;
}
#undef POINT
#undef S

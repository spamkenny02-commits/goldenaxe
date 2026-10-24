#include "source_hero_initialize.h"
#define S(t,m) do {if(!source_clock_plain(clock,t,m,source_irq_interrupt,context)) return 0;} while(0)
#define G(a) source_room_get(context,a)
#define P(a,v) source_room_put(context,a,v)
static void word(SourceIrqContext *ctx,u16 a,u16 v)
{source_room_put(ctx,a,v);source_room_put(ctx,a+1,v>>8);}
static u8 seq(SourceClock *clock,SourceIrqContext *context,const u8 *ticks,u16 count)
{
 u16 n;u8 t;
 for(n=0;n<count;n++){t=ticks[n];S(t,(t==14 || t==15 || t==19 || t==20 || t==21)?2:1);}
 return 1;
}
#define Q(a) do {if(!seq(clock,context,a,sizeof(a))) return 0;} while(0)
static u8 point(SourceClock *clock,SourceIrqContext *context,u16 pc,
 SourceGraphicsCheckpoint checkpoint,void *user)
{
 if(!source_clock_checkpoint(clock,source_irq_interrupt,context)) return 0;
 return !checkpoint || checkpoint(user,pc,clock,context);
}
#define POINT(pc) do {if(!point(clock,context,pc,checkpoint,user)) return 0;} while(0)
static u8 pose(SourceClock *clock,SourceIrqContext *context,const u8 *rom)
{
 static const u8 water[]={13,7,4,13,4,4,4,10,11,4,4,12,7,6,7,4,10};
 static const u8 bitmap[]={10,4,4,4,19,4,4,4,19,4,7,13,7};
 u8 old,c=0,selected,direction,index;u16 pointer;
 S(13,1);old=G(0x41);S(7,1);
 if(old==3)
 {
  S(12,1);Q(water);direction=G(0x30a);pointer=0x3d67+direction*4;
  S(16,1);word(context,0x43,rom[pointer]|((u16)rom[pointer+1]<<8));
  S(7,1);S(13,1);P(0x42,5);S(19,2);P(0x308,0xa0);S(19,2);P(0x309,0x80);S(10,1);return 1;
 }
 S(7,1);S(7,1);S(13,1);selected=G(0xdf);S(4,1);
 if(selected==1) {S(7,1);S(13,1);c=G(0xe1);S(4,1);c++;S(4,1);}else S(12,1);
 S(13,1);old=G(0x41);S(7,1);
 if(old==2) {S(7,1);S(8,2);c|=4;}else S(12,1);
 S(10,1);for(index=0;index<6;index++) S(4,1);
 index=c*8;S(index+160>255?7:12,1);if(index+160>255) S(4,1);
 S(16,1);word(context,0x308,0x80a0+index);Q(bitmap);
 index=((c*4)|G(0x30a))*8;
 if(old==5) {S(7,1);S(4,1);S(7,1);S(4,1);index&=0xe7;}else S(12,1);
 S(11,1);S(11,1);S(7,1);S(6,1);S(7,1);S(4,1);
 pointer=0x3b67+(u16)index*2;S(16,1);word(context,0x43,rom[pointer]|((u16)rom[pointer+1]<<8));
 S(7,1);S(8,2);S(c&4?7:12,1);if(c&4) S(4,1);
 S(13,1);P(0x42,c&4?5:4);S(10,1);return 1;
}
static u8 scan(SourceClock *clock,SourceIrqContext *context,const u8 *bytes,u16 count,u8 value,u8 *found)
{
 u16 n;
 for(n=0;n<count;n++) {S(bytes[n]==value || n+1==count?16:21,2);if(bytes[n]==value){*found=1;return 1;}}
 *found=0;return 1;
}
u8 source_hero_initialize(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,SourceGraphicsCheckpoint checkpoint,void *user)
{
 static const u16 reset[]={0x312,0x310,0x304,0x30c,0x30b};
 static const u8 defense[]={13,4,4,4,13,4,4,4,4,13,4,4};
 static const u8 attack[]={10,7,7,6,11,7,4,4,11,11,11,10,11,7,10};
 static const u8 contact[]={4,4,7,4,4,4,4,4,7,4,4,4,4,4,4,7};
 static const u8 cell[]={19,4,7,4,7,11,11,11,19,4,4,4,7,4,4};
 static const u8 cell_end[]={10,11,7,4,7,10,4,10,10};
 static const u8 classifier[]={10,15,13,19,19,19};
 static const u8 search_again[]={13,19,19,19};
 u16 n,j,address,xx,yy,table,pointer,count;u8 selected,value,x,y,terrain=0,found,matched,graphics,flags,any;
 if(!clock || !context || !context->ram || !context->audio || !context->full_ram || !rom ||
    G(0xdf)>16 || G(0x30a)>3 || G(0x40)>2) return 0;
 S(14,2);S(4,1);for(n=0;n<5;n++){S(13,1);P(reset[n],0);}
 for(n=0;n<4;n++){S(19,2);P(0x300+n,n==0?2:n==2?240:n==3?3:0);}
 S(17,1);POINT(0x369f);if(!pose(clock,context,rom)) return 0;
 POINT(0x2c8a);S(17,1);for(n=0;n<4;n++) S(10,1);P(0x330,0);
 for(n=1;n<384;n++){S(n<383?21:16,2);P(0x330+n,G(0x32f+n));}S(10,1);
 Q(defense);S(G(0xbf)?7:12,1);if(G(0xbf)) S(4,1);S(4,1);S(13,1);
 P(0x31a,(u8)((G(0xf2)-1)*2+(G(0xbf)?0:(G(0xf1)-1)*4)));
 POINT(0x2ca6);S(17,1);Q(attack);selected=G(0xdf);value=rom[0x2d9e +selected*4+G(0xe0+selected)];S(13,1);P(0x319,value);
 S(13,1);y=G(0x311);S(4,1);S(13,1);x=G(0x313);Q(contact);
 S((x|y)&7?7:12,1);if((x|y)&7) S(8,2);
 S(4,1);S(13,1);P(0x6b,((x&8)>>3)|((y&8)>>2)|(((x|y)&7)?128:0));S(10,1);S(17,1);Q(cell);
 yy=(y-12)&248;xx=((u8)(x-12)>>2)&62;S(((yy*8)&255)+xx>255?7:12,1);if(((yy*8)&255)+xx>255) S(4,1);
 Q(cell_end);address=0x1600+yy*8+xx;
 for(n=0;n<3;n++)
 {
  for(j=0;j<8;j++){S(16,2);P(0x48+n*8+j,G(address+j));}
  address+=8;S(7,1);S(4,1);S(4,1);S((address&255)+56>255?7:12,1);if((address&255)+56>255) S(4,1);
  address+=56;S(n<2?13:8,1);
 }
 S(10,1);S(11,1);S(16,1);word(context,0x60,address+0xc000+0x29be);
 S(13,1);value=G(0xec);S(4,1);S(value?12:7,1);
 if(!value)
 {
  S(10,1);S(10,1);
  for(n=0;n<12;n++){S(7,1);value=G(0x49+n*2);S(4,1);S(value&32?7:12,1);if(value&32){S(15,2);P(0x49+n*2,value|128);}S(4,1);S(4,1);S(n<11?13:8,1);}
 }
 S(13,1);graphics=G(0x40);S(7,1);
 if(graphics==1) {S(12,1);S(4,1);}
 else
 {
  S(7,1);if(!graphics){S(12,1);S(14,2);table=0x2544;}else{S(7,1);S(14,2);S(12,1);table=0x2569;}
  for(n=0;n<5;n++)
  {
   any=n==0 || n>=3;S(17,1);Q(classifier);pointer=rom[table+n*4]|((u16)rom[table+n*4+1]<<8);count=rom[table+n*4+2];if(!count)count=256;
   if(!scan(clock,context,rom+pointer,count,G(0x52),&found))return 0;
   matched=0;
   if(any && found){S(12,1);S(19,2);terrain=rom[table+n*4+3];S(10,1);matched=1;}
   else if(!any && !found) S(11,1);
   else
   {
    if(any){S(7,1);S(12,1);}else S(5,1);Q(search_again);
    if(!scan(clock,context,rom+pointer,count,G(0x54),&found))return 0;
    if(found){S(5,1);S(19,2);terrain=rom[table+n*4+3];S(10,1);matched=1;}else S(11,1);
   }
   S(matched?12:7,1);if(matched)break;
  }
  if(n==5){S(4,1);terrain=0;}
 }
 POINT(0x2d3e);S(13,1);P(0x41,terrain);S(13,1);value=G(0xf0);S(4,1);S(value?7:12,1);
 if(value)
 {
  S(13,1);S(10,1);S(7,1);S(7,1);S(8,2);flags=G(0x53)&G(0x55)&192;S(flags&64?7:12,1);
  if(flags&64)
  {
   S(4,1);S(flags&128?7:12,1);S(10,1);S(7,1);
   for(n=0;n<12;n++)
   {
    S(12,2);value=G(0x49+n*2);S(value&64?7:12,1);
    if(value&64){S(15,2);P(0x49+n*2,value&127);if(flags&128)S(12,1);}
    else if(flags&128){S(15,2);P(0x49+n*2,value|128);}
    S(6,1);S(6,1);S(n<11?13:8,1);
   }
   if(flags&128)S(12,1);
  }
 }
 S(10,1);POINT(0x24e7);return 1;
}
#undef POINT
#undef Q
#undef P
#undef G
#undef S

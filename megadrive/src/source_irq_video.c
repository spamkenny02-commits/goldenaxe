#include "source_irq_video.h"
typedef struct {const SourceIrqContext *context;SourceIrqVideo *video;u8 ram[336];} Memory;
static u8 put(Memory *m,u16 a,u8 value)
{
 if(a>=0xc000 && a<0xc050){m->ram[a-0xc000]=value;return 1;}
 if(a>=0xdd00 && a<0xde00){m->ram[80+a-0xdd00]=value;return 1;}
 return 0;
}
static u8 get(Memory *m,u16 a,u8 bank,u8 cartridge,u8 *value)
{
 if(a>=0xc000)
 {
  a=0xc000+(a&8191);
  if(a<0xc050)*value=m->ram[a-0xc000];
  else if(a>=0xdd00 && a<0xde00)*value=m->ram[80+a-0xdd00];
  else if(m->context->full_ram)*value=source_room_get(m->context,a-0xc000);
  else return 0;
 }
 else if(a<0x8000)*value=m->video->rom[a];
 else if(cartridge){if(!m->video->sram)return 0;*value=m->video->sram[a-0x8000];}
 else {if(bank>=16)return 0;*value=m->video->rom[(u32)bank*16384+(a&0x3fff)];}
 return 1;
}
static void emit(SourceIrqVideo *v,u16 a,u8 value)
{v->vram[a&0x3fff]=value;v->bytes++;}
#define READ(a,b,c,v) do {if(!get(&m,a,b,c,&v)){video->error=SOURCE_IRQ_VIDEO_READ;return 0;}} while(0)
u8 source_irq_video_publish(void *user,const SourceIrqContext *context,
 const SourceClockIrq *entry,u16 *tile_count)
{
 SourceIrqVideo *video=user;Memory m;u16 n,j,count,address,source,queue,pointer,height,width,row;
 u8 value,bank,command,bits;u16 guard;
 (void)entry;
 if(!video || !context || !context->ram || !video->rom || !video->vram || !video->cram || !video->registers || !tile_count)return 0;
 video->error=0;video->bytes=video->tiles=0;*tile_count=0;
 if(!context->ram[0x2e])return 1;
 m.context=context;m.video=video;for(n=0;n<336;n++)m.ram[n]=context->ram[n];
 video->registers[10]=m.ram[0x1a];video->registers[9]=m.ram[0x19];video->registers[8]=m.ram[0x18];
 for(n=0;n<64;n++)emit(video,0x3f00+n,m.ram[80+0x40+n]);
 for(n=0;n<128;n++)emit(video,0x3f80+n,m.ram[80+0x80+n]);
 bank=m.ram[0x42];
 if(bank)
 {
  source=m.ram[0x43]|((u16)m.ram[0x44]<<8);
  if(bank>=16 || source>=0xc000){video->error=SOURCE_IRQ_VIDEO_READ;return 0;}
  READ(source,bank,0,value);source++;count=value?value:256;*tile_count=video->tiles=count;m.ram[0x42]=0;address=0x3e00;
  for(n=0;n<count;n++)for(j=0;j<8;j++)
  {
   u16 plane;for(plane=0;plane<3;plane++){READ(source,bank,0,value);source++;emit(video,address++,value);}emit(video,address++,0);
  }
 }
 if(!m.ram[0x33] && (m.ram[0x45]&3))
 {
  bits=m.ram[0x45]&3;address=0x3d02+((u16)bits<<6);source=0xdb02+((u16)bits<<6);m.ram[0x45]=0;
  for(n=0;n<60;n++){READ(source,4,0,value);source++;emit(video,address++,value);}
 }
 if(!m.ram[0x33])for(n=0;n<32;n++){READ(0xdca0+n,4,0,value);video->cram[n]=value&63;}
 pointer=m.ram[0x34]|((u16)m.ram[0x35]<<8);
 if(!put(&m,pointer,0)){video->error=SOURCE_IRQ_VIDEO_QUEUE;return 0;}
 queue=0xdd00;
 for(guard=0;guard<128;guard++)
 {
  READ(queue,4,0,command);if(!command)return 1;
  if(command==1)
  {
   READ(queue+1,4,0,bank);READ(queue+2,4,0,value);source=value;READ(queue+3,4,0,value);source|=(u16)value<<8;
   READ(queue+4,4,0,value);address=value;READ(queue+5,4,0,value);address|=(u16)value<<8;
   READ(queue+6,4,0,value);count=value?value:256;
   for(n=0;n<count;n++)for(j=0;j<32;j++){READ(source,bank,bank&128,value);source++;emit(video,address++,value);}
   queue+=7;
  }
  else
  {
   READ(queue+1,4,0,value);height=value?value:256;READ(queue+2,4,0,value);width=(u8)(value*2);if(!width)width=256;
   READ(queue+3,4,0,value);source=value;READ(queue+4,4,0,value);source|=(u16)value<<8;
   for(row=0;row<height;row++)
   {
    address=source+0xa200;for(n=0;n<width;n++){READ(source+n,4,0,value);emit(video,address+n,value);}
    if(!put(&m,queue+1,(u8)(height-row-1))){video->error=SOURCE_IRQ_VIDEO_QUEUE;return 0;}source+=64;
   }
   queue+=5;
  }
 }
 video->error=SOURCE_IRQ_VIDEO_QUEUE;return 0;
}
#undef READ

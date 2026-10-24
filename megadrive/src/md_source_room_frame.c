#include "md_source_room_frame.h"
#define TILE_BASE 16
#define CLONE_BASE 768
#define SOLID_TILE 832
#define BLANK_TILE 833
#define BORDER_TILE 834
static u16 color(u8 value)
{
 static const u8 levels[4]={0,3,5,7};
 return ((u16)levels[value&3]<<1)|((u16)levels[(value>>2)&3]<<5)|((u16)levels[(value>>4)&3]<<9);
}
static u16 attribute(u16 value)
{return (TILE_BASE+(value&511))|((value&0x200)<<2)|((value&0x400)<<2)|((value&0x800)<<2)|((value&0x1000)<<3);}
u8 md_source_room_frame_upload(MdSourceRoomFrame *s,const u8 *vram,const u8 *cram,
 u8 reg0,u8 reg1,u8 reg6,u8 reg7,u8 reg8,u8 reg9)
{
 u16 n,row,x,word,count;const u8 *source;
 if(!s || !vram || !cram || ((u32)vram&1) || reg8 || reg9 || VDP_isEnable() ||
    VDP_getScreenWidth()!=256 || VDP_getScreenHeight()!=224 || VDP_getPlaneWidth()!=64 || VDP_getPlaneHeight()!=32)return MD_SOURCE_ROOM_INVALID;
 for(n=0;n<64;n++)s->sat[n]=vram[0x3f00+n];
 for(n=0;n<128;n++)s->sat[64+n]=vram[0x3f80+n];
 if(source_sms_sprite8_prepare(&s->sprites,s->sat,reg0,reg1,reg6,CLONE_BASE))return MD_SOURCE_ROOM_INVALID;
 s->error=0;
 for(n=0;n<64;n++)s->palette[n]=0;
 for(n=0;n<32;n++)s->palette[n]=color(cram[n]);
 s->palette[0]=s->palette[16]=0;
 s->palette[33]=color(cram[0]);s->palette[49]=color(cram[16]);s->palette[50]=color(cram[16+(reg7&15)]);
 PAL_setColors(0,s->palette,64,CPU);VDP_setBackgroundColor(0);
 for(n=0;n<512;n+=8){pattern_convert(vram+n*32,s->patterns,64);VDP_loadTileData(s->patterns,TILE_BASE+n,8,CPU);}
 for(n=0;n<8;n++)s->patterns[n]=0x11111111UL;
 VDP_loadTileData(s->patterns,SOLID_TILE,1,CPU);
 for(n=0;n<8;n++)s->patterns[n]=0;
 VDP_loadTileData(s->patterns,BLANK_TILE,1,CPU);
 for(n=0;n<8;n++)s->patterns[n]=0x22222222UL;
 VDP_loadTileData(s->patterns,BORDER_TILE,1,CPU);
 VDP_clearPlane(BG_A,TRUE);VDP_clearPlane(BG_B,TRUE);
 VDP_fillTileMapRect(BG_A,BLANK_TILE,0,0,64,32);
 VDP_fillTileMapRect(BG_B,BLANK_TILE,0,0,64,32);
 VDP_setHorizontalScroll(BG_A,0);VDP_setHorizontalScroll(BG_B,0);
 VDP_setVerticalScroll(BG_A,0);VDP_setVerticalScroll(BG_B,0);
 for(row=0;row<24;row++)
 {
  source=vram+0x3800+row*64;
  for(x=0;x<32;x++)
  {
   word=source[x*2]|((u16)source[x*2+1]<<8);s->foreground[x]=attribute(word);
   s->background[x]=SOLID_TILE|((word&0x800)?0x6000:0x4000);
  }
  if(reg0&32){s->foreground[0]=BLANK_TILE;s->background[0]=0x6000|BORDER_TILE;}
  VDP_setTileMapDataRow(BG_A,s->foreground,row+2,0,32,CPU);
  VDP_setTileMapDataRow(BG_B,s->background,row+2,0,32,CPU);
 }
 count=s->sprites.count;
 for(n=0;n<count;n++)
 {
  pattern_convert(vram+s->sprites.source_tile[n]*32,s->patterns,8);
  for(row=0;row<8;row++)s->patterns[row]=(s->sprites.rows[n]&(1<<row))?s->patterns[row]&s->sprites.columns[n]:0;
  VDP_loadTileData(s->patterns,CLONE_BASE+n,1,CPU);
 }
 VDP_resetSprites();
 for(n=0;n<count;n++)VDP_setSpriteFull(n,(s16)s->sprites.sat[n*4+3]-128,(s16)s->sprites.sat[n*4]-128,
  SPRITE_SIZE(1,1),s->sprites.sat[n*4+2],s->sprites.sat[n*4+1]);
 if(!count){VDP_setSpriteFull(0,0,0,SPRITE_SIZE(1,1),0,0);count=1;}
 VDP_updateSprites(count,CPU);return MD_SOURCE_ROOM_OK;
}

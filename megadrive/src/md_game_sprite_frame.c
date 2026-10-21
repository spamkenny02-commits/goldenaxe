#include "md_game_sprite_frame.h"
u8 md_game_sprite_frame_bind(MdGameSpriteFrame *s,const u32 *patterns,u8 r0,u8 r1,u8 r6,u16 base,u8 verify)
{
 if(!s || !patterns || ((u32)patterns&1) || s->pending || !(r0&4) || (r1&0x1b) || base>1984) return MD_Z80_PSG_INVALID;
 s->patterns=patterns;s->reg0=r0;s->reg1=r1;s->reg6=r6;s->tile_base=base;s->verify=verify;
 s->accepted=s->delivered=0;s->error=s->pending=0;s->ready=1;
 s->stream.ready=s->stream.done=s->stream.error=0;return MD_Z80_PSG_OK;
}
u8 md_game_sprite_frame_capture(void *user,const SourceGameSatPacket *p)
{
 MdGameSpriteFrame *s=user;u16 n;
 if(!s || !p || !s->ready || s->error) return 0;
 if(s->pending || p->first_xy-p->first_y!=16215UL) {s->error=1;return 0;}
 for(n=0;n<192;n++) s->packet.bytes[n]=p->bytes[n];
 s->packet.first_y=p->first_y;s->packet.first_xy=p->first_xy;
 s->pending=1;s->accepted++;return 1;
}
u8 md_game_sprite_frame_step(MdGameSpriteFrame *s,MdZ80PsgMailbox *mailbox)
{
 u8 result;
 if(!s || !mailbox || !s->ready) return MD_Z80_PSG_INVALID;
 if(s->error) return MD_Z80_PSG_FAULT;
 if(!s->pending) return MD_Z80_PSG_WAIT;
 if(s->pending==1) {
  result=md_sms_sprite8_stream_begin(&s->stream,s->packet.bytes,s->patterns,s->reg0,s->reg1,s->reg6,s->tile_base,s->verify);
  if(result) {s->error=1;return result;}
  s->pending=2;
 }
 result=md_sms_sprite8_stream_step(&s->stream,mailbox);
 if(result!=MD_Z80_PSG_OK && result!=MD_Z80_PSG_WAIT) s->error=1;
 if(result==MD_Z80_PSG_OK && s->stream.done) {s->pending=0;s->delivered++;}
 return result;
}

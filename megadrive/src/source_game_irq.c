#include "source_game_irq.h"
u8 source_game_irq_bind(SourceGameIrqContext *c,u8 *ram)
{
 if(!c || !ram || !c->timed.core.low || c->timed.core.low_bytes!=32768 || !c->timed.core.bank6 ||
    (c->timed.core.input.lines!=262 && c->timed.core.input.lines!=313)) return 0;
 c->ram=ram;c->timed.core.ram=ram;c->timed.core.audio=ram+0x1e00;
 c->error=c->producer_active=0;c->bound=1;return 1;
}
u8 source_game_irq_interrupt(void *user,const SourceClockIrq *entry,SourceClockWork *work)
{
 SourceGameIrqContext *c=user;u16 n;u8 full,accepted,status;
 if(!work) return 0;
 work->tstates=work->fetches=0;
 if(!c || !entry || !c->bound || c->error) return 0;
 status=c->vdp_status;
 if(c->status_read && !c->status_read(c->status_context,entry,&status)) {c->error=SOURCE_GAME_IRQ_STATUS;return 0;}
 if(!(status&128)) {c->error=SOURCE_GAME_IRQ_STATUS;return 0;}
 full=c->ram[0x2e]!=0;
 if(full && c->producer_active) {c->error=SOURCE_GAME_IRQ_UNSAFE;return 0;}
 /* Original003F vector write occurs before0137 callback entry. */
 c->ram[0x1b]=status;
 for(n=0;n<80;n++) c->compact[n]=c->ram[n];
 for(n=0;n<256;n++) c->compact[80+n]=c->ram[0x1d00+n];
 if(full) {
  for(n=0;n<192;n++) c->sat.bytes[n]=c->ram[0x1d40+n];
  /* SAT64 stage prefix before first OUTI:27+10+10+3*(16+12)+7+13+
   *4+11+7+11+7+10+17. First completed OUTI adds16T. SAT128 starts
   * after complete SAT64 (including RET) plus INC/OUT/DEC/OUT/CALL. */
  c->sat.first_y=entry->entry_elapsed+234UL*15;
  c->sat.first_xy=entry->entry_elapsed+(1252UL+47+16)*15;
  if(c->video && !c->video(c->video_context,&c->sat)) {c->error=SOURCE_GAME_IRQ_VIDEO;return 0;}
 }
 c->timed.core.ram=c->compact;
 accepted=source_irq_master_interrupt(&c->timed,entry,work);
 c->timed.core.ram=c->ram;
 if(!accepted) {c->error=c->timed.core.error?c->timed.core.error:SOURCE_GAME_IRQ_INVALID;return 0;}
 for(n=0;n<80;n++) c->ram[n]=c->compact[n];
 for(n=0;n<256;n++) c->ram[0x1d00+n]=c->compact[80+n];
 if(full) c->ram[0x1fff]=6; /* Wait restore later reinstates foreground bank. */
 return 1;
}

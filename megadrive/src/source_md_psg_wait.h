#ifndef GAW_SOURCE_MD_PSG_WAIT_H
#define GAW_SOURCE_MD_PSG_WAIT_H
#include <types.h>

enum {SOURCE_MD_PSG_SINGLE,SOURCE_MD_PSG_PAIR630,SOURCE_MD_PSG_QUAD315};
/* Native68000 only. Caller validates all arguments: V0..255,phase0..3419,
 * kind0..2,stable disjoint byte storage of1/2/4bytes. Standard nonlatched
 * H32/224/noninterlace only. Mask interrupts and prohibit DMA for the entire
 * call. Start at least3000master ticks before the intended line begins,
 * which must be the next occurrence of that V value. V alone cannot resolve
 * PAL/NTSC vertical aliases. No timeout or global epoch discovery.
 * Waits until the target phase,then emits. IO/poll latency is measured by the
 * diagnostic and is additional to20tickHVquantization. Fixed bursts have
 * small relative spacing errors; this API does not promise exact deadlines. */
void source_md_psg_wait_emit(u16 vertical,u16 phase,const u8 *bytes,u16 kind);
#endif

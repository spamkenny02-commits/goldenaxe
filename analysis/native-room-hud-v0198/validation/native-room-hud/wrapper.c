#include "source_room_hud.h"
typedef struct {u32 count,points;u32 *events,*snapshots;u8 *states;SourceIrqContext *irq;} LoadTrace;
static void snapshot(const SourceClock *clock,const SourceIrqContext *ctx,u32 *out)
{
 out[0]=clock->raster;out[1]=clock->until_vint;out[2]=clock->elapsed;
 out[3]=clock->foreground_tstates;out[4]=clock->foreground_m1;out[5]=clock->irq_tstates;out[6]=clock->irq_m1;
 out[7]=clock->irq_count;out[8]=clock->status_suppressions;out[9]=clock->vector_coalescences;
 out[10]=clock->refresh;out[11]=clock->iff;out[12]=clock->blocked;out[13]=clock->pending;out[14]=clock->first;
 out[15]=0;out[16]=ctx->error;out[17]=ctx->audio_de;
}
static void trace(void *context,const SourceClockIrq *entry,const SourceClockWork *work)
{
 LoadTrace *p=(LoadTrace *)context;u32 *row;if(p->count>=64) {p->count++;return;}
 row=p->events+p->count++*6;row[0]=entry->entry_elapsed;row[1]=entry->entry_raster;
 row[2]=entry->entry_refresh;row[3]=work->tstates;row[4]=work->fetches;
 row[5]=p->irq->last_irq.stages[SOURCE_IRQ_SAT64].tstates!=0;
}
static u8 point(void *context,u16 pc,const SourceClock *clock,const SourceIrqContext *ctx)
{
 static const u16 pcs[]={0x1706,0x170e,0x1720,0x1733,0x1748,0x24b9,0x192a,0x192d,0x24bc,0x1de5,0x1de8};
 LoadTrace *p=(LoadTrace *)context;u8 *state;u16 n;
 if(p->points>=11 || pc!=pcs[p->points]) return 0;
 snapshot(clock,ctx,p->snapshots+p->points*18);state=p->states+p->points*736;
 for(n=0;n<336;n++) state[n]=ctx->ram[n];
 for(n=0;n<400;n++) state[336+n]=ctx->audio[n];
 p->points++;return 1;
}
static u32 hash_more(const u8 *bytes,u16 count,u32 value)
{
 u16 n;for(n=0;n<count;n++) value=(value^bytes[n])*16777619UL;return value;
}
static u32 hash(const u8 *bytes,u16 count) { return hash_more(bytes,count,2166136261UL); }
u8 room_hud_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,
                      const u8 *bank6,u16 room,const u8 *map_bank,const u8 *patterns,const u8 *bank2,const u8 *bank11,const u8 *bank4,const u8 *hud,
                      u32 *out,u32 *events,u32 *points,u8 *states)
{
 SourceClock clock;SourceIrqContext ctx={0};LoadTrace log={0};SourceGraphicsData data;SourceWorldMapData map;
 static u8 pixels[16384],meta[2048],backup[16],terrain[1024],saved[1024],cells[256],tilemap[1536];u16 n;
 s32 raster=(s32)(phase[1]*3420)+(s32)(phase[0]-phase[2]);u32 period=phase[3]*3420;
 if((phase[3]!=262 && phase[3]!=313) || phase[5] || (phase[6]&4) || !(phase[6]&32) ||
    (phase[7]!=32 && phase[7]!=33) || (phase[11]&16)) return 0;
 while(raster<0) raster+=period;
 while((u32)raster>=period) raster-=period;
 if(!source_clock_init(&clock,phase[3],raster,refresh,phase[8],phase[9],phase[10])) return 0;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.bank6=bank6;ctx.low_bytes=32768;
 ctx.input.lines=phase[3];ctx.input.reset_mask=16;
 ctx.trace=trace;ctx.trace_context=&log;log.irq=&ctx;
 log.events=events;log.snapshots=points;log.states=states;
 for(n=0;n<sizeof(cells);n++) cells[n]=0xa7;
 for(n=0;n<sizeof(tilemap);n++) tilemap[n]=0xa7;
 map.cells=cells;map.tilemap=tilemap;
 for(n=0;n<sizeof(pixels);n++) pixels[n]=0xa7;
 for(n=0;n<sizeof(meta);n++) meta[n]=0xa7;
 for(n=0;n<sizeof(terrain);n++) terrain[n]=0xa7;
 data.patterns=pixels;data.metatiles=meta;data.backup=backup;data.terrain=terrain;data.saved_terrain=saved;
 if(!source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,point,&log) || log.count>64 || log.points!=6) return 0;
 if(!source_world_map_load(&clock,&ctx,room,1,map_bank,bank2,&data,&map,point,&log) || log.count>64 || log.points!=9) return 0;
 if(!source_room_hud_prepare(&clock,&ctx,&data,&map,bank4,hud,point,&log) || log.count>64 || log.points!=11) return 0;
 snapshot(&clock,&ctx,out);out[18]=hash(pixels,sizeof(pixels));out[19]=hash(meta,sizeof(meta));
 out[20]=hash(backup,sizeof(backup));out[21]=hash(terrain,sizeof(terrain));out[22]=hash(saved,sizeof(saved));
 out[23]=hash(pixels,6176);out[24]=hash_more(meta+0x400,56,hash(meta,912));
 out[25]=hash(backup,16);out[26]=hash(terrain,512);out[27]=hash(saved,512);
 out[28]=hash(cells,sizeof(cells));out[29]=hash(tilemap,sizeof(tilemap));out[30]=hash(map.metadata,3);
 out[31]=hash(cells,160);out[32]=hash(map.metadata,3);
 {u8 patch[8];u16 address=0xd600+(map.metadata[1]&0xf0)*8+(map.metadata[1]&15)*4;
  for(n=0;n<8;n++) {u16 dest=address+(n<4?n:n+60);patch[n]=dest>=0xdd00?ram[80+dest-0xdd00]:tilemap[dest-0xd600];}
  out[33]=hash(patch,8);}
 {u16 cell=map.metadata[1],below=cell+16;u8 pair[2];pair[0]=cells[cell];pair[1]=below<256?cells[below]:ram[80+below-256];out[34]=hash(pair,2);}
 out[35]=hash(tilemap+0x500,256);out[36]=hash(tilemap,1280);
 return 1;
}

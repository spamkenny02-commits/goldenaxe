"""Single16D0 input through native loading, reveal/fade and all16 contours to2002."""
import ctypes as c,json,os,struct,subprocess
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_native_room_load import MODULES as LOAD_MODULES,records,read_reference,reference_manifest
from validate_native_room_graphics import PREFIX_PCS
from actor_reference import load_room_actors
MODULES=['source_room_contours','source_irq_video','source_room_reveal','source_room_ready','source_hero_initialize',*LOAD_MODULES]
HERO_PCS=[0x2c63,0x369f,0x2c8a,0x2ca6,0x2d3e,0x24e7]
TAIL_PCS=[0x5b20,0x1caf,0x1cf8,0x24ed,0x1fa7]
HERO_INDICES=list(range(0x41,0x6c))+list(range(0x300,0x4b0))
WRAPPER=r'''#include "source_room_contours.h"
#include "source_irq_video.h"
static SourceVdpDirty dirty;
const u8 *room_dirty_tiles(void){return dirty.patterns;}
const u8 *room_dirty_names(void){return dirty.names;}
u32 room_dirty_palette(void){return dirty.palette;}
u8 room_dirty_sat(void){return dirty.sat;}
static u8 pixels[16384],saved[1024],hero_before[475],hero_after[475];
typedef struct {u32 count,points;u32 *events,*snapshots;u8 *states;SourceIrqContext *irq;} Trace;
static void snapshot(const SourceClock *k,const SourceIrqContext *ctx,u32 *out)
{
 out[0]=k->raster;out[1]=k->until_vint;out[2]=k->elapsed;out[3]=k->foreground_tstates;out[4]=k->foreground_m1;
 out[5]=k->irq_tstates;out[6]=k->irq_m1;out[7]=k->irq_count;out[8]=k->status_suppressions;out[9]=k->vector_coalescences;
 out[10]=k->refresh;out[11]=k->iff;out[12]=k->blocked;out[13]=k->pending;out[14]=k->first;out[15]=0;out[16]=ctx->error;out[17]=ctx->audio_de;
}
static void trace(void *user,const SourceClockIrq *entry,const SourceClockWork *work)
{
 Trace *t=user;u32 *out;if(t->count>=128){t->count++;return;}out=t->events+t->count++*6;
 out[0]=entry->entry_elapsed;out[1]=entry->entry_raster;out[2]=entry->entry_refresh;out[3]=work->tstates;out[4]=work->fetches;out[5]=t->irq->last_irq.stages[SOURCE_IRQ_SAT64].tstates!=0;
}
static u8 point(void *user,u16 pc,const SourceClock *k,const SourceIrqContext *ctx)
{
 Trace *t=user;u16 n,j;u32 *out;u8 *s,*hero;if(t->points>=114)return 0;
 out=t->snapshots+t->points*19;s=t->states+t->points*736;snapshot(k,ctx,out);out[18]=pc;
 for(n=0;n<336;n++){s[n]=ctx->ram[n];}for(n=0;n<400;n++){s[336+n]=ctx->audio[n];}
 if(pc==0x2c63 || pc==0x24e7)
 {
  hero=pc==0x2c63?hero_before:hero_after;j=0;
  for(n=0x41;n<0x6c;n++)hero[j++]=source_room_get(ctx,n);
  for(n=0x300;n<0x4b0;n++)hero[j++]=source_room_get(ctx,n);
 }
 t->points++;return 1;
}
u8 room_ready_case(const u32 *phase,u8 refresh,const u8 *rom,u8 *body,u32 *out,u32 *events,u32 *points,u8 *states)
{
 SourceClock k;SourceIrqContext ctx={0};SourceIrqVideo video={0};u8 cram[32]={0},regs[16]={0};Trace log={0};SourceGraphicsData graphics;SourceWorldMapData map;SourceRoomLoadData data;SourceRoomLoadOutput loaded;
 SourceActorListData actors={body+0x600,body+0xa2,body+0xb9,body+0x200,body+0xce};SourceActorGraphicsData actor_graphics={body+0x600,pixels,body+0x1100,body+0x67};
 u16 n,room=body[0xb9]|((u16)body[0xba]<<8);u8 ram[336],audio[400],hud[16];
 SourceRoomLoadInput input={rom+0x3c010,rom+0x8000,rom+0x2c000,rom+(8+(room>>7))*16384UL,rom+0x10000,hud,1};
 s32 raster=(s32)(phase[1]*3420)+(s32)(phase[0]-phase[2]);u32 period=phase[3]*3420;
 while(raster<0){raster+=period;}while((u32)raster>=period){raster-=period;}
 for(n=0;n<80;n++)ram[n]=body[n];
 for(n=0;n<256;n++)ram[80+n]=body[0x1d00+n];
 for(n=0;n<400;n++)audio[n]=body[0x1e00+n];
 hud[0]=body[0x318];for(n=0;n<4;n++)hud[1+n]=body[0xda+n];for(n=0;n<9;n++)hud[5+n]=body[0xcf+n];hud[14]=body[0xbf];hud[15]=body[0xf1];
 for(n=0;n<16384;n++)pixels[n]=0xa7;
 ctx.ram=ram;ctx.audio=audio;ctx.full_ram=body;ctx.low=rom;ctx.low_bytes=32768;ctx.bank6=rom+0x18000;ctx.input.lines=phase[3];ctx.input.reset_mask=16;
 source_vdp_dirty_clear(&dirty);video.dirty=&dirty;video.rom=rom;video.vram=pixels;video.cram=cram;video.registers=regs;ctx.video=source_irq_video_publish;ctx.video_context=&video;
 ctx.trace=trace;ctx.trace_context=&log;log.irq=&ctx;log.events=events;log.snapshots=points;log.states=states;
 graphics.patterns=pixels;graphics.metatiles=body+0x900;graphics.backup=body+0x80;graphics.terrain=body+0x1100;graphics.saved_terrain=saved;
 map.cells=body+0x1c00;map.tilemap=body+0x1600;data.graphics=&graphics;data.map=&map;data.room=body+0xb9;data.flags=body+0x90;data.objects=body+0x4b0;data.masks=body+0x200;
 if(!source_clock_init(&k,phase[3],raster,refresh,phase[8],phase[9],phase[10]) || !source_room_load_class0_ready(&k,&ctx,&input,&data,rom,&actors,&actor_graphics,&loaded,point,&log) || log.count>128)return 0;
 if(!source_room_reveal_prepare(&k,&ctx,rom,pixels,point,&log) || !source_room_reveal_fade(&k,&ctx,rom,point,&log))return 0;
 if(!source_room_contours_marked(&k,&ctx,rom,pixels,&dirty,point,&log))return 0;
 snapshot(&k,&ctx,out);out[18]=log.points;out[19]=loaded.history.calls;out[20]=loaded.history.restored;out[21]=loaded.completed;out[22]=source_room_get(&ctx,0x67);out[23]=source_room_get(&ctx,0xa2);
 /* Observational export after the last checkpoint; never feeds the clock. */
 for(n=0;n<8192;n++)body[n]=source_room_get(&ctx,n);
 return 1;
}
const u8 *room_ready_patterns(void){return pixels;}
const u8 *room_ready_hero_before(void){return hero_before;}
const u8 *room_ready_hero_after(void){return hero_after;}
'''

def main():
 folder=ROOT/'validation/native-room-contours-dirty';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];sdk=ROOT.parents[1]/'work/sgdk'
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'ready.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-4000:]
 lib=c.CDLL(str(folder/'ready.dll'));u8=c.POINTER(c.c_uint8);u32=c.POINTER(c.c_uint32);lib.room_ready_case.argtypes=[u32,c.c_uint8,u8,u8,u32,u32,u32,u8];lib.room_ready_case.restype=c.c_uint8
 for n in ['room_ready_patterns','room_ready_hero_before','room_ready_hero_after']:getattr(lib,n).restype=u8
 lib.room_dirty_tiles.restype=u8;lib.room_dirty_names.restype=u8;lib.room_dirty_palette.restype=c.c_uint32;lib.room_dirty_sat.restype=c.c_uint8
 original=(ROOT/'input/original.sms').read_bytes();rom=(c.c_uint8*len(original)).from_buffer_copy(original);cases=[];results=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_bytes())['routes']:
  for mask in [0,255]:
   source=ROOT/f'validation/loader-tail-refresh/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    rows=records(source,region,'tail');cycles=json.loads(read_reference(source/f'{region}-cycle-events.json','tail'));start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target);entry=next(e for e in rows if e['pc']==0x16d0 and e['time']==start);tag=(town,mask,region)
    raw=read_reference(source/f'{region}-loader-entry-records.bin','tail');before=next(raw[n+8:n+8200] for n in range(0,len(raw),8200) if struct.unpack_from('<Q',raw,n)[0]==start);assert before[:80]+before[0x1d00:0x1e00]==entry['ram'] and before[0x1e00:0x1f90]==entry['audio']
    resources=load_room_actors(original,target,before[0x200+target])[4];pcs=PREFIX_PCS+[v for _ in resources for v in [0x18ac,0x18af,0x18b7]]+[0x18e1]+HERO_PCS+TAIL_PCS+[0xaa4,0xb95,0xbb3,0xac0,0xace,0x1fb6]+[v for _ in range(16) for v in [0xb95,0xbb3,0xb95,0xbb3]]+[0x2002];assert len(pcs)<=114
    body=(c.c_uint8*8192).from_buffer_copy(before);out=(c.c_uint32*24)();events=(c.c_uint32*768)();points=(c.c_uint32*2166)();states=(c.c_uint8*83904)();assert lib.room_ready_case((c.c_uint32*12)(*entry['phase']),entry['refresh'],rom,body,out,events,points,states),(tag,'rejected')
    assert out[18]==len(pcs) and out[19]==3 and out[21]==9,(tag,'completion',out[:]);irq=json.loads(read_reference(source/f'{region}-audio-irq-events.json','tail'));cursor=start
    for n,pc in enumerate(pcs):
     if pc in [0x1fb6,0x2002]:
      endpoint=next(e for e in cycles if e[1]==pc and e[2]>cursor);p=list(points[n*19:(n+1)*19]);state=bytes(states[n*736:(n+1)*736]);assert p[18]==pc and p[2]==endpoint[2]-start and state[0x2f]==endpoint[5],(tag,'fade return time/clock');cursor=endpoint[2];continue
     end=next(r for r in rows if r['pc']==pc and r['time']>cursor);cursor=end['time'];p=list(points[n*19:(n+1)*19]);state=bytes(states[n*736:(n+1)*736]);phase=end['phase'];delta=((phase[0]-phase[2]+0x80000000)&0xffffffff)-0x80000000
     assert p[18]==pc and p[0]==(phase[1]*3420+delta)%(phase[3]*3420) and p[2]==cursor-start,(tag,hex(pc),'phase/time',p,cursor-start)
     assert p[10]==end['refresh'] and p[4]+p[6]==end['m1']-entry['m1'],(tag,n,hex(pc),'M1/R',p[10],end['refresh'],p[4]+p[6],end['m1']-entry['m1'])
     assert state[336:]==end['audio'] and all(state[j]==end['ram'][j] for j in range(336) if j not in [0x1b,0x20,0x21,0x22,0x23]),(tag,hex(pc),'RAM/audio',[(hex(j),state[j],end['ram'][j]) for j in range(336) if state[j]!=end['ram'][j]][:8])
     assert (p[11],p[13],p[14])==(phase[8],phase[10],1) and not p[12] and not p[16]
     assert [(events[j*6],bool(events[j*6+5])) for j in range(p[7])]==[(e[2]-start,bool(e[5])) for e in irq if e[1]==0x137 and start<e[2]<cursor],(tag,'IRQ schedule')
    body=bytes(body);assert body[0x1cf0:0x1d00]==end['context'][2:18] and body[0x200:0x300]==end['context'][18:274] and body[0x600:0x900]==end['actors'] and out[23]==end['active_count']
    hero_file=next(source.glob(f'{region}-hero-*-before.bin'));hero_before=read_reference(hero_file,'tail');hero_after=read_reference(hero_file.with_name(hero_file.name.replace('-before','-after')),'tail')
    hb=c.string_at(lib.room_ready_hero_before(),475);ha=c.string_at(lib.room_ready_hero_after(),475);assert hb==bytes(hero_before[j] for j in HERO_INDICES),(tag,'hero input',[(hex(j),a,hero_before[j]) for j,a in zip(HERO_INDICES,hb) if a!=hero_before[j]][:8]);assert ha==bytes(hero_after[j] for j in HERO_INDICES),(tag,'hero output')
    late=next(raw[n+8:n+8200] for n in range(0,len(raw),8200) if struct.unpack_from('<Q',raw,n)[0]==next(r['time'] for r in rows if r['pc']==0xace and r['time']>start));fields=list(range(0x1cc0,0x1ce0))+list(range(0x60,0x68))+[0xa4,0xa5,0xa8,0xae]+list(range(0x1ce0,0x1ce6));assert all(body[j]==late[j] for j in fields),(tag,'script/music state',[(hex(j),body[j],late[j]) for j in fields if body[j]!=late[j]])
    assert all((body[0x1ca0+j]&63)==(late[0x1cc0+j]&63) for j in range(32));assert body[0x1d]==12 and body[0x1600:0x1b00]==hero_before[0x1600:0x1b00],(tag,'game/collision')
    graph=read_reference(source/f'{region}-actor-graphics-records.bin','tail');graphics_time=next(r['time'] for r in rows if r['pc']==0x18e1 and r['time']>start);g=next(graph[n:n+8208] for n in range(0,len(graph),8208) if struct.unpack_from('<Q',graph,n)[0]==graphics_time);allocation=struct.unpack_from('<I',g,8)[0];pixels=c.string_at(lib.room_ready_patterns(),16384);assert out[22]==allocation and pixels[0x2000:0x2000+allocation*32]==g[16:16+allocation*32];assert pixels[0x3800:0x3e00]==body[0x1600:0x1c00]
    cases.append(dict(phase=entry['phase'],refresh=entry['refresh'],body=list(before),expected=list(out),events=list(events[:out[7]*6]),points=list(points[:len(pcs)*19]),states=list(states[:len(pcs)*736]),after_body=list(body),patterns=list(pixels),hero_before=list(hb),hero_after=list(ha),dirty_tiles=list(c.string_at(lib.room_dirty_tiles(),64)),dirty_names=list(c.string_at(lib.room_dirty_names(),96)),dirty_palette=lib.room_dirty_palette(),dirty_sat=lib.room_dirty_sat()))
    results.append(dict(town=town,target=target,mask=mask,region=region,checkpoints=len(pcs),foreground_tstates=out[3],foreground_m1=out[4],irqs=out[7],music=body[0x65],exit_refresh=out[10]));print(results[-1],flush=True)
 assert len(cases)==24;(folder/'cases.json').write_bytes((json.dumps(cases,separators=(',',':'))+'\n').encode())
 report=dict(passed=True,cases=24,checkpoints=sum(r['checkpoints'] for r in results),rng_calls=72,rows=results,source_sha256=sha(original),playable_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},headers_sha256={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_vdp_dirty.h','source_room_contours.h','source_irq_video.h','source_room_reveal.h','source_room_ready.h','source_hero_initialize.h','source_room_memory.h','source_irq_context.h']},reference_manifest_sha256=sha((reference_manifest('tail')[0]/'manifest.json').read_bytes()),production_clock_wired=False,limits=['Single16D0 full RAM/R/phase input. No intermediate hero,collision,R,seed or music injection. Source331RAM/400audio/time/M1/R/IRQ offsets at checkpoints and hero475 entry/return bytes, script/music fields, actors/history/masks and enemy patterns checked.','Remaining full-body/mirror bytes are native output only. Six controlled class0 saved-bit0 exterior destinations. Fade return1FB6 and final2002 time/clock checked; every contour wait0B95/0BB3 has full phase/M1/R/RAM/audio and all IRQ offsets checked without resetting the clock; Native IRQ VRAM/SAT/CRAM delivery is bound; physical renderer/pacing, boot entry, other classes and campaign remain open.'])
 (ROOT/'analysis/native_room_contours_dirty_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())

if __name__=='__main__':main()

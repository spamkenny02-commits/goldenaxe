"""Native1853->18E1 from source entries, with live IRQ/audio and actual pattern bytes."""
import ctypes as c,json,os,subprocess,struct
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_native_room_load import records,read_reference,reference_manifest
from validate_native_room_finish import MODULES as FINISH_MODULES
MODULES=['source_actor_graphics',*FINISH_MODULES]
WRAPPER=r'''#include "source_actor_graphics.h"
typedef struct {u32 count,points;u32 *events,*snapshots;u8 *states;SourceIrqContext *irq;} Trace;
static void snapshot(const SourceClock *k,const SourceIrqContext *ctx,u32 *out)
{
 out[0]=k->raster;out[1]=k->until_vint;out[2]=k->elapsed;out[3]=k->foreground_tstates;out[4]=k->foreground_m1;
 out[5]=k->irq_tstates;out[6]=k->irq_m1;out[7]=k->irq_count;out[8]=k->refresh;out[9]=k->iff;out[10]=k->blocked;out[11]=k->pending;out[12]=k->first;out[13]=ctx->error;
}
static void trace(void *user,const SourceClockIrq *entry,const SourceClockWork *work)
{
 Trace *t=user;u32 *out;if(t->count>=64){t->count++;return;}out=t->events+t->count++*6;
 out[0]=entry->entry_elapsed;out[1]=entry->entry_raster;out[2]=entry->entry_refresh;out[3]=work->tstates;out[4]=work->fetches;out[5]=t->irq->last_irq.stages[SOURCE_IRQ_SAT64].tstates!=0;
}
static u8 point(void *user,u16 pc,const SourceClock *k,const SourceIrqContext *ctx)
{
 Trace *t=user;u16 n;u32 *out;u8 *s;if(t->points>=10)return 0;
 out=t->snapshots+t->points*15;s=t->states+t->points*736;snapshot(k,ctx,out);out[14]=pc;
 for(n=0;n<336;n++){s[n]=ctx->ram[n];}
 for(n=0;n<400;n++){s[336+n]=ctx->audio[n];}
 t->points++;return 1;
}
u8 actor_graphics_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *rom,
 u8 *actors,u8 *patterns,u8 *terrain,u8 *allocated,u32 *out,u32 *events,u32 *points,u8 *states)
{
 SourceClock k;SourceIrqContext ctx={0};Trace log={0};SourceActorGraphicsData data={actors,patterns,terrain,allocated};
 s32 raster=(s32)(phase[1]*3420)+(s32)(phase[0]-phase[2]);u32 period=phase[3]*3420;
 while(raster<0){raster+=period;}
 while((u32)raster>=period){raster-=period;}
 if(!source_clock_init(&k,phase[3],raster,refresh,phase[8],phase[9],phase[10]))return 0;
 ctx.ram=ram;ctx.audio=audio;ctx.low=rom;ctx.bank6=rom+0x18000;ctx.low_bytes=32768;ctx.input.lines=phase[3];ctx.input.reset_mask=16;ctx.trace=trace;ctx.trace_context=&log;log.irq=&ctx;
 log.events=events;log.snapshots=points;log.states=states;
 if(!source_actor_graphics(&k,&ctx,rom,&data,point,&log) || log.count>64)return 0;
 snapshot(&k,&ctx,out);out[14]=log.points;return 1;
}
'''

def main():
 folder=ROOT/'validation/native-actor-graphics';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'graphics.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 lib=c.CDLL(str(folder/'graphics.dll'));u8=c.POINTER(c.c_uint8);u32=c.POINTER(c.c_uint32);lib.actor_graphics_case.argtypes=[u32,c.c_uint8,*([u8]*7),u32,u32,u32,u8];lib.actor_graphics_case.restype=c.c_uint8
 original=(ROOT/'input/original.sms').read_bytes();arr=lambda b:(c.c_uint8*len(b)).from_buffer_copy(b);rom=arr(original);cases=[];results=[]
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_bytes())['routes']:
  for mask in [0,255]:
   source=ROOT/f'validation/actor-graphics-refresh/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    rows=records(source,region,'graphics');cycles=json.loads(read_reference(source/f'{region}-cycle-events.json','graphics'));start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target);entry=next(e for e in rows if e['pc']==0x1853 and e['time']>start);start=entry['time'];tag=(town,mask,region)
    ram=arr(entry['ram']);audio=arr(entry['audio']);actors=arr(entry['actors']);patterns=arr(bytes([0xa7])*16384);terrain=arr(bytes([0xa7])*1024);allocated=(c.c_uint8*1)(0xa7);out=(c.c_uint32*15)();events=(c.c_uint32*384)();points=(c.c_uint32*150)();states=(c.c_uint8*7360)()
    assert lib.actor_graphics_case((c.c_uint32*12)(*entry['phase']),entry['refresh'],ram,audio,rom,actors,patterns,terrain,allocated,out,events,points,states),(tag,'rejected')
    observed=[r for r in rows if r['time']>start and r['pc'] in [0x18ac,0x18af,0x18b7,0x18e1]];stop=next(i for i,r in enumerate(observed) if r['pc']==0x18e1);observed=observed[:stop+1];assert out[14]==len(observed)
    irq=json.loads(read_reference(source/f'{region}-audio-irq-events.json','graphics'))
    for n,end in enumerate(observed):
     p=list(points[n*15:(n+1)*15]);state=bytes(states[n*736:(n+1)*736]);phase=end['phase'];delta=((phase[0]-phase[2]+0x80000000)&0xffffffff)-0x80000000
     assert p[14]==end['pc'] and p[0]==(phase[1]*3420+delta)%(phase[3]*3420) and p[2]==end['time']-start,(tag,hex(end['pc']),'phase/time',p,end['time']-start)
     assert p[8]==end['refresh'] and p[4]+p[6]==end['m1']-entry['m1'],(tag,hex(end['pc']),'M1/R',p,end['refresh'],end['m1']-entry['m1'])
     assert state[336:]==end['audio'] and all(state[i]==end['ram'][i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,hex(end['pc']),'RAM/audio',[(i,a,b) for i,(a,b) in enumerate(zip(state[:336],end['ram'])) if a!=b])
     assert (p[9],p[11],p[12])==(phase[8],phase[10],1) and not p[10] and not p[13]
     assert [(events[j*6],bool(events[j*6+5])) for j in range(p[7])]==[(e[2]-start,bool(e[5])) for e in irq if e[1]==0x137 and start<e[2]<end['time']],(tag,'IRQ schedule')
    graph=read_reference(source/f'{region}-actor-graphics-records.bin','graphics');record=next(graph[n:n+8208] for n in range(0,len(graph),8208) if struct.unpack_from('<Q',graph,n)[0]==observed[-1]['time']);count=struct.unpack_from('<I',record,8)[0];assert allocated[0]==count and bytes(actors)==observed[-1]['actors']
    assert bytes(patterns[0x2000:0x2000+count*32])==record[16:16+count*32],(tag,'patterns')
    cases.append(dict(phase=entry['phase'],refresh=entry['refresh'],ram=list(entry['ram']),audio=list(entry['audio']),actors=list(entry['actors']),expected=list(out),events=list(events[:out[7]*6]),points=list(points[:out[14]*15]),states=list(states[:out[14]*736]),after_actors=list(actors),after_patterns=list(patterns),after_terrain=list(terrain),allocated=count))
    results.append(dict(town=town,mask=mask,region=region,checkpoints=out[14],pattern_bytes=count*32,foreground_tstates=out[3],foreground_m1=out[4],irqs=out[7],exit_refresh=out[8]));print(results[-1],flush=True)
 assert len(cases)==24
 (folder/'cases.json').write_bytes((json.dumps(cases,separators=(',',':'))+'\n').encode())
 report=dict(passed=True,cases=24,rows=results,source_sha256=sha(original),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},reference_manifest_sha256=sha((reference_manifest('graphics')[0]/'manifest.json').read_bytes()),production_clock_wired=False,limits=['Source1853 entry phase/R/RAM/audio/actors observed once per case; dynamic native IRQ/audio thereafter, source RAM331/audio400/time/R/M1/IRQ offsets and final actor/pattern bytes compare.','Six ordinary room lists with masks00/FF. Scratch terrain state is host output only; complete chain from16D0, other lists, physical VRAM/pacing and full campaign remain to verify.'])
 (ROOT/'analysis/native_actor_graphics_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())

if __name__=='__main__':main()

"""Exact source RAM deltas and instruction dates checked on native68000."""
import argparse,contextlib,io,json,os,re,struct,subprocess
from run_core import run
from validate_sprite_scene_timed import ROOT,sha
from validate_source_sprite_scene import vectors
MAIN=r'''
#include <genesis.h>
#include "source_sprite_scene_timed.h"
#include "offsets.h"
extern const u8 scene_inputs[][8192],scene_bank[16384],scene_trace_ntsc[],scene_trace_pal[];
static u8 ram[8192],saved[8192],expected[581];
typedef struct {const u8 *cursor;u32 count,index,elapsed,raster,period,irqs;} Compare;
volatile u32 gaw_checks,gaw_failures,gaw_points,gaw_irqs,gaw_failure_case,gaw_failure_point,gaw_failure_kind;
volatile u16 gaw_done;
static u16 little16(const u8 *p) {return p[0]|((u16)p[1]<<8);}
static u32 little32(const u8 *p) {return little16(p)|((u32)little16(p+2)<<16);}
static u8 fail(u16 kind) {if(!gaw_failures) {gaw_failure_point=gaw_points;gaw_failure_kind=kind;}gaw_failures++;return 0;}
static u8 trace(void *user,u16 pc,const SourceClock *clock,const u8 *bytes) {
 Compare *s=user;const u8 *p=s->cursor;u16 n,changes;
 if(s->index>=s->count) return fail(1);
 s->elapsed+=little16(p+2);s->raster+=little16(p+2);if(s->raster>=s->period) s->raster-=s->period;
 if(little16(p)!=pc) return fail(2);
 if(s->elapsed!=clock->elapsed || s->raster!=clock->raster) return fail(3);
 if(p[4]!=clock->refresh || p[5]!=clock->iff) return fail(4);
 changes=little16(p+6);p+=8;
 for(n=0;n<changes;n++,p+=3) {u16 index=little16(p);if(index>=581) return fail(5);expected[index]=p[2];}
 if(memcmp(bytes+0x24,expected,4) || bytes[0x303]!=expected[4] || memcmp(bytes+0x1100,expected+5,128) ||
    memcmp(bytes+0x1d40,expected+197,192) || memcmp(bytes+0x1f00,expected+389,192)) return fail(6);
 for(n=0;n<32;n++) if(memcmp(bytes+0x300+n*48+0x1b,expected+133+n*2,2)) return fail(7);
 s->cursor=p;s->index++;gaw_points++;return 1;
}
static u8 interrupt(void *user,const SourceClockIrq *entry,SourceClockWork *work) {
 Compare *s=user;(void)entry;memcpy(ram+0x1f00,ram+0x1d40,192);s->irqs++;work->tstates=4179;work->fetches=398;return 1;
}
int main(bool reset) {
 u16 row,region=SYS_isPAL()?1:0,lines=region?313:262;const u8 *all=region?scene_trace_pal:scene_trace_ntsc,*header;
 SourceClock clock;SourceSpriteSceneOutput result;Compare state;u32 final_time,final_raster,final_until;u8 final_refresh,final_iff,final_pending;(void)reset;
 SYS_disableInts();VDP_setEnable(FALSE);
 for(row=0;row<SCENE_CASES && !gaw_failures;row++) {
  header=all+trace_offsets[region][row];gaw_failure_case=row;
  memcpy(ram,scene_inputs[row],8192);memcpy(expected,header+32,581);memcpy(ram+0x1f00,expected+389,192);
  state.cursor=header+613;state.count=little32(header);state.index=state.elapsed=state.irqs=0;state.raster=little32(header+4);state.period=(u32)lines*3420;
  if(!source_clock_init(&clock,lines,state.raster,header[8],header[9],0,0) ||
     !source_sprite_scene_timed(&clock,ram,scene_bank,&result,interrupt,&state,trace,&state) ||
     !trace(&state,65535,&clock,ram) || state.index!=state.count) {if(!gaw_failures) fail(8);break;}
  final_time=clock.elapsed;
  if(clock.foreground_tstates!=little32(header+12) || clock.foreground_m1!=little32(header+16) ||
     state.irqs!=little32(header+20) || final_time!=little32(header+24) || result.count!=little32(header+28)) {fail(9);break;}
  gaw_irqs+=state.irqs;memcpy(saved,ram,8192);final_raster=clock.raster;final_until=clock.until_vint;
  final_refresh=clock.refresh;final_iff=clock.iff;final_pending=clock.pending;
  /* Trace hooks must not change source work or the interrupt-visible table. */
  memcpy(ram,scene_inputs[row],8192);memcpy(ram+0x1f00,header+32+389,192);state.irqs=0;
  if(!source_clock_init(&clock,lines,little32(header+4),header[8],header[9],0,0) ||
     !source_sprite_scene_timed(&clock,ram,scene_bank,&result,interrupt,&state,0,0) ||
     memcmp(ram,saved,8192) || clock.elapsed!=final_time || state.irqs!=little32(header+20) ||
     clock.foreground_tstates!=little32(header+12) || clock.foreground_m1!=little32(header+16) ||
     clock.raster!=final_raster || clock.until_vint!=final_until || clock.refresh!=final_refresh ||
     clock.iff!=final_iff || clock.pending!=final_pending) {fail(10);break;}
  gaw_checks++;
 }
 gaw_done=1;while(TRUE) __asm__ volatile("nop");return 0;
}
'''
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--interrupts',action='store_true');args=parser.parse_args();suffix='-irq' if args.interrupts else ''
 rom,rows=vectors();source=ROOT/('validation/sprite-scene-timed'+suffix);folder=ROOT/('validation/sprite-scene-timed'+suffix+'-68k');src=folder/'src';src.mkdir(parents=True,exist_ok=True)
 parent=ROOT/('analysis/sprite_scene_timed'+suffix.replace('-','_')+'_report.json');previous=json.loads(parent.read_bytes());offsets=[];totals={}
 for region in ['ntsc','pal']:
  raw=(source/(region+'-records.bin')).read_bytes();assert sha(raw)==next(x['records_sha256'] for x in previous['results'] if x['region']==region);pos=0;packed=bytearray();places=[];points=irqs=0
  for index in range(len(rows)):
   tag,size=struct.unpack_from('<II',raw,pos);pos+=8;assert tag==index;events=raw[pos:pos+size];pos+=size;count=size//608;times=[struct.unpack_from('<I',events,n*608+4)[0] for n in range(count)]
   deltas=[0]+[(b-a)&0xffffffff for a,b in zip(times,times[1:])];assert max(deltas)<65536
   irq=sum(x>=4179*15 for x in deltas);instructions=[struct.unpack_from('<I',events,n*608)[0] for n in range(count-1)];m1=sum(2 if rom[pc] in [0xcb,0xdd,0xed,0xfd] else 1 for pc in instructions)
   elapsed=(times[-1]-times[0])&0xffffffff;assert not (elapsed-irq*4179*15)%15;tstates=(elapsed-irq*4179*15)//15
   raster,refresh,iff=struct.unpack_from('<III',events,8);final=events[(count-1)*608+24:count*608];sprites=int.from_bytes(final[:2],'little')-0xdd40
   places.append(len(packed));packed.extend(struct.pack('<IIBB2xIIIII',count,raster,refresh,iff,tstates,m1,irq,elapsed,sprites));initial=events[24:24+581];packed.extend(initial);before=initial
   for n,delta in enumerate(deltas):
    point=events[n*608:(n+1)*608];pc,_,_,r,f,_=struct.unpack_from('<6I',point);now=point[24:24+581];changes=[(k,v) for k,(u,v) in enumerate(zip(before,now)) if u!=v]
    packed.extend(struct.pack('<HHBBH',pc,delta,r,f,len(changes)))
    for k,v in changes:packed.extend(struct.pack('<HB',k,v))
    before=now
   points+=count;irqs+=irq
  assert pos==len(raw);(src/(region+'.bin')).write_bytes(packed);offsets.append(places);totals[region]=dict(points=points,irqs=irqs,packed_bytes=len(packed))
 (src/'inputs.bin').write_bytes(b''.join(raw for _,raw in rows));(src/'bank.bin').write_bytes(rom[0x30000:0x34000]);asm='.section .rodata\n.align 2\n'
 for name,file in [('inputs','inputs'),('bank','bank'),('trace_ntsc','ntsc'),('trace_pal','pal')]:asm+='.global scene_'+name+'\nscene_'+name+':\n.incbin "src/'+file+'.bin"\n.align 2\n'
 (src/'assets.s').write_bytes(asm.encode());(src/'offsets.h').write_text('#define SCENE_CASES '+str(len(rows))+'\nstatic const u32 trace_offsets[2][SCENE_CASES]={'+','.join('{'+','.join(map(str,o))+'}' for o in offsets)+'};\n');(src/'main.c').write_bytes(MAIN.encode())
 for name in ['source_sprite_scene_timed','source_clock','source_rng']:(src/(name+'.c')).write_text('#include "../../../megadrive/src/'+name+'.c"\n')
 (src/'source_sprite_scene_timed.h').write_text('#include "../../../megadrive/src/source_sprite_scene_timed.h"\n')
 sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];temp=folder/'compiler-tmp';temp.mkdir(exist_ok=True)
 for key in ['TMPDIR','TMP','TEMP']:env[key]=temp.as_posix()
 path=sdk.as_posix();unix='/'+path[0].lower()+path[2:];built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
 kernel=folder/'out/release/rom.bin';symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match('([0-9a-fA-F]+) [a-zA-Z] (.+)',line))};results=[]
 for region in ['ntsc','pal']:
  observed={}
  def observe(frame,ram):
   def value(name,width):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+n)&65535)^1] for n in range(width)),'big')
   observed.update(frame=frame,done=value('gaw_done',2))
   for name in ['checks','failures','points','irqs','failure_case','failure_point','failure_kind']:observed[name]=value('gaw_'+name,4)
  with contextlib.redirect_stdout(io.StringIO()):run(kernel,60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,stop_when=lambda:bool(observed.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert observed['done'] and observed['checks']==len(rows) and not observed['failures'] and observed['points']==totals[region]['points'] and observed['irqs']==totals[region]['irqs'],observed
  results.append(dict(region=region,**observed,**{'packed_bytes':totals[region]['packed_bytes']}));print(results[-1],flush=True)
 report=dict(kernel_sha256=sha(kernel.read_bytes()),kernel_bytes=kernel.stat().st_size,source_report_sha256=sha(parent.read_bytes()),interrupts=args.interrupts,sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_sprite_scene_timed.c','source_sprite_scene_timed.h','source_clock.c','source_clock.h','source_rng.c','source_rng.h','source_sprite_scene.h']},results=results,limits=['Actual68000 compares source instruction PC/time/R/IFF/raster and581 exact RAM bytes through lossless state deltas, not hashes. Refresh/M1 and foreground time derive from original opcode bytes/dates. Custom snapshot ISR only; original full game IRQ/video publication remains unproved. Both trace and no-trace native paths agree on complete8192-byte final RAM, work and interrupt count. No full-game/render deadline claim.'])
 (ROOT/('analysis/sprite_scene_timed'+suffix.replace('-','_')+'_68k_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

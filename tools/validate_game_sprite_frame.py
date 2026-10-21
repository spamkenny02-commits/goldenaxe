"""Original0938 ->0B95 full IRQ/SAT/PSG vs native shared-RAM frame."""
import contextlib,ctypes as c,io,json,os,struct,subprocess
from game_sprite_frame_fixture import ROOT,generate,unpack_body
from run_core import run
from validate_sprite_scene_timed import sha
from validate_native_audio_reader import MODULES as AUDIO
MODULES=['source_game_irq','source_game_frame','source_sprite_scene_timed','source_clock','source_rng','source_irq','source_irq_master_context','source_audio_reader_master','source_audio_prefix_timed','source_audio_fast_timed',*AUDIO]
WRAPPER=r'''
#include "source_game_irq.h"
typedef struct {const u8 *points,*psg,*sat,*statuses;u32 points_count,psg_count,sat_count,point,psg_at,sat_at,status_at,status_count,origin;u32 *out;SourceGameIrqContext *irq;} Compare;
static u32 little(const u8 *p) {return p[0]|((u32)p[1]<<8)|((u32)p[2]<<16)|((u32)p[3]<<24);}
static u8 check_port(Compare *s,const u8 *base,u32 count,u32 *at,u32 time,u8 value,u16 kind) {
 const u8 *p;s->out[0]=kind;s->out[1]=*at;
 if(*at>=count) {s->out[2]=1;return 0;}
 p=base+*at*20;
 if(little(p+4)-s->origin!=time || little(p+8)!=value) {s->out[2]=2;s->out[3]=little(p+4)-s->origin;s->out[4]=time;s->out[5]=little(p+8);s->out[6]=value;return 0;}
 (*at)++;return 1;
}
static u8 status(void *user,const SourceClockIrq *entry,u8 *value) {
 Compare *s=user;const u8 *p;s->out[0]=4;s->out[1]=s->status_at;
 if(s->status_at>=s->status_count) {s->out[2]=1;return 0;}
 p=s->statuses+960*s->status_at;
 if(little(p+4)-s->origin!=entry->entry_elapsed || little(p+8)!=entry->entry_raster || little(p+12)!=entry->entry_refresh) {s->out[2]=3;s->out[3]=little(p+4)-s->origin;s->out[4]=entry->entry_elapsed;s->out[5]=little(p+12);s->out[6]=entry->entry_refresh;return 0;}
 *value=p[28+27];s->status_at++;return 1;
}
static void audio(void *user,const u8 *writes,const u32 *dates,u16 count) {
 Compare *s=user;u16 n;for(n=0;n<count;n++) if(!check_port(s,s->psg,s->psg_count,&s->psg_at,dates[n],writes[n],1)) return;
}
static u8 video(void *user,const SourceGameSatPacket *packet) {
 Compare *s=user;u16 n;for(n=0;n<192;n++) if(!check_port(s,s->sat,s->sat_count,&s->sat_at,(n<64?packet->first_y+(u32)n*240:packet->first_xy+(u32)(n-64)*240),packet->bytes[n],2)) return 0;return 1;
}
static u8 point(void *user,u16 pc,const SourceClock *clock,const u8 *ram) {
 Compare *s=user;const u8 *p;u8 bytes[930];u16 n,k=0;s->out[0]=3;s->out[1]=s->point;
 if(s->point>=s->points_count) {s->out[2]=1;return 0;}
 p=s->points+s->point*960;
 if(little(p)!=pc || little(p+4)-s->origin!=clock->elapsed || little(p+8)!=clock->raster || little(p+12)!=clock->refresh || little(p+16)!=clock->iff) {s->out[2]=3;s->out[3]=little(p);s->out[4]=pc;s->out[5]=little(p+4)-s->origin;s->out[6]=clock->elapsed;s->out[14]=little(p+12);s->out[15]=clock->refresh;return 0;}
 for(n=0;n<80;n++) bytes[k++]=ram[n];
 bytes[k++]=ram[0x303];for(n=0;n<128;n++) bytes[k++]=ram[0x1100+n];
 for(n=0;n<32;n++) {bytes[k++]=ram[0x300+n*48+0x1b];bytes[k++]=ram[0x300+n*48+0x1c];}
 for(n=0;n<256;n++) bytes[k++]=ram[0x1d00+n];
 for(n=0;n<400;n++) bytes[k++]=ram[0x1e00+n];
 bytes[k++]=ram[0x1fff];
 for(n=0;n<930;n++) if(bytes[n]!=p[28+n]) {s->out[2]=4;s->out[3]=n;s->out[4]=p[28+n];s->out[5]=bytes[n];return 0;}
 s->point++;return 1;
}
u8 game_frame_case(u8 *ram,const u8 *low,const u8 *bank6,const u8 *bank12,u16 lines,const u8 *points,u32 count,
 const u8 *psg,u32 psg_count,const u8 *sat,u32 sat_count,const u8 *statuses,u32 status_count,u8 traced,u32 *out) {
 SourceClock clock;SourceGameIrqContext ctx={0};SourceSpriteSceneOutput scene;SourceWaitOutput wait;Compare state;u16 n;
 for(n=0;n<32;n++) out[n]=0;
 state.points=points;state.points_count=count;state.psg=psg;state.psg_count=psg_count;state.sat=sat;state.sat_count=sat_count;
 state.statuses=statuses;state.status_count=status_count;state.status_at=0;
 state.point=state.psg_at=state.sat_at=0;state.origin=little(points+4);state.out=out;state.irq=&ctx;
 ctx.timed.core.low=low;ctx.timed.core.low_bytes=32768;ctx.timed.core.bank6=bank6;ctx.timed.core.input.lines=lines;ctx.timed.core.input.reset_mask=16;
 ctx.status_read=status;ctx.status_context=&state;ctx.timed.sink=audio;ctx.timed.sink_context=&state;ctx.video=video;ctx.video_context=&state;
 if(!source_game_irq_bind(&ctx,ram) || !source_clock_init(&clock,lines,little(points+8),little(points+12),little(points+16),0,0)) return 0;
 if(!source_game_sprite_frame(&clock,&ctx,bank12,&scene,&wait,traced?point:0,&state)) {out[7]=ctx.error;out[8]=ctx.timed.core.error;return 0;}
 if(!traced) {state.point=count-1;if(!point(&state,65535,&clock,ram)) return 0;}
 if(out[2] || state.point!=count || state.psg_at!=psg_count || state.sat_at!=sat_count || state.status_at!=status_count) return 0;
 out[9]=clock.irq_count;out[10]=sat_count/192;out[11]=psg_count;out[12]=scene.count;out[13]=wait.taken;out[14]=clock.elapsed;out[15]=clock.raster;
 out[16]=clock.refresh;out[17]=clock.iff;out[18]=clock.pending;out[19]=clock.until_vint;
 out[20]=clock.foreground_tstates;out[21]=clock.foreground_m1;out[22]=clock.irq_tstates;out[23]=clock.irq_m1;
 out[24]=clock.blocked;out[25]=clock.first;out[26]=clock.status_suppressions;out[27]=clock.vector_coalescences;return 1;
}

static u8 reject_status(void *user,const SourceClockIrq *entry,u8 *value) {(void)user;(void)entry;(void)value;return 0;}
static u8 reject_video(void *user,const SourceGameSatPacket *packet) {u8 *ram=user;ram[0x1d40]^=255;return packet->bytes[0]==ram[0x1d40];}
u8 game_frame_contracts(const u8 *low,const u8 *bank6,u16 lines) {
 static u8 bytes[8192];SourceGameIrqContext ctx={0};SourceClockWork work={99,99};SourceClockIrq entry={0,0,0};u16 n;
 for(n=0;n<8192;n++) bytes[n]=0;
 ctx.timed.core.low=low;ctx.timed.core.low_bytes=32768;ctx.timed.core.bank6=bank6;ctx.timed.core.input.lines=lines;
 if(!source_game_irq_bind(&ctx,bytes)) return 0;
 ctx.vdp_status=31;bytes[0x1b]=17;
 if(source_game_irq_interrupt(&ctx,&entry,&work) || ctx.error!=SOURCE_GAME_IRQ_STATUS || bytes[0x1b]!=17 || work.tstates || work.fetches) return 0;
 if(source_game_irq_interrupt(&ctx,&entry,&work) || bytes[0x1b]!=17) return 0;
 if(!source_game_irq_bind(&ctx,bytes)) return 0;
 ctx.vdp_status=159;ctx.status_read=reject_status;
 if(source_game_irq_interrupt(&ctx,&entry,&work) || ctx.error!=SOURCE_GAME_IRQ_STATUS || bytes[0x1b]!=17) return 0;
 if(!source_game_irq_bind(&ctx,bytes)) return 0;
 ctx.status_read=0;bytes[0x2e]=1;ctx.producer_active=1;
 if(source_game_irq_interrupt(&ctx,&entry,&work) || ctx.error!=SOURCE_GAME_IRQ_UNSAFE || bytes[0x1b]!=17) return 0;
 if(!source_game_irq_bind(&ctx,bytes)) return 0;
 ctx.video=reject_video;ctx.video_context=bytes;bytes[0x1d40]=42;
 if(source_game_irq_interrupt(&ctx,&entry,&work) || ctx.error!=SOURCE_GAME_IRQ_VIDEO || bytes[0x1b]!=159 ||
    ctx.sat.bytes[0]!=42 || bytes[0x1d40]!=213 || work.tstates || work.fetches) return 0;
 return 1;
}

'''

def source_dependencies():
 import re
 folder=ROOT/'megadrive/src';pending=[n+'.c' for n in MODULES];result={}
 while pending:
  name=pending.pop()
  if name in result:continue
  b=(folder/name).read_bytes();result[name]=sha(b)
  pending.extend(n for n in re.findall(r'#include "([^"/]+)"',b.decode()) if (folder/n).exists())
 return dict(sorted(result.items()))

def main():
 folder=ROOT/'validation/game-sprite-frame';folder.mkdir(parents=True,exist_ok=True);image,rows,labels=generate();path=folder/'source-fixture.sms';path.write_bytes(image)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_game_sprite_frame_libretro.dll';dll=c.CDLL(str(core));dll.gaw_frame_reset.argtypes=[c.c_uint]
 for name in ['gaw_frame_count','gaw_frame_errors','gaw_frame_port_count']:getattr(dll,name).restype=c.c_uint
 for name in ['gaw_frame_data','gaw_frame_port_data']:getattr(dll,name).restype=c.c_void_p
 captures={};results=[]
 for region in ['ntsc','pal']:
  dll.gaw_frame_reset(0);points={n:bytearray() for n in range(len(rows))};ports={n:bytearray() for n in range(len(rows))}
  def observe(frame,ram):
   assert not dll.gaw_frame_errors();size=dll.gaw_frame_count();raw=c.string_at(dll.gaw_frame_data(),size*960)
   for pos in range(0,len(raw),960):tag=struct.unpack_from('<I',raw,pos+20)[0];assert tag<len(rows);points[tag].extend(raw[pos:pos+960])
   size=dll.gaw_frame_port_count();raw=c.string_at(dll.gaw_frame_port_data(),size*20)
   for pos in range(0,len(raw),20):tag=struct.unpack_from('<I',raw,pos+16)[0];assert tag<len(rows);ports[tag].extend(raw[pos:pos+20])
   dll.gaw_frame_reset(1)
  with contextlib.redirect_stdout(io.StringIO()):run(path,len(rows)*12+50,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  packed=bytearray();portbytes=bytearray()
  for n in range(len(rows)):
   pcs=[struct.unpack_from('<I',points[n],p)[0] for p in range(0,len(points[n]),960)];assert pcs[0]==0x938 and pcs[-1]==65535 and pcs.count(0xb95)==pcs.count(0xbb3)==1,(region,n,pcs)
   packed.extend(struct.pack('<II',n,len(points[n]))+points[n]);portbytes.extend(struct.pack('<II',n,len(ports[n]))+ports[n])
  (folder/(region+'-points.bin')).write_bytes(packed);(folder/(region+'-ports.bin')).write_bytes(portbytes);captures[region]=(points,ports)
  print(region,'source frame captures',len(rows),flush=True)
 sdk=ROOT.parents[1]/'work/sgdk';(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 modules=list(dict.fromkeys(MODULES));cmd=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]+[str(ROOT/'megadrive/src'/(n+'.c')) for n in modules]+['-o',str(folder/'frame.dll')]
 built=subprocess.run(cmd,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
 native=c.CDLL(str(folder/'frame.dll'));fn=native.game_frame_case;p8=c.POINTER(c.c_uint8);fn.argtypes=[p8,p8,p8,p8,c.c_uint16,p8,c.c_uint32,p8,c.c_uint32,p8,c.c_uint32,p8,c.c_uint32,c.c_uint8,c.POINTER(c.c_uint32)];fn.restype=c.c_uint8
 contract=native.game_frame_contracts;contract.argtypes=[p8,p8,c.c_uint16];contract.restype=c.c_uint8
 low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank6=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);bank12=(c.c_uint8*16384).from_buffer_copy(image[0x30000:0x34000]);checks=[]
 for region in ['ntsc','pal']:
  assert contract(low,bank6,262 if region=='ntsc' else 313),('contract',region)
  points,ports=captures[region]
  for index,(name,raw) in enumerate(rows):
   all_points=points[index];selected=b''.join(all_points[p:p+960] for p in range(0,len(all_points),960) if struct.unpack_from('<I',all_points,p)[0]!=0x137);p=selected[:960];seed=bytearray(raw)
   for address,value in unpack_body(p[28:28+930]):seed[address:address+len(value)]=value
   status_bytes=b''.join(all_points[p:p+960] for p in range(0,len(all_points),960) if struct.unpack_from('<I',all_points,p)[0]==0x137)
   statuses=(c.c_uint8*len(status_bytes)).from_buffer_copy(status_bytes)
   streams=[b''.join(ports[index][j:j+20] for j in range(0,len(ports[index]),20) if struct.unpack_from('<I',ports[index],j)[0]==kind) for kind in [1,2]]
   ram=(c.c_uint8*8192).from_buffer_copy(seed);out=(c.c_uint32*32)();pp=(c.c_uint8*len(selected)).from_buffer_copy(selected);psg=(c.c_uint8*len(streams[0])).from_buffer_copy(streams[0]);sat=(c.c_uint8*len(streams[1])).from_buffer_copy(streams[1])
   assert fn(ram,low,bank6,bank12,262 if region=='ntsc' else 313,pp,len(selected)//960,psg,len(streams[0])//20,sat,len(streams[1])//20,statuses,len(status_bytes)//960,1,out),(region,index,name,list(out))
   untraced=(c.c_uint8*8192).from_buffer_copy(seed);second=(c.c_uint32*32)()
   assert fn(untraced,low,bank6,bank12,262 if region=='ntsc' else 313,pp,len(selected)//960,psg,len(streams[0])//20,sat,len(streams[1])//20,statuses,len(status_bytes)//960,0,second),(region,index,'no-trace',list(second))
   assert bytes(untraced)==bytes(ram) and list(second)[9:]==list(out)[9:],(region,index,'trace-dependent')
   checks.append(dict(region=region,case=index,name=name,irq_count=out[9],full_irqs=out[10],psg_bytes=out[11],sprites=out[12],wait_taken=out[13]))
  results.append(dict(region=region,cases=len(rows),points_sha256=sha((folder/(region+'-points.bin')).read_bytes()),ports_sha256=sha((folder/(region+'-ports.bin')).read_bytes())));print(region,len(rows),'native full sprite/wait/IRQ frames exact',flush=True)
 report=dict(source_rom_sha256=sha((ROOT/'input/original.sms').read_bytes()),fixture_sha256=sha(image),observer_core_sha256=sha(core.read_bytes()),sources=source_dependencies(),results=results,cases=checks,contract_checks_per_region=5,trace_disabled_full_ram_clock_agree=True,limits=['Original0938,0B95,IRQ vector/body,bank4 SAT routines andbank6 audio unchanged. RAM caller/input fixtures, display disabled, VDPstatus supplied from each observed IRQ (hardware input, not predicted)/joy0/reset16.930-byte state at sprite entry,wait entry,restore entry and caller; PC/master/raster/R/IFF, all192 full-IRQ SAT OUTI values/dates and every PSG byte/date compare exactly. This is native host composition;68000/hardware renderer delivery/deadlines/fullgame still require proof. Initial source entry state supplied, not boot predicted.'])
 (ROOT/'analysis/game_sprite_frame_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

"""Original instruction stream vs dedicated native0938 translation, byte exact."""
import argparse,contextlib,ctypes as c,gzip,hashlib,io,json,os,struct,subprocess
from pathlib import Path
from run_core import run
from validate_source_sprite_scene import ROOT,vectors,fixture
def sha(b):return hashlib.sha256(b).hexdigest()
WRAPPER=r'''
#include "source_sprite_scene_timed.h"
typedef struct {const u8 *events;u32 count,index,origin;u32 *out;u8 *ram;u16 irqs;} Compare;
static u32 little(const u8 *p) {return p[0]|((u32)p[1]<<8)|((u32)p[2]<<16)|((u32)p[3]<<24);}
static u8 compare(void *user,u16 pc,const SourceClock *clock,const u8 *ram) {
 Compare *c=(Compare*)user;const u8 *p;u8 bytes[584];u16 n,k=0;
 c->out[0]=c->index;c->out[3]=pc;
 if(c->index>=c->count) {c->out[1]=1;return 0;}
 p=c->events+c->index*608;c->out[2]=little(p);
 if(little(p)!=pc) {c->out[1]=2;return 0;}
 if(little(p+4)-c->origin!=clock->elapsed) {c->out[1]=3;c->out[4]=little(p+4)-c->origin;c->out[5]=clock->elapsed;return 0;}
 if(little(p+8)!=clock->raster) {c->out[1]=7;c->out[4]=little(p+8);c->out[5]=clock->raster;return 0;}
 if(little(p+12)!=clock->refresh) {c->out[1]=4;c->out[4]=little(p+12);c->out[5]=clock->refresh;return 0;}
 if(little(p+16)!=clock->iff) {c->out[1]=5;return 0;}
 for(n=0;n<4;n++) bytes[k++]=ram[0x24+n];
 bytes[k++]=ram[0x303];
 for(n=0;n<128;n++) bytes[k++]=ram[0x1100+n];
 for(n=0;n<32;n++) {bytes[k++]=ram[0x300+n*48+0x1b];bytes[k++]=ram[0x300+n*48+0x1c];}
 for(n=0;n<192;n++) bytes[k++]=ram[0x1d40+n];
 for(n=0;n<192;n++) bytes[k++]=ram[0x1f00+n];
 for(n=0;n<581;n++) if(bytes[n]!=p[24+n]) {c->out[1]=6;c->out[4]=n;c->out[5]=((u16)p[24+n]<<8)|bytes[n];return 0;}
 c->index++;return 1;
}
static u8 snapshot_irq(void *user,const SourceClockIrq *entry,SourceClockWork *work) {
 Compare *c=(Compare*)user;u16 n;(void)entry;
 for(n=0;n<192;n++) c->ram[0x1f00+n]=c->ram[0x1d40+n];
 c->irqs++;work->tstates=4179;work->fetches=398;return 1;
}
u8 timed_scene_case(u8 *ram,const u8 *bank,const u8 *events,u32 count,u16 lines,u32 *out) {
 SourceClock clock;SourceSpriteSceneOutput result;Compare state;u16 n;
 for(n=0;n<10;n++) out[n]=0;
 state.events=events;state.count=count;state.index=0;state.origin=little(events+4);state.out=out;state.ram=ram;state.irqs=0;
 for(n=0;n<192;n++) ram[0x1f00+n]=events[24+389+n];
 if(!source_clock_init(&clock,lines,little(events+8),little(events+12),little(events+16),0,0)) return 0;
 if(!source_sprite_scene_timed(&clock,ram,bank,&result,snapshot_irq,&state,compare,&state)) return 0;
 if(!compare(&state,65535,&clock,ram) || state.index!=count) return 0;
 out[6]=clock.foreground_tstates;out[7]=clock.foreground_m1;out[8]=result.count;out[9]=state.index;out[1]=state.irqs;return 1;
}
'''
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--interrupts',action='store_true');args=parser.parse_args();suffix='-irq' if args.interrupts else ''
 folder=ROOT/('validation/sprite-scene-timed'+suffix);folder.mkdir(parents=True,exist_ok=True);rom,rows=vectors();image=fixture(rom,rows,case_before=True,interrupts=args.interrupts);path=folder/'source-fixture.sms';path.write_bytes(image)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_spritescene_libretro.dll';dll=c.CDLL(str(core));dll.gaw_sprite_reset.argtypes=[c.c_uint];dll.gaw_sprite_count.restype=dll.gaw_sprite_errors.restype=c.c_uint;dll.gaw_sprite_data.restype=c.c_void_p
 captures={};regions=[]
 for region in ['ntsc','pal']:
  dll.gaw_sprite_reset(0);records={n:bytearray() for n in range(len(rows))}
  def observe(frame,ram):
   assert not dll.gaw_sprite_errors();size=dll.gaw_sprite_count();raw=c.string_at(dll.gaw_sprite_data(),size*608);dll.gaw_sprite_reset(1)
   for pos in range(0,len(raw),608):
    tag=struct.unpack_from('<I',raw,pos+20)[0];assert tag<len(rows),tag;records[tag].extend(raw[pos:pos+608])
  with contextlib.redirect_stdout(io.StringIO()):run(path,len(rows)*8+25,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  packed=bytearray()
  for n,raw in records.items():
   assert struct.unpack_from('<I',raw)[0]==0x938 and struct.unpack_from('<I',raw,len(raw)-608)[0]==65535
   packed.extend(struct.pack('<II',n,len(raw))+raw)
  (folder/(region+'-records.bin')).write_bytes(packed);captures[region]=records;regions.append(dict(region=region,instructions=sum(len(b)//608-1 for b in records.values()),records_sha256=sha(packed)))
 sdk=ROOT.parents[1]/'work/sgdk';(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 modules=['source_sprite_scene_timed','source_clock','source_rng'];compiler_args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]+[str(ROOT/'megadrive/src'/(n+'.c')) for n in modules]+['-o',str(folder/'timed.dll')]
 built=subprocess.run(compiler_args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
 native=c.CDLL(str(folder/'timed.dll'));fn=native.timed_scene_case;p8=c.POINTER(c.c_uint8);fn.argtypes=[p8,p8,p8,c.c_uint32,c.c_uint16,c.POINTER(c.c_uint32)];fn.restype=c.c_uint8
 bank=(c.c_uint8*16384).from_buffer_copy(rom[0x30000:0x34000]);checks=[]
 for region in ['ntsc','pal']:
  for index,(name,seed) in enumerate(rows):
   raw=captures[region][index];ram=(c.c_uint8*8192).from_buffer_copy(seed);events=(c.c_uint8*len(raw)).from_buffer_copy(raw);out=(c.c_uint32*10)()
   assert fn(ram,bank,events,len(raw)//608,262 if region=='ntsc' else 313,out),(region,index,name,list(out))
   checks.append(dict(region=region,case=index,name=name,instructions=out[9]-1,tstates=out[6],m1=out[7],sprites=out[8],irq_count=out[1]))
  print(region,len(rows),'instruction/R/RAM traces exact',flush=True)
 report=dict(source_rom_sha256=sha(rom),fixture_sha256=sha(image),observer_core_sha256=sha(core.read_bytes()),observer_build_sha256=sha((ROOT/'validation/sprite-scene-observer/build.json').read_bytes()),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in [*(x+'.c' for x in modules),'source_sprite_scene_timed.h','source_sprite_scene.h','source_clock.h','source_rng.h']},results=regions,cases=checks,limits=['Original0938..0AA3 and bank12 unchanged, test caller/boot/vector/inputs. Every instruction-start PC, relative master time, physical raster, refresh R, IFF and581 RAM bytes compare exactly; end includes RET. Stack writes/foreground register values not compared. Source fixtures run DI; physical IRQ chronology is not covered by these captures. Native generic callback boundaries still require interrupt-enabled source verification. No renderer/frame-deadline/full-game claim.'])
 if args.interrupts:
  assert sum(x['irq_count'] for x in checks)>20
  report['limits']=['Original0938..0AA3 and bank12 unchanged. Custom snapshot IRQ saves registers, acknowledges VDP at35T, copies192 current SAT bytes to DF00, restores registers/EI/RET:4179T/398M1 including accept. Native callback reproduces its RAM/work. Every foreground instruction PC/master/raster/R/IFF and581 RAM bytes compare exactly, including partial SAT snapshots across IRQs. This verifies callback timing with a controlled ISR; original full game IRQ/SAT-to-VDP publication/audio and source reveal deadlines remain unproved. Stack/foreground register values are not compared.']
 report['interrupts']=args.interrupts
 (ROOT/('analysis/sprite_scene_timed'+suffix.replace('-','_')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

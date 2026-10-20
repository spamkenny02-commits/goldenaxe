"""Native state-order, retention and pre-beam rejection checks for the scene stream."""
import argparse,contextlib,ctypes as c,hashlib,io,json,os,re,subprocess
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
MAIN=r'''
#include <genesis.h>
#include "../../../megadrive/src/md_z80_video_span.c"
#include "../../../megadrive/src/source_class0_video.c"
#include "../../../megadrive/src/md_class0_video_stream.c"
static MdClass0VideoStream scene,saved;
static MdZ80PsgMailbox mailbox;
static u8 source[1536],upper[16];
volatile u32 gaw_checks,gaw_failures;volatile u16 gaw_done;
static void check(u16 ok) {gaw_checks++;if(!ok) gaw_failures++;}
static u16 same(void) {return memcmp(&scene,&saved,sizeof(scene))==0;}
int main(bool reset) {
 (void)reset;SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 *(volatile u16*)0xc00010=0x34;
 check(md_class0_video_stream_begin(0,1)==MD_Z80_PSG_INVALID);
 saved=scene;check(md_class0_video_stream_map(&scene,source)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_palette(&scene,upper)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_step(0,&mailbox)==MD_Z80_PSG_INVALID);
 check(md_class0_video_stream_step(&scene,0)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_begin(&scene,1)==MD_Z80_PSG_OK && scene.ready==1 && !scene.done);
 saved=scene;check(md_class0_video_stream_begin(&scene,1)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_map(0,source)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_map(&scene,0)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_map(&scene,source+1)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_palette(&scene,upper)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_step(&scene,&mailbox)==MD_Z80_PSG_WAIT && same());
 mailbox.stamp.ready=1;check(md_class0_video_stream_step(&scene,&mailbox)==MD_Z80_PSG_INVALID && same());
 mailbox.stamp.ready=3;check(md_class0_video_stream_step(&scene,&mailbox)==MD_Z80_PSG_WAIT && scene.kind==1 && scene.job.ready==0xd600);
 saved=scene;check(md_class0_video_stream_step(&scene,&mailbox)==MD_Z80_PSG_WAIT && same());
 check(md_class0_video_stream_map(&scene,source)==MD_Z80_PSG_OK && scene.ready==3 && scene.job.ready==saved.job.ready && scene.payload[0]==saved.payload[0]);
 check(scene.map[0]==16 && scene.map[767]==16);
 source[0]=1;check(scene.map[0]==16);
 saved=scene;check(md_class0_video_stream_map(&scene,source)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_palette(0,upper)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_palette(&scene,0)==MD_Z80_PSG_INVALID && same());
 check(md_class0_video_stream_palette(&scene,upper)==MD_Z80_PSG_OK && scene.ready==7 && scene.palette[16]==0);
 upper[0]=63;check(scene.palette[16]==0);
 saved=scene;check(md_class0_video_stream_palette(&scene,upper)==MD_Z80_PSG_INVALID && same());
 mailbox.stamp.error=1;check(md_class0_video_stream_step(&scene,&mailbox)==MD_Z80_PSG_FAULT && scene.error);
 mailbox.stamp.error=0;check(md_class0_video_stream_step(&scene,&mailbox)==MD_Z80_PSG_FAULT && scene.error);
 scene=saved;scene.done=1;saved=scene;check(md_class0_video_stream_step(&scene,&mailbox)==MD_Z80_PSG_WAIT && same());
 check(md_class0_video_stream_begin(&scene,0)==MD_Z80_PSG_OK && scene.ready==1 && !scene.kind && !scene.verify && !scene.job.ready);
 scene.done=1;saved=scene;VDP_setScreenWidth320();
 check(md_class0_video_stream_begin(&scene,1)==MD_Z80_PSG_INVALID && same());VDP_setScreenWidth256();
 gaw_done=1;while(TRUE) {}return 0;
}
'''
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--variant',default='');args=parser.parse_args();assert not args.variant or re.fullmatch(r'[a-z0-9-]+',args.variant);suffix='-'+args.variant if args.variant else ''
 folder=ROOT/('validation/md-class0-stream-contract'+suffix);src=folder/'src';src.mkdir(parents=True,exist_ok=True)
 (src/'main.c').write_bytes(MAIN.encode());sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
 temp=folder/'compiler-tmp';temp.mkdir(exist_ok=True)
 for key in ['TMPDIR','TMP','TEMP']:env[key]=temp.resolve().as_posix()
 path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
 (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
 symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_z80_psg_io_libretro.dll';dll=c.CDLL(str(core));dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
 results=[]
 for region,lines in [('ntsc',262),('pal',313)]:
  observed={};events=[];dll.gaw_io_reset(0)
  def observe(frame,ram):
   count=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data()
   events.extend([[int(ptr[n*4]),(frame-1)*lines*3420+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(count)]);dll.gaw_io_reset(1)
   def val(name,width):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+i)&65535)^1] for i in range(width)),'big')
   observed.update(frame=frame,done=val('gaw_done',2),checks=val('gaw_checks',4),failures=val('gaw_failures',4))
  with contextlib.redirect_stdout(io.StringIO()):run(folder/'out/release/rom.bin',120,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
  assert observed['done'] and observed['checks']==29 and not observed['failures'],observed
  start=next(i for i,e in enumerate(events) if e[0]==3 and e[2]==0x34)
  assert not any(e[0] in (4,7) for e in events[start+1:])
  raw=json.dumps(events,separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
  results.append(dict(region=region,**observed,events_sha256=sha(raw)));print(results[-1],flush=True)
 report=dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['md_class0_video_stream.c','md_class0_video_stream.h','source_class0_video.c','source_class0_video.h','source_class0_video_assets_generated.h','md_z80_video_span.c','md_z80_video_span.h']},results=results,limits=['State order, null/misaligned input, owned conversion copies, retained WAIT token, sticky fault and pre-beam/bus rejection only. Successful physical DMA, palette blanking and deadline behavior require the separate live captures.'])
 (ROOT/('analysis/md_class0_stream_contract'+suffix.replace('-','_')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

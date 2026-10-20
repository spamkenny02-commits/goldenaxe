"""Native ownership/retention and pre-beam rejection checks for the sprite stream."""
import argparse,contextlib,ctypes as c,hashlib,io,json,os,re,subprocess
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
MAIN=r'''
#include <genesis.h>
#include "../../../megadrive/src/md_z80_video_span.c"
#include "../../../megadrive/src/source_sms_sprite8.c"
#include "../../../megadrive/src/md_sms_sprite8_stream.c"
static MdSmsSprite8Stream state,saved;
static MdZ80PsgMailbox mailbox;
static u8 sat[192];static const u32 patterns[4096]={0};
volatile u32 gaw_checks,gaw_failures;volatile u16 gaw_done;
static void check(u16 ok) {gaw_checks++;if(!ok) gaw_failures++;}
static u16 same(void) {return memcmp(&state,&saved,sizeof(state))==0;}
int main(bool reset) {
 u16 n,address;(void)reset;SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 for(n=0;n<192;n++) sat[n]=208;
 *(volatile u16*)0xc00010=0x34;
 check(md_sms_sprite8_stream_begin(0,sat,patterns,6,224,255,1024,1)==MD_Z80_PSG_INVALID);
 saved=state;check(md_sms_sprite8_stream_begin(&state,0,patterns,6,224,255,1024,1)==MD_Z80_PSG_INVALID && same());
 check(md_sms_sprite8_stream_begin(&state,sat,0,6,224,255,1024,1)==MD_Z80_PSG_INVALID && same());
 check(md_sms_sprite8_stream_begin(&state,sat,(const u32*)((const u8*)patterns+1),6,224,255,1024,1)==MD_Z80_PSG_INVALID && same());
 check(md_sms_sprite8_stream_begin(&state,sat,patterns,6,226,255,1024,1)==MD_Z80_PSG_INVALID && same());
 check(md_sms_sprite8_stream_begin(&state,sat,patterns,6,224,255,1985,1)==MD_Z80_PSG_INVALID && same());
 address=VDP_getSpriteListAddress();VDP_setSpriteListAddress(0x8000);
 check(md_sms_sprite8_stream_begin(&state,sat,patterns,6,224,255,1024,1)==MD_Z80_PSG_INVALID && same());VDP_setSpriteListAddress(address);
 VDP_setEnable(TRUE);check(md_sms_sprite8_stream_begin(&state,sat,patterns,6,224,255,1024,1)==MD_Z80_PSG_INVALID && same());VDP_setEnable(FALSE);
 VDP_setScreenWidth320();check(md_sms_sprite8_stream_begin(&state,sat,patterns,6,224,255,1024,1)==MD_Z80_PSG_INVALID && same());VDP_setScreenWidth256();
 check(md_sms_sprite8_stream_begin(&state,sat,patterns,6,224,255,1024,1)==MD_Z80_PSG_OK && state.ready && !state.frame.count);
 saved=state;check(md_sms_sprite8_stream_begin(&state,sat,patterns,6,224,255,1024,1)==MD_Z80_PSG_INVALID && same());
 check(md_sms_sprite8_stream_step(0,&mailbox)==MD_Z80_PSG_INVALID);
 check(md_sms_sprite8_stream_step(&state,0)==MD_Z80_PSG_INVALID && same());
 check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_WAIT && same());
 mailbox.stamp.ready=1;check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_INVALID && same());
 mailbox.stamp.ready=3;check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_WAIT && state.kind==2 && state.job.ready==0xd600 && state.count==4);
 saved=state;check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_WAIT && same());
 VDP_setEnable(TRUE);check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_INVALID && same());VDP_setEnable(FALSE);
 mailbox.stamp.error=1;check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_FAULT && state.error);
 mailbox.stamp.error=0;check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_FAULT);
 for(n=0;n<sizeof(state);n++) ((u8*)&state)[n]=0;
 for(n=0;n<9;n++) {sat[n]=31;sat[64+n*2]=n*8;sat[65+n*2]=n;}
 check(md_sms_sprite8_stream_begin(&state,sat,patterns,6,224,255,1024,1)==MD_Z80_PSG_OK && state.frame.count==9 && state.frame.overflow && !state.frame.rows[8]);
 check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_WAIT && state.kind==1 && state.count==4 && state.job.ready==0xd600);
 saved=state;check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_WAIT && same());
 VDP_setScreenWidth320();check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_INVALID && same());VDP_setScreenWidth256();
 check(md_sms_sprite8_stream_step(&state,&mailbox)==MD_Z80_PSG_WAIT && same());
 gaw_done=1;while(TRUE) __asm__ volatile("nop");return 0;
}
'''
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--variant',default='');args=parser.parse_args();assert not args.variant or re.fullmatch(r'[a-z0-9-]+',args.variant);suffix='-'+args.variant if args.variant else ''
 folder=ROOT/('validation/md-sms-sprite8-contract'+suffix);src=folder/'src';src.mkdir(parents=True,exist_ok=True)
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
  assert observed['done'] and observed['checks']==25 and not observed['failures'],observed
  start=next(i for i,e in enumerate(events) if e[0]==3 and e[2]==0x34)
  assert not any(e[0] in (4,7) for e in events[start+1:])
  raw=json.dumps(events,separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
  results.append(dict(region=region,**observed,events_sha256=sha(raw)));print(results[-1],flush=True)
 report=dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['md_sms_sprite8_stream.c','md_sms_sprite8_stream.h','source_sms_sprite8.c','source_sms_sprite8.h','md_z80_video_span.c','md_z80_video_span.h']},results=results,limits=['State order, null/misaligned input, owned conversion copies, retained WAIT token, sticky fault and pre-beam/bus rejection only. Successful physical clone/SAT DMA and deadline behavior require the separate live captures.'])
 (ROOT/('analysis/md_sms_sprite8_contract'+suffix.replace('-','_')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

"""Original IRQ SAT -> owned native frame -> physical MD hidden DMA."""
import contextlib,io,json,os,re,struct,subprocess
from pathlib import Path
from verify_game_sprite_frame_assets import read,records
from validate_game_sprite_frame import WRAPPER,MODULES
from validate_game_sprite_frame_68k import MAIN
from game_sprite_frame_fixture import ROOT
from md_sms_sprite8_fixture import inputs
from md_z80_source_video_fixture import convert_sms_patterns
from validate_sms_sprite8 import source_plane
from validate_sprite_scene_timed import sha
from run_core import run
EXTRA=r'''
#include "md_game_sprite_frame.h"
#include "driver.h"
extern const u32 frame_patterns[];
static MdGameSpriteFrame delivery;
static MdZ80PsgMailbox frame_mailbox;
static u8 capture_frame;
volatile u32 gaw_published,gaw_sat_base,gaw_video_jobs,gaw_video_words,gaw_video_errors,gaw_video_waits,gaw_video_contracts;
static u8 captured_video(const SourceGameSatPacket *p) {
 return !capture_frame || md_game_sprite_frame_capture(&delivery,p);
}
static u8 delivery_contracts(void) {
 SourceGameSatPacket p;u16 n;
 memset(&delivery,0,sizeof(delivery));
 if(md_game_sprite_frame_bind(&delivery,frame_patterns,FRAME_R0,FRAME_R1,FRAME_R6,1024,1)) return 0;
 for(n=0;n<192;n++) p.bytes[n]=(u8)n;
 p.first_y=0xfffffff0UL;p.first_xy=p.first_y+16215UL;
 if(!md_game_sprite_frame_capture(&delivery,&p)) return 0;
 p.bytes[0]=255;
 if(delivery.packet.bytes[0]!=0 || delivery.packet.first_y!=0xfffffff0UL || delivery.packet.first_xy!=p.first_xy) return 0;
 gaw_video_contracts++;
 if(md_game_sprite_frame_capture(&delivery,&p) || !delivery.error || delivery.accepted!=1 || delivery.packet.bytes[0]!=0) return 0;
 gaw_video_contracts++;
 if(md_game_sprite_frame_step(&delivery,&frame_mailbox)!=MD_Z80_PSG_FAULT || delivery.delivered) return 0;
 gaw_video_contracts++;
 if(md_game_sprite_frame_bind(&delivery,frame_patterns,FRAME_R0,FRAME_R1,FRAME_R6,1024,1)!=MD_Z80_PSG_INVALID || delivery.packet.bytes[0]!=0) return 0;
 gaw_video_contracts++;
 memset(&delivery,0,sizeof(delivery));
 if(md_game_sprite_frame_bind(&delivery,frame_patterns,FRAME_R0,FRAME_R1,FRAME_R6,1024,1)) return 0;
 p.first_xy++;
 if(md_game_sprite_frame_capture(&delivery,&p) || !delivery.error || delivery.accepted || delivery.pending) return 0;
 gaw_video_contracts++;memset(&delivery,0,sizeof(delivery));return 1;
}
static u8 flush_frame(void) {
 u32 guard=0;u8 status;
 while(delivery.pending && ++guard<1000000UL) {
  status=md_game_sprite_frame_step(&delivery,&frame_mailbox);
  if(status==MD_Z80_PSG_OK) gaw_video_jobs++;
  else if(status==MD_Z80_PSG_WAIT) gaw_video_waits++;
  else return 0;
 }
 gaw_video_words+=delivery.stream.readback_words;gaw_video_errors+=delivery.stream.readback_errors;
 return !delivery.pending && delivery.delivered==1 && !delivery.error;
}
'''
def physical_plane(vram,base):
 raw=bytes(vram[n^1] for n in range(65536));entries=[raw[base+n*8:base+n*8+8] for n in range(64)];out=bytearray(256*192)
 for y in range(192):
  eligible=[];index=0
  for _ in range(64):
   e=entries[index];top=(int.from_bytes(e[:2],'big')&511)-144
   if top<=y<top+8:eligible.append((e,y-top))
   link=e[3]&127
   if not link:break
   assert link<64;index=link
  for e,row in reversed(eligible[:16]):
   x=(int.from_bytes(e[6:8],'big')&511)-128;tile=int.from_bytes(e[4:6],'big')&2047;word=int.from_bytes(raw[tile*32+row*4:tile*32+row*4+4],'big')
   for column in range(8):
    xx=x+column;color=(word>>((7-column)*4))&15
    if color and 0<=xx<256:out[y*256+xx]=color
 return bytes(out),raw[base:base+512]

def main():
 prior=ROOT/'validation/game-sprite-frame-68k';folder=ROOT/'validation/md-game-sprite-frame';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
 for name in ['inputs.bin','low.bin','bank6.bin','bank12.bin','ntsc.bin','pal.bin','offsets.h','assets.s']:(src/name).write_bytes(read(prior/('src/'+name)))
 sat,patterns,regs=inputs();(src/'patterns.bin').write_bytes(convert_sms_patterns(patterns));p=src/'assets.s';p.write_bytes(p.read_bytes()+b'.global frame_patterns\nframe_patterns:\n.incbin "src/patterns.bin"\n.align 2\n')
 wrapper=WRAPPER.replace('packet->bytes[n],2)) return 0;return 1;', 'packet->bytes[n],2)) return 0;return captured_video(packet);');assert wrapper!=WRAPPER
 main=MAIN.replace('SYS_disableInts();VDP_setEnable(FALSE);', '''SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 Z80_requestBus(TRUE);if(md_z80_psg_start(&frame_mailbox,region?313:262,driver,sizeof(driver))) {gaw_failures++;gaw_kind=7;}
 gaw_sat_base=VDP_getSpriteListAddress();if(!delivery_contracts()) {gaw_failures++;gaw_kind=10;}''')
 needle='  seed(frame_inputs[row],p);';assert main.count(needle)==1
 main=main.replace(needle,'''  if(md_game_sprite_frame_bind(&delivery,frame_patterns,FRAME_R0,FRAME_R1,FRAME_R6,1024,1)) {gaw_failures++;gaw_kind=8;break;}
  capture_frame=1;'''+needle)
 needle='  memcpy(saved,ram,8192);seed(frame_inputs[row],p);';assert needle in main
 main=main.replace(needle,'''  capture_frame=0;
  /* Mutation proves the IRQ packet is owned, not a live game-RAM view. */
  memcpy(saved,ram,8192);memset(ram+0x1d40,0x3c,192);
  if(!flush_frame()) {gaw_failures++;gaw_kind=9;gaw_error=delivery.error;break;}
  gaw_published++;VDP_waitVSync();VDP_waitVSync();
  seed(frame_inputs[row],p);''')
 text='#include <genesis.h>\n#include "offsets.h"\n'+EXTRA+wrapper+main
 for key,value in zip(['FRAME_R0','FRAME_R1','FRAME_R6'],regs):text=text.replace(key,str(value))
 (src/'main.c').write_bytes(text.encode());modules=list(dict.fromkeys(MODULES+['md_game_sprite_frame','source_sms_sprite8','md_sms_sprite8_stream','md_z80_video_span','md_z80_psg_start','md_service_clock_start']))
 for name in modules:(src/(name+'.c')).write_text('#include "../../../megadrive/src/'+name+'.c"\n')
 for name in ['source_game_irq','md_game_sprite_frame']:(src/(name+'.h')).write_text('#include "../../../megadrive/src/'+name+'.h"\n')
 sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];temp=folder/'compiler-tmp';temp.mkdir(exist_ok=True)
 for key in ['TMPDIR','TMP','TEMP']:env[key]=temp.as_posix()
 asm=ROOT/'megadrive/z80/md_psg_refresh_z80.asm';built=subprocess.run([str(sdk/'bin/sjasm.exe'),str(asm),str(folder/'driver.bin'),str(folder/'driver.lst')],env=env,capture_output=True,text=True);(folder/'z80-build.log').write_text(built.stdout+built.stderr);assert not built.returncode and 'Errors: 0' in built.stdout
 (src/'driver.h').write_text('static const u8 driver[]={'+','.join(map(str,(folder/'driver.bin').read_bytes()))+'};\n')
 path=sdk.as_posix();unix='/'+path[0].lower()+path[2:];built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,(built.stdout+built.stderr)[-4000:]
 kernel=folder/'out/release/rom.bin';symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match('([0-9a-fA-F]+) [a-zA-Z] (.+)',line))};results=[]
 for region in ['ntsc','pal']:
  observed={};checked=[];ports=records(read(ROOT/('validation/game-sprite-frame/'+region+'-ports.bin')))
  def observe(frame,ram):
   def value(name,width):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+n)&65535)^1] for n in range(width)),'big')
   observed.update(frame=frame,done=value('gaw_done',2))
   for name in ['checks','failures','case','kind','error','detail','expected','actual','irqs','sat','psg','published','sat_base','video_jobs','video_words','video_errors','video_waits','video_contracts']:observed[name]=value('gaw_'+name,4)
  def video(frame,vram):
   if observed.get('published',0)==len(checked):return
   assert observed['published']==len(checked)+1,(region,observed,len(checked));index=len(checked);port=ports[index];sat=bytes(struct.unpack_from('<I',port,k+8)[0] for k in range(0,len(port),20) if struct.unpack_from('<I',port,k)[0]==2);assert len(sat)==192
   wanted,_,_=source_plane(sat,patterns,regs[0],regs[2]);actual,raw=physical_plane(vram,observed['sat_base']);assert actual==wanted,(region,index,'physical-plane')
   count=next((i for i,y in enumerate(sat[:64]) if y==208),64);assert raw[count*8:]==bytes((64-count)*8)
   checked.append(dict(case=index,frame=frame,sprites=count,plane_sha256=sha(actual),sat_sha256=sha(sat)));(folder/(region+'-'+str(index)+'-vram.bin')).write_bytes(vram)
  with contextlib.redirect_stdout(io.StringIO()):run(kernel,60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,vram_observer=video,stop_when=lambda:bool(observed.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert observed['done'] and observed['checks']==133 and not observed['failures'] and observed['published']==len(checked)==133 and not observed['video_errors'] and observed['video_contracts']==5 and observed['video_waits']>0,observed
  results.append(dict(region=region,**observed,cases=checked));print(region,{k:v for k,v in observed.items() if k not in ['sat_base']},flush=True)
 report=dict(kernel_sha256=sha(kernel.read_bytes()),kernel_bytes=kernel.stat().st_size,source_report_sha256=sha((ROOT/'analysis/game_sprite_frame_report.json').read_bytes()),sources={n+ext:sha((ROOT/'megadrive/src'/(n+ext)).read_bytes()) for n in modules for ext in ['.c','.h'] if (ROOT/'megadrive/src'/(n+ext)).exists()},results=results,limits=['All133 native original sprite/wait/IRQ compositions per region feed owned IRQ SAT into hidden bounded MD DMA. Game RAM SAT is deliberately overwritten after capture to prove ownership. Every physical VRAM sprite plane compares all49152pixels with independent original SAT/planar-pattern reference, and old SAT tails are cleared. Source PSG commands remain exact comparisons, not hardware PSG delivery in this fixture. Patterns are immutable captured input; VDP display stays disabled. No frame reveal/deadline/waveform/fullgame claim.'])
 (ROOT/'analysis/md_game_sprite_frame_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

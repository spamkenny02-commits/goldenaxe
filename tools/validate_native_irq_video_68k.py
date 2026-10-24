"""Run all288 source video vectors on68000, in six ROM shards."""
import contextlib,io,json,os,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
from validate_native_irq_video import WRAPPER
def main():
 folder=ROOT/'validation/native-irq-video';host=json.loads((ROOT/'analysis/native_irq_video_report.json').read_bytes());allcases=json.loads((folder/'cases.json').read_bytes());assert host['passed'] and len(allcases)==288
 cases=allcases
 assert sha((ROOT/'megadrive/src/source_irq_video.c').read_bytes())==host['module_sha256']['source_irq_video.c']
 array=lambda values:'{'+','.join(str(v)+'UL' for v in values)+'}';results=[]
 for shard in range(6):
  base=folder/f'kernel-{shard}';src=base/'src';src.mkdir(parents=True,exist_ok=True)
  lines=['static const u8 rom[]='+array((ROOT/'input/original.sms').read_bytes())+';', 'static const u8 sram[]='+array((folder/'sram.bin').read_bytes())+';', 'typedef struct {u8 before[8192],vram[16384],cram[32],registers[16],after_vram[16384],after_cram[32],after_registers[16];u32 output[2];} Case;','static const Case cases[]={']
  for v in cases[shard*48:(shard+1)*48]:lines.append('{'+','.join(array(v[k]) for k in ['before','vram','cram','registers','after_vram','after_cram','after_registers','output'])+'},')
  lines.append('};');(src/'expected.h').write_bytes(('\n'.join(lines)+'\n').encode())
  (src/'source_irq_video.c').write_bytes(b'#include "../../../../megadrive/src/source_irq_video.c"\n')
  (src/'wrapper.c').write_bytes(WRAPPER.replace('#include "source_irq_video.h"','#include "../../../../megadrive/src/source_irq_video.h"').encode())
  (src/'main.c').write_bytes(r'''#include <genesis.h>
#include "expected.h"
u8 video_case(const u8*,const u8*,u8*,u8*,u8*,u8*,u32*);
volatile u32 gaw_video_cases,gaw_video_failures,gaw_video_first_error;
volatile u16 gaw_video_done;
static u8 body[8192],vram[16384],cram[32],regs[16];static u32 out[2];
static void fail(u32 code){if(!gaw_video_failures)gaw_video_first_error=code;gaw_video_failures++;}
int main(bool hard_reset)
{
 u16 row;VDP_setEnable(FALSE);SYS_disableInts();
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  const Case *c=cases+row;memcpy(body,c->before,8192);memcpy(vram,c->vram,16384);memcpy(cram,c->cram,32);memcpy(regs,c->registers,16);
  if(!video_case(rom,sram,body,vram,cram,regs,out))fail(row*100+1);
  if(memcmp(vram,c->after_vram,16384))fail(row*100+2);
  if(memcmp(cram,c->after_cram,32) || memcmp(regs,c->after_registers,16))fail(row*100+3);
  if(memcmp(body,c->before,8192) || memcmp(out,c->output,8))fail(row*100+4);
  gaw_video_cases++;
 }
 gaw_video_done=1;while(TRUE);return 0;
}
'''.encode())
  sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
  built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',sdkpath,sdkunix],cwd=base,env=env,capture_output=True,text=True);(base/'build.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
  cart=base/'out/release/rom.bin';sy=symbols(base/'out/release/symbol.txt')
  for region in ['auto','pal']:
   state={}
   def observe(f,r):
    value=lambda n,size:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(size)),'big')
    state.update(frame=f,done=value('gaw_video_done',2),cases=value('gaw_video_cases',4),failures=value('gaw_video_failures',4),first_error=value('gaw_video_first_error',4))
   with contextlib.redirect_stdout(io.StringIO()):run(cart,1000,base/region,set(),[],skip_intro=False,ram_observer=observe,stop_when=lambda:bool(state.get('done')),core_options={'genesis_plus_gx_region_detect':region})
   assert state['done'] and state['cases']==48 and not state['failures'],(shard,region,state);results.append(dict(shard=shard,region=region,test_rom_sha256=sha(cart.read_bytes()),**state));print(results[-1],flush=True)
 report=dict(passed=True,source_cases=288,distinct_vectors=288,native_cases=576,results=results,module_sha256=host['module_sha256'],headers_sha256={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_irq_video.h','source_irq_context.h']},source_cases_sha256=sha((folder/'cases.json').read_bytes()),production_clock_wired=False,limits=['Dedicated68000 cartridges, physical IRQs disabled.288 source vectors in each physical region; full mirrors and output counts match host.','Not physical display pacing, byte deadlines, global boot or full campaign proof.'])
 (ROOT/'analysis/native_irq_video_68k_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
if __name__=='__main__':main()

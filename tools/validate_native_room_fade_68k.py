"""Native68000 execution of the original palette fade and live IRQ waits."""
import contextlib,io,json,os,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
from validate_native_room_fade import MODULES,WRAPPER

def main():
 folder=ROOT/'validation/native-room-fade';cases=json.loads((folder/'cases.json').read_bytes());host=json.loads((ROOT/'analysis/native_room_fade_report.json').read_bytes());assert host['passed'] and len(cases)==96
 for n,h in host['module_sha256'].items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 base=folder/'kernel';src=base/'src';src.mkdir(parents=True,exist_ok=True);rom=(ROOT/'input/original.sms').read_bytes();array=lambda values:'{'+','.join(str(v)+'UL' for v in values)+'}'
 lines=['static const u8 rom[]='+array(rom)+';', 'typedef struct {u32 phase[12];u8 refresh,body[8192];u32 expected[9];u8 after[8192];} Case;', 'static const Case cases[]={']
 for c in cases:lines.append('{'+','.join([array(c['phase']),str(c['refresh']),array(c['body']),array(c['expected']),array(c['after'])])+'},')
 lines.append('};');(src/'expected.h').write_bytes(('\n'.join(lines)+'\n').encode())
 for n in MODULES:(src/(n+'.c')).write_bytes(('#include "../../../../megadrive/src/'+n+'.c"\n').encode())
 (src/'wrapper.c').write_bytes(WRAPPER.replace('#include "source_room_reveal.h"','#include "../../../../megadrive/src/source_room_reveal.h"').encode())
 (src/'main.c').write_bytes(r'''#include <genesis.h>
#include "expected.h"
u8 fade_case(const u32*,u8,const u8*,u8*,u32*,u8*);
volatile u32 gaw_ready_cases,gaw_ready_failures,gaw_ready_first_error;
volatile u16 gaw_ready_done;
static u8 body[8192],after[8192];static u32 out[9];
static void fail(u32 code){if(!gaw_ready_failures)gaw_ready_first_error=code;gaw_ready_failures++;}
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);SYS_disableInts();
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  const Case *c=cases+row;memcpy(body,c->body,8192);
  if(!fade_case(c->phase,c->refresh,rom,body,out,after))fail(row*100+1);
  for(n=0;n<9;n++)if(out[n]!=c->expected[n])fail(row*100+2);
  if(memcmp(after,c->after,8192))fail(row*100+3);
  gaw_ready_cases++;
 }
 gaw_ready_done=1;while(TRUE);return 0;
}
'''.encode())
 sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',sdkpath,sdkunix],cwd=base,env=env,capture_output=True,text=True)
 (base/'build.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-4000:]
 cart=base/'out/release/rom.bin';sy=symbols(base/'out/release/symbol.txt');results=[]
 for region in ['auto','pal']:
  state={}
  def observe(f,r):
   value=lambda n,size:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(size)),'big')
   state.update(frame=f,done=value('gaw_ready_done',2),cases=value('gaw_ready_cases',4),failures=value('gaw_ready_failures',4),first_error=value('gaw_ready_first_error',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cart,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,stop_when=lambda:bool(state.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert state['done'] and state['cases']==96 and not state['failures'],(region,state);results.append(dict(region=region,**state));print(results[-1],flush=True)
 report=dict(passed=True,cases=96,native_cases=192,results=results,module_sha256=host['module_sha256'],headers_sha256=host['headers_sha256'],source_cases_sha256=sha((folder/'cases.json').read_bytes()),test_rom_sha256=sha(cart.read_bytes()),playable_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),production_clock_wired=False,limits=['Dedicated68000 cartridge; physical IRQs disabled, virtual source clock and live native IRQ/audio.96 source fade cases executed in each physical region. Time/M1/R and full output compared to host; only331 compact RAM,400 audio and64 palette bytes are source-checked.','Remaining body bytes compare to host parity. No physical renderer/pacing, full loader composition or complete campaign proof.'])
 (ROOT/'analysis/native_room_fade_68k_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())

if __name__=='__main__':main()

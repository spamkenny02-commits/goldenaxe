"""Execute the source-checked history and loading prefix on native68000."""
import contextlib,io,json,os,subprocess
from run_core import ROOT,run
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
 folder=ROOT/'validation/history-timed-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
 reports=[];rows=[]
 for mode,name in enumerate(['history-timed','history-prefix-timed']):
  report=json.loads((ROOT/('analysis/'+name.replace('-','_')+'_source_report.json')).read_bytes());assert report['passed'];reports.append(report)
  for n,h in report['module_sha256'].items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
  cases=json.loads((ROOT/('validation/'+name)/'cases.json').read_bytes());assert len(cases)==report['total_cases']
  for c in cases:
   before=bytes.fromhex(c['masks']);after=bytes.fromhex(c['masks_after']);assert len(set(before))==1
   changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b];assert len(changed)<=5 and all(after[i]==255 for i in changed)
   rows.append((mode,c,before[0],changed))
  wrapper=(ROOT/('validation/'+name)/'wrapper.c').read_text().replace('#include "source_room_history_timed.h"','#include "../../../megadrive/src/source_room_history_timed.h"').replace('run_history(',('run_prefix' if mode else 'run_history')+'(')
  (src/(name+'.c')).write_bytes(('#include <genesis.h>\n'+wrapper).encode())
 for name in ['source_clock','source_rng','source_rng_timed','source_room_history_timed']:
  (src/(name+'.c')).write_bytes(('#include "../../../megadrive/src/'+name+'.c"\n').encode())
 lines=['typedef struct {u32 input[6],expected[10];u8 mode,history[16],after[16],seed[2],mask,count,changed[5];} Case;','static const Case cases[]={']
 array=lambda v:'{'+','.join(str(x)+'UL' for x in v)+'}'
 for mode,c,mask,changed in rows:
  lines.append('{'+array(c['input'])+','+array(c['expected'])+','+str(mode)+','+array(bytes.fromhex(c['history']))+','+array(bytes.fromhex(c['history_after']))+','+array(bytes.fromhex(c['seed']))+','+str(mask)+','+str(len(changed))+','+array(changed+[0]*(5-len(changed)))+'},')
 lines.append('};');(src/'expected.h').write_bytes(('\n'.join(lines)+'\n').encode())
 (src/'main.c').write_bytes(r'''#include <genesis.h>
#include "expected.h"
u8 run_history(u16,u32,u8,u8,u8*,u8*,u8*,u8*,u32*);
u8 run_prefix(u16,u32,u8,u8,u8*,u8*,u8*,u8*,u32*);
volatile u32 gaw_history_cases,gaw_history_failures,gaw_history_first_error;
volatile u16 gaw_history_done;
static void fail(u32 code){if(!gaw_history_failures)gaw_history_first_error=code;gaw_history_failures++;}
int main(bool hard_reset)
{
 u32 n,out[10];u16 i,j;u8 room[2],seed[2],history[16],masks[256],expected,ok;
 VDP_setEnable(FALSE);SYS_disableInts();
 for(n=0;n<sizeof(cases)/sizeof(cases[0]);n++)
 {
  const Case *c=cases+n;
  room[0]=c->input[4];room[1]=c->input[4]>>8;seed[0]=c->input[5];seed[1]=c->input[5]>>8;
  memcpy(history,c->history,16);memset(masks,c->mask,256);memset(out,0,sizeof(out));
  ok=c->mode?run_prefix(c->input[0],c->input[1],c->input[2],c->input[3],room,seed,history,masks,out):run_history(c->input[0],c->input[1],c->input[2],c->input[3],room,seed,history,masks,out);
  if(!ok)fail(n*100+1);
  for(i=0;i<10;i++)if(out[i]!=c->expected[i])fail(n*100+10+i);
  if(memcmp(seed,c->seed,2) || memcmp(history,c->after,16))fail(n*100+2);
  for(i=0;i<256;i++)
  {
   expected=c->mask;for(j=0;j<c->count;j++)if(c->changed[j]==i)expected=255;
   if(masks[i]!=expected)fail(n*100+3);
  }
  gaw_history_cases++;
 }
 gaw_history_done=1;while(TRUE);return 0;
}
'''.encode())
 sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix],cwd=folder,env=env,capture_output=True,text=True)
 (folder/'build.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 cart=folder/'out/release/rom.bin';sy=symbols(folder/'out/release/symbol.txt');results=[]
 for region in ['auto','pal']:
  state={}
  def observe(f,r):
   value=lambda n,size:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(size)),'big')
   state.update(frame=f,done=value('gaw_history_done',2),cases=value('gaw_history_cases',4),failures=value('gaw_history_failures',4),first_error=value('gaw_history_first_error',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cart,60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,stop_when=lambda:bool(state.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert state['done'] and state['cases']==len(rows) and not state['failures'],(region,state)
  results.append(dict(region=region,**state));print(results[-1],flush=True)
 result=dict(passed=True,results=results,native_cases=len(rows)*2,module_sha256=reports[0]['module_sha256'],test_rom_sha256=sha(cart.read_bytes()),playable_rom_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),production_integrated=False,limits=['Dedicated68000 cartridge; physical interrupts disabled, source IRQs use paused563T/59M1 model.','Controlled entry phases/R; no whole-game clock propagation or gameplay RNG replacement.'])
 (ROOT/'analysis/history_timed_68k_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())

if __name__=='__main__':main()

"""Run repeat/block arithmetic parity cases on the actual SGDK68000 build."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from run_core import run
from validate_clock_repeat_fast import WRAPPER

def main():
 base=ROOT/'validation/clock-repeat-fast-68k';src=base/'src';src.mkdir(parents=True,exist_ok=True)
 cases=json.loads((ROOT/'validation/clock-repeat-fast/cases.json').read_text())
 lines=['typedef struct {u32 input[10],accepted,state[16];} Case;','static const Case cases[]={']
 for row in cases:lines.append('{{'+','.join(str(v)+'UL' for v in row['inputs'])+'},'+str(row['accepted'])+',{'+','.join(str(v)+'UL' for v in row['expected'])+'}},')
 (src/'expected.h').write_text('\n'.join(lines+['};'])+'\n')
 for name in ['source_clock','source_rng']:(src/(name+'.c')).write_text('#include "../../../megadrive/src/'+name+'.c"\n')
 reference=(ROOT/'validation/clock-repeat-fast/reference.c').read_text()
 for name in ['source_clock','source_rng']:reference=reference.replace('#include "'+name+'.h"','#include "../../../megadrive/src/'+name+'.h"')
 (src/'reference.c').write_text(reference)
 (src/'wrapper.c').write_text(WRAPPER.replace('#include "source_clock.h"','#include "../../../megadrive/src/source_clock.h"'))
 (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 repeat_pair(u16,u32,u8,u8,u8,u8,u8,u16,u8,u16,u32*);
volatile u32 gaw_repeat_cases,gaw_repeat_failures;volatile u16 gaw_repeat_done;
static u32 output[34];
int main(bool hard_reset)
{
 u16 r,n;VDP_setEnable(FALSE);
 for(r=0;r<sizeof(cases)/sizeof(cases[0]);r++)
 {
  const u32 *v=cases[r].input;
  if(!repeat_pair(v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8],v[9],output)) gaw_repeat_failures++;
  if(output[0]!=cases[r].accepted || output[1]!=cases[r].accepted) gaw_repeat_failures++;
  for(n=0;n<16;n++) if(output[2+n]!=cases[r].state[n] || output[18+n]!=cases[r].state[n]) gaw_repeat_failures++;
  gaw_repeat_cases++;
 }
 gaw_repeat_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
 sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=base,env=env,capture_output=True,text=True)
 (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2000:]
 symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};rom=base/'out/release/rom.bin';results=[]
 for region in ['auto','pal']:
  observed={}
  def observe(frame,ram):
   def get(name,size):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(size)),'big')
   observed.update(frame=frame,done=get('gaw_repeat_done',2),cases=get('gaw_repeat_cases',4),failures=get('gaw_repeat_failures',4))
  with contextlib.redirect_stdout(io.StringIO()):run(rom,20000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
  assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),observed
  results.append(dict(region=region,**observed));print(results[-1],flush=True)
 report=dict(results=results,kernel_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),cases_sha256=hashlib.sha256((ROOT/'validation/clock-repeat-fast/cases.json').read_bytes()).hexdigest(),helpers={name:hashlib.sha256((ROOT/'megadrive/src'/name).read_bytes()).hexdigest() for name in ['source_clock.c','source_clock.h']})
 (ROOT/'analysis/clock_repeat_fast_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()

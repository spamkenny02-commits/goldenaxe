"""Run the native instruction clock in a separate SGDK Mega Drive cartridge."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from validate_native_source_clock import WRAPPER
from run_core import run

def main():
 folder=ROOT/'validation/native-clock-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve();data=json.loads((ROOT/'validation/native-source-clock/cases.json').read_text());plans=data['plans'];cases=data['cases']
 lines=[]
 for n,plan in enumerate(plans):lines.append(f'static const u16 plan_{n}[]={{'+','.join(str(v) for step in plan for v in step)+'};')
 lines.append('static const u16 * const plans[]={'+','.join(f'plan_{n}' for n in range(len(plans)))+'};')
 lines.append('static const u16 lengths[]={'+','.join(str(len(p)) for p in plans)+'};')
 lines.append('typedef struct {u32 input[8];u16 plan,accepted;u32 expected[18];} ClockCase;')
 lines.append('static const ClockCase cases[]={')
 for row in cases:lines.append('{{'+','.join(f'0x{v:x}UL' for v in row['input'])+'},'+str(row['plan'])+','+str(row.get('accepted',1))+',{'+','.join(f'0x{v:x}UL' for v in row['expected'])+'}},')
 lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
 for name in ['source_clock','source_rng']:(src/f'{name}.c').write_text(f'#include "../../../megadrive/src/{name}.c"\n')
 (src/'wrapper.c').write_text(WRAPPER.replace('#include "source_clock.h"','#include "../../../megadrive/src/source_clock.h"'))
 (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 clock_case(const u32 *input,const u16 *plan,u16 length,u32 *out);
volatile u32 gaw_clock_cases,gaw_clock_failures,gaw_clock_rejections;
volatile u16 gaw_clock_done;
int main(bool hard_reset)
{
 u32 i,output[18];u16 n;u8 accepted;VDP_setEnable(FALSE);
 for(i=0;i<sizeof(cases)/sizeof(cases[0]);i++)
 {
  accepted=clock_case(cases[i].input,plans[cases[i].plan],lengths[cases[i].plan],output);
  if(accepted!=cases[i].accepted) gaw_clock_failures++;
  if(accepted) { for(n=0;n<18;n++) if(output[n]!=cases[i].expected[n]) gaw_clock_failures++; }
  else gaw_clock_rejections++;
  gaw_clock_cases++;
 }
 gaw_clock_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
 env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
 args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
 result=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr[-3000:]
 cartridge=folder/'out/release/rom.bin';symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};rows=[]
 for region in ['auto','pal']:
  observed={}
  def observe(frame,ram):
   if observed.get('done'):return
   def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
   observed.update(frame=frame,done=value('gaw_clock_done',2),cases=value('gaw_clock_cases',4),failures=value('gaw_clock_failures',4),rejections=value('gaw_clock_rejections',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cartridge,60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert observed.get('done') and (observed['cases'],observed['failures'],observed['rejections'])==(len(cases),0,5),(region,observed)
  rows.append(dict(region=region,**observed));print(region,'68000 clock execution:',observed,flush=True)
 report=dict(rows=rows,test_ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),production_ROM_changed=False,production_clock_integrated=False,limits=['Original native source_clock/source_rng C included unchanged in isolated SGDK cartridge. CPU code executed under GPG PAL/NTSC with synthetic instruction plans andconstant modeled audio IRQ work. Dynamic native RAM/audio callback,production wiring,real hardware/full game remain open.'])
 (ROOT/'analysis/native_source_clock_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

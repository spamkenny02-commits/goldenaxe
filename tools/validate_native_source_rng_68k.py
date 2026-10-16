"""Execute the native RNG C in an isolated Mega Drive test cartridge."""
import contextlib,hashlib,io,json,os,re,subprocess
from actor_reference import ROOT
from source_rng_reference import source_rng
from run_core import run

def main():
 folder=ROOT/'validation/native-rng-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve()
 expected=[source_rng(seed,0)['seed'] for seed in range(65536)]
 (src/'expected.h').write_text('static const u16 expected_seed[65536]={\n'+',\n'.join(','.join(f'0x{v:04x}' for v in expected[n:n+16]) for n in range(0,65536,16))+'\n};\n')
 (src/'source_rng.c').write_text('#include "../../../megadrive/src/source_rng.c"\n')
 (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_rng.h"
#include "expected.h"
volatile u32 gaw_rng_seed_cases,gaw_rng_output_cases,gaw_rng_refresh_cases,gaw_rng_failures;
volatile u16 gaw_rng_done;
int main(bool hard_reset)
{
 u32 seed,low,high,r,n,count;u16 highs[3]={0,0x8000,0xff00};
 const u32 wide_counts[5]={256UL,65535UL,65536UL,0x80000000UL,0xffffffffUL};
 VDP_setEnable(FALSE);
 for(seed=0;seed<65536UL;seed++) { if(source_rng_next_seed((u16)seed)!=expected_seed[seed]) gaw_rng_failures++;gaw_rng_seed_cases++; }
 for(high=0;high<3;high++) for(low=0;low<256;low++) for(r=0;r<256;r++)
 { if(source_rng_value(highs[high]|low,r)!=(r^low)) gaw_rng_failures++;gaw_rng_output_cases++; }
 for(r=0;r<256;r++) for(n=0;n<261;n++)
 { count=n<256?n:wide_counts[n-256];if(source_refresh_advance(r,count)!=((r&128)|((r+(count&127))&127))) gaw_rng_failures++;gaw_rng_refresh_cases++; }
 gaw_rng_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
 env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
 args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
 result=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr[-3000:]
 cartridge=folder/'out/release/rom.bin';symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};rows=[]
 for region in ['auto','pal']:
  observed={}
  def observe(frame,ram):
   def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
   if value('gaw_rng_done',2):
    observed.update(frame=frame,seeds=value('gaw_rng_seed_cases',4),outputs=value('gaw_rng_output_cases',4),refresh=value('gaw_rng_refresh_cases',4),failures=value('gaw_rng_failures',4))
  with contextlib.redirect_stdout(io.StringIO()):run(cartridge,1200,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert observed and (observed['seeds'],observed['outputs'],observed['refresh'],observed['failures'])==(65536,196608,66816,0),(region,observed)
  rows.append(dict(region=region,**observed));print(region,'68000 RNG execution:',observed,flush=True)
 report=dict(rows=rows,executed_68000=True,test_ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),production_ROM_changed=False,production_RNG_replaced=False,limits=['Separate test cartridge; original C source included unchanged. SGDK68000 code runs under local Genesis Plus GX PAL/NTSC. Production gameplay clock/RNG integration andphysical hardware not proved.'])
 (ROOT/'analysis/native_source_rng_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

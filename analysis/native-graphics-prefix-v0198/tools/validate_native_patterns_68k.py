"""Execute the pattern decoder and its work counters on compiled68000."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from validate_native_patterns import ROOT,Trace,decode,pattern_rle,vectors
from run_core import run

def main():
    base=ROOT/'validation/native-patterns/kernel';src=base/'src';src.mkdir(parents=True,exist_ok=True)
    rows=[];packed=bytearray()
    for stream,address in vectors():
        trace=Trace(stream);pattern_rle(trace,0,address);expected,used=decode(stream)
        digest=2166136261
        for value in expected:digest=((digest^value)*16777619)&0xffffffff
        rows.append((len(packed),used,address,trace.foreground_tstates,trace.fetches,digest));packed.extend(stream)
    (src/'expected.h').write_text('static const u8 packed[]={'+','.join(map(str,packed))+'};\n'
        'static const u32 cases[][6]={'+','.join('{'+','.join(str(v)+'UL' for v in row)+'}' for row in rows)+'};\n')
    (src/'source_pattern.c').write_text('#include "../../../../megadrive/src/source_pattern.c"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_pattern.h"
#include "expected.h"
volatile u32 gaw_pattern_cases,gaw_pattern_failures;
volatile u16 gaw_pattern_done;
static u8 output[16384];
int main(bool hard_reset)
{
 u16 row,n,mode;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(mode=0;mode<2;mode++)
  {
   SourceClockWork work;const u8 *end;u32 hash=2166136261UL;
   for(n=0;n<sizeof(output);n++) output[n]=0xa7;
   end=source_pattern_decode(packed+cases[row][0],output,cases[row][2],mode?&work:0);
   if(end!=packed+cases[row][0]+cases[row][1]) gaw_pattern_failures++;
   for(n=0;n<sizeof(output);n++) hash=(hash^output[n])*16777619UL;
   if(hash!=cases[row][5]) gaw_pattern_failures++;
   if(mode && (work.tstates!=cases[row][3] || work.fetches!=cases[row][4])) gaw_pattern_failures++;
  }
  gaw_pattern_cases++;
 }
 gaw_pattern_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2',
                          'build',sdkpath,sdkunix],cwd=base,env=env,capture_output=True,text=True)
    (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2500:]
    cartridge=base/'out/release/rom.bin'
    symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines()
             if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,raw):
            def value(name,n):return int.from_bytes(bytes(raw[(symbols[name]+i)^1] for i in range(n)),'big')
            observed.update(frame=frame,done=value('gaw_pattern_done',2),cases=value('gaw_pattern_cases',4),failures=value('gaw_pattern_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):
            run(cartridge,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and (observed['cases'],observed['failures'])==(len(rows),0),observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(cases=len(rows),results=results,
                module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_pattern.c').read_bytes()).hexdigest(),
                kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),
                limits=['Decoder bytes checked via FNV32 and source pointer; work against existing instruction model.',
                        'Does not prove live source IRQ/clock integration or full game fidelity.'])
    (ROOT/'analysis/native_patterns_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()

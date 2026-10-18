"""Exhaustive compiled68000 window-T conversion versus independent C division."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run


def main():
    folder=ROOT/'validation/pattern-window-divu';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../megadrive/src/source_pattern_clock.c"
volatile u32 gaw_window_cases,gaw_window_failures;volatile u16 gaw_window_done;
static const u32 extra[]={983024UL,983025UL,983026UL,983039UL,983040UL,0x7fffffffUL,0xffff0000UL,0xffffffffUL};
static void check(u32 master)
{
 u32 expected=master/15;if(expected>65535) expected=65535;
 if(window_ticks(master)!=expected) gaw_window_failures++;
 gaw_window_cases++;
}
int main(bool hard_reset)
{
 u32 n;VDP_setEnable(FALSE);
 for(n=0;n<=313UL*3420;n++) check(n);
 for(n=0;n<sizeof(extra)/sizeof(extra[0]);n++) check(extra[n]);
 gaw_window_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    results=[];rom=folder/'out/release/rom.bin';assert rom.stat().st_size<=4*1024*1024
    for region in ['auto','pal']:
        observed={}
        def observe(frame,ram):
            def value(name,width):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_window_done',2),cases=value('gaw_window_cases',4),failures=value('gaw_window_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):
            run(rom,20000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and observed['cases']==1070469 and not observed['failures'],observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(results=results,kernel_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_pattern_clock.c').read_bytes()).hexdigest(),
        limits=['Compiled68000 canonical private window helper versus independent general C divide-and-clamp for every master tick0..PAL period1070460 inclusive,plus saturation/32-bit boundaries. Native DIVU selected by SGDK_GCC; source-stage state/date equivalence is checked separately.'])
    (ROOT/'analysis/pattern_window_divu_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()

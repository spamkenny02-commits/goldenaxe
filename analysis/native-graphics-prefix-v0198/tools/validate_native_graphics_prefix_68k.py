"""Execute source-checked graphics prefix vectors on compiled68000 PAL/NTSC."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_graphics_prefix import MODULES,WRAPPER
from validate_native_patterns import decode

def main():
    folder=ROOT/'validation/native-graphics-prefix';cases=json.loads((folder/'cases.json').read_text())
    base=folder/'kernel';src=base/'src';src.mkdir(parents=True,exist_ok=True)
    rom=(ROOT/'input/original.sms').read_bytes();_,used=decode(rom[0x3c010:]);max_events=max(len(row['events']) for row in cases)
    lines=['static const u8 low[]={'+','.join(map(str,rom[:32768]))+'};',
           'static const u8 bank6[]={'+','.join(map(str,rom[0x18000:0x1c000]))+'};',
           'static const u8 patterns[]={'+','.join(map(str,rom[0x3c010:0x3c010+used]))+'};',
           f'typedef struct {{u32 phase[12];u8 refresh,ram[336],audio[400],after_ram[336],after_audio[400];u32 expected[19],events[{max_events}];}} PrefixCase;',
           'static const PrefixCase cases[]={']
    for row in cases:
        events=row['events']+[0]*(max_events-len(row['events']))
        lines.append('{{'+','.join(str(v)+'UL' for v in row['phase'])+'},'+str(row['refresh'])+
                     ',{'+','.join(map(str,row['ram']))+'},{'+','.join(map(str,row['audio']))+'},{'+','.join(map(str,row['expected_ram']))+
                     '},{'+','.join(map(str,row['expected_audio']))+'},{'+','.join(str(v)+'UL' for v in row['expected'])+'},{'+','.join(str(v)+'UL' for v in events)+'}},')
    lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
    for name in MODULES:(src/f'{name}.c').write_text(f'#include "../../../../megadrive/src/{name}.c"\n')
    (src/'wrapper.c').write_text(WRAPPER.replace('#include "source_pattern_clock.h"','#include "../../../../megadrive/src/source_pattern_clock.h"'))
    (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 graphics_prefix_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,const u8 *bank6,const u8 *patterns,u16 tile_count,u32 *out,u32 *events);
volatile u32 gaw_prefix_cases,gaw_prefix_failures;
volatile u16 gaw_prefix_done;
static u8 ram[336],audio[400];static u32 output[19],events[96];
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  if(!graphics_prefix_case(cases[row].phase,cases[row].refresh,ram,audio,low,bank6,patterns,0,output,events)) gaw_prefix_failures++;
  for(n=0;n<19;n++) if(output[n]!=cases[row].expected[n]) gaw_prefix_failures++;
  for(n=0;n<output[7]*6;n++) if(events[n]!=cases[row].events[n]) gaw_prefix_failures++;
  for(n=0;n<336;n++) if(ram[n]!=cases[row].after_ram[n]) gaw_prefix_failures++;
  for(n=0;n<400;n++) if(audio[n]!=cases[row].after_audio[n]) gaw_prefix_failures++;
  gaw_prefix_cases++;
 }
 gaw_prefix_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2',
                          'build',sdkpath,sdkunix],cwd=base,env=env,capture_output=True,text=True)
    (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2500:]
    cartridge=base/'out/release/rom.bin';assert cartridge.stat().st_size<=0x400000
    symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines()
             if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,raw):
            def value(name,n):return int.from_bytes(bytes(raw[(symbols[name]+i)^1] for i in range(n)),'big')
            observed.update(frame=frame,done=value('gaw_prefix_done',2),cases=value('gaw_prefix_cases',4),failures=value('gaw_prefix_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):
            run(cartridge,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(cases=len(cases),results=results,helpers={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                source_case_sha256=hashlib.sha256((folder/'cases.json').read_bytes()).hexdigest(),
                kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),production_clock_wired=False,
                limits=['Compiled68000 vectors retain source phase/R/M1/331RAM/400audio/IRQ-offset assertions; other fields are host parity.',
                        'Graphics prefix only; physical uploads/contention, all graphics classes and global entry-state propagation remain pending.'])
    (ROOT/'analysis/native_graphics_prefix_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()

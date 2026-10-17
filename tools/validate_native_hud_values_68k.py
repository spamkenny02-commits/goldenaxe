"""Replay all original HUD value/buffer vectors on compiled68000."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_hud_values import FORMAT,WRAPPER,MODULES

def main():
    folder=ROOT/'validation/native-hud-values';raw=(folder/'vectors.bin').read_bytes();assert len(raw)%FORMAT.size==0
    rows=[FORMAT.unpack_from(raw,n) for n in range(0,len(raw),FORMAT.size)]
    assert all(rows[n][3]==rows[n-1][4] for n in range(1,len(rows)))
    rom=(ROOT/'input/original.sms').read_bytes();results=[];sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    for part,start in enumerate(range(0,len(rows),1000)):
        cases=rows[start:start+1000];base=folder/f'part-{part}';src=base/'src';src.mkdir(parents=True,exist_ok=True)
        lines=['static const u8 low[]={'+','.join(map(str,rom[:32768]))+'};',
               'static const u8 bank4[]={'+','.join(map(str,rom[0x10000:0x14000]))+'};',
               'static const u8 initial[]={'+','.join(map(str,cases[0][3]))+'};',
               'typedef struct {u8 hud[16],memory[768];u32 tstates,m1;} HudCase;',
               'static const HudCase cases[]={']
        for hud,t,m1,before,after in cases:
            lines.append('{{'+','.join(map(str,hud))+'},{'+','.join(map(str,after))+'},'+str(t)+'UL,'+str(m1)+'UL},')
        lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
        for name in MODULES:(src/f'{name}.c').write_text(f'#include "../../../../megadrive/src/{name}.c"\n')
        (src/'wrapper.c').write_text(WRAPPER.replace('#include "source_room_hud.h"','#include "../../../../megadrive/src/source_room_hud.h"'))
        (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 hud_value_case(const u8 *hud,const u8 *bank4,const u8 *low,u8 *memory,u32 *out);
volatile u32 gaw_value_cases,gaw_value_failures;
volatile u16 gaw_value_done;
static u8 memory[768];static u32 output[2];
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);for(n=0;n<768;n++) memory[n]=initial[n];
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  if(!hud_value_case(cases[row].hud,bank4,low,memory,output)) gaw_value_failures++;
  if(output[0]!=cases[row].tstates || output[1]!=cases[row].m1) gaw_value_failures++;
  for(n=0;n<768;n++) if(memory[n]!=cases[row].memory[n]) gaw_value_failures++;
  gaw_value_cases++;
 }
 gaw_value_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
        env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
        built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2',
                              'build',sdkpath,sdkunix],cwd=base,env=env,capture_output=True,text=True)
        (base/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-2500:]
        cartridge=base/'out/release/rom.bin';assert cartridge.stat().st_size<=0x400000
        symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines()
                 if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
        for region in ['auto','pal']:
            observed={}
            def observe(frame,ram):
                def value(name,n):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(n)),'big')
                observed.update(frame=frame,done=value('gaw_value_done',2),cases=value('gaw_value_cases',4),failures=value('gaw_value_failures',4))
            with contextlib.redirect_stdout(io.StringIO()):
                run(cartridge,60000,base/region,set(),[],skip_intro=False,ram_observer=observe,
                    core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
            assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(part,region,observed)
            results.append(dict(part=part,region=region,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),**observed));print(part,region,observed,flush=True)
    report=dict(cases=len(rows),results=results,vector_sha256=hashlib.sha256(raw).hexdigest(),
                helpers={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                limits=['Compiled68000 all source768-byte buffer and foreground T vectors; M1 model parity. Same carry memory preserved between cases, including zero-capacity DC/DD overlap.',
                        'Isolated HUD with IRQ disabled; live phase/R/audio/IRQ coverage is the separate24-entry eleven-checkpoint chain.'])
    (ROOT/'analysis/native_hud_values_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()

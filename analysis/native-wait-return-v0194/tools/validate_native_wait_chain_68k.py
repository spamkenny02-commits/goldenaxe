"""Execute joined source double waits in one persistent68000 context."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from native_wait_return_support import MODULES,WRAPPER,CHAIN_FUNCTION,helpers


def main():
    folder=ROOT/'validation/native-wait-chain-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();cases=json.loads((ROOT/'validation/native-wait-return/chain-cases.json').read_text())
    image=(ROOT/'input/original.sms').read_bytes();max_events=max(len(row['events']) for row in cases)
    lines=['static const u8 low[]={'+','.join(map(str,image[:32768]))+'};',
           'static const u8 bank6[]={'+','.join(map(str,image[0x18000:0x1c000]))+'};',
           f'typedef struct {{u32 phase[12];u8 refresh;u16 tile_count;u8 ram[336],audio[400],after_ram[336],after_audio[400];u32 expected[18],events[{max_events}];}} ChainCase;',
           'static const ChainCase cases[]={']
    for row in cases:
        events=row['events']+[0]*(max_events-len(row['events']))
        lines.append('{{'+','.join(str(v)+'UL' for v in row['phase'])+'},'+str(row['refresh'])+','+str(row['tile_count'])+
                     ',{'+','.join(map(str,row['ram']))+'},{'+','.join(map(str,row['audio']))+'},{'+','.join(map(str,row['expected_ram']))+
                     '},{'+','.join(map(str,row['expected_audio']))+'},{'+','.join(str(v)+'UL' for v in row['expected'])+'},{'+','.join(str(v)+'UL' for v in events)+'}},')
    lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
    for name in MODULES:(src/f'{name}.c').write_text(f'#include "../../../megadrive/src/{name}.c"\n')
    (src/'wrapper.c').write_text((WRAPPER+CHAIN_FUNCTION).replace('#include "source_wait_restore.h"','#include "../../../megadrive/src/source_wait_restore.h"'))
    (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 wait_chain_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,const u8 *bank6,u16 tile_count,u16 repetitions,u32 *out,u32 *events);
volatile u32 gaw_chain_cases,gaw_chain_failures;
volatile u16 gaw_chain_done;
static u8 ram[336],audio[400];static u32 output[18],events[96];
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  if(!wait_chain_case(cases[row].phase,cases[row].refresh,ram,audio,low,bank6,cases[row].tile_count,2,output,events)) gaw_chain_failures++;
  for(n=0;n<18;n++) if(output[n]!=cases[row].expected[n]) gaw_chain_failures++;
  for(n=0;n<output[7]*6;n++) if(events[n]!=cases[row].events[n]) gaw_chain_failures++;
  for(n=0;n<336;n++) if(ram[n]!=cases[row].after_ram[n]) gaw_chain_failures++;
  for(n=0;n<400;n++) if(audio[n]!=cases[row].after_audio[n]) gaw_chain_failures++;
  gaw_chain_cases++;
 }
 gaw_chain_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
    args=[str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "EXTRA_FLAGS=-fno-inline -fno-inline-functions" -j2','build',sdkpath,sdkunix]
    built=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr[-3000:]
    cartridge=folder/'out/release/rom.bin';assert cartridge.stat().st_size<=0x400000
    symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,raw):
            def value(name,n):return int.from_bytes(bytes(raw[(symbols[name]+i)^1] for i in range(n)),'big')
            observed.update(frame=frame,done=value('gaw_chain_done',2),cases=value('gaw_chain_cases',4),failures=value('gaw_chain_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):
            run(cartridge,60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and (observed['cases'],observed['failures'])==(len(cases),0),(region,observed)
        results.append(dict(region=region,**observed));print(region,observed,'persistent native double waits exact',flush=True)
    report=dict(chains=len(cases),results=results,ROM_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),helper_sha256=helpers(),
                limits=['Compiled68000 persistent clock/RAM/audio across two joined original source waits, no intermediate source reinjection.',
                        'Same source caller phase/R/M1/331RAM/400audio/IRQ-entry checks as host. Production clock wiring/hardware/full natural progression open.'])
    (ROOT/'analysis/native_wait_chain_68k_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
